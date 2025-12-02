"""
API endpoints for file operations
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Path, Query
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
    file: UploadFile = File(..., description="File to upload")
):
    """
    Upload a file to GridFS and notify Core Service via RabbitMQ.
    
    Parameters:
    - **user_id**: User identifier
    - **file**: Binary file to upload
    
    Returns:
    - **file_id**: ObjectId of stored file
    - **status**: Upload status
    - **size**: File size in bytes
    - **filename**: Original filename
    - **content_type**: MIME type
    """
    try:
        # Read file content
        file_content = await file.read()
        
        # Upload to GridFS
        success, file_id, error = await FileService.upload_file(
            filename=file.filename,
            file_content=file_content,
            content_type=file.content_type,
            user_id=user_id
        )
        
        if not success:
            status_code = 400 if "Invalid" in error else 413 if "too large" in error else 500
            raise HTTPException(status_code=status_code, detail=error)
        
        # Publish event to RabbitMQ
        publish_file_event(
            event_type="FILE_UPLOADED",
            user_id=user_id,
            file_id=file_id,
            file_size=len(file_content)
        )
        
        return FileUploadResponse(
            file_id=file_id,
            status="uploaded",
            size=len(file_content),
            filename=file.filename,
            content_type=file.content_type
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/download/{file_id}")
async def download_file(file_id: str = Path(..., description="File ID (ObjectId)")):
    """
    Download a file from GridFS.
    
    Parameters:
    - **file_id**: MongoDB ObjectId of the file
    
    Returns:
    - Binary file stream
    """
    try:
        # Download from GridFS
        success, file_content, metadata, error = await FileService.download_file(file_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=error)
        
        # Return streaming response
        async def file_stream():
            yield file_content
        
        return StreamingResponse(
            file_stream(),
            media_type=metadata["content_type"],
            headers={"Content-Disposition": f"attachment; filename={metadata['filename']}"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise HTTPException(status_code=500, detail="Download failed")


@router.delete("/files/{file_id}", response_model=FileDeleteResponse)
async def delete_file(
    file_id: str = Path(..., description="File ID (ObjectId)"),
    user_id: str = Query(None, description="User requesting deletion (optional)")
):
    """
    Delete a file from GridFS and notify Core Service.
    
    Parameters:
    - **file_id**: MongoDB ObjectId of the file
    - **user_id**: User requesting deletion (for audit, optional)
    
    Returns:
    - Deletion status
    """
    try:
        # Delete from GridFS
        success, file_size, error = await FileService.delete_file(file_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=error)
        
        # Publish deletion event if user_id provided
        if user_id:
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
async def get_file_metadata(file_id: str = Path(..., description="File ID (ObjectId)")):
    """
    Get metadata for a file without downloading it.
    
    Parameters:
    - **file_id**: MongoDB ObjectId of the file
    
    Returns:
    - File metadata (size, name, type, owner, upload time)
    """
    try:
        # Get metadata
        success, metadata, error = await FileService.get_file_metadata(file_id)
        
        if not success:
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
