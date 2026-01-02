"""
API endpoints for public folder links (Phase 4).
Handles creating and managing public access links for folders.
"""

from fastapi import APIRouter, HTTPException, Path, Query, Depends, Body, Request
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from app.application.public_folder_links_service import PublicFolderLinksService, PublicFolderLink
from app.application.dtos import (
    PublicFolderLinkCreate,
    PublicFolderLinkResponse,
    PublicFolderAccessRequest,
    PublicFolderAccessResponse,
)
from app.utils.security import (
    get_current_user_id,
    create_download_token,
)
from app.database import get_mongo_db
from app.infrastructure.database.mongo_repository import MongoFolderRepository, MongoGridFSRepository
from app.presentation.dependencies import get_folder_service
from app.core.config import settings
from app.infrastructure.security.encryption import AESCryptoService
from app.infrastructure.messaging.no_op_publisher import NoOpEventPublisher
from app.infrastructure.http.auth_client import HttpQuotaRepository
from app.infrastructure.http.logger import HttpActivityLogger
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
router = APIRouter()


async def get_public_links_service() -> PublicFolderLinksService:
    """Dependency injection for PublicFolderLinksService"""
    try:
        db = get_mongo_db()
        folder_repo = MongoFolderRepository(db)
        service = PublicFolderLinksService(folder_repo, db)
        return service
    except Exception as e:
        logger.error(f"Failed to build PublicFolderLinksService: {e}")
        raise


# ============================================================================
# PUBLIC FOLDER LINK ENDPOINTS (Protected)
# ============================================================================
@router.post("/folders/{folder_id}/public-links", response_model=PublicFolderLinkResponse)
async def create_public_link(
    folder_id: str = Path(..., description="Folder ID"),
    request_body: PublicFolderLinkCreate = Body(...),
    current_user_id: str = Depends(get_current_user_id),
    service: PublicFolderLinksService = Depends(get_public_links_service),
):
    """
    Create a public access link for a folder.
    
    Args:
        folder_id: ID of folder to create link for
        request_body: Link creation request with optional expiration/password
        current_user_id: ID of user creating the link
        
    Returns:
        PublicFolderLinkResponse with the generated link
    """
    try:
        folder_id = folder_id.strip()
        logger.info(f"[create-link] User {current_user_id} creating public link for folder {folder_id}")
        
        link = await service.create_link(
            folder_id=folder_id,
            user_id=current_user_id,
            expires_in_days=request_body.expires_at.day if request_body.expires_at else None,
            password=request_body.password,
            max_downloads=request_body.max_downloads,
        )
        
        # Generate public URL
        public_url = f"/public/folders/{link.token}"
        
        return PublicFolderLinkResponse(
            link_id=link.link_id,
            link=public_url,
            folder_id=link.folder_id,
            expires_at=link.expires_at,
            password_protected=link.password_hash is not None,
            created_at=link.created_at,
        )
        
    except ValueError as e:
        logger.error(f"[create-link] Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[create-link] Error creating link: {e}")
        raise HTTPException(status_code=500, detail="Failed to create public link")


@router.get("/folders/{folder_id}/public-links")
async def list_public_links(
    folder_id: str = Path(..., description="Folder ID"),
    current_user_id: str = Depends(get_current_user_id),
    service: PublicFolderLinksService = Depends(get_public_links_service),
):
    """
    List all public links for a folder.
    
    Args:
        folder_id: ID of folder
        current_user_id: ID of user (owner)
        
    Returns:
        List of public links
    """
    try:
        folder_id = folder_id.strip()
        logger.info(f"[list-links] User {current_user_id} listing public links for folder {folder_id}")
        
        links = await service.list_links(folder_id, current_user_id)
        
        return {
            "folder_id": folder_id,
            "links": [
                {
                    "link_id": link.link_id,
                    "token": link.token,
                    "created_at": link.created_at,
                    "expires_at": link.expires_at,
                    "password_protected": link.password_hash is not None,
                    "max_downloads": link.max_downloads,
                    "download_count": link.download_count,
                    "enabled": link.enabled,
                }
                for link in links
            ],
            "total": len(links),
        }
        
    except ValueError as e:
        logger.error(f"[list-links] Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[list-links] Error listing links: {e}")
        raise HTTPException(status_code=500, detail="Failed to list public links")


@router.get("/public-links")
async def list_all_public_links(
    current_user_id: str = Depends(get_current_user_id),
    service: PublicFolderLinksService = Depends(get_public_links_service),
):
    """
    List all public links created by the current user across all folders.
    
    Args:
        current_user_id: ID of user (owner)
        
    Returns:
        List of all public links
    """
    try:
        logger.info(f"[list-all-links] User {current_user_id} listing all public links")
        
        links = await service.list_all_links(current_user_id)
        
        return {
            "links": [
                {
                    "link_id": link.link_id,
                    "token": link.token,
                    "folder_id": link.folder_id,
                    "created_at": link.created_at,
                    "expires_at": link.expires_at,
                    "password_protected": link.password_hash is not None,
                    "max_downloads": link.max_downloads,
                    "download_count": link.download_count,
                    "enabled": link.enabled,
                }
                for link in links
            ],
            "total": len(links),
        }
        
    except ValueError as e:
        logger.error(f"[list-all-links] Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[list-all-links] Error listing links: {e}")
        raise HTTPException(status_code=500, detail="Failed to list public links")


