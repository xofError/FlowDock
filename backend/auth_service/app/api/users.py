"""
User endpoints for retrieving user information and sharing data.
These endpoints support the Media Service's need to look up users and sharing information.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import Generator, List, Optional
from app.database import SessionLocal
from app.models.user import User
from app.schemas.user import UserResponse
from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime

router = APIRouter()


# ============================================================================
# Schemas
# ============================================================================
class UserPublicInfo(BaseModel):
    """Public user information (limited fields)"""
    id: UUID
    email: EmailStr
    full_name: Optional[str] = None

    class Config:
        orm_mode = True


class FileMetadataResponse(BaseModel):
    """Basic file metadata (owner's view)"""
    file_id: str
    file_name: Optional[str] = None
    size: Optional[int] = None
    created_at: Optional[datetime] = None


class SharedFileInfo(BaseModel):
    """Information about a file shared with the user"""
    file_id: str
    shared_by_user_id: UUID
    shared_by_email: Optional[str] = None
    permission: str
    expires_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        orm_mode = True


class FileSharedByUserInfo(BaseModel):
    """Information about a file the user shared with others"""
    file_id: str
    shared_with_user_id: UUID
    shared_with_email: Optional[str] = None
    permission: str
    expires_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        orm_mode = True


class ShareLinkInfo(BaseModel):
    """Information about a public share link"""
    id: UUID
    file_id: str
    token: str
    has_password: bool
    expires_at: Optional[datetime] = None
    max_downloads: int
    downloads_used: int
    active: bool
    created_at: datetime

    class Config:
        orm_mode = True


# ============================================================================
# Dependencies
# ============================================================================
def get_db() -> Generator[Session, None, None]:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/api/users/by-email/{email}", response_model=UserPublicInfo)
def get_user_by_email(email: str, db: Session = Depends(get_db)):
    """
    Look up a user by email address.
    
    Used by Media Service to resolve email addresses to user IDs for sharing.
    
    Args:
        email: User's email address
        
    Returns:
        UserPublicInfo with id, email, full_name
        
    Raises:
        HTTPException 404: User not found
    """
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email '{email}' not found"
        )
    
    return user


@router.get("/api/users/{user_id}", response_model=UserResponse)
def get_user_by_id(user_id: UUID, db: Session = Depends(get_db)):
    """
    Get user information by ID.
    
    Args:
        user_id: User UUID
        
    Returns:
        UserResponse with full user information
        
    Raises:
        HTTPException 404: User not found
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' not found"
        )
    
    return user


@router.get("/api/users/{user_id}/files", response_model=List[FileMetadataResponse])
def get_user_files(user_id: UUID, db: Session = Depends(get_db)):
    """
    Get all files owned by a user.
    
    This endpoint returns metadata about files the user has uploaded.
    File metadata is stored in MongoDB, but this endpoint provides
    a reference point for listing files.
    
    Args:
        user_id: User UUID
        
    Returns:
        List of FileMetadataResponse objects
        
    Raises:
        HTTPException 404: User not found
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' not found"
        )
    
    # NOTE: File metadata is stored in MongoDB (GridFS)
    # This endpoint returns an empty list because the actual file list
    # should be retrieved from the Media Service's MongoDB database.
    # In a production system, you might maintain a reference table
    # in PostgreSQL that maps user_id to file_ids for quick lookups.
    
    # For now, return empty list - Media Service will handle file listing
    return []


@router.get("/api/users/{user_id}/files/shared-with-me", response_model=List[SharedFileInfo])
def get_files_shared_with_user(user_id: UUID, db: Session = Depends(get_db)):
    """
    Get all files that have been shared with the user by others.
    
    NOTE: Sharing data is now stored exclusively in Media Service.
    For sharing information, query the Media Service endpoints directly.
    This endpoint is kept for API contract compatibility and returns an empty list.
    
    Args:
        user_id: User UUID
        
    Returns:
        Empty list (sharing data is in Media Service)
        
    Raises:
        HTTPException 404: User not found
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' not found"
        )
    
    # Sharing data is now in Media Service only
    return []


@router.get("/api/users/{user_id}/files/shared-by-me", response_model=List[FileSharedByUserInfo])
def get_files_shared_by_user(user_id: UUID, db: Session = Depends(get_db)):
    """
    Get all files that the user has shared with others.
    
    NOTE: Sharing data is now stored exclusively in Media Service.
    For sharing information, query the Media Service endpoints directly.
    This endpoint is kept for API contract compatibility and returns an empty list.
    
    Args:
        user_id: User UUID
        
    Returns:
        Empty list (sharing data is in Media Service)
        
    Raises:
        HTTPException 404: User not found
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' not found"
        )
    
    # Sharing data is now in Media Service only
    return []


@router.get("/api/users/{user_id}/share-links", response_model=List[ShareLinkInfo])
def get_user_share_links(user_id: UUID, db: Session = Depends(get_db)):
    """
    Get all public share links created by the user.
    
    NOTE: Sharing data is now stored exclusively in Media Service.
    For sharing information, query the Media Service endpoints directly.
    This endpoint is kept for API contract compatibility and returns an empty list.
    
    Args:
        user_id: User UUID
        
    Returns:
        Empty list (sharing data is in Media Service)
        
    Raises:
        HTTPException 404: User not found
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' not found"
        )
    
    # Sharing data is now in Media Service only
    return []
