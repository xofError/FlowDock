"""
API endpoints for file operations with Clean Architecture and dependency injection.
All business logic is in the application service layer.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Path, Query, Depends, Request
from fastapi.responses import StreamingResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging

from app.application.services import FileService
from app.presentation.dependencies import get_file_service, get_folder_service
from app.application.dtos import (
    FileUploadResponse,
    FileMetadataResponse,
    FileDeleteResponse,
    FileListResponse,
    HealthCheckResponse,
    UserContentResponse,
)
from app.services.sharing_service import SharingService
from datetime import datetime, timezone
import httpx
import os
from app.schemas.sharing import (
    ShareCreate,
    ShareLinkCreate,
    ShareLinkResponse,
    AccessLinkRequest,
    AccessLinkResponse,
    ShareFileResponse
)
from app.utils.validators import format_file_size
from app.utils.security import (
    create_download_token,
    get_current_user_id,
    verify_download_token,
    verify_user_ownership,
    decode_jwt_token
)
from app.models.share import Share, ShareLink
from sqlalchemy.orm import Session
import uuid
from app.database import get_db, get_mongo_db


logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# DEPENDENCY: Optional User Authentication
# ============================================================================
async def get_optional_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[str]:
    """
    FastAPI dependency for optional JWT authentication.
    Returns user_id if valid token provided, None otherwise.
    """
    if not credentials:
        return None

    payload = decode_jwt_token(credentials.credentials)

    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    return user_id


# ============================================================================
# HEALTH CHECK
# ============================================================================
@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    return HealthCheckResponse(
        status="healthy",
        service="media_service",
        mongodb="connected"
    )


# ============================================================================
# GET USER CONTENT (Consolidated: Folders + Files at root level)
# ============================================================================
@router.get("/user/{user_id}/content", response_model=UserContentResponse)
async def get_user_content(
    user_id: str = Path(..., description="User ID"),
    current_user_id: str = Depends(get_current_user_id),
    file_service: FileService = Depends(get_file_service),
    folder_service = Depends(get_folder_service),
):
    """
    Get all root-level folders and files for a user.
    
    **Security**: Requires valid JWT token. Users can only access their own content.
    
    **Parameters**:
    - **user_id**: User identifier (must match JWT token)
    
    **Returns**:
    - folders: List of root folders
    - files: List of root-level files
    - total_folders: Total folder count
    - total_files: Total file count
    """
    try:
        # Verify ownership
        if user_id != current_user_id:
            raise HTTPException(
                status_code=403,
                detail="Cannot access content for other users"
            )

        # Get root folders
        success, folders_list, error = await folder_service.list_folders(
            user_id=current_user_id,
            parent_id=None,
        )

        if not success:
            folders_list = []
            logger.warning(f"Failed to list folders for user {user_id}: {error}")

        # Get root files (explicitly pass folder_id=None to ensure only root files)
        success, files, error = await file_service.list_user_files(user_id, folder_id=None)

        if not success:
            files = []
            logger.warning(f"Failed to list files for user {user_id}: {error}")
        
        logger.info(f"[getUserContent] Retrieved {len(files) if files else 0} root files for user {user_id}")

        # Convert folders to response format
        formatted_folders = []
        if folders_list:
            for folder in folders_list:
                # folders_list already contains dicts from the service
                formatted_folders.append({
                    "folder_id": folder.get("folder_id"),
                    "name": folder.get("name"),
                    "parent_id": folder.get("parent_id"),
                    "created_at": folder.get("created_at"),
                    "updated_at": folder.get("updated_at"),
                })

        # Convert files to response format
        formatted_files = []
        if files:
            for file_info in files:
                formatted_files.append({
                    "file_id": file_info["file_id"],
                    "filename": file_info["filename"],
                    "size": file_info["size"],
                    "content_type": file_info["content_type"],
                    "upload_date": file_info["upload_date"],
                    "metadata": file_info.get("metadata", {}),
                })

        return UserContentResponse(
            folders=formatted_folders,
            files=formatted_files,
            total_folders=len(formatted_folders),
            total_files=len(formatted_files),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user content error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user content: {str(e)}")


# ============================================================================
# FILE UPLOAD
# ============================================================================
@router.post("/upload/{user_id}", response_model=FileUploadResponse)
async def upload_file(
    user_id: str = Path(..., description="User ID"),
    file: UploadFile = File(..., description="File to upload"),
    folder_id: Optional[str] = Query(None, description="Optional folder ID for file placement"),
    request: Request = None,
    current_user_id: str = Depends(get_current_user_id),
    service: FileService = Depends(get_file_service),
):
    """
    Upload a file with envelope encryption.

    **Security**: Requires valid JWT token. User can only upload files for their own user_id.

    **Encryption**: Files are encrypted using envelope encryption (unique File Key per file,
    wrapped by Master Key).

    Parameters:
    - **user_id**: User identifier (from path, must match JWT token)
    - **file**: Binary file to upload
    - **folder_id**: Optional folder ID to place file in (must be owned by user)

    Returns:
    - **file_id**: ObjectId of stored encrypted file
    - **status**: Upload status
    - **size**: Original file size in bytes
    - **filename**: Original filename
    - **content_type**: MIME type
    """
    # Verify user ownership
    verify_user_ownership(current_user_id, user_id)

    try:
        # Capture client IP address for logging
        ip_address = request.client.host if request else None
        
        logger.info(f"[upload] Starting file upload: filename='{file.filename}', size_est={file.size or 'unknown'}, user={user_id}, ip={ip_address}, folder_id={folder_id}")

        # Use injected service to upload encrypted file (now includes virus scan)
        success, file_id, original_size, error, scan_metadata = await service.upload_file_encrypted(
            user_id=user_id,
            file=file,
            ip_address=ip_address,
            folder_id=folder_id,  # NEW: Pass folder_id parameter
        )

        if not success:
            status_code = 400 if "Invalid" in error or "infected" in error.lower() else 413 if "too large" in error else 500
            logger.error(f"[upload] Upload FAILED: {file.filename}, error='{error}', status={status_code}")
            raise HTTPException(status_code=status_code, detail=error)

        # Log successful upload with scan results
        scan_status = scan_metadata.get('scan_status', 'unknown') if scan_metadata else 'unknown'
        file_hash = scan_metadata.get('hash', 'N/A')[:16] + '...' if scan_metadata and scan_metadata.get('hash') else 'N/A'
        logger.info(f"[upload] SUCCESS: filename='{file.filename}', file_id={file_id}, size={original_size}, scan_status={scan_status}, hash={file_hash}")

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
        logger.error(f"[upload] Upload error: filename='{file.filename}', error={str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# ============================================================================
# FILE DOWNLOAD
# ============================================================================
@router.get("/download/{file_id}")
async def download_file(
    file_id: str = Path(..., description="File ID (ObjectId)"),
    token: str = Query(None, description="Download token for public links"),
    current_user_id: Optional[str] = Depends(get_optional_user_id),
    service: FileService = Depends(get_file_service),
    db: Session = Depends(get_db),
):
    """
    Download and decrypt a file.

    Supports both authenticated users (via JWT) and public link access (via download token).

    **Security**:
    - For authenticated users: Requires valid JWT token and enforces ownership
    - For public links: Requires valid download token (short-lived, 1 minute)

    Parameters:
    - **file_id**: MongoDB ObjectId of the encrypted file
    - **token**: Optional download token for public link access

    Returns:
    - Decrypted binary file stream
    """
    try:
        is_authorized = False
        requester_user_id = None
        access_type = "unknown"

        # Case A: Public Link with Download Token
        if token:
            token_valid = verify_download_token(token, file_id)
            if token_valid:
                is_authorized = True
                requester_user_id = "public_link"
                access_type = "public_link"
                logger.info(f"[download] Public link access via token for file_id={file_id}")
            else:
                logger.warning(f"[download] Invalid/expired token for file_id={file_id}")

        # Case B: Logged-in User
        elif current_user_id:
            requester_user_id = current_user_id
            is_authorized = True
            access_type = "authenticated_user"
            logger.info(f"[download] User {current_user_id} requesting file_id={file_id}")

        if not is_authorized:
            logger.error(f"[download] Access denied for file_id={file_id}")
            raise HTTPException(status_code=403, detail="Permission denied")

        # If requester is logged in user, allow shared access if a direct share exists
        allow_shared = False
        if requester_user_id and requester_user_id != "public_link":
            # First, try to get metadata to verify ownership quickly
            ok, meta, err = await service.get_file_metadata(file_id=file_id, requester_user_id=requester_user_id)
            if ok:
                # requester is owner; proceed normally
                allow_shared = False
            else:
                # Not owner; check direct file shares in DB
                try:
                    import uuid
                    uid = uuid.UUID(requester_user_id)
                except Exception:
                    uid = None

                if uid:
                    share = db.query(Share).filter(
                        Share.file_id == file_id,
                        Share.shared_with_user_id == uid,
                        Share.expires_at > datetime.now(timezone.utc)
                    ).first()
                    if share:
                        allow_shared = True

                # ===== FIX 4: Check Folder Share (Inheritance) =====
                if not allow_shared and service.folder_repo:
                    try:
                        # Get the file to find its folder
                        file_meta = await service.repo.get_file_metadata(file_id)
                        
                        if file_meta and file_meta.folder_id:
                            # Check if user has access to the immediate parent folder
                            mongo_db = service.folder_repo.db
                            if mongo_db:
                                # Look for folder share
                                folder_shares = mongo_db["folder_shares"]
                                share = await folder_shares.find_one({
                                    "folder_id": file_meta.folder_id,
                                    "target_id": requester_user_id
                                })
                                if share:
                                    allow_shared = True
                                    logger.info(f"[download] User {requester_user_id} has folder share access for file {file_id}")
                    except Exception as e:
                        logger.warning(f"[download] Error checking folder share: {e}")

        # Download using injected service; allow shared access when applicable
        success, file_stream, metadata, error = await service.download_file(
            file_id=file_id,
            requester_user_id=requester_user_id,
            allow_shared=allow_shared,
        )

        if not success:
            if error == "Access denied":
                logger.warning(f"[download] Access denied for user {requester_user_id} on file_id={file_id}")
                raise HTTPException(status_code=403, detail=error)
            logger.error(f"[download] Download failed for file_id={file_id}, error={error}")
            raise HTTPException(status_code=404, detail=error)

        logger.info(f"[download] SUCCESS: file_id={file_id}, filename='{metadata['filename']}', size={metadata.get('size', 'unknown')}, access_type={access_type}")
        
        return StreamingResponse(
            file_stream,
            media_type=metadata["content_type"],
            headers={"Content-Disposition": f"attachment; filename={metadata['filename']}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[download] Unexpected error for file_id={file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Download failed")


# ============================================================================
# FILE DELETION
# ============================================================================
@router.delete("/files/{file_id}", response_model=FileDeleteResponse)
async def delete_file(
    file_id: str = Path(..., description="File ID (ObjectId)"),
    user_id: str = Query(None, description="User requesting deletion"),
    request: Request = None,
    current_user_id: str = Depends(get_current_user_id),
    service: FileService = Depends(get_file_service),
    db: Session = Depends(get_db),
):
    """
    Delete an encrypted file.

    **Security**: Requires valid JWT token. User can only delete their own files.

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
        # Capture client IP address for logging
        ip_address = request.client.host if request else None
        
        logger.info(f"[delete] Attempting to delete file_id={file_id}, user={current_user_id}, ip={ip_address}")

        # Delete using injected service
        success, file_size, error = await service.delete_file(
            file_id=file_id,
            requester_user_id=current_user_id,
            ip_address=ip_address
        )

        if not success:
            if error == "Access denied":
                logger.warning(f"[delete] Access denied for user {current_user_id} on file_id={file_id}")
                raise HTTPException(status_code=403, detail=error)
            logger.error(f"[delete] Delete failed for file_id={file_id}, error={error}")
            raise HTTPException(status_code=404, detail=error)

        # Cascade: Delete all shares for this file
        try:
            shares_deleted = db.query(Share).filter(Share.file_id == file_id).delete()
            db.commit()
            if shares_deleted > 0:
                logger.info(f"[delete] CASCADE: Deleted {shares_deleted} share(s) for file {file_id}")
        except Exception as share_error:
            logger.warning(f"[delete] Failed to cascade delete shares for file {file_id}: {share_error}")
            db.rollback()

        logger.info(f"[delete] SUCCESS: file_id={file_id}, size_freed={file_size} bytes")
        
        return FileDeleteResponse(
            status="deleted",
            file_id=file_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[delete] Unexpected error for file_id={file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Deletion failed")


# ============================================================================
# RESTORE FILE (From Trash)
# ============================================================================
@router.post("/files/{file_id}/restore")
async def restore_file(
    file_id: str = Path(..., description="File ID (ObjectId)"),
    request: Request = None,
    current_user_id: str = Depends(get_current_user_id),
    service: FileService = Depends(get_file_service),
):
    """
    Restore a soft-deleted file from trash.

    **Security**: Requires valid JWT token. User can only restore their own deleted files.

    Parameters:
    - **file_id**: MongoDB ObjectId of the deleted file

    Returns:
    - Restoration status
    """
    try:
        # Capture client IP address for logging
        ip_address = request.client.host if request else None
        
        logger.info(f"[restore] Attempting to restore file_id={file_id}, user={current_user_id}, ip={ip_address}")

        # Restore using injected service
        success, error = await service.restore_file(
            file_id=file_id,
            requester_user_id=current_user_id,
            ip_address=ip_address
        )

        if not success:
            if error == "Access denied":
                logger.warning(f"[restore] Access denied for user {current_user_id} on file_id={file_id}")
                raise HTTPException(status_code=403, detail=error)
            logger.error(f"[restore] Restore failed for file_id={file_id}, error={error}")
            raise HTTPException(status_code=404, detail=error)

        logger.info(f"[restore] SUCCESS: file_id={file_id}")
        
        return {
            "status": "restored",
            "file_id": file_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[restore] Unexpected error for file_id={file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Restoration failed")


# ============================================================================
# PERMANENTLY DELETE FILE (From Trash - Hard Delete)
# ============================================================================
@router.delete("/files/{file_id}/permanent")
async def permanently_delete_file(
    file_id: str = Path(..., description="File ID (ObjectId)"),
    request: Request = None,
    current_user_id: str = Depends(get_current_user_id),
    service: FileService = Depends(get_file_service),
    db: Session = Depends(get_db),
):
    """
    Permanently delete a soft-deleted file from trash (hard delete).

    **Security**: Requires valid JWT token. User can only permanently delete their own files.

    Parameters:
    - **file_id**: MongoDB ObjectId of the file to permanently delete

    Returns:
    - Permanent deletion status
    """
    try:
        # Capture client IP address for logging
        ip_address = request.client.host if request else None
        
        logger.info(f"[permanent_delete] Attempting to permanently delete file_id={file_id}, user={current_user_id}, ip={ip_address}")

        # Get file metadata to verify ownership and get GridFS ID
        file = await service.repo.get_file_metadata(file_id)
        if not file:
            logger.error(f"[permanent_delete] File not found: {file_id}")
            raise HTTPException(status_code=404, detail="File not found")

        if file.owner_id != current_user_id:
            logger.warning(f"[permanent_delete] Access denied for user {current_user_id} on file_id={file_id}")
            raise HTTPException(status_code=403, detail="Access denied")

        # Hard delete from GridFS (both file and metadata chunks)
        success = await service.repo.delete_file_from_gridfs(file_id)
        if not success:
            logger.error(f"[permanent_delete] Failed to delete from GridFS: {file_id}")
            raise HTTPException(status_code=500, detail="Failed to permanently delete file")

        # Update user quota (file no longer exists)
        try:
            # This would integrate with quota service if available
            logger.info(f"[permanent_delete] File quota would be updated for user {current_user_id}")
        except Exception as quota_err:
            logger.warning(f"[permanent_delete] Failed to update quota: {quota_err}")

        # Log activity
        if service.activity_logger:
            await service.activity_logger.log_activity(
                current_user_id,
                "FILE_PERMANENTLY_DELETE",
                {
                    "file_id": file_id,
                    "filename": file.filename,
                    "size": file.size,
                },
                ip_address,
            )

        # Cascade: Delete all shares for this file
        try:
            shares_deleted = db.query(Share).filter(Share.file_id == file_id).delete()
            db.commit()
            if shares_deleted > 0:
                logger.info(f"[permanent_delete] CASCADE: Deleted {shares_deleted} share(s) for file {file_id}")
        except Exception as share_error:
            logger.warning(f"[permanent_delete] Failed to cascade delete shares for file {file_id}: {share_error}")
            db.rollback()

        logger.info(f"[permanent_delete] SUCCESS: file_id={file_id}, size_freed={file.size} bytes")
        
        return {
            "status": "permanently_deleted",
            "file_id": file_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[permanent_delete] Unexpected error for file_id={file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Permanent deletion failed")


# ============================================================================
# GET TRASH (Soft-Deleted Files)
# ============================================================================
@router.get("/trash/{user_id}")
async def get_trash(
    user_id: str = Path(..., description="User ID"),
    request: Request = None,
    current_user_id: str = Depends(get_current_user_id),
    service: FileService = Depends(get_file_service),
):
    """
    Get list of soft-deleted files (trash) for a user.

    **Security**: Requires valid JWT token. Users can only view their own trash.

    Parameters:
    - **user_id**: User identifier

    Returns:
    - List of deleted files in trash
    """
    # Verify user ownership
    verify_user_ownership(current_user_id, user_id)
    
    try:
        # Capture client IP address for logging
        ip_address = request.client.host if request else None
        
        logger.info(f"[trash] Retrieving trash for user {user_id}")

        # Query MongoDB directly for deleted files only
        mongo_db = service.folder_repo.db if hasattr(service, 'folder_repo') and hasattr(service.folder_repo, 'db') else None
        
        if mongo_db is not None:
            fs_files = mongo_db.get_collection("fs.files")
            query = {
                "metadata.owner": user_id,
                "metadata.is_deleted": True
            }
            # Use await to convert async cursor to list
            cursor = fs_files.find(query).sort("uploadDate", -1)
            docs = await cursor.to_list(None)
            
            trash_files = []
            for doc in docs:
                meta = doc.get("metadata", {})
                trash_files.append({
                    "file_id": str(doc["_id"]),
                    "name": doc.get("filename", ""),
                    "filename": doc.get("filename", ""),
                    "size": doc.get("length", 0),
                    "deleted_at": meta.get("deleted_at"),
                    "uploaded_at": doc.get("uploadDate"),
                    "content_type": meta.get("contentType", ""),
                })
            
            logger.info(f"[trash] Found {len(trash_files)} deleted files for user {user_id}")
            
            # Log activity
            if service.activity_logger:
                await service.activity_logger.log_activity(
                    current_user_id,
                    "TRASH_VIEW",
                    {
                        "trash_count": len(trash_files),
                    },
                    ip_address,
                )
            
            return {
                "trash": trash_files,
                "total": len(trash_files)
            }
        
        logger.warning(f"[trash] MongoDB not available")
        
        # Log activity even if MongoDB is not available
        if service.activity_logger:
            await service.activity_logger.log_activity(
                current_user_id,
                "TRASH_VIEW",
                {
                    "trash_count": 0,
                    "error": "MongoDB not available",
                },
                ip_address,
            )
        
        return {
            "trash": [],
            "total": 0
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[trash] Error retrieving trash for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve trash")


# ============================================================================
# MOVE FILE
# ============================================================================
@router.patch("/files/{file_id}/move", response_model=FileMetadataResponse)
async def move_file(
    file_id: str = Path(..., description="File ID (ObjectId)"),
    folder_id: str = Query(..., description="Destination folder ID"),
    current_user_id: str = Depends(get_current_user_id),
    service: FileService = Depends(get_file_service),
):
    """
    Move a file to a different folder.

    **Security**: Requires valid JWT token. User can only move their own files.

    Parameters:
    - **file_id**: MongoDB ObjectId of the file
    - **folder_id**: MongoDB ObjectId of the destination folder

    Returns:
    - Updated file metadata
    """
    try:
        file_id = file_id.strip()
        folder_id = folder_id.strip()

        success, error = await service.move_file(
            file_id=file_id,
            new_folder_id=folder_id,
            user_id=current_user_id,
        )

        if not success:
            if error == "File not found or access denied":
                raise HTTPException(status_code=403, detail=error)
            raise HTTPException(status_code=400, detail=error)

        # Get updated file metadata to return full response
        success, file_dict, error = await service.get_file_metadata(file_id, current_user_id)
        if success:
            return FileMetadataResponse(**file_dict)
        else:
            raise HTTPException(status_code=500, detail="Failed to retrieve moved file")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Move file error: {e}")
        raise HTTPException(status_code=500, detail="Move file failed")


# ============================================================================
# FILE METADATA
# ============================================================================
@router.get("/files/{file_id}/metadata", response_model=FileMetadataResponse)
async def get_file_metadata(
    file_id: str = Path(..., description="File ID (ObjectId)"),
    current_user_id: str = Depends(get_current_user_id),
    service: FileService = Depends(get_file_service),
):
    """
    Get metadata for a file without downloading it.

    **Security**: Requires valid JWT token. Enforces ownership.

    Parameters:
    - **file_id**: MongoDB ObjectId of the file

    Returns:
    - File metadata (size, name, type, owner, upload time)
    """
    try:
        # Get metadata using injected service
        success, metadata, error = await service.get_file_metadata(
            file_id=file_id,
            requester_user_id=current_user_id
        )

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
            metadata=metadata.get("metadata", {})
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Metadata retrieval error: {e}")
        raise HTTPException(status_code=500, detail="Metadata retrieval failed")


# ============================================================================
# LIST USER FILES
# ============================================================================
@router.get("/user/{user_id}/files", response_model=list[FileMetadataResponse])
async def list_user_files(
    user_id: str = Path(..., description="User ID"),
    current_user_id: str = Depends(get_current_user_id),
    service: FileService = Depends(get_file_service),
):
    """
    List all files uploaded by a user.

    **Security**: Requires valid JWT token. Users can only list their own files.

    Parameters:
    - **user_id**: User identifier (must match JWT token)

    Returns:
    - List of FileMetadataResponse objects
    """
    try:
        # Verify ownership
        if user_id != current_user_id:
            logger.warning(f"[list_user_files] Unauthorized list attempt: user {current_user_id} tried to list files for {user_id}")
            raise HTTPException(
                status_code=403,
                detail="Cannot list files for other users"
            )

        logger.info(f"[list_user_files] Listing files for user {user_id}")

        # List files using injected service
        success, files, error = await service.list_user_files(user_id)

        if not success:
            logger.error(f"[list_user_files] Failed to list files for user {user_id}: {error}")
            raise HTTPException(status_code=500, detail=error or "Failed to list files")

        # Convert to response models
        response_files = []
        for file_info in files:
            response_files.append(
                FileMetadataResponse(
                    file_id=file_info["file_id"],
                    filename=file_info["filename"],
                    size=file_info["size"],
                    content_type=file_info["content_type"],
                    upload_date=file_info["upload_date"],
                    metadata=file_info.get("metadata", {})
                )
            )

        logger.info(f"[list_user_files] SUCCESS: Retrieved {len(response_files)} files for user {user_id}")
        return response_files

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[list_user_files] Unexpected error for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list files")


# ============================================================================
# SHARING QUERY ENDPOINTS
# ============================================================================

@router.get("/users/{user_id}/files/shared-with-me")
async def get_files_shared_with_user(
    user_id: str = Path(..., description="User ID"),
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    file_service: FileService = Depends(get_file_service),
):
    """
    Get all files that have been shared with the user by others.

    Returns list of direct shares (not public links) with file metadata.

    **Security**: Requires valid JWT token. Users can only view shares intended for them.
    """
    # Verify the requester is viewing their own shares
    if user_id != current_user_id:
        raise HTTPException(
            status_code=403,
            detail="Cannot view shares for other users"
        )

    try:
        try:
            uid = uuid.UUID(user_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid user_id")

        shares = db.query(Share).filter(Share.shared_with_user_id == uid).all()

        result = []
        for share in shares:
            # Fetch file metadata to get actual file name
            file_name = "Unknown"
            try:
                ok, metadata, err = await file_service.get_file_metadata(share.file_id, requester_user_id=current_user_id, allow_shared=True)
                if ok and metadata:
                    file_name = metadata.get("filename", "Unknown")
            except Exception as e:
                logger.warning(f"Failed to fetch metadata for file {share.file_id}: {e}")
            
            result.append({
                "share_id": str(share.id),
                "file_id": share.file_id,
                "file_name": file_name,
                "shared_by_user_id": str(share.shared_by_user_id),
                "permission": share.permission,
                "expires_at": share.expires_at,
                "created_at": share.created_at
            })

        return result
    except Exception as e:
        logger.error(f"Get shared files error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve shared files")


@router.get("/users/{user_id}/files/shared-by-me")
async def get_files_shared_by_user(
    user_id: str = Path(..., description="User ID"),
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    file_service: FileService = Depends(get_file_service),
):
    """
    Get all files that the user has shared with others (direct shares).

    Returns list of direct shares created by this user (not public links) with file metadata.

    **Security**: Requires valid JWT token. Users can only view shares they created.
    """
    # Verify the requester owns these shares
    if user_id != current_user_id:
        raise HTTPException(
            status_code=403,
            detail="Cannot view shares created by other users"
        )

    try:
        try:
            uid = uuid.UUID(user_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid user_id")

        shares = db.query(Share).filter(Share.shared_by_user_id == uid).all()

        result = []
        for share in shares:
            # Fetch file metadata to get actual file name
            file_name = "Unknown"
            try:
                ok, metadata, err = await file_service.get_file_metadata(share.file_id, requester_user_id=current_user_id)
                if ok and metadata:
                    file_name = metadata.get("filename", "Unknown")
            except Exception as e:
                logger.warning(f"Failed to fetch metadata for file {share.file_id}: {e}")
            
            result.append({
                "share_id": str(share.id),
                "file_id": share.file_id,
                "file_name": file_name,
                "shared_with_user_id": str(share.shared_with_user_id),
                "permission": share.permission,
                "expires_at": share.expires_at,
                "created_at": share.created_at
            })

        return result
    except Exception as e:
        logger.error(f"Get user's shared files error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve shared files")



@router.get("/users/{user_id}/share-links")
async def get_user_share_links(
    user_id: str = Path(..., description="User ID"),
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get all public share links created by the user.

    Returns list of public share links and their metadata.

    **Security**: Requires valid JWT token. Users can only view links they created.
    """
    # Verify the requester owns these links
    if user_id != current_user_id:
        raise HTTPException(
            status_code=403,
            detail="Cannot view share links created by other users"
        )

    try:
        try:
            uid = uuid.UUID(user_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid user_id")

        links = db.query(ShareLink).filter(ShareLink.created_by_user_id == uid).all()

        result = []
        for link in links:
            result.append({
                "id": str(link.id),
                "file_id": link.file_id,
                "token": link.token,
                "has_password": bool(link.password_hash),
                "expires_at": link.expires_at,
                "max_downloads": link.max_downloads,
                "downloads_used": link.downloads_used,
                "active": link.active,
                "created_at": link.created_at,
                "link_url": f"https://localhost:8001/s/{link.token}"
            })

        return result
    except Exception as e:
        logger.error(f"Get user's share links error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve share links")


# ============================================================================
# FILE SHARING ENDPOINTS
# ============================================================================

@router.post("/share/user", response_model=ShareFileResponse)
async def share_file_with_user(
    data: ShareCreate,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """Share a file with a specific user by email"""
    try:
        # Verify the requester actually owns the file before creating share
        service = await get_file_service()
        ok, metadata, err = await service.get_file_metadata(data.file_id, requester_user_id=current_user_id)
        if not ok:
            raise HTTPException(status_code=403, detail="Only file owner can create shares")

        # Look up owner email from Auth Service for record-keeping
        auth_service_url = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
        owner_email = None
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(f"{auth_service_url}/api/users/{current_user_id}", timeout=5.0)
                if r.status_code == 200:
                    owner_email = r.json().get("email")
        except Exception:
            owner_email = None

        share = await SharingService.share_file(
            db,
            owner_id=current_user_id,
            owner_email=owner_email or "",
            data=data,
        )

        return ShareFileResponse(
            status="shared",
            file_id=data.file_id,
            target=data.target_email
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Share file error: {e}")
        raise HTTPException(status_code=500, detail="Failed to share file")


@router.post("/share/link", response_model=ShareLinkResponse)
async def create_public_share_link(
    data: ShareLinkCreate,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """Create a public share link for a file"""
    try:
        # Verify requester owns the file before creating a public link
        service = await get_file_service()
        ok, metadata, err = await service.get_file_metadata(data.file_id, requester_user_id=current_user_id)
        if not ok:
            raise HTTPException(status_code=403, detail="Only file owner can create share links")

        link = SharingService.create_link(db, current_user_id, data)

        # Return fields matching `ShareLinkResponse` schema
        return ShareLinkResponse(
            short_code=link.token,
            link_url=f"http://localhost:8001/media/s/{link.token}/access",
            expires_at=link.expires_at,
            has_password=bool(link.password_hash),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create share link error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create share link")


# ============================================================================
# REVOKE FILE SHARE
# ============================================================================
@router.delete("/shares/{share_id}")
async def revoke_share(
    share_id: str = Path(..., description="Share ID to revoke (UUID for files, ObjectId for folders)"),
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Revoke a share (file or folder) by removing the share record.
    
    [FIX: Unified Share Revocation]
    Handles BOTH file and folder shares:
    - File shares: UUID format (SQL-based)
    - Folder shares: MongoDB ObjectId format
    
    Security:
    - ONLY the owner (shared_by_user_id) can revoke the share
    - Recipients CANNOT revoke shares
    
    Parameters:
    - **share_id**: UUID for files, hex ObjectId for folders
    
    Returns:
    - Success message if share was revoked
    """
    try:
        import re
        
        share_id = share_id.strip()
        
        # [FIX] Detect share type by ID format
        # File shares: UUID (8-4-4-4-12 hex with dashes)
        # Folder shares: 24-character hex without dashes (MongoDB ObjectId)
        is_uuid = re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', 
                          share_id, re.IGNORECASE)
        is_objectid = re.match(r'^[0-9a-f]{24}$', share_id, re.IGNORECASE)
        
        if is_uuid:
            # FILE share revocation (SQL)
            logger.info(f"[revoke-share] Detected FILE share (UUID): {share_id[:10]}...")
            try:
                share_uuid = uuid.UUID(share_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid file share ID format")
            
            # Find the share
            share = db.query(Share).filter(Share.id == share_uuid).first()
            
            if not share:
                raise HTTPException(status_code=404, detail="File share not found")
            
            # Security: ONLY the owner can revoke
            if str(share.shared_by_user_id) != current_user_id:
                logger.warning(f"[revoke-share] User {current_user_id} not authorized to revoke file share {share_id} (owner: {share.shared_by_user_id})")
                raise HTTPException(status_code=403, detail="Only the share owner can revoke this share")
            
            # Delete the share
            db.delete(share)
            db.commit()
            
            logger.info(f"[revoke-share] Revoked FILE share {share_id[:10]}... by {current_user_id}")
            
            return {
                "status": "revoked",
                "share_id": share_id,
                "share_type": "file",
                "message": "File share has been revoked successfully"
            }
        
        elif is_objectid:
            # FOLDER share revocation (MongoDB)
            logger.info(f"[revoke-share] Detected FOLDER share (ObjectId): {share_id[:10]}...")
            
            from bson import ObjectId as BsonObjectId
            
            # Get mongo DB and folder_shares collection (where folder shares are stored)
            mongo_db = get_mongo_db()
            shares_collection = mongo_db["folder_shares"]
            
            try:
                # Find the share by its MongoDB _id
                share_doc = await shares_collection.find_one({"_id": BsonObjectId(share_id)})
                
                if not share_doc:
                    logger.warning(f"[revoke-share] Folder share not found: {share_id}")
                    raise HTTPException(status_code=404, detail="Folder share not found")
                
                # Security: ONLY the owner (shared_by field) can revoke
                if str(share_doc.get("shared_by", "")) != current_user_id:
                    logger.warning(f"[revoke-share] User {current_user_id} not authorized to revoke folder share {share_id} (owner: {share_doc.get('shared_by')})")
                    raise HTTPException(status_code=403, detail="Only the share owner can revoke this share")
                
                # Delete the share by its _id
                result = await shares_collection.delete_one({"_id": BsonObjectId(share_id)})
                
                if result.deleted_count == 0:
                    raise HTTPException(status_code=500, detail="Failed to revoke folder share")
                
                logger.info(f"[revoke-share] Revoked FOLDER share {share_id[:10]}... by {current_user_id}")
                
                return {
                    "status": "revoked",
                    "share_id": share_id,
                    "share_type": "folder",
                    "message": "Folder share has been revoked successfully"
                }
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"[revoke-share] Error revoking folder share: {e}")
                raise HTTPException(status_code=500, detail="Failed to revoke folder share")
        
        else:
            raise HTTPException(status_code=400, detail="Invalid share ID format (must be UUID or ObjectId)")
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"[revoke-share] Error revoking share: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to revoke share")


# ============================================================================
# PUBLIC LINK MANAGEMENT
# ============================================================================
@router.get("/files/{file_id}/public-links")
async def get_file_public_links(
    file_id: str = Path(..., description="File ID"),
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get all public links for a file.
    
    Security:
    - Only the file owner can retrieve public links for their file
    
    Parameters:
    - **file_id**: ID of the file
    
    Returns:
    - List of public links with metadata
    """
    try:
        service = await get_file_service()
        # Verify requester owns the file
        ok, metadata, err = await service.get_file_metadata(file_id, requester_user_id=current_user_id)
        if not ok:
            raise HTTPException(status_code=403, detail="Only file owner can view public links")
        
        # Query public links for this file
        links = db.query(ShareLink).filter(
            ShareLink.file_id == file_id,
            ShareLink.created_by_user_id == current_user_id
        ).all()
        
        # Format response
        return [{
            "id": str(link.id),
            "short_code": link.token,
            "file_id": link.file_id,
            "created_at": link.created_at.isoformat() if link.created_at else None,
            "expires_at": link.expires_at.isoformat() if link.expires_at else None,
            "has_password": bool(link.password_hash),
            "max_downloads": link.max_downloads,
            "downloads_used": link.downloads_used,
            "active": link.active
        } for link in links]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get file public links error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve public links")


@router.get("/users/{user_id}/public-links")
async def get_user_public_links(
    user_id: str = Path(..., description="User ID"),
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get all public links created by a user.
    
    Security:
    - Users can only view their own public links
    
    Parameters:
    - **user_id**: ID of the user
    
    Returns:
    - List of all public links created by the user
    """
    try:
        # Security: Users can only view their own links
        if user_id != current_user_id:
            raise HTTPException(status_code=403, detail="You can only view your own public links")
        
        # Query all public links created by user
        links = db.query(ShareLink).filter(
            ShareLink.created_by_user_id == user_id
        ).all()
        
        # Format response
        return [{
            "id": str(link.id),
            "short_code": link.token,
            "file_id": link.file_id,
            "created_at": link.created_at.isoformat() if link.created_at else None,
            "expires_at": link.expires_at.isoformat() if link.expires_at else None,
            "has_password": bool(link.password_hash),
            "max_downloads": link.max_downloads,
            "downloads_used": link.downloads_used,
            "active": link.active
        } for link in links]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user public links error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve public links")


@router.delete("/share-links/{link_id}")
async def delete_public_link(
    link_id: str = Path(..., description="Public link ID to delete"),
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Delete a public link by marking it as inactive.
    
    Security:
    - Only the user who created the link can delete it
    
    Parameters:
    - **link_id**: UUID of the public link to delete
    
    Returns:
    - Success message
    """
    try:
        # Convert link_id to UUID
        try:
            link_uuid = uuid.UUID(link_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid link ID format")
        
        # Find the link
        link = db.query(ShareLink).filter(ShareLink.id == link_uuid).first()
        
        if not link:
            raise HTTPException(status_code=404, detail="Public link not found")
        
        # Security: Verify the requester created the link
        if str(link.created_by_user_id) != current_user_id:
            raise HTTPException(status_code=403, detail="You don't have permission to delete this link")
        
        # Mark as inactive instead of deleting (preserves history)
        link.active = False
        db.commit()
        
        logger.info(f"✓ Public link {link_id} deactivated by {current_user_id}")
        
        return {
            "status": "deleted",
            "link_id": link_id,
            "message": "Public link has been deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Delete public link error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete public link")


@router.patch("/share-links/{link_id}/extend-expiry")
async def extend_public_link_expiry(
    link_id: str = Path(..., description="Public link ID"),
    new_expiry: datetime = Query(..., description="New expiry date (ISO format)"),
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Extend the expiry date of a public link.
    
    Security:
    - Only the user who created the link can extend it
    
    Parameters:
    - **link_id**: UUID of the public link
    - **new_expiry**: New expiry date in ISO format
    
    Returns:
    - Updated link metadata
    """
    try:
        from datetime import timezone
        
        # Convert link_id to UUID
        try:
            link_uuid = uuid.UUID(link_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid link ID format")
        
        # Find the link
        link = db.query(ShareLink).filter(ShareLink.id == link_uuid).first()
        
        if not link:
            raise HTTPException(status_code=404, detail="Public link not found")
        
        # Security: Verify the requester created the link
        if str(link.created_by_user_id) != current_user_id:
            raise HTTPException(status_code=403, detail="You don't have permission to modify this link")
        
        # Validate new expiry is in the future
        if new_expiry.tzinfo is None:
            new_expiry = new_expiry.replace(tzinfo=timezone.utc)
        
        if new_expiry <= datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Expiry date must be in the future")
        
        # Update expiry
        link.expires_at = new_expiry
        db.commit()
        
        logger.info(f"✓ Public link {link_id} expiry extended by {current_user_id}")
        
        return {
            "id": str(link.id),
            "short_code": link.token,
            "file_id": link.file_id,
            "created_at": link.created_at.isoformat() if link.created_at else None,
            "expires_at": link.expires_at.isoformat() if link.expires_at else None,
            "has_password": bool(link.password_hash),
            "max_downloads": link.max_downloads,
            "downloads_used": link.downloads_used,
            "active": link.active,
            "message": "Expiry date updated successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Extend public link expiry error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to extend public link expiry")


@router.patch("/share-links/{link_id}/update-download-limit")
async def update_public_link_download_limit(
    link_id: str = Path(..., description="Public link ID"),
    max_downloads: int = Query(..., description="New maximum download limit (0 for unlimited)"),
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Update the download limit of a public link.
    
    Security:
    - Only the user who created the link can update it
    
    Parameters:
    - **link_id**: UUID of the public link
    - **max_downloads**: New maximum downloads (0 for unlimited)
    
    Returns:
    - Updated link metadata
    """
    try:
        # Convert link_id to UUID
        try:
            link_uuid = uuid.UUID(link_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid link ID format")
        
        # Find the link
        link = db.query(ShareLink).filter(ShareLink.id == link_uuid).first()
        
        if not link:
            raise HTTPException(status_code=404, detail="Public link not found")
        
        # Security: Verify the requester created the link
        if str(link.created_by_user_id) != current_user_id:
            raise HTTPException(status_code=403, detail="You don't have permission to modify this link")
        
        # Validate max_downloads
        if max_downloads < 0:
            raise HTTPException(status_code=400, detail="Maximum downloads must be 0 or greater")
        
        # If reducing limit below current usage, reject
        if max_downloads > 0 and max_downloads < link.downloads_used:
            raise HTTPException(status_code=400, detail="Cannot set limit below current download count")
        
        # Update download limit
        link.max_downloads = max_downloads
        db.commit()
        
        logger.info(f"✓ Public link {link_id} download limit updated by {current_user_id}")
        
        return {
            "id": str(link.id),
            "short_code": link.token,
            "file_id": link.file_id,
            "created_at": link.created_at.isoformat() if link.created_at else None,
            "expires_at": link.expires_at.isoformat() if link.expires_at else None,
            "has_password": bool(link.password_hash),
            "max_downloads": link.max_downloads,
            "downloads_used": link.downloads_used,
            "active": link.active,
            "message": "Download limit updated successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Update public link download limit error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update public link download limit")


@router.get("/s/{token}/metadata")
async def get_public_link_file_metadata(
    token: str = Path(..., description="Share link token"),
    password: str = Query(None, description="Password if link is protected"),
    db: Session = Depends(get_db),
    file_service: FileService = Depends(get_file_service),
):
    """
    Get file metadata for a public link (without downloading).
    
    Used by PublicLink.jsx page to display file information.
    No authentication required - anyone with valid token can access metadata.
    
    Parameters:
    - **token**: Share link token from the URL
    - **password**: Optional password if link is protected
    
    Returns:
    - File metadata (name, size, type, etc.)
    """
    try:
        # 1. Find the share link
        share_link = db.query(ShareLink).filter(ShareLink.token == token).first()
        
        if not share_link:
            raise HTTPException(status_code=404, detail="Share link not found")
        
        # 2. Verify link is active
        if not share_link.active:
            raise HTTPException(status_code=410, detail="Share link is no longer active")
        
        # 3. Verify not expired
        if share_link.expires_at and datetime.now(timezone.utc) > share_link.expires_at:
            raise HTTPException(status_code=410, detail="Share link has expired")
        
        # 4. Verify download limit not exceeded
        if share_link.max_downloads > 0 and share_link.downloads_used >= share_link.max_downloads:
            raise HTTPException(status_code=410, detail="Download limit exceeded")
        
        # 5. Verify password if protected
        if share_link.password_hash:
            if not password:
                raise HTTPException(status_code=403, detail="Password required")

            # Verify password using Argon2 (same as auth_service)
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
            if not pwd_context.verify(password, share_link.password_hash):
                raise HTTPException(status_code=403, detail="Invalid password")
        
        # 5. Get file metadata from file service (as public_link user)
        success, metadata, error = await file_service.get_file_metadata(
            share_link.file_id,
            requester_user_id="public_link"
        )
        
        if not success or not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        # 6. Return metadata
        return {
            "file_id": share_link.file_id,
            "name": metadata.get("filename", "Unknown"),
            "size": metadata.get("size", 0),
            "type": metadata.get("content_type", "unknown"),
            "created_at": metadata.get("created_at"),
            "token": token,
            "is_password_protected": bool(share_link.password_hash),
            "max_downloads": share_link.max_downloads,
            "downloads_used": share_link.downloads_used,
            "expires_at": share_link.expires_at.isoformat() if share_link.expires_at else None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get public link metadata error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve file metadata")


@router.get("/s/{token}/access")
async def access_shared_file_get(
    token: str = Path(..., description="Share link token"),
    password: Optional[str] = Query(None, description="Password if link is password-protected"),
    db: Session = Depends(get_db)
):
    """
    GET endpoint for accessing a public share link (for browser-based access).

    Redirects to the frontend PublicLink.jsx page where users can view file info
    before downloading.

    Parameters:
    - **token**: Share link token from the URL (path parameter)
    - **password**: Optional password if link is password-protected (query parameter)

    Returns:
    - Redirect to frontend PublicLink page if successful, or JSON error response
    """
    try:
        logger.info(f"[1] Access share link - token: {token}, password provided: {password is not None}")

        # 1. Validate permissions (Password, Expiry, Limits)
        logger.info(f"[2] About to validate link access")
        link = SharingService.validate_link_access(db, token, password)
        logger.info(f"[3] Validation passed, link is valid")

        # 2. Redirect to frontend PublicLink page
        # The frontend will handle fetching metadata and downloading
        frontend_url = f"http://localhost/#/s/{token}/access"
        
        logger.info(f"[8] Share link access granted - redirecting to frontend PublicLink page")
        return RedirectResponse(url=frontend_url)
    except HTTPException as e:
        logger.error(f"[ERROR] Share link access denied - status: {e.status_code}, detail: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"[ERROR] Access share link error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to access share link")


@router.get("/s/{token}/debug")
async def debug_share_link(
    token: str = Path(..., description="Share link token"),
    db: Session = Depends(get_db)
):
    """
    Debug endpoint to check share link status without validation.
    """
    try:
        link = db.query(ShareLink).filter(ShareLink.token == token).first()

        if not link:
            raise HTTPException(status_code=404, detail="Link not found")

        return {
            "token": link.token,
            "file_id": str(link.file_id),
            "created_by_user_id": str(link.created_by_user_id),
            "has_password": bool(link.password_hash),
            "active": link.active,
            "expires_at": link.expires_at,
            "created_at": link.created_at,
            "max_downloads": link.max_downloads,
            "downloads_used": link.downloads_used
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Debug share link error: {e}")
        raise HTTPException(status_code=500, detail="Debug failed")


@router.post("/s/{token}/access", response_model=AccessLinkResponse)
def access_shared_file_post(
    token: str = Path(..., description="Share link token"),
    req: AccessLinkRequest = None,
    db: Session = Depends(get_db)
):
    """
    POST endpoint for accessing a public share link (for API/programmatic access).

    This endpoint validates:
    - Link exists and is active
    - Link has not expired
    - Password is correct (if required)
    - Download limit not exceeded

    Returns a temporary download token that can be used with the download endpoint.

    Parameters:
    - **token**: Share link token from the URL (path parameter)
    - **password**: Password if the link is password-protected (body)

    Returns:
    - Download authorization status and temporary download token
    """
    try:
        if not req:
            req = AccessLinkRequest()

        # 1. Validate permissions (Password, Expiry, Limits)
        link = SharingService.validate_link_access(db, token, req.password)

        # 2. Increment download stats
        SharingService.increment_download_count(db, token)

        # 3. Generate the short-lived download ticket
        download_token = create_download_token(link.file_id)

        # 4. Return the download URL with the ticket embedded
        # The frontend will use the download endpoint
        download_url = f"http://localhost:8001/media/download/{link.file_id}?token={download_token}"

        return AccessLinkResponse(
            download_url=download_url
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Access share link error: {e}")
        raise HTTPException(status_code=500, detail="Failed to access share link")


# ============================================================================
# FOLDER UPLOAD (Phase 2)
# ============================================================================
@router.post("/upload-folder/{user_id}", response_model=dict)
async def upload_folder(
    user_id: str = Path(..., description="User ID"),
    files: list[UploadFile] = File(..., description="Files to upload as folder structure"),
    parent_folder_id: Optional[str] = Query(None, description="Parent folder to upload into"),
    request: Request = None,
    current_user_id: str = Depends(get_current_user_id),
    service: FileService = Depends(get_file_service),
    folder_service = Depends(get_folder_service),
):
    """
    Upload multiple files maintaining directory structure.
    
    Files are expected to have paths like: folder1/file.txt, folder1/subfolder/file2.txt
    This endpoint will create the folder hierarchy and place files accordingly.
    
    Args:
        user_id: User uploading the files
        files: List of files with relative paths
        parent_folder_id: Parent folder to create structure under
        
    Returns:
        FolderUploadResponse with created folder ID and upload statistics
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    # Verify user ownership
    verify_user_ownership(user_id, current_user_id)
    
    logger.info(f"[folder-upload] User {user_id} uploading {len(files)} files")
    
    # Extract folder structure from file paths
    folder_structure = {}  # path -> folder_id mapping
    files_uploaded = 0
    failed_files = 0
    total_size = 0
    
    try:
        # Log all file filenames for debugging
        logger.info(f"[folder-upload] Received files: {[f.filename for f in files]}")
        
        # Create root folder for this upload
        root_folder_name = files[0].filename.split('/')[0] if '/' in files[0].filename else "uploaded_folder"
        logger.info(f"[folder-upload] Root folder name: {root_folder_name}")
        
        success, root_folder_id, error = await folder_service.create_folder(
            user_id=user_id,
            name=root_folder_name,
            parent_id=parent_folder_id,
        )
        if not success:
            raise HTTPException(status_code=400, detail=f"Failed to create root folder: {error}")
        
        logger.info(f"[folder-upload] Created root folder: {root_folder_id}")
        folder_structure[""] = root_folder_id
        folder_structure[root_folder_name] = root_folder_id  # Map root folder name to its ID
        
        # Process each file
        for file in files:
            try:
                # Log file details for debugging
                logger.info(f"[folder-upload] Processing file - filename: '{file.filename}'")
                
                # Extract path components
                path_parts = file.filename.split('/')
                file_name = path_parts[-1]
                folder_path = '/'.join(path_parts[:-1])
                
                logger.info(f"[folder-upload] Path parts: {path_parts}, folder_path: '{folder_path}', file_name: '{file_name}'")
                
                # Create folder hierarchy if needed
                # NOTE: Skip the root folder name from the path since we already created it
                current_folder_id = root_folder_id
                if folder_path and folder_path != root_folder_name:
                    # Only create subfolders beyond the root folder name
                    # Remove the root folder name from the path if it exists
                    path_to_create = folder_path
                    if path_to_create.startswith(root_folder_name + '/'):
                        path_to_create = path_to_create[len(root_folder_name) + 1:]
                    
                    if path_to_create:
                        # Create intermediate folders
                        parts = path_to_create.split('/')
                        for i, part in enumerate(parts):
                            partial_path = '/'.join(parts[:i+1])
                            # Use root_folder_name as prefix to track absolute path
                            full_path = root_folder_name + '/' + partial_path
                            
                            if full_path not in folder_structure:
                                success, folder_id, error = await folder_service.create_folder(
                                    user_id=user_id,
                                    name=part,
                                    parent_id=current_folder_id,
                                )
                                if not success:
                                    logger.error(f"Failed to create folder {part}: {error}")
                                    failed_files += 1
                                    continue
                                logger.info(f"[folder-upload] Created subfolder '{part}' with ID {folder_id}")
                                folder_structure[full_path] = folder_id
                            current_folder_id = folder_structure[full_path]
                
                # Update file.filename to be just the filename, not the full path
                file.filename = file_name
                
                # Upload file to the target folder (includes virus scanning)
                success, file_id, size, error, scan_metadata = await service.upload_file_encrypted(
                    user_id=user_id,
                    file=file,
                    ip_address=request.client.host if request else None,
                    folder_id=current_folder_id,
                )
                
                if success:
                    files_uploaded += 1
                    total_size += size
                    logger.info(f"[folder-upload] Uploaded {file_name} to folder {current_folder_id}")
                else:
                    failed_files += 1
                    logger.error(f"[folder-upload] Failed to upload {file_name}: {error}")
                    # The activity logging for infected files happens in service.upload_file_encrypted
                    # This captures all failure reasons including virus scan failures
                    
            except Exception as e:
                failed_files += 1
                logger.error(f"[folder-upload] Error uploading {file.filename}: {e}")
                continue
        
        logger.info(f"[folder-upload] Completed: {files_uploaded} uploaded, {failed_files} failed")
        
        return {
            "status": "uploaded",
            "folder_id": root_folder_id,
            "files_uploaded": files_uploaded,
            "total_size": total_size,
            "failed_files": failed_files,
        }
        
    except Exception as e:
        logger.error(f"[folder-upload] Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Folder upload failed: {str(e)}")

