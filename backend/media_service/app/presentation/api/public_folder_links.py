"""
API endpoints for public folder links (Phase 4).
Handles creating and managing public access links for folders.
"""

from fastapi import APIRouter, HTTPException, Path, Query, Depends, Body, Request
from fastapi.responses import JSONResponse
from typing import Optional
import logging
from bson import ObjectId

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
        
        # Calculate days until expiration
        expires_in_days = None
        if request_body.expires_at:
            from datetime import datetime as dt, timezone
            expiry_date = request_body.expires_at
            if isinstance(expiry_date, str):
                # Parse ISO format date string
                expiry_date = dt.fromisoformat(expiry_date.replace('Z', '+00:00'))
            
            # Calculate days from now until expiry
            now = dt.now(timezone.utc) if expiry_date.tzinfo else dt.utcnow()
            delta = expiry_date - now
            expires_in_days = max(0, delta.days)  # Ensure non-negative
        
        link = await service.create_link(
            folder_id=folder_id,
            user_id=current_user_id,
            expires_in_days=expires_in_days,
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
            token=link.token,  # Include token for frontend
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
        
        # Get folder details for each link
        folder_repo = MongoFolderRepository(get_mongo_db())
        result_links = []
        for link in links:
            try:
                folder = await folder_repo.get_folder_by_id(link.folder_id)
                folder_name = folder.name if folder else "Unknown Folder"
            except:
                folder_name = "Unknown Folder"
            
            result_links.append({
                "link_id": link.link_id,
                "token": link.token,
                "folder_id": link.folder_id,
                "folder_name": folder_name,
                "created_at": link.created_at,
                "expires_at": link.expires_at,
                "password_protected": link.password_hash is not None,
                "max_downloads": link.max_downloads,
                "download_count": link.download_count,
                "enabled": link.enabled,
            })
        
        return {
            "links": result_links,
            "total": len(result_links),
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


@router.delete("/public-links/{link_id}")
async def delete_public_link_by_id(
    link_id: str = Path(..., description="Link ID"),
    current_user_id: str = Depends(get_current_user_id),
    service: PublicFolderLinksService = Depends(get_public_links_service),
):
    """
    Delete a public folder link by ID only (without requiring folder_id).
    This endpoint is used when deleting from a list where folder context is not available.
    
    Args:
        link_id: ID of link to delete
        current_user_id: ID of user (owner)
        
    Returns:
        Deletion status
    """
    try:
        link_id = link_id.strip()
        logger.info(f"[delete-link-by-id] User {current_user_id} deleting link {link_id[:10]}...")
        
        success = await service.delete_link_by_id(link_id, current_user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Link not found")
        
        return {
            "status": "deleted",
            "link_id": link_id,
        }
        
    except ValueError as e:
        logger.error(f"[delete-link-by-id] Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[delete-link-by-id] Error deleting link: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete public link: {str(e)}")


# Alias for /share-links pattern for compatibility with file links
@router.delete("/share-links/{link_id}")
async def delete_folder_link_by_id(
    link_id: str = Path(..., description="Link ID"),
    current_user_id: str = Depends(get_current_user_id),
    service: PublicFolderLinksService = Depends(get_public_links_service),
):
    """
    Delete a public folder link using share-links pattern (alias for compatibility).
    
    Args:
        link_id: ID of link to delete
        current_user_id: ID of user (owner)
        
    Returns:
        Deletion status
    """
    try:
        link_id = link_id.strip()
        logger.info(f"[delete-share-link] User {current_user_id} deleting share-link {link_id[:10]}...")
        
        success = await service.delete_link_by_id(link_id, current_user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Link not found or not authorized")
        
        return {
            "status": "deleted",
            "link_id": link_id,
        }
        
    except ValueError as e:
        logger.error(f"[delete-share-link] Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[delete-share-link] Error deleting link: {str(e)}")
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


@router.patch("/public-links/{link_id}/extend-expiry")
async def extend_public_link_expiry(
    link_id: str = Path(..., description="Public link ID"),
    new_expiry: datetime = Query(..., description="New expiry date (ISO format)"),
    current_user_id: str = Depends(get_current_user_id),
    service: PublicFolderLinksService = Depends(get_public_links_service),
):
    """
    Extend the expiry date of a public folder link.
    
    Security:
    - Only the user who created the link can extend it
    
    Parameters:
    - **link_id**: Hex ID of the public folder link
    - **new_expiry**: New expiry date in ISO format
    
    Returns:
    - Updated link metadata
    """
    try:
        from datetime import timezone
        
        link_id = link_id.strip()
        logger.info(f"[extend-expiry] User {current_user_id} extending link {link_id[:10]}...")
        
        # Get link
        link = await service.get_link_by_id(link_id)
        if not link:
            raise HTTPException(status_code=404, detail="Link not found")
        
        # Verify ownership
        if link.created_by != current_user_id:
            raise HTTPException(status_code=403, detail="You don't have permission to modify this link")
        
        # Validate new expiry is in the future
        if new_expiry.tzinfo is None:
            new_expiry = new_expiry.replace(tzinfo=timezone.utc)
        
        if new_expiry <= datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Expiry date must be in the future")
        
        # Update expiry in database
        await service.links_collection.update_one(
            {"link_id": link_id},
            {"$set": {"expires_at": new_expiry}}
        )
        
        logger.info(f"[extend-expiry] Extended expiry for link {link_id}")
        
        return {
            "link_id": link_id,
            "token": link.token,
            "expires_at": new_expiry.isoformat(),
            "message": "Expiry date extended successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[extend-expiry] Error extending expiry: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to extend expiry: {str(e)}")


@router.get("/public/folders/{token}/subfolder/{subfolder_id}/contents")
async def get_public_subfolder_contents(
    token: str = Path(..., description="Public link token"),
    subfolder_id: str = Path(..., description="Subfolder ID to retrieve"),
    password: Optional[str] = Query(None, description="Password if link is protected"),
    service: PublicFolderLinksService = Depends(get_public_links_service),
    folder_service = Depends(get_folder_service),
):
    """
    Get contents of a subfolder within a public folder.
    
    Args:
        token: Public link token
        subfolder_id: ID of the subfolder to retrieve
        password: Optional password if link is protected
        
    Returns:
        Subfolder contents (files and subfolders)
    """
    try:
        token = token.strip()
        subfolder_id = subfolder_id.strip()
        logger.info(f"[public-subfolder-contents] Retrieving subfolder {subfolder_id} for link {token[:10]}...")
        
        # Verify access
        has_access = await service.verify_access(token, password)
        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get link to verify subfolder belongs to it
        link = await service.get_link(token)
        if not link:
            raise HTTPException(status_code=404, detail="Link not found")
        
        folder_id = link.folder_id
        
        # Verify that subfolder_id is actually a subfolder of the main folder
        # Get folder tree to check if subfolder is in this tree
        try:
            db = service.db
            folders_coll = db["folders"]
            
            # Convert to ObjectId if valid format
            from bson import ObjectId
            try:
                subfolder_oid = ObjectId(subfolder_id) if len(subfolder_id) == 24 else subfolder_id
            except:
                subfolder_oid = subfolder_id
            
            # Check if subfolder exists and is part of the folder tree
            subfolder = await folders_coll.find_one({"_id": subfolder_oid})
            if not subfolder:
                raise HTTPException(status_code=404, detail="Subfolder not found")
            
            # Verify subfolder is part of the public folder tree
            # by checking if it has folder_id as an ancestor or is a direct child
            current_id = subfolder_oid
            found = False
            visited = set()
            
            while current_id and str(current_id) not in visited:
                visited.add(str(current_id))
                
                try:
                    current_oid = ObjectId(str(current_id)) if len(str(current_id)) == 24 else current_id
                except:
                    current_oid = current_id
                
                current_folder = await folders_coll.find_one({"_id": current_oid})
                if not current_folder:
                    break
                
                if str(current_id) == str(folder_id):
                    found = True
                    break
                
                current_id = current_folder.get("parent_id")
            
            if not found:
                raise HTTPException(status_code=403, detail="Access denied - subfolder not in shared folder")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to verify subfolder: {e}")
            raise HTTPException(status_code=500, detail="Failed to verify subfolder access")
        
        # Increment download count
        await service.increment_download_count(token)
        
        # Get subfolder contents
        success, contents_dict, error = await folder_service.get_folder_contents(
            subfolder_id, 
            user_id="public_link",
            allow_public=True
        )
        
        if not success:
            logger.warning(f"Could not retrieve subfolder contents: {error}")
            raise HTTPException(status_code=404, detail=f"Subfolder not found: {error}")
        
        return contents_dict
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[public-subfolder-contents] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get subfolder contents: {str(e)}")


@router.get("/public/folders/{token}/download-file/{file_id}")
async def download_file_from_public_folder(
    token: str = Path(..., description="Public link token"),
    file_id: str = Path(..., description="File ID to download"),
    password: Optional[str] = Query(None, description="Password if link is protected"),
    service: PublicFolderLinksService = Depends(get_public_links_service),
    folder_service = Depends(get_folder_service),
):
    """
    Download a file from a public folder link.
    
    Args:
        token: Public link token
        file_id: ID of the file to download
        password: Optional password if link is protected
        
    Returns:
        File content as binary
    """
    try:
        token = token.strip()
        file_id = file_id.strip()
        logger.info(f"[public-file-download] Downloading file {file_id} from link {token[:10]}...")
        
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
        
        # Verify file is in the folder tree
        try:
            db = service.db
            fs = db.get_collection("fs.files")  # GridFS files collection
            
            file_doc = await fs.find_one({"_id": ObjectId(file_id) if len(file_id) == 24 else file_id})
            if not file_doc:
                raise HTTPException(status_code=404, detail="File not found")
            
            # Check if file is in the shared folder (check via folder_id field in metadata)
            file_metadata = file_doc.get("metadata", {})
            file_folder_id = file_metadata.get("folder_id")
            
            # Verify this folder belongs to the public link's folder tree
            current_id = file_folder_id
            found = False
            visited = set()
            
            while current_id and current_id not in visited:
                visited.add(str(current_id))
                if str(current_id) == folder_id or str(current_id) == str(folder_id):
                    found = True
                    break
                
                current_folder = await db["folders"].find_one({"_id": current_id if isinstance(current_id, ObjectId) else ObjectId(current_id) if len(str(current_id)) == 24 else current_id})
                if not current_folder:
                    break
                
                current_id = current_folder.get("parent_id")
            
            if not found:
                raise HTTPException(status_code=403, detail="File not in shared folder")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to verify file: {e}")
            raise HTTPException(status_code=500, detail="Failed to verify file access")
        
        # Download file using folder_service
        from fastapi.responses import StreamingResponse
        try:
            # Get file metadata and encrypted stream
            file_meta, stream = await folder_service.file_repo.get_file_stream(file_id)
            
            if not file_meta:
                raise HTTPException(status_code=404, detail="File content not found")
            
            # Decrypt the stream if file is encrypted
            if file_meta.encrypted:
                try:
                    file_key = folder_service.crypto.unwrap_key(bytes.fromhex(file_meta.encrypted_key))
                    nonce = bytes.fromhex(file_meta.nonce)
                    stream = folder_service.crypto.decrypt_stream(stream, file_key, nonce)
                except Exception as e:
                    logger.error(f"Decryption failed for file {file_id}: {e}")
                    raise HTTPException(status_code=500, detail="Failed to decrypt file")
            
            filename = file_meta.filename or "download"
            
            return StreamingResponse(
                stream,
                media_type="application/octet-stream",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Content-Length": str(file_meta.size)
                }
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to download file: {e}")
            raise HTTPException(status_code=500, detail="Failed to download file")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[public-file-download] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}")


@router.get("/public/folders/{token}/download-zip")
async def download_public_folder_as_zip(
    token: str = Path(..., description="Public link token"),
    password: Optional[str] = Query(None, description="Password if link is protected"),
    service: PublicFolderLinksService = Depends(get_public_links_service),
    folder_service = Depends(get_folder_service),
):
    """
    Download entire public folder as ZIP.
    
    Args:
        token: Public link token
        password: Optional password if link is protected
        
    Returns:
        ZIP file content
    """
    try:
        token = token.strip()
        logger.info(f"[public-zip-download] Downloading folder as ZIP for link {token[:10]}...")
        
        # Verify access
        has_access = await service.verify_access(token, password)
        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Increment download count
        await service.increment_download_count(token)
        
        # Get link
        link = await service.get_link(token)
        if not link:
            raise HTTPException(status_code=404, detail="Link not found")
        
        folder_id = link.folder_id
        
        # Use folder_service to download as ZIP (with public access)
        from fastapi.responses import StreamingResponse
        try:
            # Archive folder with public access (no ownership check)
            success, stream, filename, error = await folder_service.archive_folder_public(folder_id)
            
            if not success:
                raise HTTPException(status_code=400, detail=error or "Failed to create archive")
            
            return StreamingResponse(
                stream,
                media_type="application/zip",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                }
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to create ZIP: {e}")
            raise HTTPException(status_code=500, detail="Failed to download folder")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[public-zip-download] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download folder: {str(e)}")


@router.patch("/public-links/{link_id}/update-download-limit")
async def update_public_link_download_limit(
    link_id: str = Path(..., description="Public link ID"),
    max_downloads: int = Query(..., description="New maximum download limit (0 for unlimited)"),
    current_user_id: str = Depends(get_current_user_id),
    service: PublicFolderLinksService = Depends(get_public_links_service),
):
    """
    Update the download limit of a public folder link.
    
    Security:
    - Only the user who created the link can update it
    
    Parameters:
    - **link_id**: Hex ID of the public folder link
    - **max_downloads**: New maximum downloads (0 for unlimited)
    
    Returns:
    - Updated link metadata
    """
    try:
        link_id = link_id.strip()
        logger.info(f"[update-limit] User {current_user_id} updating limit for link {link_id[:10]}...")
        
        # Validate input
        if max_downloads < 0:
            raise HTTPException(status_code=400, detail="Max downloads must be 0 or greater")
        
        # Get link
        link = await service.get_link_by_id(link_id)
        if not link:
            raise HTTPException(status_code=404, detail="Link not found")
        
        # Verify ownership
        if link.created_by != current_user_id:
            raise HTTPException(status_code=403, detail="You don't have permission to modify this link")
        
        # Update limit in database
        await service.links_collection.update_one(
            {"link_id": link_id},
            {"$set": {"max_downloads": max_downloads}}
        )
        
        logger.info(f"[update-limit] Updated download limit to {max_downloads} for link {link_id}")
        
        return {
            "link_id": link_id,
            "token": link.token,
            "max_downloads": max_downloads,
            "download_count": link.download_count,
            "message": "Download limit updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[update-limit] Error updating limit: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update download limit: {str(e)}")

