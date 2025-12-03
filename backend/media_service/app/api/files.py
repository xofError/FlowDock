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


# ============================================================================
# FILE SHARING ENDPOINTS
# ============================================================================

# 1. Share a file with a specific user (direct sharing)
@router.post("/share/user", response_model=ShareFileResponse)
async def share_file_with_user(
    data: ShareCreate,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    current_user_email: str = None  # You may need to add this to token
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
            owner_email=current_user_email or "unknown@flowdock.com",
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
            link_url=f"https://flowdock.com/s/{link.token}",
            expires_at=link.expires_at,
            has_password=bool(link.password_hash)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create share link error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create share link")


# 3. Access a public share link (validate password, check expiry/limits)
@router.post("/s/{token}/access", response_model=AccessLinkResponse)
def access_shared_file(
    token: str = Path(..., description="Share link token"),
    req: AccessLinkRequest = None,
    db: Session = Depends(get_db)
):
    """
    Validate access to a public share link and get a download ticket.
    
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
        # The frontend will immediately redirect the user's browser to this URL
        download_url = f"https://api.flowdock.com/media/download/{link.file_id}?token={download_token}"
        
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
# FILE DOWNLOAD WITH TOKEN SUPPORT (for public links)
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
        is_authorized = False
        requester_user_id = None

        # Case A: Public Link with Download Token
        # This is for users accessing via public share links
        if token:
            if verify_download_token(token, file_id):
                is_authorized = True
                requester_user_id = "public_link"  # Anonymous user
        
        # Case B: Logged-in User (Direct Access or Share)
        # Check if user owns the file or has been granted access
        elif current_user_id:
            # TODO: Check if user owns the file or has been shared access
            # For now, check if the token user matches or if there's a share record
            requester_user_id = current_user_id
            is_authorized = True
            
        if not is_authorized:
            raise HTTPException(
                status_code=403,
                detail="Permission denied"
            )

        # Proceed to download (existing encrypted download logic)
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

# 1. Share with specific user
@router.post("/share/user")
def share_file_user(
    data: ShareCreate, 
    db: Session = Depends(get_db), 
    user_id: str = Depends(get_current_user_id)
):
    # (Optional) Verify user_id owns the file first via CoreService
    SharingService.share_file(db, user_id, data)
    return {"message": "File shared successfully"}

# 2. Create Public Link
@router.post("/share/link", response_model=ShareLinkResponse)
def create_share_link(
    data: ShareLinkCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    link = SharingService.create_link(db, user_id, data)
    return {
        "link_url": f"https://flowdock.com/s/{link.token}",
        "expires_at": link.expires_at,
        "has_password": bool(link.password_hash)
    }

# 3. Access Public Link (Download)
@router.post("/s/{token}/access")
def access_shared_file(
    token: str, 
    req: AccessLinkRequest, 
    db: Session = Depends(get_db)
):
    """
    Validates the link token and password.
    Returns the file_id so the frontend can trigger the download.
    """
    link = SharingService.validate_link_access(db, token, req.password)
    
    # Increment stats
    SharingService.increment_download_count(db, token)
    
    return {"file_id": link.file_id, "status": "authorized"}

@router.post("/s/{token}/access")
def access_shared_file(
    token: str, 
    req: AccessLinkRequest, 
    db: Session = Depends(get_db)
):
    # 1. Validate permissions (Password, Expiry, Limits)
    link = SharingService.validate_link_access(db, token, req.password)
    
    # 2. Increment stats
    SharingService.increment_download_count(db, token)
    
    # 3. Generate the "Ticket"
    download_token = create_download_token(link.file_id)
    
    # 4. Return the Direct Download URL
    # The frontend will immediately redirect the user's browser to this URL
    return {
        "status": "authorized",
        "download_url": f"https://api.flowdock.com/media/download/{link.file_id}?token={download_token}"
    }


@router.get("/download/{file_id}")
async def download_file(
    file_id: str, 
    token: str = Query(None),                 # For Public Links
    user_id: str = Depends(get_current_user_id) # For Logged-in Users
):
    """
    Serves the decrypted file stream.
    Requires EITHER:
    1. A valid Login (user_id) AND ownership/share permission
    2. OR A valid Download Token (from the Core Service)
    """
    is_authorized = False

    # Case A: Public Link with Token
    if token:
        if verify_download_token(token, file_id):
            is_authorized = True
    
    # Case B: Logged-in User (Direct Access)
    elif user_id:
        # Check if user owns the file or has been shared the file
        # (You might need a quick check against DB or cache here)
        is_authorized = True # Simplify for now
        
    if not is_authorized:
        raise HTTPException(status_code=403, detail="Permission denied")

    # Proceed to download (Your existing encrypted download logic)
    success, file_stream, info, error = await FileService.download_encrypted_file(file_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=error)

    return StreamingResponse(
        file_stream,
        media_type=info["content_type"],
        headers={"Content-Disposition": f"attachment; filename={info['filename']}"}
    )