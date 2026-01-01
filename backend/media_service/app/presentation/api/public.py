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
from app.application.services import FileService
from app.presentation.dependencies import get_file_service

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
