"""
Presentation Layer: User API Routes

These routes use the clean architecture services to provide user information.
Used by Media Service for user resolution and internal APIs.
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from uuid import UUID
from datetime import datetime
from typing import Optional, Annotated
from pydantic import BaseModel, EmailStr

from app.presentation.dependencies import get_db, get_user_repository, get_current_user, get_user_service, get_twofa_service
from app.application.dtos import UserDTO, UserUpdateDTO, PasswordChangeDTO
from app.application.services import UserService
from app.application.twofa_service import TwoFAService
from app.domain.entities import User
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

@router.get("/by-email/{email}", response_model=UserPublicInfo)
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


@router.get("/{user_id}", response_model=UserDetailResponse)
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


@router.get("")
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


# ============ Settings & Profile Management (Authenticated) ============

@router.get("/me", response_model=UserDTO)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Get current user profile."""
    return UserDTO(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        verified=current_user.verified,
        is_2fa_enabled=current_user.twofa_enabled,
        storage_used=current_user.storage_used,
        storage_limit=current_user.storage_limit,
        created_at=current_user.created_at.isoformat() if current_user.created_at else None,
    )


@router.put("/me", response_model=UserDTO)
async def update_user_me(
    user_update: UserUpdateDTO,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[UserService, Depends(get_user_service)]
):
    """Update user profile information."""
    updated_user = await service.update_user(current_user.id, user_update)
    return UserDTO(
        id=str(updated_user.id),
        email=updated_user.email,
        full_name=updated_user.full_name,
        verified=updated_user.verified,
        is_2fa_enabled=updated_user.twofa_enabled,
        storage_used=updated_user.storage_used,
        storage_limit=updated_user.storage_limit,
        created_at=updated_user.created_at.isoformat() if updated_user.created_at else None,
    )


@router.put("/me/password")
async def change_password(
    password_data: PasswordChangeDTO,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[UserService, Depends(get_user_service)]
):
    """Change user password."""
    await service.change_password(
        current_user.id, 
        password_data.current_password, 
        password_data.new_password
    )
    return {"message": "Password updated successfully"}


@router.post("/me/2fa/setup")
async def setup_2fa(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TwoFAService, Depends(get_twofa_service)]
):
    """Generate a TOTP secret for 2FA setup."""
    try:
        secret, uri = service.initiate_totp_setup(current_user.email)
        return {"secret": secret, "otpauth_url": uri}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/me/2fa/enable")
async def enable_2fa(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TwoFAService, Depends(get_twofa_service)],
    code: str = Query(..., description="6-digit TOTP code")
):
    """Verify code and enable 2FA."""
    try:
        recovery_codes = service.enable_2fa_with_code(
            current_user.email, 
            code
        )
        return {"message": "Two-factor authentication enabled", "recovery_codes": recovery_codes}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/me/2fa/disable")
async def disable_2fa(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TwoFAService, Depends(get_twofa_service)],
    user_service: Annotated[UserService, Depends(get_user_service)],
    password: str = Query(..., description="User password for verification"),
):
    """Disable 2FA (requires password verification)."""
    try:
        valid_pass = await user_service.verify_password(current_user.email, password)
        if not valid_pass:
            raise HTTPException(status_code=403, detail="Invalid password")
        
        service.disable_totp(current_user.email)
        return {"message": "Two-factor authentication disabled"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))



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
