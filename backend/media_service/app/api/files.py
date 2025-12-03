"""
API endpoints for file operations with envelope encryption and streaming.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Path, Query, Depends
from fastapi.responses import StreamingResponse
import logging

from app.services.file_service import FileService
from app.services.rabbitmq_service import publish_file_event
from app.schemas.file import (
    FileUploadResponse,
    FileMetadataResponse,
    FileDeleteResponse,
    HealthCheckResponse
)
from app.utils.validators import format_file_size
from app.utils.security import get_current_user_id, verify_user_ownership

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    return HealthCheckResponse(
        status="healthy",
        service="media_service",
        mongodb="connected",
        rabbitmq="connected"
    )


@router.post("/upload/{user_id}", response_model=FileUploadResponse)
async def upload_file(
    user_id: str = Path(..., description="User ID"),
    file: UploadFile = File(..., description="File to upload"),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Upload a file to GridFS with envelope encryption and notify Core Service via RabbitMQ.
    
    **Security**: Requires valid JWT token. User can only upload files for their own user_id.
    
    **Encryption**: Files are encrypted using envelope encryption (unique File Key per file,
    wrapped by Master Key). File Key is stored encrypted in MongoDB metadata.
    
    Parameters:
    - **user_id**: User identifier (from path, must match JWT token)
    - **file**: Binary file to upload
    
    Returns:
    - **file_id**: ObjectId of stored encrypted file
    - **status**: Upload status
    - **size**: Original file size in bytes
    - **filename**: Original filename
    - **content_type**: MIME type
    """
    # Verify user ownership: token user must match path user_id
    verify_user_ownership(current_user_id, user_id)
    
    try:
        # Upload encrypted file using streaming (does not load full file into RAM)
        success, file_id, original_size, error = await FileService.upload_encrypted_file(
            user_id=user_id,
            file=file
        )
        
        if not success:
            status_code = 400 if "Invalid" in error else 413 if "too large" in error else 500
            raise HTTPException(status_code=status_code, detail=error)
        
        # Publish FILE_UPLOADED event to RabbitMQ for quota tracking
        publish_file_event(
            event_type="FILE_UPLOADED",
            user_id=user_id,
            file_id=file_id,
            file_size=original_size
        )
        
        return FileUploadResponse(
            file_id=file_id,
            status="uploaded",
            size=original_size,
            filename=file.filename,
            content_type=file.content_type
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/download/{file_id}")
async def download_file(
    file_id: str = Path(..., description="File ID (ObjectId)"),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Download and decrypt a file from GridFS.
    
    **Security**: Requires valid JWT token. Enforces ownership — users can only download
    their own files.
    
    **Decryption**: Files are decrypted on-the-fly using the File Key retrieved from
    MongoDB metadata and unwrapped with the Master Key.
    
    Parameters:
    - **file_id**: MongoDB ObjectId of the encrypted file
    
    Returns:
    - Decrypted binary file stream
    """
    try:
        # Download and decrypt file using streaming
        success, file_stream, file_info, error = await FileService.download_encrypted_file(
            file_id=file_id,
            requester_user_id=current_user_id
        )

        if not success:
            if error == "Access denied":
                raise HTTPException(status_code=403, detail=error)
            raise HTTPException(status_code=404, detail=error)
        
        return StreamingResponse(
            file_stream,
            media_type=file_info["content_type"],
            headers={"Content-Disposition": f"attachment; filename={file_info['filename']}"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise HTTPException(status_code=500, detail="Download failed")


@router.delete("/files/{file_id}", response_model=FileDeleteResponse)
async def delete_file(
    file_id: str = Path(..., description="File ID (ObjectId)"),
    user_id: str = Query(None, description="User requesting deletion"),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Delete an encrypted file from GridFS and notify Core Service.
    
    **Security**: Requires valid JWT token. User can only delete files if user_id matches their token.
    
    Parameters:
    - **file_id**: MongoDB ObjectId of the file
    - **user_id**: User requesting deletion (from query, must match JWT token)
    
    Returns:
    - Deletion status
    """
    # Verify user ownership if user_id provided
    if user_id:
        verify_user_ownership(current_user_id, user_id)
    else:
        user_id = current_user_id
    
    try:
        # Delete from GridFS (service enforces ownership)
        success, file_size, error = await FileService.delete_file(file_id, current_user_id)

        if not success:
            if error == "Access denied":
                raise HTTPException(status_code=403, detail=error)
            raise HTTPException(status_code=404, detail=error)
        
        # Publish FILE_DELETED event to RabbitMQ for quota restoration
        publish_file_event(
            event_type="FILE_DELETED",
            user_id=user_id,
            file_id=file_id,
            file_size=file_size
        )
        
        return FileDeleteResponse(
            status="deleted",
            file_id=file_id
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail="Deletion failed")


@router.get("/files/{file_id}/metadata", response_model=FileMetadataResponse)
async def get_file_metadata(
    file_id: str = Path(..., description="File ID (ObjectId)"),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get metadata for an encrypted file without downloading it.
    
    **Security**: Requires valid JWT token. Enforces ownership — users can only view
    metadata for their own files.
    
    Parameters:
    - **file_id**: MongoDB ObjectId of the file
    
    Returns:
    - File metadata (size, name, type, owner, upload time)
    """
    try:
        # Get metadata (service enforces ownership)
        success, metadata, error = await FileService.get_file_metadata(file_id, current_user_id)

        if not success:
            if error == "Access denied":
                raise HTTPException(status_code=403, detail=error)
            raise HTTPException(status_code=404, detail=error)
        
        return FileMetadataResponse(
            file_id=metadata["file_id"],
            filename=metadata["filename"],
            size=metadata["size"],
            content_type=metadata["content_type"],
            upload_date=metadata["upload_date"],
            metadata=metadata["metadata"] or {}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Metadata retrieval error: {e}")
        raise HTTPException(status_code=500, detail="Metadata retrieval failed")