"""
Public Folder Links Service - Phase 4 Implementation
Handles creating and managing public access links for folders with optional
password protection and expiration dates.
"""

import logging
import secrets
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from app.infrastructure.database.mongo_repository import MongoFolderRepository

logger = logging.getLogger(__name__)


@dataclass
class PublicFolderLink:
    """Represents a public access link for a folder"""
    link_id: str
    folder_id: str
    created_by: str
    token: str  # Unique token for the link
    password_hash: Optional[str] = None  # BCrypt hash if password protected
    created_at: datetime = None
    expires_at: Optional[datetime] = None
    max_downloads: Optional[int] = None
    download_count: int = 0
    enabled: bool = True
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def is_expired(self) -> bool:
        """Check if link has expired"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def is_download_limited(self) -> bool:
        """Check if download limit reached"""
        if self.max_downloads is None:
            return False
        return self.download_count >= self.max_downloads
    
    def is_accessible(self) -> bool:
        """Check if link is currently accessible"""
        return (
            self.enabled and
            not self.is_expired() and
            not self.is_download_limited()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB"""
        return {
            "link_id": self.link_id,
            "folder_id": self.folder_id,
            "created_by": self.created_by,
            "token": self.token,
            "password_hash": self.password_hash,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "max_downloads": self.max_downloads,
            "download_count": self.download_count,
            "enabled": self.enabled,
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "PublicFolderLink":
        """Create from dictionary"""
        link = PublicFolderLink(
            link_id=data.get("link_id"),
            folder_id=data.get("folder_id"),
            created_by=data.get("created_by"),
            token=data.get("token"),
            password_hash=data.get("password_hash"),
            created_at=data.get("created_at"),
            expires_at=data.get("expires_at"),
            max_downloads=data.get("max_downloads"),
            download_count=data.get("download_count", 0),
            enabled=data.get("enabled", True),
        )
        return link


class PublicFolderLinksService:
    """
    Service for managing public folder links.
    Provides token-based access to folders without authentication.
    
    Features:
    - Generate unique tokens for folders
    - Optional password protection
    - Expiration dates
    - Download limits
    - Access tracking
    """
    
    def __init__(self, folder_repo: MongoFolderRepository, mongo_db):
        """
        Initialize public folder links service.
        
        Args:
            folder_repo: MongoFolderRepository for folder operations
            mongo_db: MongoDB database instance
        """
        self.folder_repo = folder_repo
        self.db = mongo_db
        self.links_collection = mongo_db["public_folder_links"]
    
    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def _verify_password(password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return PublicFolderLinksService._hash_password(password) == password_hash
    
    async def create_link(
        self,
        folder_id: str,
        user_id: str,
        expires_in_days: Optional[int] = None,
        password: Optional[str] = None,
        max_downloads: Optional[int] = None,
    ) -> PublicFolderLink:
        """
        Create a public access link for a folder.
        
        Args:
            folder_id: ID of folder to create link for
            user_id: ID of user creating the link
            expires_in_days: Days until link expires (None = never)
            password: Optional password to protect access
            max_downloads: Optional maximum download count
            
        Returns:
            PublicFolderLink object
        """
        logger.info(f"[create-link] User {user_id} creating public link for folder {folder_id}")
        
        # Verify folder exists and belongs to user
        folder = await self.folder_repo.get_folder(folder_id, user_id)
        if not folder:
            raise ValueError(f"Folder {folder_id} not found or not owned by user")
        
        # Generate unique token
        token = secrets.token_urlsafe(32)
        link_id = secrets.token_hex(8)
        
        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        # Hash password if provided
        password_hash = None
        if password:
            password_hash = self._hash_password(password)
        
        # Create link object
        link = PublicFolderLink(
            link_id=link_id,
            folder_id=folder_id,
            created_by=user_id,
            token=token,
            password_hash=password_hash,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            max_downloads=max_downloads,
        )
        
        # Store in MongoDB
        await self.links_collection.insert_one(link.to_dict())
        logger.info(f"[create-link] Created link {link_id} for folder {folder_id}")
        
        return link
    
    async def get_link(self, token: str) -> Optional[PublicFolderLink]:
        """
        Retrieve a link by token.
        
        Args:
            token: The link token
            
        Returns:
            PublicFolderLink if found, None otherwise
        """
        try:
            link_data = await self.links_collection.find_one({"token": token})
            if link_data:
                return PublicFolderLink.from_dict(link_data)
            return None
        except Exception as e:
            logger.error(f"[get-link] Error retrieving link: {e}")
            return None
    
    async def get_link_by_id(self, link_id: str) -> Optional[PublicFolderLink]:
        """
        Retrieve a link by link_id (internal identifier).
        
        Args:
            link_id: The link_id (internal hex identifier)
            
        Returns:
            PublicFolderLink if found, None otherwise
        """
        try:
            link_data = await self.links_collection.find_one({"link_id": link_id})
            if link_data:
                return PublicFolderLink.from_dict(link_data)
            return None
        except Exception as e:
            logger.error(f"[get-link-by-id] Error retrieving link: {e}")
            return None
    
    async def verify_access(
        self,
        token: str,
        password: Optional[str] = None,
    ) -> bool:
        """
        Verify access to a public link.
        
        Args:
            token: The link token
            password: Password if link is protected
            
        Returns:
            True if access granted, False otherwise
        """
        logger.info(f"[verify-access] Verifying access for token {token[:10]}...")
        
        link = await self.get_link(token)
        if not link:
            logger.info(f"[verify-access] Link not found")
            return False
        
        # Check if accessible
        if not link.is_accessible():
            logger.info(f"[verify-access] Link not accessible (expired/limited/disabled)")
            return False
        
        # Check password if required
        if link.password_hash:
            if not password:
                logger.info(f"[verify-access] Password required but not provided")
                return False
            if not self._verify_password(password, link.password_hash):
                logger.info(f"[verify-access] Password incorrect")
                return False
        
        logger.info(f"[verify-access] Access verified for link {link.link_id}")
        return True
    
    async def increment_download_count(self, token: str) -> bool:
        """
        Increment download count for a link.
        
        Args:
            token: The link token
            
        Returns:
            True if successful, False if limit reached
        """
        try:
            link = await self.get_link(token)
            if not link:
                return False
            
            # Check if at limit
            if link.is_download_limited():
                logger.warning(f"[download] Link {link.link_id} download limit reached")
                return False
            
            # Increment count
            await self.links_collection.update_one(
                {"token": token},
                {"$inc": {"download_count": 1}}
            )
            
            logger.info(f"[download] Incremented downloads for link {link.link_id}")
            return True
            
        except Exception as e:
            logger.error(f"[download] Error incrementing download count: {e}")
            return False
    
    async def list_links(self, folder_id: str, user_id: str) -> list[PublicFolderLink]:
        """
        List all public links for a folder.
        
        Args:
            folder_id: Folder ID
            user_id: User ID (for ownership verification)
            
        Returns:
            List of PublicFolderLink objects
        """
        logger.info(f"[list-links] Listing links for folder {folder_id}")
        
        # Verify ownership
        folder = await self.folder_repo.get_folder(folder_id, user_id)
        if not folder:
            raise ValueError(f"User {user_id} does not own folder {folder_id}")
        
        # Get links
        links_data = await self.links_collection.find(
            {"folder_id": folder_id}
        ).to_list(None)
        
        return [PublicFolderLink.from_dict(data) for data in links_data]
    
    async def list_all_links(self, user_id: str) -> list[PublicFolderLink]:
        """
        List all public links created by a user across all folders.
        
        Args:
            user_id: User ID (owner of the links)
            
        Returns:
            List of PublicFolderLink objects
        """
        logger.info(f"[list-all-links] Listing all public links for user {user_id}")
        
        try:
            # Get all links created by this user
            links_data = await self.links_collection.find(
                {"created_by": user_id}
            ).to_list(None)
            
            return [PublicFolderLink.from_dict(data) for data in links_data]
        except Exception as e:
            logger.error(f"[list-all-links] Error listing links: {e}")
            return []
    
    async def disable_link(self, token: str, user_id: str) -> bool:
        """
        Disable a public link by token.
        
        Args:
            token: The link token
            user_id: User ID (for ownership verification)
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"[disable-link] Disabling link {token[:10]}...")
        
        try:
            link = await self.get_link(token)
            if not link:
                return False
            
            # Verify ownership
            if link.created_by != user_id:
                logger.warning(f"[disable-link] User {user_id} does not own link {link.link_id}")
                return False
            
            # Disable link
            await self.links_collection.update_one(
                {"token": token},
                {"$set": {"enabled": False}}
            )
            
            logger.info(f"[disable-link] Disabled link {link.link_id}")
            return True
            
        except Exception as e:
            logger.error(f"[disable-link] Error disabling link: {e}")
            return False
    
    async def disable_link_by_id(self, link_id: str, user_id: str) -> bool:
        """
        Disable a public link by link_id.
        
        Args:
            link_id: The link_id (internal identifier)
            user_id: User ID (for ownership verification)
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"[disable-link-by-id] Disabling link {link_id}...")
        
        try:
            link = await self.get_link_by_id(link_id)
            if not link:
                return False
            
            # Verify ownership
            if link.created_by != user_id:
                logger.warning(f"[disable-link-by-id] User {user_id} does not own link {link.link_id}")
                return False
            
            # Disable link
            await self.links_collection.update_one(
                {"link_id": link_id},
                {"$set": {"enabled": False}}
            )
            
            logger.info(f"[disable-link-by-id] Disabled link {link.link_id}")
            return True
            
        except Exception as e:
            logger.error(f"[disable-link-by-id] Error disabling link: {e}")
            return False
    
    async def delete_link(self, token: str, user_id: str) -> bool:
        """
        Delete a public link by token.
        
        Args:
            token: The link token
            user_id: User ID (for ownership verification)
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"[delete-link] Deleting link {token[:10]}...")
        
        try:
            link = await self.get_link(token)
            if not link:
                return False
            
            # Verify ownership
            if link.created_by != user_id:
                logger.warning(f"[delete-link] User {user_id} does not own link {link.link_id}")
                return False
            
            # Delete link
            result = await self.links_collection.delete_one({"token": token})
            
            logger.info(f"[delete-link] Deleted link {link.link_id}")
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"[delete-link] Error deleting link: {e}")
            return False
    
    async def delete_link_by_id(self, link_id: str, user_id: str) -> bool:
        """
        Delete a public link by link_id.
        
        Args:
            link_id: The link_id (internal identifier)
            user_id: User ID (for ownership verification)
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"[delete-link-by-id] Deleting link {link_id}...")
        
        try:
            link = await self.get_link_by_id(link_id)
            if not link:
                return False
            
            # Verify ownership
            if link.created_by != user_id:
                logger.warning(f"[delete-link-by-id] User {user_id} does not own link {link.link_id}")
                return False
            
            # Delete link
            result = await self.links_collection.delete_one({"link_id": link_id})
            
            logger.info(f"[delete-link-by-id] Deleted link {link.link_id}")
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"[delete-link-by-id] Error deleting link: {e}")
            return False

