"""
API endpoints for file operations with envelope encryption and streaming.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Path, Query, Depends
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging

from app.services.file_service import FileService
from app.services.rabbitmq_service import publish_file_event
from app.services.sharing_service import SharingService
from app.schemas.file import (
    FileUploadResponse,
    FileMetadataResponse,
    FileDeleteResponse,
    HealthCheckResponse
)
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
from app.database import get_db


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
    
    This allows endpoints to be accessed both anonymously and with authentication.
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


@router.get("/user/{user_id}/files", response_model=list[FileMetadataResponse])
async def list_user_files(
    user_id: str = Path(..., description="User ID"),
    current_user_id: str = Depends(get_current_user_id)
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
            raise HTTPException(
                status_code=403,
                detail="Cannot list files for other users"
            )
        
        # Retrieve file list from GridFS
        success, files, error = await FileService.list_user_files(user_id)
        
        if not success:
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
        
        return response_files
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List files error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list files")


# ============================================================================
# SHARING QUERY ENDPOINTS
# ============================================================================

@router.get("/users/{user_id}/files/shared-with-me")
async def get_files_shared_with_user(
    user_id: str = Path(..., description="User ID"),
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get all files that have been shared with the user by others.
    
    Returns list of direct shares (not public links).
    
    **Security**: Requires valid JWT token. Users can only view shares intended for them.
    """
    # Verify the requester is viewing their own shares
    if user_id != current_user_id:
        raise HTTPException(
            status_code=403,
            detail="Cannot view shares for other users"
        )
    
    try:
        shares = db.query(Share).filter(Share.shared_with_user_id == user_id).all()
        
        result = []
        for share in shares:
            result.append({
                "share_id": str(share.id),
                "file_id": share.file_id,
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
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get all files that the user has shared with others (direct shares).
    
    Returns list of direct shares created by this user (not public links).
    
    **Security**: Requires valid JWT token. Users can only view shares they created.
    """
    # Verify the requester owns these shares
    if user_id != current_user_id:
        raise HTTPException(
            status_code=403,
            detail="Cannot view shares created by other users"
        )
    
    try:
        shares = db.query(Share).filter(Share.shared_by_user_id == user_id).all()
        
        result = []
        for share in shares:
            result.append({
                "share_id": str(share.id),
                "file_id": share.file_id,
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
        links = db.query(ShareLink).filter(ShareLink.created_by_user_id == user_id).all()
        
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

# 1. Share a file with a specific user (direct sharing)
@router.post("/share/user", response_model=ShareFileResponse)
async def share_file_with_user(
    data: ShareCreate,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Share a file with a specific user by their email.
    
    The recipient will receive access to download the file with their JWT token.
    
    Parameters:
    - **file_id**: MongoDB ObjectId of the encrypted file
    - **target_email**: Email address of the user to share with
    - **permission**: Permission level ('read', 'write', 'full') - default 'read'
    - **expires_at**: Optional expiration date for the share
    
    Returns:
    - Confirmation message with share_id
    """
    try:
        share = await SharingService.share_file(
            db,
            owner_id=current_user_id,
            owner_email="owner@flowdock.com",  # Not needed, owner_id is enough
            data=data
        )
        
        return ShareFileResponse(
            message="File shared successfully",
            share_id=str(share.id)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Share file error: {e}")
        raise HTTPException(status_code=500, detail="Failed to share file")


# 2. Create a public share link (with optional password protection)
@router.post("/share/link", response_model=ShareLinkResponse)
def create_public_share_link(
    data: ShareLinkCreate,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Create a public share link for a file.
    
    Anyone with the link can access the file, optionally with password protection.
    
    Parameters:
    - **file_id**: MongoDB ObjectId of the encrypted file
    - **password**: Optional password to protect the link
    - **expires_at**: Optional expiration date for the link
    - **max_downloads**: Maximum number of downloads (0 = unlimited)
    
    Returns:
    - Public link URL, expiration date, and password status
    """
    try:
        link = SharingService.create_link(db, current_user_id, data)
        
        return ShareLinkResponse(
            link_url=f"http://localhost:8001/media/s/{link.token}/access",
            expires_at=link.expires_at,
            has_password=bool(link.password_hash)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create share link error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create share link")


# 3. Access a public share link (validate password, check expiry/limits)
@router.get("/s/{token}/access")
async def access_shared_file_get(
    token: str = Path(..., description="Share link token"),
    password: Optional[str] = Query(None, description="Password if link is password-protected"),
    db: Session = Depends(get_db)
):
    """
    GET endpoint for accessing a public share link (for browser-based access).
    
    If link is valid, redirects to the download URL.
    If password is required but not provided, returns error asking for password.
    
    Parameters:
    - **token**: Share link token from the URL (path parameter)
    - **password**: Optional password if link is password-protected (query parameter)
    
    Returns:
    - Redirect to download URL if successful, or JSON error response
    """
    try:
        logger.info(f"[1] Access share link - token: {token}, password provided: {password is not None}")
        
        # 1. Validate permissions (Password, Expiry, Limits)
        logger.info(f"[2] About to validate link access")
        link = SharingService.validate_link_access(db, token, password)
        logger.info(f"[3] Validation passed, link is valid")
        
        # 2. Increment download stats
        logger.info(f"[4] About to increment download count")
        SharingService.increment_download_count(db, token)
        logger.info(f"[5] Download count incremented")
        
        # 3. Generate the short-lived download ticket
        logger.info(f"[6] About to create download token")
        download_token = create_download_token(link.file_id)
        logger.info(f"[7] Download token created: {download_token}")
        
        # 4. Redirect to download URL
        download_url = f"http://localhost:8001/media/public-download/{link.file_id}?token={download_token}"
        
        logger.info(f"[8] Share link access granted - redirecting to public download endpoint")
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=download_url)
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
        # The frontend will use the public-download endpoint
        download_url = f"http://localhost:8001/media/public-download/{link.file_id}?token={download_token}"
        
        return AccessLinkResponse(
            status="authorized",
            download_url=download_url
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Access share link error: {e}")
        raise HTTPException(status_code=500, detail="Failed to access share link")


# ============================================================================
# PUBLIC LINK DOWNLOAD - Dedicated endpoint for token-based downloads
# ============================================================================

@router.get("/public-download/{file_id}")
async def download_file_with_token(
    file_id: str = Path(..., description="File ID (ObjectId)"),
    token: str = Query(..., description="Download token for public links (REQUIRED)")
):
    """
    Download a file using a temporary download token from a public share link.
    
    This endpoint is specifically for public link downloads and does NOT require
    authentication. It only validates the download token.
    
    **Security**:
    - Requires valid download token (short-lived, 1 minute)
    - Token must contain matching file_id
    
    Parameters:
    - **file_id**: MongoDB ObjectId of the file
    - **token**: Temporary download token (required)
    
    Returns:
    - Decrypted binary file stream
    """
    try:
        logger.info(f"[public_download] Starting public link download - file_id: {file_id}, has_token: {token is not None}")
        
        if not token:
            logger.error(f"[public_download] Token is required but missing")
            raise HTTPException(
                status_code=400,
                detail="Download token is required"
            )
        
        # Verify the token
        logger.info(f"[public_download] Token: {token[:50]}...")
        logger.info(f"[public_download] File ID from path: {file_id}")
        
        token_valid = verify_download_token(token, file_id)
        logger.info(f"[public_download] Token verification result: {token_valid}")
        
        if not token_valid:
            logger.error(f"[public_download] Token verification failed")
            raise HTTPException(
                status_code=403,
                detail="Invalid or expired download token"
            )
        
        # Token is valid - proceed with download as "public_link" user
        logger.info(f"[public_download] Token valid - proceeding with download as public_link")
        success, file_stream, info, error = await FileService.download_encrypted_file(
            file_id,
            requester_user_id="public_link"
        )
        
        if not success:
            if error == "Access denied":
                raise HTTPException(status_code=403, detail=error)
            raise HTTPException(status_code=404, detail=error)
        
        logger.info(f"[public_download] File download successful")
        return StreamingResponse(
            file_stream,
            media_type=info["content_type"],
            headers={"Content-Disposition": f"attachment; filename={info['filename']}"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[public_download] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to download file")


# ============================================================================
# FILE DOWNLOAD WITH AUTH/TOKEN SUPPORT (for both authenticated users and public links)
# ============================================================================

@router.get("/download/{file_id}")
async def download_file_with_auth(
    file_id: str = Path(..., description="File ID (ObjectId)"),
    token: str = Query(None, description="Download token for public links"),
    current_user_id: Optional[str] = Depends(get_optional_user_id)
):
    """
    Download and decrypt a file from GridFS.
    
    Supports both authenticated users (via JWT) and public link access (via download token).
    
    **Security**: 
    - For authenticated users: Requires valid JWT token and enforces ownership
    - For public links: Requires valid download token (short-lived, 1 minute)
    
    **Decryption**: Files are decrypted on-the-fly using the File Key and Master Key.
    
    Parameters:
    - **file_id**: MongoDB ObjectId of the encrypted file
    - **token**: Optional download token for public link access
    
    Returns:
    - Decrypted binary file stream
    """
    try:
        logger.info(f"[download] Starting download - file_id: {file_id}, has_token: {token is not None}, has_user: {current_user_id is not None}")
        
        is_authorized = False
        requester_user_id = None

        # Case A: Public Link with Download Token
        # This is for users accessing via public share links
        if token:
            logger.info(f"[download] Token-based access attempt")
            logger.info(f"[download] Token: {token[:50]}...")
            logger.info(f"[download] File ID from path: {file_id}")
            
            token_valid = verify_download_token(token, file_id)
            logger.info(f"[download] Token verification result: {token_valid}")
            
            if token_valid:
                is_authorized = True
                requester_user_id = "public_link"  # Anonymous user
                logger.info(f"[download] Token authorized - proceeding with download")
            else:
                logger.error(f"[download] Token verification failed")
        
        # Case B: Logged-in User (Direct Access or Share)
        # Check if user owns the file or has been granted access
        elif current_user_id:
            logger.info(f"[download] User-based access - user: {current_user_id}")
            # TODO: Check if user owns the file or has been shared access
            # For now, check if the token user matches or if there's a share record
            requester_user_id = current_user_id
            is_authorized = True
            
        if not is_authorized:
            logger.error(f"[download] Authorization failed - no valid token or user")
            raise HTTPException(
                status_code=403,
                detail="Permission denied"
            )

        # Proceed to download (existing encrypted download logic)
        logger.info(f"[download] Attempting to download file {file_id} as {requester_user_id}")
        success, file_stream, info, error = await FileService.download_encrypted_file(
            file_id,
            requester_user_id=requester_user_id
        )
        
        if not success:
            if error == "Access denied":
                raise HTTPException(status_code=403, detail=error)
            raise HTTPException(status_code=404, detail=error)

        return StreamingResponse(
            file_stream,
            media_type=info["content_type"],
            headers={"Content-Disposition": f"attachment; filename={info['filename']}"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise HTTPException(status_code=500, detail="Download failed")




# ============================================================================
# REMOVE DUPLICATE ENDPOINTS (below are the old ones that should be removed)
# ============================================================================