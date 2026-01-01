"""
Security utilities for JWT validation and token verification in Media Service.
Validates JWT tokens issued by Auth Service and verifies user ownership.
"""

from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from typing import Dict, Any, Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# JWT configuration - matches Auth Service
JWT_SECRET = settings.jwt_secret
JWT_ALGORITHM = settings.jwt_algorithm

security = HTTPBearer()


def decode_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate JWT token (matches Auth Service pattern).
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload or None if invalid
    """
    try:
        logger.info(f"[decode] Attempting to decode token with secret length: {len(JWT_SECRET)}, algo: {JWT_ALGORITHM}")
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        logger.info(f"[decode] Token decoded successfully")
        return payload
    except JWTError as e:
        logger.error(f"[decode] JWT decode failed: {e}")
        return None


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    FastAPI dependency to verify JWT token from Authorization header.
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid, expired, or malformed
    """
    token = credentials.credentials
    payload = decode_jwt_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload


async def get_current_user_id(token_payload: Dict[str, Any] = Depends(verify_token)) -> str:
    """
    FastAPI dependency to extract and validate user_id from JWT token.
    
    Args:
        token_payload: Decoded JWT payload
        
    Returns:
        User ID (UUID) from token 'sub' field
        
    Raises:
        HTTPException: If user_id not found in token
    """
    user_id = token_payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token"
        )
    return user_id


def verify_user_ownership(token_user_id: str, requested_user_id: str) -> bool:
    """
    Verify that the token user_id matches the requested user_id.
    Prevents users from uploading/deleting files for other users.
    
    Args:
        token_user_id: User ID from JWT token
        requested_user_id: User ID from request path/params
        
    Returns:
        True if ownership matches
        
    Raises:
        HTTPException: If user_id mismatch (403 Forbidden)
    """
    if token_user_id != requested_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: cannot access other users' files"
        )
    return True


def create_download_token(file_id: str) -> str:
    """
    Generates a short-lived (1 minute) token that grants access 
    to download a SINGLE specific file.
    
    Args:
        file_id: MongoDB ObjectId or identifier of the file to download
        
    Returns:
        JWT token string
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=1)

    payload = {
        "sub": "download_permit",
        "file_id": file_id,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "type": "download"
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_download_token(token: str, file_id: str) -> bool:
    """
    Verifies the token is valid, not expired, AND is for the correct file.
    
    Args:
        token: JWT token string to verify
        file_id: The file_id that should be contained in the token
        
    Returns:
        True if token is valid and matches the file_id, False otherwise
    """
    logger.info(f"[verify_token] Starting verification - token: {token[:50]}..., file_id: {file_id}")
    
    payload = decode_jwt_token(token)
    logger.info(f"[verify_token] Decoded payload: {payload}")
    
    if not payload:
        logger.error(f"[verify_token] Failed to decode token")
        return False
    
    token_type = payload.get("type")
    logger.info(f"[verify_token] Token type: {token_type} (expected: download)")
    
    if token_type != "download":
        logger.error(f"[verify_token] Wrong token type: {token_type}")
        return False
    
    token_file_id = payload.get("file_id")
    logger.info(f"[verify_token] Token file_id: {token_file_id}, path file_id: {file_id}")
    
    if token_file_id != file_id:
        logger.error(f"[verify_token] File ID mismatch: {token_file_id} != {file_id}")
        return False
    
    logger.info(f"[verify_token] Token verification PASSED")
    return True