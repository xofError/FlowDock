"""
API endpoints for folder sharing operations (Phase 3).
Handles sharing folders with users/groups and managing permissions.
"""

from fastapi import APIRouter, HTTPException, Path, Depends, Request, Body
from typing import Optional, List
import logging

from app.application.folder_sharing_service import FolderSharingService
from app.application.dtos import (
    FolderShareRequest,
    FolderShareResponse,
    FolderShareListResponse,
    FolderUnshareRequest,
)
from app.utils.security import (
    get_current_user_id,
)
from app.database import get_mongo_db
from app.infrastructure.database.mongo_repository import MongoFolderRepository
from app.presentation.dependencies import get_folder_service

logger = logging.getLogger(__name__)
router = APIRouter()


async def get_folder_sharing_service() -> FolderSharingService:
    """Dependency injection for FolderSharingService"""
    try:
        db = get_mongo_db()
        folder_repo = MongoFolderRepository(db)
        service = FolderSharingService(folder_repo, db)
        return service
    except Exception as e:
        logger.error(f"Failed to build FolderSharingService: {e}")
        raise


# ============================================================================
# FOLDER SHARING ENDPOINTS
# ============================================================================
@router.post("/folders/{folder_id}/share", response_model=FolderShareResponse)
async def share_folder(
    folder_id: str = Path(..., description="Folder ID"),
    request_body: FolderShareRequest = Body(...),
    current_user_id: str = Depends(get_current_user_id),
    service: FolderSharingService = Depends(get_folder_sharing_service),
):
    """
    Share a folder with one or more users/groups.
    
    Args:
        folder_id: ID of folder to share
        request_body: Share request with targets and permissions
        current_user_id: ID of user making the request
        
    Returns:
        FolderShareResponse with sharing results
    """
    try:
        folder_id = folder_id.strip()
        logger.info(f"[share-folder] User {current_user_id} sharing folder {folder_id}")
        
        result = await service.share_folder(
            folder_id=folder_id,
            owner_id=current_user_id,
            targets=request_body.targets,
            permission=request_body.permission,
            cascade=request_body.cascade,
            expires_at=request_body.expires_at,
        )
        
        return FolderShareResponse(
            status=result["status"],
            folder_id=result["folder_id"],
            targets_count=result["targets_count"],
        )
        
    except ValueError as e:
        logger.error(f"[share-folder] Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[share-folder] Error sharing folder: {e}")
        raise HTTPException(status_code=500, detail="Failed to share folder")


@router.get("/folders/{folder_id}/shares", response_model=FolderShareListResponse)
async def get_folder_shares(
    folder_id: str = Path(..., description="Folder ID"),
    current_user_id: str = Depends(get_current_user_id),
    service: FolderSharingService = Depends(get_folder_sharing_service),
):
    """
    Get list of users/groups a folder is shared with.
    
    Args:
        folder_id: ID of folder
        current_user_id: ID of user making the request
        
    Returns:
        FolderShareListResponse with list of shares
    """
    try:
        folder_id = folder_id.strip()
        logger.info(f"[get-shares] Retrieving shares for folder {folder_id}")
        
        shares = await service.get_folder_shares(
            folder_id=folder_id,
            owner_id=current_user_id,
        )
        
        return FolderShareListResponse(
            folder_id=folder_id,
            shared_with=shares,
        )
        
    except ValueError as e:
        logger.error(f"[get-shares] Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[get-shares] Error getting shares: {e}")
        raise HTTPException(status_code=500, detail="Failed to get folder shares")


@router.delete("/folders/{folder_id}/unshare")
async def unshare_folder(
    folder_id: str = Path(..., description="Folder ID"),
    request_body: FolderUnshareRequest = Body(...),
    current_user_id: str = Depends(get_current_user_id),
    service: FolderSharingService = Depends(get_folder_sharing_service),
):
    """
    Remove sharing for a specific user/group from a folder.
    
    Args:
        folder_id: ID of folder
        request_body: Unshare request with target to revoke
        current_user_id: ID of user making the request
        
    Returns:
        Unshare result
    """
    try:
        logger.info(f"[unshare] Revoking access on folder {folder_id}")
        
        result = await service.unshare_folder(
            folder_id=folder_id,
            owner_id=current_user_id,
            target_id=request_body.target,
            cascade=request_body.cascade,
        )
        
        return result
        
    except ValueError as e:
        logger.error(f"[unshare] Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[unshare] Error unsharing folder: {e}")
        raise HTTPException(status_code=500, detail="Failed to unshare folder")


# ============================================================================
# SHARED FOLDER ACCESS ENDPOINTS (for users accessing shared folders)
# ============================================================================

@router.get("/shared-folders", response_model=dict)
async def list_shared_folders(
    current_user_id: str = Depends(get_current_user_id),
    service: FolderSharingService = Depends(get_folder_sharing_service),
):
    """
    List all folders shared with the current user.
    
    Args:
        current_user_id: ID of current user
        
    Returns:
        List of folders shared with the user
    """
    try:
        logger.info(f"[list-shared] User {current_user_id} listing shared folders")
        
        shares = await service.list_shared_folders(current_user_id)
        
        return {
            "shared_folders": shares,
            "total": len(shares),
        }
        
    except Exception as e:
        logger.error(f"[list-shared] Error listing shared folders: {e}")
        raise HTTPException(status_code=500, detail="Failed to list shared folders")


@router.get("/shared-folders/{folder_id}/contents", response_model=dict)
async def get_shared_folder_contents(
    folder_id: str = Path(..., description="Folder ID"),
    current_user_id: str = Depends(get_current_user_id),
    service: FolderSharingService = Depends(get_folder_sharing_service),
    folder_service = Depends(get_folder_service),
):
    """
    Get contents of a folder that is shared with the current user.
    
    Args:
        folder_id: ID of shared folder
        current_user_id: ID of current user
        
    Returns:
        Folder contents (files and subfolders) if user has access
    """
    try:
        folder_id = folder_id.strip()
        logger.info(f"[get-shared-contents] User {current_user_id} accessing folder {folder_id}")
        
        # Check if user has access to this folder
        permission = await service.check_folder_access(folder_id, current_user_id)
        if not permission:
            logger.warning(f"[get-shared-contents] User {current_user_id} does not have access to {folder_id}")
            raise HTTPException(status_code=403, detail="Access denied - folder not shared with you")
        
        # Get folder contents (with public=True to bypass ownership check)
        success, contents_dict, error = await folder_service.get_folder_contents(
            folder_id,
            user_id=current_user_id,
            allow_public=True,
        )
        
        if not success:
            logger.warning(f"[get-shared-contents] Could not retrieve folder contents: {error}")
            raise HTTPException(status_code=404, detail=f"Folder not found: {error}")
        
        return contents_dict
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"[get-shared-contents] Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[get-shared-contents] Error getting folder contents: {e}")
        raise HTTPException(status_code=500, detail="Failed to get folder contents")