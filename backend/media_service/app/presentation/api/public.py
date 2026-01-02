"""
Public file sharing endpoints.
Allows unauthenticated users to download files via share token.
"""

from fastapi import APIRouter, HTTPException, Path, Query, Depends
from fastapi.responses import StreamingResponse
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.share import ShareLink
from app.application.services import FileService, FolderService
from app.application.public_folder_links_service import PublicFolderLinksService
from app.presentation.dependencies import get_file_service, get_folder_service, get_public_folder_link_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public", tags=["Public Sharing"])


# ============================================================================
# PUBLIC DOWNLOAD VIA SHARE TOKEN
# ============================================================================
@router.get("/{token}", responses={200: {"description": "File content"}})
async def download_public_file(
    token: str = Path(..., description="Share token"),
    password: str = Query(None, description="Password if link is protected"),
    db: Session = Depends(get_db),
    file_service: FileService = Depends(get_file_service),
):
    """
    Download a file using a public share token.
    
    **No authentication required** - anyone with a valid token can access.
    
    **Security**:
    - Token must exist and be active
    - Token must not be expired
    - Token must not exceed max downloads
    - If password-protected, password must be provided and correct
    
    **Parameters**:
    - **token**: Public share token (from email/link)
    - **password**: Optional password if link is protected
    
    **Returns**: File content stream
    """
    try:
        # 1. Find the share link in PostgreSQL
        share_link: ShareLink = db.query(ShareLink).filter_by(token=token).first()

        if not share_link:
            raise HTTPException(status_code=404, detail="Share link not found")

        # 2. Verify share link is active
        if not share_link.active:
            raise HTTPException(status_code=410, detail="Share link is no longer active")

        # 3. Verify share link is not expired
        if share_link.expires_at and datetime.now(timezone.utc) > share_link.expires_at:
            raise HTTPException(status_code=410, detail="Share link has expired")

        # 4. Verify max downloads not exceeded
        if share_link.max_downloads > 0 and share_link.downloads_used >= share_link.max_downloads:
            raise HTTPException(status_code=410, detail="Share link download limit exceeded")

        # 5. Verify password if protected
        if share_link.password_hash:
            if not password:
                raise HTTPException(status_code=403, detail="Password required for this link")

            # Simple password verification (in production use bcrypt or similar)
            import hashlib
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if password_hash != share_link.password_hash:
                raise HTTPException(status_code=403, detail="Invalid password")

        # 6. Get file from file service (public_link is a special requester_id)
        success, stream, metadata, error = await file_service.download_file(
            share_link.file_id,
            requester_user_id="public_link",
            allow_shared=True,
        )

        if not success:
            raise HTTPException(status_code=404, detail=error or "File not found")

        # 7. Increment download counter
        share_link.downloads_used += 1
        db.commit()

        logger.info(f"✓ Public download of file {share_link.file_id} via token {token[:20]}...")

        # 8. Return file stream
        return StreamingResponse(
            stream,
            media_type=metadata.get("content_type", "application/octet-stream") if metadata else "application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{metadata.get("filename", "file") if metadata else "file"}"'
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Public download error: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


# ============================================================================
# GET SHARE LINK INFO (without password)
# ============================================================================
@router.head("/{token}")
async def check_share_link(
    token: str = Path(..., description="Share token"),
    db: Session = Depends(get_db),
):
    """
    Check if a share link is valid (without downloading).
    
    **No authentication required**.
    
    Returns HTTP 200 if valid, 404 if not found, 410 if expired/inactive.
    
    **Use case**: Frontend can check if link is valid before showing download button.
    """
    try:
        share_link: ShareLink = db.query(ShareLink).filter_by(token=token).first()

        if not share_link:
            raise HTTPException(status_code=404, detail="Share link not found")

        if not share_link.active:
            raise HTTPException(status_code=410, detail="Share link is no longer active")

        if share_link.expires_at and datetime.now(timezone.utc) > share_link.expires_at:
            raise HTTPException(status_code=410, detail="Share link has expired")

        if share_link.max_downloads > 0 and share_link.downloads_used >= share_link.max_downloads:
            raise HTTPException(status_code=410, detail="Share link download limit exceeded")

        return {"status": "valid", "password_protected": bool(share_link.password_hash)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Check share link error: {e}")
        raise HTTPException(status_code=500, detail="Check failed")


# ============================================================================
# PUBLIC FOLDER LINK - FILE DOWNLOAD
# ============================================================================
@router.get("/folder/{share_token}/download/{file_id}")
@router.get("/folder/{share_token}/file/{file_id}/download")
async def download_file_from_public_folder(
    share_token: str = Path(..., description="Public folder link token"),
    file_id: str = Path(..., description="File ID to download"),
    password: str = Query(None, description="Password if folder link is protected"),
    file_service: FileService = Depends(get_file_service),
):
    """
    Download a file from a publicly shared folder.
    
    **No authentication required** - user only needs a valid folder share token.
    
    **Security Checks**:
    1. Token must be valid and not expired
    2. File must be inside the shared folder (or its subfolders)
    3. If password-protected, password must be correct
    
    **Parameters**:
    - **share_token**: Public folder link token
    - **file_id**: File ID to download
    - **password**: Optional password if folder link is protected
    
    **Returns**: File content stream
    """
    try:
        from app.presentation.dependencies import get_public_folder_link_service
        from app.application.public_folder_links_service import PublicFolderLinksService
        
        # Get public folder link service
        link_service: PublicFolderLinksService = get_public_folder_link_service()
        
        # 1. Validate the public folder link
        logger.info(f"[public-download] Validating token {share_token[:10]}...")
        link = await link_service.get_link(share_token)
        if not link:
            logger.warning(f"[public-download] Link not found: {share_token}")
            raise HTTPException(status_code=404, detail="Link not found or expired")
        
        # 2. Check if link is accessible
        if not link.is_accessible():
            logger.warning(f"[public-download] Link not accessible (expired/disabled/limit-reached)")
            raise HTTPException(status_code=410, detail="Link has expired or been disabled")
        
        # 3. Verify password if required
        if link.password_hash:
            if not password:
                raise HTTPException(status_code=403, detail="Password required")
            if not link_service._verify_password(password, link.password_hash):
                logger.warning(f"[public-download] Wrong password for link {link.link_id}")
                raise HTTPException(status_code=403, detail="Wrong password")
        
        # 4. Verify file is inside the shared folder tree (critical security check)
        logger.info(f"[public-download] Checking if file {file_id} is in folder {link.folder_id}")
        is_in_scope = await file_service.is_file_in_folder_tree(file_id, link.folder_id)
        if not is_in_scope:
            logger.error(f"[public-download] File {file_id} is NOT in folder {link.folder_id} - access denied")
            raise HTTPException(status_code=403, detail="File not in shared folder")
        
        # 5. Increment download counter
        await link_service.increment_download_count(share_token)
        
        # 6. Download and decrypt file
        logger.info(f"[public-download] Downloading file {file_id}")
        success, file_stream, metadata, error = await file_service.download_file(
            file_id=file_id,
            requester_user_id="public_link",
            allow_shared=False,
        )
        
        if not success:
            logger.error(f"[public-download] Download failed: {error}")
            if error == "Access denied":
                raise HTTPException(status_code=403, detail="Cannot download file")
            raise HTTPException(status_code=404, detail=error or "File not found")
        
        logger.info(f"[public-download] Streaming file {metadata['filename']}")
        return StreamingResponse(
            file_stream,
            media_type=metadata["content_type"],
            headers={"Content-Disposition": f"attachment; filename=\"{metadata['filename']}\""}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[public-download] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


# ============================================================================
# PUBLIC FOLDER ZIP DOWNLOAD
# ============================================================================
@router.get("/folder/{share_token}/download-zip")
async def download_public_folder_zip(
    share_token: str = Path(..., description="Public folder share token"),
    password: str = Query(None, description="Password if link is protected"),
    folder_service: FolderService = Depends(get_folder_service),
    service=Depends(get_public_folder_link_service),
):
    """
    Download a public shared folder as a ZIP archive.
    
    **Parameters**:
    - **share_token**: Public folder share token (URL-safe)
    - **password**: Password if link is protected (optional)
    
    **Returns**: ZIP file stream
    """
    try:
        share_token = share_token.strip()
        
        # 1. Verify public folder link access
        is_valid = await service.verify_access(share_token, password)
        if not is_valid:
            raise HTTPException(status_code=403, detail="Invalid or expired share token")
        
        # 2. Get link to retrieve folder ID
        link = await service.get_link(share_token)
        if not link:
            raise HTTPException(status_code=403, detail="Invalid share token")
        
        folder_id = link.folder_id
        
        # 3. Archive the folder (use system context for public access)
        success, stream, filename, error = await folder_service.archive_folder_public(folder_id)
        
        if not success:
            raise HTTPException(status_code=400, detail=error)
        
        # Increment download count
        await service.increment_download_count(share_token)
        
        return StreamingResponse(
            stream,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[download-public-folder-zip] Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to download folder")

