"""
Presentation Layer: Logs API Endpoints

These endpoints expose activity logging functionality.
The /internal/logs endpoint is for internal service-to-service communication.
"""

from fastapi import APIRouter, status, HTTPException, Depends
from fastapi.responses import JSONResponse
from uuid import UUID
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.application.dtos import ActivityLogCreateDTO, ActivityLogResponseDTO
from app.infrastructure.database.repositories import PostgresLogRepository
from app.domain.entities import ActivityLog
from app.database import SessionLocal
from app.presentation.dependencies import verify_internal_service, get_current_user_id, verify_jwt_token

router = APIRouter(tags=["Activity Logging"])


def get_log_repo() -> PostgresLogRepository:
    """Get the log repository with a new database session."""
    db = SessionLocal()
    return PostgresLogRepository(db)


@router.post("/internal", status_code=status.HTTP_201_CREATED)
def create_activity_log(
    data: ActivityLogCreateDTO,
    _: None = Depends(verify_internal_service),
):
    """
    Internal endpoint for other services (like Media Service) 
    to write activity logs to PostgreSQL.
    
    This is an internal-only endpoint and requires X-API-Key header.
    It's called by other microservices to log user activities.
    
    Args:
        data: ActivityLogCreateDTO with user_id, action, details, ip_address
        _: Validates internal service authentication via verify_internal_service
        
    Returns:
        {"status": "logged", "id": log_id}
    """
    repo = get_log_repo()
    
    try:
        # Parse user_id as UUID if it's a string
        try:
            user_id = UUID(data.user_id)
        except (ValueError, AttributeError):
            user_id = data.user_id

        # Create domain entity
        log = ActivityLog(
            user_id=user_id,
            action=data.action,
            details=data.details or {},
            ip_address=data.ip_address,
        )

        # Persist to database
        created_log = repo.create_log(log)

        return {
            "status": "logged",
            "id": str(created_log.id),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create activity log: {str(e)}",
        )


@router.get("/user/{user_id}", response_model=list[ActivityLogResponseDTO])
def get_user_activity_logs(
    user_id: str,
    limit: int = 50,
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Get activity logs for a specific user.
    
    Requires JWT authentication. Users can only view their own logs,
    unless they have admin access (future feature).
    
    Args:
        user_id: User ID as string (will be converted to UUID)
        limit: Maximum number of logs to return (default 50, max 100)
        current_user_id: Authenticated user ID from JWT token
        
    Returns:
        List of ActivityLogResponseDTO objects
        
    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 403 if trying to view another user's logs
    """
    # Authorization check: users can only view their own logs
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot view activity logs for other users",
        )
    
    repo = get_log_repo()
    
    try:
        # Clamp limit to reasonable value
        limit = min(limit, 100)
        
        # Parse user_id as UUID
        try:
            user_uuid = UUID(user_id)
        except (ValueError, AttributeError):
            user_uuid = user_id

        logs = repo.get_logs_by_user(user_uuid, limit=limit)

        return [
            ActivityLogResponseDTO(
                id=str(log.id),
                user_id=str(log.user_id),
                action=log.action,
                details=log.details,
                ip_address=log.ip_address,
                created_at=log.created_at.isoformat() if log.created_at else None,
            )
            for log in logs
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve activity logs: {str(e)}",
        )


@router.get("/action/{action}", response_model=list[ActivityLogResponseDTO])
def get_logs_by_action(
    action: str,
    limit: int = 50,
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Get activity logs for a specific action type.
    
    Requires JWT authentication. Note: Users can see logs for any action type
    (not restricted to own logs since action queries are useful for analytics).
    
    Args:
        action: Action name (e.g., "USER_LOGIN", "FILE_UPLOAD")
        limit: Maximum number of logs to return (default 50, max 100)
        current_user_id: Current user ID from JWT token
        
    Returns:
        List of ActivityLogResponseDTO objects
    """
    repo = get_log_repo()
    
    try:
        # Clamp limit to reasonable value
        limit = min(limit, 100)
        
        logs = repo.get_logs_by_action(action, limit=limit)

        return [
            ActivityLogResponseDTO(
                id=str(log.id),
                user_id=str(log.user_id),
                action=log.action,
                details=log.details,
                ip_address=log.ip_address,
                created_at=log.created_at.isoformat() if log.created_at else None,
            )
            for log in logs
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve activity logs: {str(e)}",
        )


@router.get("/all", response_model=list[ActivityLogResponseDTO])
def get_all_activity_logs(
    limit: int = 50,
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Get all activity logs.
    
    Requires JWT authentication. All authenticated users can access this endpoint
    to view all activity logs (useful for analytics, auditing, etc).
    
    Args:
        limit: Maximum number of logs to return (default 50, max 100)
        current_user_id: Authenticated user ID from JWT token
        
    Returns:
        List of ActivityLogResponseDTO objects
    """
    repo = get_log_repo()
    
    try:
        # Clamp limit to reasonable value
        limit = min(limit, 100)
        
        logs = repo.get_all_logs(limit=limit)

        return [
            ActivityLogResponseDTO(
                id=str(log.id),
                user_id=str(log.user_id),
                action=log.action,
                details=log.details,
                ip_address=log.ip_address,
                created_at=log.created_at.isoformat() if log.created_at else None,
            )
            for log in logs
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve activity logs: {str(e)}",
        )
