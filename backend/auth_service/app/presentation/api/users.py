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
    db: Session = Depends(get_db),
    user_repo = Depends(get_user_repository),
):
    """
    List all users (internal use only).
    
    Returns:
        List of UserDetailResponse
    """
    users = user_repo.get_all()
    
    return [
        UserDetailResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            verified=user.verified,
            twofa_enabled=user.twofa_enabled,
            storage_used=user.storage_used,
            storage_limit=user.storage_limit,
            created_at=user.created_at,
        )
        for user in users
    ]


# ============ Internal APIs (Called by Media Service) ============

class QuotaUpdate(BaseModel):
    """DTO for internal quota update requests."""
    user_id: str
    size_delta: int


@router.post("/internal/quota/update", status_code=status.HTTP_200_OK)
def update_user_quota(
    data: QuotaUpdate,
    db: Session = Depends(get_db),
    user_repo = Depends(get_user_repository),
):
    """
    Internal endpoint called by Media Service to update storage usage.
    
    This is meant to be called only from within the backend (Media Service)
    to notify about file uploads/deletions.
    
    Args:
        data: QuotaUpdate DTO with user_id and size_delta (positive for upload, negative for delete)
        
    Returns:
        Success response with updated quota info
        
    Raises:
        HTTPException 500: If update fails
    """
    try:
        user = user_repo.get_by_id(data.user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID '{data.user_id}' not found",
            )
        
        # Update storage usage
        user.storage_used += data.size_delta
        user_repo.update(user)
        
        return {
            "status": "success",
            "user_id": data.user_id,
            "delta": data.size_delta,
            "storage_used": user.storage_used,
            "storage_limit": user.storage_limit,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
