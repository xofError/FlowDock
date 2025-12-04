"""
User endpoints for retrieving user information.
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
