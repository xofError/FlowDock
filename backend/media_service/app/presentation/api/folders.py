"""
API endpoints for folder management.
Supports hierarchical folder structure with parent_id pattern.
"""

from fastapi import APIRouter, HTTPException, Path, Query, Depends, Request
from fastapi.responses import StreamingResponse
from typing import Optional
import logging

from app.application.services import FolderService
from app.presentation.dependencies import get_folder_service
from app.application.dtos import (
    FolderCreateRequest,
    FolderResponse,
    FolderListResponse,
    FolderUpdateRequest,
    FolderDeleteResponse,
)
from app.utils.security import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/folders", tags=["Folders"])


# ============================================================================
# CREATE FOLDER
# ============================================================================
@router.post("", response_model=FolderResponse, status_code=201)
async def create_folder(
    request: Request,
    folder_data: FolderCreateRequest,
    current_user_id: str = Depends(get_current_user_id),
    service: FolderService = Depends(get_folder_service),
):
    """
    Create a new folder.
    
    **Security**: Requires valid JWT token.
    
    **Parameters**:
    - **name**: Folder name (1-255 characters)
    - **parent_id**: Optional parent folder ID (None for root folder)
    
    **Returns**: Folder metadata
    """
    try:
        ip_address = request.client.host if request else None
        
        success, folder_id, error = await service.create_folder(
            user_id=current_user_id,
            name=folder_data.name,
            parent_id=folder_data.parent_id,
            ip_address=ip_address,
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=error)

        # Get the created folder to return full response
        success, folder_dict, error = await service.get_folder(folder_id, current_user_id)
        if success:
            return FolderResponse(**folder_dict)
        else:
            raise HTTPException(status_code=500, detail="Failed to retrieve created folder")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create folder error: {e}")
        raise HTTPException(status_code=500, detail=f"Create folder failed: {str(e)}")


# ============================================================================
# GET FOLDER
# ============================================================================
@router.get("/{folder_id}", response_model=FolderResponse)
async def get_folder(
    folder_id: str = Path(..., description="Folder ID"),
    current_user_id: str = Depends(get_current_user_id),
    service: FolderService = Depends(get_folder_service),
):
    """
    Get folder metadata.
    
    **Security**: Requires valid JWT token and folder ownership.
    
    **Parameters**:
    - **folder_id**: MongoDB ObjectId of the folder
    
    **Returns**: Folder metadata
    """
    try:
        folder_id = folder_id.strip()
        success, folder_dict, error = await service.get_folder(folder_id, current_user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=error)

        return FolderResponse(**folder_dict)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get folder error: {e}")
        raise HTTPException(status_code=500, detail=f"Get folder failed: {str(e)}")


# ============================================================================
# GET FOLDER CONTENTS (Files + Subfolders)
# ============================================================================
@router.get("/{folder_id}/contents")
async def get_folder_contents(
    folder_id: str = Path(..., description="Folder ID"),
    current_user_id: str = Depends(get_current_user_id),
    service: FolderService = Depends(get_folder_service),
):
    """
    Get folder contents (files and direct subfolders).
    
    **Security**: Requires valid JWT token and folder ownership.
    
    **Parameters**:
    - **folder_id**: MongoDB ObjectId of the folder
    
    **Returns**: 
    {
        "folder": {folder metadata},
        "files": [{file details}],
        "subfolders": [{subfolder details}]
    }
    """
    try:
        folder_id = folder_id.strip()
        success, contents_dict, error = await service.get_folder_contents(folder_id, current_user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=error)

        return contents_dict

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get folder contents error: {e}")
        raise HTTPException(status_code=500, detail=f"Get folder contents failed: {str(e)}")


