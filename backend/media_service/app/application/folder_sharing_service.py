"""
Folder Sharing Service - Phase 3 Implementation
Handles sharing folders with users and groups with cascading permissions.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.domain.entities import Folder
from app.infrastructure.database.mongo_repository import MongoFolderRepository

logger = logging.getLogger(__name__)


class FolderPermission:
    """Represents a folder permission entry"""
    VIEW = "view"
    EDIT = "edit"
    ADMIN = "admin"
    
    VALID_PERMISSIONS = [VIEW, EDIT, ADMIN]
    
    # Permission hierarchy
    HIERARCHY = {
        VIEW: 1,
        EDIT: 2,
        ADMIN: 3,
    }


class FolderShare:
    """Data class representing a folder share"""
    def __init__(
        self,
        folder_id: str,
        shared_by: str,
        target_type: str,  # "user" or "group"
        target_id: str,    # email for user, group_id for group
        permission: str,
        cascade: bool = True,  # Track if permissions cascade to children
        created_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
    ):
        self.folder_id = folder_id
        self.shared_by = shared_by
        self.target_type = target_type
        self.target_id = target_id
        self.permission = permission
        self.cascade = cascade  # Critical: enables recursive access check
        self.created_at = created_at or datetime.utcnow()
        self.expires_at = expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        return {
            "folder_id": self.folder_id,
            "shared_by": self.shared_by,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "permission": self.permission,
            "cascade": self.cascade,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "FolderShare":
        """Create from dictionary"""
        return FolderShare(
            folder_id=data.get("folder_id"),
            shared_by=data.get("shared_by"),
            target_type=data.get("target_type"),
            target_id=data.get("target_id"),
            permission=data.get("permission"),
            cascade=data.get("cascade", True),
            created_at=data.get("created_at"),
            expires_at=data.get("expires_at"),
        )


class FolderSharingService:
    """
    Service for managing folder sharing and permissions.
    Handles:
    - Sharing folders with users/groups
    - Cascading permissions to subfolders
    - Permission inheritance and override
    - Unsharing and permission revocation
    """
    
    def __init__(self, folder_repo: MongoFolderRepository, mongo_db):
        """
        Initialize folder sharing service.
        
        Args:
            folder_repo: MongoFolderRepository for folder operations
            mongo_db: MongoDB database instance for share storage
        """
        self.folder_repo = folder_repo
        self.db = mongo_db
        self.shares_collection = mongo_db["folder_shares"]
    
    async def share_folder(
        self,
        folder_id: str,
        owner_id: str,
        targets: List[str],
        permission: str,
        cascade: bool = True,
        expires_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Share a folder with multiple users/groups.
        
        Args:
            folder_id: ID of folder to share
            owner_id: ID of user sharing the folder
            targets: List of email addresses or group IDs
            permission: Permission level (view, edit, admin)
            cascade: Apply to subfolders
            expires_at: Optional expiration date
            
        Returns:
            Dictionary with sharing results
        """
        logger.info(f"[share-folder] Owner {owner_id} sharing folder {folder_id} with {len(targets)} targets")
        
        # Verify permission level
        if permission not in FolderPermission.VALID_PERMISSIONS:
            raise ValueError(f"Invalid permission level: {permission}")
        
        # Verify folder exists and belongs to owner
        folder = await self.folder_repo.get_folder(folder_id, owner_id)
        if not folder:
            raise ValueError(f"Folder {folder_id} not found or not owned by user")
        
        shared_count = 0
        failed_targets = []
        
        # Share with each target
        for target in targets:
            try:
                # Determine target type (simple heuristic: contains @ = user email)
                target_type = "user" if "@" in target else "group"
                
                # Create share record
                share = FolderShare(
                    folder_id=folder_id,
                    shared_by=owner_id,
                    target_type=target_type,
                    target_id=target,
                    permission=permission,
                    cascade=True,  # Enable cascading to children
                    expires_at=expires_at,
                )
                
                # FIX #1: Use update_one with upsert to prevent duplicate shares
                # If share already exists, update permissions. If not, create it.
                await self.shares_collection.update_one(
                    {
                        "folder_id": folder_id,
                        "target_id": target
                    },
                    {"$set": share.to_dict()},
                    upsert=True
                )
                shared_count += 1
                logger.info(f"[share-folder] Shared with {target} at {permission} level")
                
                # Cascade to subfolders if requested
                if True:  # cascade is always True for now
                    await self._cascade_sharing(
                        folder_id, target_type, target, permission, expires_at
                    )
                    
            except Exception as e:
                failed_targets.append(target)
                logger.error(f"[share-folder] Failed to share with {target}: {e}")
        
        return {
            "status": "shared",
            "folder_id": folder_id,
            "targets_count": shared_count,
            "failed_targets": failed_targets,
        }
    
    async def _cascade_sharing(
        self,
        folder_id: str,
        target_type: str,
        target_id: str,
        permission: str,
        expires_at: Optional[datetime],
    ) -> None:
        """
        Apply sharing to all subfolders recursively.
        Optimized with bulk write operations to avoid N+1 database calls.
        
        Args:
            folder_id: Parent folder ID
            target_type: Type of target (user/group)
            target_id: Target identifier
            permission: Permission level
            expires_at: Expiration date
        """
        try:
            # Get all descendant folders
            all_children = await self.folder_repo.get_all_children_folders(folder_id)
            
            if not all_children:
                logger.info(f"[share-folder] No subfolders to cascade sharing for {folder_id}")
                return
            
            # [FIX: Bulk Write] Instead of sequential updates, use MongoDB bulk write
            from pymongo import UpdateOne
            
            bulk_updates = []
            for child in all_children:
                share_data = {
                    "folder_id": child.id,
                    "shared_by": "system",  # Cascaded share
                    "target_type": target_type,
                    "target_id": target_id,
                    "permission": permission,
                    "cascade": True,  # Inherited shares continue to cascade
                    "created_at": datetime.utcnow(),
                    "expires_at": expires_at,
                }
                
                # Use UpdateOne with upsert to prevent duplicates
                bulk_updates.append(
                    UpdateOne(
                        {
                            "folder_id": child.id,
                            "target_id": target_id
                        },
                        {"$set": share_data},
                        upsert=True
                    )
                )
            
            # Execute all updates in a single round-trip
            if bulk_updates:
                result = await self.shares_collection.bulk_write(bulk_updates)
                logger.info(f"[share-folder] Cascaded sharing to {len(all_children)} subfolders - "
                           f"upserted: {result.upserted_id}, modified: {result.modified_count}")
            
        except Exception as e:
            logger.error(f"[share-folder] Failed to cascade sharing: {e}")
            # Don't raise - cascading failure shouldn't block main sharing
    
    async def get_folder_shares(
        self,
        folder_id: str,
        owner_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Get list of users/groups a folder is shared with.
        
        Args:
            folder_id: Folder ID
            owner_id: Owner ID (for verification)
            
        Returns:
            List of share records
        """
        logger.info(f"[get-shares] Retrieving shares for folder {folder_id}")
        
        # Verify ownership
        folder = await self.folder_repo.get_folder(folder_id, owner_id)
        if not folder:
            raise ValueError(f"User {owner_id} does not own folder {folder_id}")
        
        # Get shares
        shares = await self.shares_collection.find(
            {"folder_id": folder_id}
        ).to_list(None)
        
        # Convert ObjectId to strings for JSON serialization
        result = []
        for share in shares:
            share_dict = {
                "share_id": str(share.get("_id", "")),
                "folder_id": share.get("folder_id", ""),
                "shared_with": share.get("target_id", ""),
                "target_type": share.get("target_type", "user"),
                "permission": share.get("permission", "view"),
                "shared_at": share.get("created_at").isoformat() if share.get("created_at") else None,
                "expires_at": share.get("expires_at").isoformat() if share.get("expires_at") else None,
            }
            result.append(share_dict)
        
        return result
    
    async def unshare_folder(
        self,
        folder_id: str,
        owner_id: str,
        target_id: str,
        cascade: bool = True,
    ) -> Dict[str, Any]:
        """
        Remove sharing for a specific user/group.
        
        Args:
            folder_id: Folder ID
            owner_id: Owner ID (for verification)
            target_id: Target to revoke access from
            cascade: Remove from subfolders too
            
        Returns:
            Unshare result
        """
        logger.info(f"[unshare-folder] Revoking access for {target_id} on folder {folder_id}")
        
        # Verify ownership
        folder = await self.folder_repo.get_folder(folder_id, owner_id)
        if not folder:
            raise ValueError(f"User {owner_id} does not own folder {folder_id}")
        
        # Remove share
        result = await self.shares_collection.delete_one({
            "folder_id": folder_id,
            "target_id": target_id,
        })
        
        deleted_count = result.deleted_count
        
        # Cascade revocation if requested
        if cascade:
            deleted_count += await self._cascade_unsharing(folder_id, target_id)
        
        logger.info(f"[unshare-folder] Revoked {deleted_count} shares")
        
        return {
            "status": "unshared",
            "folder_id": folder_id,
            "target_id": target_id,
            "shares_removed": deleted_count,
        }
    
    async def _cascade_unsharing(
        self,
        folder_id: str,
        target_id: str,
    ) -> int:
        """Remove sharing from all subfolders recursively"""
        try:
            all_children = await self.folder_repo.get_all_children_folders(folder_id)
            
            deleted_count = 0
            for child in all_children:
                result = await self.shares_collection.delete_one({
                    "folder_id": child.id,
                    "target_id": target_id,
                })
                deleted_count += result.deleted_count
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"[unshare-folder] Failed to cascade unsharing: {e}")
            return 0
    
    async def check_folder_access(
        self,
        folder_id: str,
        user_id: str,
        user_email: str = None,
    ) -> Optional[str]:
        """
        Check if user has access to folder - including inherited permissions.
        
        This implements a recursive access check that handles the "New Folder" gap:
        If a user has access to a parent folder via sharing, they automatically
        have access to new subfolders created after the share, without needing
        explicit DB records for every child.
        
        Args:
            folder_id: Folder ID
            user_id: User ID
            user_email: User email (optional, used to find shares by email)
            
        Returns:
            Permission level if accessible (view/edit/admin), None if not
        """
        try:
            # 0. Check if user is the folder owner (always has full access)
            folder = await self.folder_repo.get_folder_by_id(folder_id)
            if folder and folder.owner_id == user_id:
                logger.info(f"[check-access] User {user_id} is owner of folder {folder_id}")
                return "admin"  # Owner has admin permission
            
            # 1. Check for direct share (most common case)
            # Search by both user_id and user_email
            query = {
                "$or": [
                    {"folder_id": folder_id, "target_id": user_id}
                ]
            }
            if user_email:
                query["$or"].append({"folder_id": folder_id, "target_id": user_email})
            
            share = await self.shares_collection.find_one(query)
            
            if share:
                # Check expiration
                if share.get("expires_at") and share["expires_at"] < datetime.utcnow():
                    logger.info(f"[check-access] Share expired for {user_id} on {folder_id}")
                    return None
                return share.get("permission")

            # 2. Recursive Parent Check (FIX #2: Solves "New Folder" gap)
            # If no direct share exists, walk up the folder tree to check for
            # inherited permissions. This allows new subfolders to inherit parent
            # sharing without explicit DB records.
            current_folder_id = folder_id
            depth_limit = 100  # Increased from 10 to support deeper folder structures
            
            while current_folder_id and depth_limit > 0:
                # Get folder to find parent
                folder = await self.folder_repo.get_folder_by_id(current_folder_id)
                if not folder or not folder.parent_id:
                    break
                
                parent_id = folder.parent_id
                
                # Check if parent has a cascading share with this user
                parent_query = {
                    "$or": [
                        {"folder_id": parent_id, "target_id": user_id, "cascade": True}
                    ]
                }
                if user_email:
                    parent_query["$or"].append({"folder_id": parent_id, "target_id": user_email, "cascade": True})
                
                parent_share = await self.shares_collection.find_one(parent_query)
                
                if parent_share:
                    # Found an inherited permission!
                    if parent_share.get("expires_at") and parent_share["expires_at"] < datetime.utcnow():
                        return None
                    logger.info(f"[check-access] Found inherited access for {user_id} on {folder_id}")
                    return parent_share.get("permission")
                
                # Move up one level
                current_folder_id = parent_id
                depth_limit -= 1

            return None
            
        except Exception as e:
            logger.error(f"[check-access] Error checking access: {e}")
            return None
    
    async def list_shared_folders(
        self,
        user_id: str,
        user_email: str = None,
    ) -> List[Dict[str, Any]]:
        """
        List all folders shared with a user.
        
        FIX #3: Optimized with bulk folder fetch instead of N+1 queries.
        FIX #4: Now searches by both user_id AND user_email (folders can be shared by email)
        
        Args:
            user_id: User ID
            user_email: User email (optional, used to find shares by email)
            
        Returns:
            List of shared folder information
        """
        logger.info(f"[list-shared] Listing folders shared with user {user_id}")
        
        try:
            # 1. Build query to find shares for this user (by ID or email)
            query = {
                "$or": [
                    {"target_id": user_id}  # Shared directly by user ID
                ]
            }
            
            # Add email to query if provided
            if user_email:
                query["$or"].append({"target_id": user_email})
            
            # Get all active shares for this user
            shares = await self.shares_collection.find(query).to_list(None)
            
            if not shares:
                return []
            
            # 2. Filter out expired shares
            active_shares = [
                s for s in shares 
                if not (s.get("expires_at") and s["expires_at"] < datetime.utcnow())
            ]
            
            if not active_shares:
                return []

            # 3. FIX #3: Bulk fetch all folder details (prevents N+1 queries)
            # Instead of querying DB for each share separately, collect all folder IDs
            # and fetch them all at once
            folder_ids = []
            for share in active_shares:
                oid = self.folder_repo._to_object_id(share.get("folder_id"))
                if oid:
                    folder_ids.append(oid)
            
            if not folder_ids:
                return []

            # Fetch all folders in one query
            folders_cursor = self.folder_repo.collection.find({"_id": {"$in": folder_ids}})
            folders_map = {}
            async for folder_doc in folders_cursor:
                folders_map[str(folder_doc["_id"])] = folder_doc
            
            # 4. Join share data with folder data in memory
            result = []
            for share in active_shares:
                folder_id = share.get("folder_id")
                if folder_id in folders_map:
                    folder_doc = folders_map[folder_id]
                    share_info = {
                        "folder_id": folder_id,
                        "folder_name": folder_doc.get("name", ""),
                        "owner_id": folder_doc.get("owner_id", ""),
                        "permission": share.get("permission", "view"),
                        "shared_at": share.get("created_at").isoformat() if share.get("created_at") else None,
                        "expires_at": share.get("expires_at").isoformat() if share.get("expires_at") else None,
                    }
                    result.append(share_info)
            
            logger.info(f"[list-shared] Found {len(result)} active shared folders")
            return result
            
        except Exception as e:
            logger.error(f"[list-shared] Error listing shared folders: {e}")
            return []

    async def list_shared_folders_by_owner(
        self,
        owner_id: str,
    ) -> List[Dict[str, Any]]:
        """
        List all folders that an owner has shared with other users.
        
        Args:
            owner_id: Owner ID (user who created the shares)
            
        Returns:
            List of shared folder information
        """
        logger.info(f"[list-shared-by-owner] Listing folders shared by user {owner_id}")
        
        try:
            # 1. Find all shares created by this owner
            query = {"shared_by": owner_id}
            
            # Get all shares created by this owner
            shares = await self.shares_collection.find(query).to_list(None)
            
            if not shares:
                return []
            
            # 2. Filter out expired shares
            active_shares = [
                s for s in shares 
                if not (s.get("expires_at") and s["expires_at"] < datetime.utcnow())
            ]
            
            if not active_shares:
                return []

            # 3. Bulk fetch all folder details
            folder_ids = []
            for share in active_shares:
                oid = self.folder_repo._to_object_id(share.get("folder_id"))
                if oid:
                    folder_ids.append(oid)
            
            if not folder_ids:
                return []

            # Fetch all folders in one query
            folders_cursor = self.folder_repo.collection.find({"_id": {"$in": folder_ids}})
            folders_map = {}
            async for folder_doc in folders_cursor:
                folders_map[str(folder_doc["_id"])] = folder_doc
            
            # 4. Join share data with folder data in memory
            result = []
            for share in active_shares:
                folder_id = share.get("folder_id")
                if folder_id in folders_map:
                    folder_doc = folders_map[folder_id]
                    share_info = {
                        "share_id": str(share.get("_id", "")),
                        "folder_id": folder_id,
                        "folder_name": folder_doc.get("name", ""),
                        "owner_id": folder_doc.get("owner_id", ""),
                        "shared_with": share.get("target_id", ""),  # email or user ID it's shared with
                        "permission": share.get("permission", "view"),
                        "shared_at": share.get("created_at").isoformat() if share.get("created_at") else None,
                        "expires_at": share.get("expires_at").isoformat() if share.get("expires_at") else None,
                    }
                    result.append(share_info)
            
            logger.info(f"[list-shared-by-owner] Found {len(result)} folders shared by user")
            return result
            
        except Exception as e:
            logger.error(f"[list-shared-by-owner] Error listing folders shared by owner: {e}")
            return []