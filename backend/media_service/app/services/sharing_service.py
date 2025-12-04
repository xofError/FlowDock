import secrets
import os
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException
from passlib.context import CryptContext
import httpx

from app.models.share import Share, ShareLink
from app.schemas.sharing import ShareCreate, ShareLinkCreate

# Use Argon2 for password hashing (same as auth_service)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash password using Argon2"""
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(password, hashed)


class SharingService:
    """
    Service for handling file sharing logic.
    
    Supports two sharing modes:
    1. Direct Sharing: Grant specific users access to a file
    2. Public Links: Create a public URL with optional password protection
    """
    
    # ============================================================================
    # DIRECT SHARING: Share with specific user
    # ============================================================================
    @staticmethod
    async def share_file(db: Session, owner_id: str, owner_email: str, data: ShareCreate):
        """
        Share a file with a specific user.
        
        Args:
            db: PostgreSQL database session
            owner_id: UUID of the user sharing the file
            owner_email: Email of the owner (for validation)
            data: ShareCreate schema with target email and permission
            
        Returns:
            Share model instance
            
        Raises:
            HTTPException: If user not found or trying to share with self
        """
        # 1. Prevent sharing with self
        if data.target_email == owner_email:
            raise HTTPException(
                status_code=400,
                detail="Cannot share file with yourself"
            )
        
        # 2. Look up target user by email via Auth Service
        # Note: In a production system, you might want to cache this or use
        # a shared database. For now, we'll create the share record with the
        # email and let the recipient claim it, or use a service-to-service call.
        auth_service_url = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{auth_service_url}/api/users/by-email/{data.target_email}",
                    timeout=5.0
                )
                if response.status_code == 404:
                    raise HTTPException(
                        status_code=404,
                        detail="User not found"
                    )
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to look up user"
                    )
                
                user_data = response.json()
                target_user_id = user_data.get("id")
                
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=500,
                detail="Unable to reach Auth Service"
            )

        # 3. Normalize/validate expires_at and create share record
        if data.expires_at:
            expires = data.expires_at
            # Ensure timezone-aware (assume UTC if naive)
            if expires.tzinfo is None:
                expires = datetime.now(timezone.utc) + timedelta(days=30)
        else:
            # Default: 30 days from now
            expires = datetime.now(timezone.utc) + timedelta(days=30)

        new_share = Share(
            file_id=data.file_id,
            shared_by_user_id=owner_id,
            shared_with_user_id=target_user_id,
            permission=data.permission,
            expires_at=expires
        )
        db.add(new_share)
        db.commit()
        db.refresh(new_share)
        return new_share

    # ============================================================================
    # PUBLIC LINKS: Create shareable link with optional password
    # ============================================================================
    @staticmethod
    def create_link(db: Session, user_id: str, data: ShareLinkCreate):
        """
        Create a public share link for a file.
        
        Args:
            db: PostgreSQL database session
            user_id: UUID of the user creating the link
            data: ShareLinkCreate schema with optional password and expiry
            
        Returns:
            ShareLink model instance
        """
        # 1. Generate unique URL token (e.g., 'D5s_8s7d_jK2p...')
        token = secrets.token_urlsafe(16)
        
        # 2. Hash password if provided (using Argon2 via auth_service)
        pwd_hash = hash_password(data.password) if data.password else None
        
        # 3. Normalize/validate expires_at and create share link record
        if data.expires_at:
            link_expires = data.expires_at
            if link_expires.tzinfo is None:
                link_expires = link_expires = datetime.now(timezone.utc) + timedelta(days=30)
        else:
            # Default: 30 days from now
            link_expires = datetime.now(timezone.utc) + timedelta(days=30)

        link = ShareLink(
            file_id=data.file_id,
            created_by_user_id=user_id,
            token=token,
            password_hash=pwd_hash,
            expires_at=link_expires,
            max_downloads=data.max_downloads
        )
        db.add(link)
        db.commit()
        db.refresh(link)
        return link

    @staticmethod
    def validate_link_access(db: Session, token: str, password: str = None):
        """
        Validate that a share link is accessible.
        
        Checks:
        - Link exists and is active
        - Link has not expired
        - Download limit not exceeded
        - Password is correct (if required)
        
        Args:
            db: PostgreSQL database session
            token: The share link token from the URL
            password: Optional password provided by user
            
        Returns:
            ShareLink model instance if valid
            
        Raises:
            HTTPException: If link is invalid, expired, limited, or password wrong
        """
        link = db.query(ShareLink).filter(ShareLink.token == token).first()
        
        if not link or not link.active:
            raise HTTPException(
                status_code=404,
                detail="Link not found or inactive"
            )
            
        # 1. Check Expiry (use timezone-aware now)
        if link.expires_at:
            # Ensure DB value is timezone-aware for safe comparison
            expires = link.expires_at
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if expires < datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=410,
                    detail="Link expired"
                )
            
        # 2. Check Download Limit
        if link.max_downloads > 0 and link.downloads_used >= link.max_downloads:
            raise HTTPException(
                status_code=410,
                detail="Download limit reached"
            )
            
        # 3. Check Password (if required)
        if link.password_hash:
            if not password:
                raise HTTPException(
                    status_code=401,
                    detail="Password required"
                )
            if not verify_password(password, link.password_hash):
                raise HTTPException(
                    status_code=403,
                    detail="Invalid password"
                )
                
        return link

    @staticmethod
    def increment_download_count(db: Session, token: str):
        """
        Increment the download counter for a share link.
        
        Args:
            db: PostgreSQL database session
            token: The share link token
        """
        link = db.query(ShareLink).filter(ShareLink.token == token).first()
        if link:
            link.downloads_used += 1
            db.commit()
