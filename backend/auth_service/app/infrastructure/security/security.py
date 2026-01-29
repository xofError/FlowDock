"""
Infrastructure Layer: Security Implementations

Implementations of password hashing and JWT token operations.
"""

import hmac
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
from uuid import UUID

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings
from app.domain.interfaces import IPasswordHasher, ITokenGenerator


JWT_SECRET = settings.secret_key
JWT_ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_DAYS = 30  # You can add this to settings if needed

# Argon2 password hashing
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class ArgonPasswordHasher(IPasswordHasher):
    """Argon2 password hashing implementation."""

    def hash(self, password: str) -> str:
        """Hash a password using Argon2."""
        return pwd_context.hash(password)

    def verify(self, password: str, hashed: str) -> bool:
        """Verify a password against its Argon2 hash."""
        return pwd_context.verify(password, hashed)


class JWTTokenGenerator(ITokenGenerator):
    """JWT token generation and validation."""

    def _ensure_jwt_secret(self) -> None:
        if not JWT_SECRET:
            raise RuntimeError("JWT_SECRET environment variable is not set")

    def create_access_token(self, user_id: UUID, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token with optional custom expiry."""
        self._ensure_jwt_secret()
        now = datetime.now(timezone.utc)
        
        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        payload: Dict[str, Any] = {
            "sub": str(user_id),
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
            "type": "access",
        }

        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    def create_2fa_pending_token(self, user_id: UUID, expires_delta: Optional[timedelta] = None) -> str:
        """Create a temporary token scoped only for 2FA verification (valid for 5 minutes)."""
        self._ensure_jwt_secret()
        now = datetime.now(timezone.utc)
        
        # 2FA pending tokens expire in 5 minutes
        if expires_delta is None:
            expires_delta = timedelta(minutes=5)
        
        expire = now + expires_delta

        payload: Dict[str, Any] = {
            "sub": str(user_id),
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
            "type": "2fa_pending",
        }

        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    def verify_2fa_pending_token(self, token: str) -> Optional[str]:
        """Verify a 2FA pending token and return user_id if valid."""
        self._ensure_jwt_secret()
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            if payload.get("type") != "2fa_pending":
                return None
            return payload.get("sub")
        except JWTError:
            return None

    def decode_access_token(self, token: str) -> Optional[Dict]:
        """Decode and validate an access token."""
        self._ensure_jwt_secret()
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except JWTError:
            return None

    def create_refresh_token(self, user_id: UUID) -> Tuple[str, str, datetime]:
        """Create a refresh token.
        
        Returns:
            (plaintext_token, hashed_token, expiry_datetime)
        """
        token = secrets.token_urlsafe(40)
        hashed = self._hash_token(token)
        expiry = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        return token, hashed, expiry

    def verify_refresh_token(self, token: str, stored_hash: str) -> bool:
        """Verify a refresh token against its stored hash."""
        candidate = self._hash_token(token)
        return hmac.compare_digest(candidate, stored_hash)

    @staticmethod
    def _hash_token(token: str) -> str:
        """Hash a token for storage."""
        return hashlib.sha256(token.encode("utf-8")).hexdigest()