# ============================================================================
# LIST FOLDERS
# ============================================================================
@router.get("", response_model=FolderListResponse)
async def list_folders(
    parent_id: Optional[str] = Query(None, description="Parent folder ID (None for root folders)"),
    current_user_id: str = Depends(get_current_user_id),
    service: FolderService = Depends(get_folder_service),
):
    """
    List folders for the authenticated user.
    
    **Security**: Requires valid JWT token.
    
    **Parameters**:
    - **parent_id**: Optional parent folder ID to list subfolders. None lists root folders.
    
    **Returns**: List of folder metadata
    """
    try:
        success, folders_list, error = await service.list_folders(
            user_id=current_user_id,
            parent_id=parent_id,
        )
        
        if not success:
            raise HTTPException(status_code=500, detail=error)

        return FolderListResponse(
            folders=folders_list or [],
            total=len(folders_list or []),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List folders error: {e}")
        raise HTTPException(status_code=500, detail=f"List folders failed: {str(e)}")


# ============================================================================
# UPDATE FOLDER
# ============================================================================
@router.patch("/{folder_id}", response_model=FolderResponse)
async def update_folder(
    folder_id: str = Path(..., description="Folder ID"),
    folder_data: FolderUpdateRequest = None,
    current_user_id: str = Depends(get_current_user_id),
    service: FolderService = Depends(get_folder_service),
):
    """
    Update folder metadata.
    
    **Security**: Requires valid JWT token and folder ownership.
    
    **Parameters**:
    - **folder_id**: MongoDB ObjectId of the folder
    - **name**: New folder name (optional)
    
    **Returns**: Updated folder metadata
    """
    try:
        folder_id = folder_id.strip()
        if not folder_data:
            raise HTTPException(status_code=400, detail="No update data provided")

        success, error = await service.update_folder(
            folder_id=folder_id,
            user_id=current_user_id,
            name=folder_data.name,
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=error)

        # Get updated folder to return full response
        success, folder_dict, error = await service.get_folder(folder_id, current_user_id)
        if success:
            return FolderResponse(**folder_dict)
        else:
            raise HTTPException(status_code=500, detail="Failed to retrieve updated folder")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update folder error: {e}")
        raise HTTPException(status_code=500, detail=f"Update folder failed: {str(e)}")


# ============================================================================
# DELETE FOLDER
# ============================================================================
@router.delete("/{folder_id}", response_model=FolderDeleteResponse)
async def delete_folder(
    folder_id: str = Path(..., description="Folder ID"),
    current_user_id: str = Depends(get_current_user_id),
    service: FolderService = Depends(get_folder_service),
    request: Request = None,
):
    """
    Delete a folder and all its contents.
    
    **Security**: Requires valid JWT token and folder ownership.
    
    **Parameters**:
    - **folder_id**: MongoDB ObjectId of the folder
    
    **Returns**: Deletion confirmation
    
    **Notes**: Recursively deletes all files and subfolders within.
    """
    try:
        folder_id = folder_id.strip()
        ip_address = request.client.host if request else None
        
        success, error = await service.delete_folder_recursive(
            user_id=current_user_id,
            folder_id=folder_id,
            ip_address=ip_address,
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=error)

        return FolderDeleteResponse(
            status="deleted",
            folder_id=folder_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete folder error: {e}")
        raise HTTPException(status_code=500, detail=f"Delete folder failed: {str(e)}")


# ============================================================================
# MOVE FOLDER
# ============================================================================
@router.patch("/{folder_id}/move", response_model=FolderResponse)
async def move_folder(
    folder_id: str = Path(..., description="Folder ID to move"),
    parent_id: Optional[str] = Query(None, description="New parent folder ID (None for root)"),
    current_user_id: str = Depends(get_current_user_id),
    service: FolderService = Depends(get_folder_service),
):
    """
    Move a folder to a different parent folder.
    
    **Security**: Requires valid JWT token and folder ownership.
    
    **Parameters**:
    - **folder_id**: MongoDB ObjectId of the folder to move
    - **parent_id**: New parent folder ID (optional, None moves to root)
    
    **Returns**: Updated folder metadata
    
    **Notes**: Prevents circular dependencies (cannot move into descendant folder).
    """
    try:
        folder_id = folder_id.strip()
        if parent_id:
            parent_id = parent_id.strip()

        success, error = await service.move_folder(
            folder_id=folder_id,
            new_parent_id=parent_id,
            user_id=current_user_id,
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=error)

        # Get updated folder to return full response
        success, folder_dict, error = await service.get_folder(folder_id, current_user_id)
        if success:
            return FolderResponse(**folder_dict)
        else:
            raise HTTPException(status_code=500, detail="Failed to retrieve moved folder")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Move folder error: {e}")
        raise HTTPException(status_code=500, detail=f"Move folder failed: {str(e)}")


# ============================================================================
# DOWNLOAD FOLDER AS ZIP
# ============================================================================
@router.get("/{folder_id}/download")
async def download_folder_zip(
    folder_id: str = Path(..., description="Folder ID"),
    current_user_id: str = Depends(get_current_user_id),
    service: FolderService = Depends(get_folder_service),
):
    """
    Download a folder as a ZIP archive.
    
    **Security**: Requires valid JWT token and folder ownership.
    
    **Parameters**:
    - **folder_id**: MongoDB ObjectId of the folder
    
    **Returns**: ZIP file stream with all folder contents
    
    **Notes**: 
    - Files are organized in the zip with full folder hierarchy
    - Infected files are excluded from the archive
    - Large folders may take time to process
    """
    try:
        folder_id = folder_id.strip()
        
        success, stream, filename, error = await service.archive_folder(folder_id, current_user_id)
        
        if not success:
            raise HTTPException(status_code=400, detail=error)

        return StreamingResponse(
            stream,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Folder download error: {e}")
        raise HTTPException(status_code=500, detail="Failed to download folder")

