"""
Presentation Layer: Session Management API Routes

These routes manage user sessions and device/browser information.
"""

import logging
from fastapi import APIRouter, HTTPException, status, Depends, Request
from uuid import UUID
from datetime import datetime
from typing import Optional, Annotated, List
from pydantic import BaseModel

from app.presentation.dependencies import get_db, get_current_user
from app.domain.entities import User
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions", tags=["sessions"])


# ============ DTOs ============

class SessionInfo(BaseModel):
    """Session information."""
    id: str
    user_id: str
    device_info: Optional[str] = None
    browser_name: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    active: bool = True

    class Config:
        from_attributes = True


class SessionsListResponse(BaseModel):
    """Response for listing sessions."""
    sessions: List[SessionInfo]
    total: int


class RevokeSessionRequest(BaseModel):
    """Request to revoke a session."""
    session_id: str


class RevokeAllSessionsRequest(BaseModel):
    """Request to revoke all sessions."""
    confirm: bool = True


# ============ Endpoints ============

@router.get("/me", response_model=List[SessionInfo])
async def list_my_sessions(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> List[SessionInfo]:
    """
    Get all active sessions for the current user.
    
    **Security**: Requires valid JWT token. Returns only the user's own sessions.
    
    Returns:
    - List of active sessions with device info
    """
    try:
        # Get all sessions for the user (both active and inactive)
        from app.infrastructure.database.models import SessionModel
        db_sessions = db.query(SessionModel).filter(
            SessionModel.user_id == current_user.id
        ).order_by(SessionModel.created_at.desc()).all()
        
        sessions = []
        for db_session in db_sessions:
            sessions.append(SessionInfo(
                id=str(db_session.id),
                user_id=str(db_session.user_id),
                device_info=db_session.device_info,
                browser_name=db_session.browser_name,
                ip_address=db_session.ip_address,
                created_at=db_session.created_at,
                expires_at=db_session.expires_at,
                active=db_session.active,
            ))
        
        logger.info(f"Listed {len(sessions)} sessions for user {current_user.id}")
        
        return sessions
        
    except Exception as e:
        logger.error(f"Error listing sessions for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sessions"
        )


@router.get("/{session_id}", response_model=SessionInfo)
async def get_session_details(
    session_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> SessionInfo:
    """
    Get details of a specific session.
    
    **Security**: Requires valid JWT token. Users can only view their own sessions.
    
    Parameters:
    - **session_id**: Session identifier
    
    Returns:
    - Session details including device and browser info
    """
    try:
        from app.infrastructure.database.models import SessionModel
        
        try:
            session_uuid = UUID(session_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid session ID format"
            )
        
        db_session = db.query(SessionModel).filter(
            SessionModel.id == session_uuid,
            SessionModel.user_id == current_user.id
        ).first()
        
        if not db_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        logger.info(f"Retrieved session {session_id} for user {current_user.id}")
        
        return SessionInfo(
            id=str(db_session.id),
            user_id=str(db_session.user_id),
            device_info=db_session.device_info,
            browser_name=db_session.browser_name,
            ip_address=db_session.ip_address,
            created_at=db_session.created_at,
            expires_at=db_session.expires_at,
            active=db_session.active,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session details"
        )


@router.delete("/{session_id}")
async def revoke_session(
    session_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Revoke (logout) a specific session.
    
    **Security**: Requires valid JWT token. Users can only revoke their own sessions.
    
    Parameters:
    - **session_id**: Session identifier to revoke
    
    Returns:
    - Success message
    """
    try:
        from app.infrastructure.database.models import SessionModel
        
        try:
            session_uuid = UUID(session_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid session ID format"
            )
        
        db_session = db.query(SessionModel).filter(
            SessionModel.id == session_uuid,
            SessionModel.user_id == current_user.id
        ).first()
        
        if not db_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Mark session as inactive
        db_session.active = False
        db.add(db_session)
        db.commit()
        
        logger.info(f"Revoked session {session_id} for user {current_user.id}")
        
        return {
            "status": "success",
            "message": "Session revoked successfully",
            "session_id": session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke session"
        )


@router.delete("/revoke/all")
async def revoke_all_sessions(
    request: RevokeAllSessionsRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Revoke all sessions for the current user (logout from all devices).
    
    **Security**: Requires valid JWT token and confirmation flag.
    
    Parameters:
    - **confirm**: Set to true to confirm revocation of all sessions
    
    Returns:
    - Summary of revoked sessions
    """
    if not request.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please set 'confirm' to true to revoke all sessions"
        )
    
    try:
        from app.infrastructure.database.models import SessionModel
        
        # Get all active sessions for the user
        active_sessions = db.query(SessionModel).filter(
            SessionModel.user_id == current_user.id,
            SessionModel.active == True
        ).all()
        
        revoked_count = len(active_sessions)
        
        # Revoke all sessions
        db.query(SessionModel).filter(
            SessionModel.user_id == current_user.id,
            SessionModel.active == True
        ).update({"active": False})
        db.commit()
        
        logger.info(f"Revoked all {revoked_count} sessions for user {current_user.id}")
        
        return {
            "status": "success",
            "message": f"Revoked {revoked_count} sessions",
            "revoked_count": revoked_count,
        }
        
    except Exception as e:
        logger.error(f"Error revoking all sessions for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke all sessions"
        )


@router.get("/active/count")
async def get_active_sessions_count(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Get count of active sessions for the current user.
    
    **Security**: Requires valid JWT token.
    
    Returns:
    - Number of active sessions
    """
    try:
        from app.infrastructure.database.models import SessionModel
        
        count = db.query(SessionModel).filter(
            SessionModel.user_id == current_user.id,
            SessionModel.active == True
        ).count()
        
        logger.info(f"User {current_user.id} has {count} active sessions")
        
        return {
            "active_sessions": count,
            "user_id": str(current_user.id),
        }
        
    except Exception as e:
        logger.error(f"Error getting active sessions count: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get active sessions count"
        )
