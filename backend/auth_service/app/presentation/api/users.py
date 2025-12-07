"""
Presentation Layer: User API Routes

These routes use the clean architecture services to provide user information.
Used by Media Service for user resolution and internal APIs.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr

from app.presentation.dependencies import get_db, get_user_repository
from sqlalchemy.orm import Session

router = APIRouter()


# ============ DTOs ============

class UserPublicInfo(BaseModel):
    """Public user information (limited fields for external services)."""
    id: str
    email: str
    full_name: Optional[str] = None

    class Config:
        from_attributes = True


class UserDetailResponse(BaseModel):
    """Detailed user information for authenticated requests."""
    id: str
    email: str
    full_name: Optional[str] = None
    verified: bool
    twofa_enabled: bool
    storage_used: int
    storage_limit: int
    created_at: Optional[datetime] = None


# ============ Endpoints ============

@router.get("/api/users/by-email/{email}", response_model=UserPublicInfo)
def get_user_by_email(
    email: str,
    db: Session = Depends(get_db),
    user_repo = Depends(get_user_repository),
):
    """
    Look up a user by email address.
    
    Used by Media Service to resolve email addresses to user IDs.
    Returns limited public information.
    
    Args:
        email: User's email address
        
    Returns:
        UserPublicInfo with id, email, full_name
        
    Raises:
        HTTPException 404: User not found
    """
    user = user_repo.get_by_email(email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email '{email}' not found",
        )
    
    return UserPublicInfo(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
    )


@router.get("/api/users/{user_id}", response_model=UserDetailResponse)
def get_user_by_id(
    user_id: UUID,
    db: Session = Depends(get_db),
    user_repo = Depends(get_user_repository),
):
    """
    Get detailed user information by ID.
    
    Args:
        user_id: User UUID
        
    Returns:
        UserDetailResponse with full user information
        
    Raises:
        HTTPException 404: User not found
    """
    user = user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found",
        )
    
    return UserDetailResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        verified=user.verified,
        twofa_enabled=user.twofa_enabled,
        storage_used=user.storage_used,
        storage_limit=user.storage_limit,
        created_at=user.created_at,
    )


@router.get("/api/users")
def list_users_paginated(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """
    List users with pagination (internal use only).
    
    Args:
        skip: Number of users to skip
        limit: Number of users to return
        
    Returns:
        List of UserDetailResponse
    """
    # TODO: Implement proper pagination with repository
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="List users endpoint not yet implemented",
    )