@router.delete("/folders/{folder_id}/public-links/{link_id}")
async def delete_public_link(
    folder_id: str = Path(..., description="Folder ID"),
    link_id: str = Path(..., description="Link ID"),
    current_user_id: str = Depends(get_current_user_id),
    service: PublicFolderLinksService = Depends(get_public_links_service),
):
    """
    Delete a public link.
    
    Args:
        folder_id: ID of folder
        link_id: ID of link to delete
        current_user_id: ID of user (owner)
        
    Returns:
        Deletion status
    """
    try:
        folder_id = folder_id.strip()
        link_id = link_id.strip()
        logger.info(f"[delete-link] User {current_user_id} deleting link {link_id[:10]}...")
        
        success = await service.delete_link_by_id(link_id, current_user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Link not found")
        
        return {
            "status": "deleted",
            "link_id": link_id,
        }
        
    except ValueError as e:
        logger.error(f"[delete-link] Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[delete-link] Error deleting link: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete public link: {str(e)}")


@router.patch("/folders/{folder_id}/public-links/{link_id}/disable")
async def disable_public_link(
    folder_id: str = Path(..., description="Folder ID"),
    link_id: str = Path(..., description="Link ID"),
    current_user_id: str = Depends(get_current_user_id),
    service: PublicFolderLinksService = Depends(get_public_links_service),
):
    """
    Disable a public link without deleting it.
    
    Args:
        folder_id: ID of folder
        link_id: ID of link to disable
        current_user_id: ID of user (owner)
        
    Returns:
        Update status
    """
    try:
        folder_id = folder_id.strip()
        link_id = link_id.strip()
        logger.info(f"[disable-link] User {current_user_id} disabling link {link_id[:10]}...")
        
        success = await service.disable_link_by_id(link_id, current_user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Link not found")
        
        return {
            "status": "disabled",
            "link_id": link_id,
        }
        
    except ValueError as e:
        logger.error(f"[disable-link] Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[disable-link] Error disabling link: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to disable public link: {str(e)}")


# ============================================================================
# PUBLIC FOLDER ACCESS ENDPOINTS (Unprotected)
# ============================================================================
@router.post("/public/folders/{token}/access", response_model=PublicFolderAccessResponse)
async def access_public_folder(
    token: str = Path(..., description="Public link token"),
    request_body: Optional[PublicFolderAccessRequest] = Body(None),
    service: PublicFolderLinksService = Depends(get_public_links_service),
):
    """
    Request access to a public folder link.
    Verifies password (if required) and returns access token.
    
    Args:
        token: Public link token
        request_body: Access request with optional password
        
    Returns:
        PublicFolderAccessResponse with access token
    """
    try:
        token = token.strip()
        logger.info(f"[public-access] Requesting access to folder link {token[:10]}...")
        
        password = request_body.password if request_body else None
        
        # Verify access
        has_access = await service.verify_access(token, password)
        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get link details
        link = await service.get_link(token)
        if not link:
            raise HTTPException(status_code=404, detail="Link not found")
        
        # Get folder details
        # TODO: Get actual folder name from repository
        
        # Generate access token valid for 1 hour
        access_token = create_download_token(link.folder_id, expires_in=3600)
        
        return PublicFolderAccessResponse(
            access_token=access_token,
            folder_id=link.folder_id,
            folder_name="shared_folder",  # TODO: Get from folder repo
            expires_in=3600,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[public-access] Error accessing folder: {e}")
        raise HTTPException(status_code=500, detail="Failed to access public folder")


@router.get("/public/folders/{token}/contents")
async def get_public_folder_contents(
    token: str = Path(..., description="Public link token"),
    password: Optional[str] = Query(None, description="Password if link is protected"),
    service: PublicFolderLinksService = Depends(get_public_links_service),
    folder_service = Depends(get_folder_service),
):
    """
    Get contents of a public folder (files and subfolders).
    Requires valid token and password (if applicable).
    
    Args:
        token: Public link token
        password: Optional password if link is protected
        
    Returns:
        Folder contents (files and subfolders)
    """
    try:
        token = token.strip()
        logger.info(f"[public-contents] Retrieving contents for link {token[:10]}...")
        
        # Verify access
        has_access = await service.verify_access(token, password)
        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Increment download count
        await service.increment_download_count(token)
        
        # Get link to find folder_id
        link = await service.get_link(token)
        if not link:
            raise HTTPException(status_code=404, detail="Link not found")
        
        folder_id = link.folder_id
        
        # Get folder contents with public access (no ownership verification)
        success, contents_dict, error = await folder_service.get_folder_contents(
            folder_id, 
            user_id="public_link",  # This is just a placeholder, ownership is not checked
            allow_public=True
        )
        
        if not success:
            # Return error with proper message
            logger.warning(f"Could not retrieve folder contents for public link: {error}")
            raise HTTPException(status_code=404, detail=f"Folder not found: {error}")
        
        return contents_dict
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[public-contents] Error getting folder contents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get folder contents: {str(e)}")

