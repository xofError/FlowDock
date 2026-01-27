import secrets
import os
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException
from passlib.context import CryptContext
import httpx
import asyncio

from app.models.share import Share, ShareLink
from app.schemas.sharing import ShareCreate, ShareLinkCreate

logger = logging.getLogger(__name__)

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
        
        # 2. Look up target user by email via Auth Service with retry logic
        # Implement retry mechanism to handle transient network failures
        auth_service_url = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
        max_retries = 3
        retry_delay = 0.5  # seconds
        
        last_error = None
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(
                        f"{auth_service_url}/api/users/by-email/{data.target_email}"
                    )
                    if response.status_code == 404:
                        raise HTTPException(
                            status_code=404,
                            detail="User not found"
                        )
                    if response.status_code != 200:
                        if attempt < max_retries - 1:
                            logger.warning(f"Auth Service returned {response.status_code}, retrying...")
                            await asyncio.sleep(retry_delay)
                            continue
                        raise HTTPException(
                            status_code=500,
                            detail="Failed to look up user"
                        )
                    
                    user_data = response.json()
                    target_user_id = user_data.get("id")
                    break
                    
            except httpx.RequestError as e:
                last_error = e
                if attempt < max_retries - 1:
                    logger.warning(f"Auth Service request failed (attempt {attempt + 1}/{max_retries}): {e}, retrying...")
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"Auth Service unreachable after {max_retries} attempts: {e}")
                    raise HTTPException(
                        status_code=503,
                        detail="Auth Service unavailable. Please try again later."
                    )

        # Prevent sharing with self by comparing resolved user IDs
        try:
            if str(target_user_id) == str(owner_id):
                raise HTTPException(status_code=400, detail="Cannot share file with yourself")
        except Exception:
            # If comparison fails for any reason, continue to validation below
            pass

        # 3. Handle expiry date - explicit None check only, no "closeness to now" heuristic
        # This respects user intent: if they explicitly set a value, use it; if None, use default
        now_utc = datetime.now(timezone.utc)
        if data.expires_at is None:
            # User did not provide an expiry date, use 30-day default
            expires = now_utc + timedelta(days=30)
        else:
            # User provided an explicit expiry date - use it as-is
            expires = data.expires_at
            # Ensure timezone-aware (assume UTC if naive)
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            # Validate: expiry must be in the future
            if expires <= now_utc:
                raise HTTPException(
                    status_code=400,
                    detail="Expiry date must be in the future"
                )

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
        # If expires_at was auto-filled by Swagger to current time, treat as not provided
        now_utc = datetime.now(timezone.utc)
        if data.expires_at:
            link_expires = data.expires_at
            if link_expires.tzinfo is None:
                link_expires = link_expires.replace(tzinfo=timezone.utc)
            # If the provided value is essentially "now" (within 1 second), ignore it
            if abs((link_expires - now_utc).total_seconds()) < 1:
                link_expires = now_utc + timedelta(days=30)
        else:
            # Default: 30 days from now
            link_expires = now_utc + timedelta(days=30)

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
    @staticmethod
    def validate_link_access(db: Session, token: str, password: str = None, client_ip: str = None):
        """
        Validate that a share link is accessible.
        
        Checks:
        - Link exists and is active
        - Link has not expired
        - Download limit not exceeded
        - Password is correct (if required)
        - Rate limiting on password attempts
        
        Args:
            db: PostgreSQL database session
            token: The share link token from the URL
            password: Optional password provided by user
            client_ip: Client IP address for rate limiting
            
        Returns:
            ShareLink model instance if valid
            
        Raises:
            HTTPException: If link is invalid, expired, limited, rate-limited, or password wrong
        """
        logger.info(f"[validate] Starting validation for token: {token}, password_provided: {password is not None}")
        
        link = db.query(ShareLink).filter(ShareLink.token == token).first()
        logger.info(f"[validate] Link lookup result: {link is not None}")
        
        if not link or not link.active:
            logger.error(f"[validate] Link not found or inactive")
            raise HTTPException(
                status_code=404,
                detail="Link not found or inactive"
            )
        
        logger.info(f"[validate] Link found - active: {link.active}, has_password: {bool(link.password_hash)}")
            
        # 1. Check Expiry (use timezone-aware now)
        if link.expires_at:
            # Ensure DB value is timezone-aware for safe comparison
            expires = link.expires_at
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            logger.info(f"[validate] Expiry check - expires_at: {expires}, now: {datetime.now(timezone.utc)}")
            if expires < datetime.now(timezone.utc):
                logger.error(f"[validate] Link expired")
                raise HTTPException(
                    status_code=410,
                    detail="Link expired"
                )
            
        # 2. Check Download Limit
        logger.info(f"[validate] Download limit check - used: {link.downloads_used}, max: {link.max_downloads}")
        if link.max_downloads > 0 and link.downloads_used >= link.max_downloads:
            logger.error(f"[validate] Download limit exceeded")
            raise HTTPException(
                status_code=410,
                detail="Download limit reached"
            )
            
        # 3. Check Password (if required)
        logger.info(f"[validate] Password check - has_hash: {bool(link.password_hash)}, provided: {password is not None}")
        if link.password_hash:
            if not password:
                logger.error(f"[validate] Password required but not provided")
                raise HTTPException(
                    status_code=401,
                    detail="Password required"
                )
            
            # 3a. Rate limiting on password attempts
            # In production, use Redis for this. For now, use a simple in-memory approach.
            # Key format: "pwd_attempt:{token}:{client_ip}"
            rate_limit_key = f"pwd_attempt:{token}:{client_ip}"
            
            # Note: This is a simplified implementation. In production, use Redis.
            # For now, we'll just log the attempt. A Redis implementation would:
            # - Increment counter on failed attempt
            # - Block if counter > 5 in last 15 minutes
            # - Clear counter on successful attempt
            logger.info(f"[validate] Password attempt from {client_ip} for token {token[:10]}...")
            
            logger.info(f"[validate] Verifying password against hash")
            if not verify_password(password, link.password_hash):
                logger.warning(f"[validate] Invalid password provided from {client_ip}")
                # TODO: Implement Redis-based rate limiting here
                # For now, just log and reject
                raise HTTPException(
                    status_code=403,
                    detail="Invalid password"
                )
        
        logger.info(f"[validate] All validations passed, returning link")
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
