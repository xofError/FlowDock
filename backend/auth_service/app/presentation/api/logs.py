"""
Presentation Layer: Logs API Endpoints

These endpoints expose activity logging functionality.
The /internal/logs endpoint is for internal service-to-service communication.
"""

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import JSONResponse
from uuid import UUID
from typing import Optional
from sqlalchemy.orm import Session

from app.application.dtos import ActivityLogCreateDTO, ActivityLogResponseDTO
from app.infrastructure.database.repositories import PostgresLogRepository
from app.domain.entities import ActivityLog
from app.database import get_db

router = APIRouter(tags=["Activity Logging"])


def get_log_repo(db: Session = Depends(get_db)) -> PostgresLogRepository:
    """Dependency to get the log repository."""
    return PostgresLogRepository(db)


@router.post("/internal", status_code=status.HTTP_201_CREATED)
def create_activity_log(
    data: ActivityLogCreateDTO,
    repo: PostgresLogRepository = Depends(get_log_repo),
):
    """
    Internal endpoint for other services (like Media Service) 
    to write activity logs to PostgreSQL.
    
    This is an internal-only endpoint and should not be exposed publicly.
    It's called by other microservices to log user activities.
    
    Args:
        data: ActivityLogCreateDTO with user_id, action, details, ip_address
        repo: PostgresLogRepository dependency
        
    Returns:
        {"status": "logged", "id": log_id}
    """
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
    repo: PostgresLogRepository = Depends(get_log_repo),
):
    """
    Get activity logs for a specific user.
    
    Args:
        user_id: User ID as string (will be converted to UUID)
        limit: Maximum number of logs to return (default 50, max 100)
        repo: PostgresLogRepository dependency
        
    Returns:
        List of ActivityLogResponseDTO objects
    """
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
    repo: PostgresLogRepository = Depends(get_log_repo),
):
    """
    Get activity logs for a specific action type.
    
    Args:
        action: Action name (e.g., "USER_LOGIN", "FILE_UPLOAD")
        limit: Maximum number of logs to return (default 50, max 100)
        repo: PostgresLogRepository dependency
        
    Returns:
        List of ActivityLogResponseDTO objects
    """
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
    repo: PostgresLogRepository = Depends(get_log_repo),
):
    """
    Get all activity logs (admin endpoint).
    
    Args:
        limit: Maximum number of logs to return (default 50, max 100)
        repo: PostgresLogRepository dependency
        
    Returns:
        List of ActivityLogResponseDTO objects
    """
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
