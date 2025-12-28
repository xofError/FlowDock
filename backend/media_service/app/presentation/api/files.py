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
from app.presentation.dependencies import get_file_service
from app.application.dtos import (
    FileUploadResponse,
    FileMetadataResponse,
    FileDeleteResponse,
    FileListResponse,
    HealthCheckResponse,
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
# FILE UPLOAD
# ============================================================================
@router.post("/upload/{user_id}", response_model=FileUploadResponse)
async def upload_file(
    user_id: str = Path(..., description="User ID"),
    file: UploadFile = File(..., description="File to upload"),
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

        # Use injected service to upload encrypted file
        success, file_id, original_size, error = await service.upload_file_encrypted(
            user_id=user_id,
            file=file,
            ip_address=ip_address
        )

        if not success:
            status_code = 400 if "Invalid" in error else 413 if "too large" in error else 500
            raise HTTPException(status_code=status_code, detail=error)

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

        # Case A: Public Link with Download Token
        if token:
            token_valid = verify_download_token(token, file_id)
            if token_valid:
                is_authorized = True
                requester_user_id = "public_link"
            else:
                logger.error(f"Token verification failed")

        # Case B: Logged-in User
        elif current_user_id:
            requester_user_id = current_user_id
            is_authorized = True

        if not is_authorized:
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
                # Not owner; check direct shares in DB
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

        # Download using injected service; allow shared access when applicable
        success, file_stream, metadata, error = await service.download_file(
            file_id=file_id,
            requester_user_id=requester_user_id,
            allow_shared=allow_shared,
        )

        if not success:
            if error == "Access denied":
                raise HTTPException(status_code=403, detail=error)
            raise HTTPException(status_code=404, detail=error)

        return StreamingResponse(
            file_stream,
            media_type=metadata["content_type"],
            headers={"Content-Disposition": f"attachment; filename={metadata['filename']}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error: {e}")
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

        # Delete using injected service
        success, file_size, error = await service.delete_file(
            file_id=file_id,
            requester_user_id=current_user_id,
            ip_address=ip_address
        )

        if not success:
            if error == "Access denied":
                raise HTTPException(status_code=403, detail=error)
            raise HTTPException(status_code=404, detail=error)

        return FileDeleteResponse(
            status="deleted",
            file_id=file_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail="Deletion failed")


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
            raise HTTPException(
                status_code=403,
                detail="Cannot list files for other users"
            )

        # List files using injected service
        success, files, error = await service.list_user_files(user_id)

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
                    metadata={}
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
        try:
            uid = uuid.UUID(user_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid user_id")

        shares = db.query(Share).filter(Share.shared_with_user_id == uid).all()

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
        try:
            uid = uuid.UUID(user_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid user_id")

        shares = db.query(Share).filter(Share.shared_by_user_id == uid).all()

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
            link_url=f"http://localhost:8001/media/s/{link.token}/access",
            expires_at=link.expires_at,
            has_password=bool(link.password_hash),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create share link error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create share link")


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
        download_url = f"http://localhost:8001/media/download/{link.file_id}?token={download_token}"

        logger.info(f"[8] Share link access granted - redirecting to download endpoint")
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
        # The frontend will use the download endpoint
        download_url = f"http://localhost:8001/media/download/{link.file_id}?token={download_token}"

        return AccessLinkResponse(
            download_token=download_token,
            file_id=link.file_id,
            filename=link.file_id  # TODO: Get actual filename from metadata
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Access share link error: {e}")
        raise HTTPException(status_code=500, detail="Failed to access share link")
