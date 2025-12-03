"""
Security utilities for JWT validation and token verification in Media Service.
Validates JWT tokens issued by Auth Service and verifies user ownership.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from typing import Dict, Any, Optional
import os

# JWT configuration - matches Auth Service
JWT_SECRET = os.getenv("JWT_SECRET", "secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

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
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
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
