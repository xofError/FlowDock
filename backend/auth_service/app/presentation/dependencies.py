"""
Presentation Layer: Dependency Injection Setup

This wires together all the layers:
- Domain interfaces are implemented by infrastructure classes
- Application services use injected repositories
- API routes use injected services via FastAPI dependencies
"""

from fastapi import Header, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from app.database import SessionLocal
from app.application.services import AuthService, RedisService, UserService
from app.application.twofa_service import TwoFAService
from app.application.user_util_service import UserUtilService
from app.application.quota_service import StorageQuotaService
from app.application.oauth_service import OAuthService
from app.domain.entities import User
from app.infrastructure.database.repositories import (
    PostgresUserRepository,
    PostgresRecoveryTokenRepository,
    PostgresLogRepository,
    PostgresSessionRepository,
)
from app.infrastructure.security.security import (
    ArgonPasswordHasher,
    JWTTokenGenerator,
)
from app.infrastructure.security.totp import TOTPService
from app.infrastructure.security.token_store import RefreshTokenStore
from app.infrastructure.email.email import get_email_service


async def verify_internal_service(x_api_key: str = Header(None)) -> None:
    """
    Verify that the request comes from an authorized internal service.
    
    This dependency validates the X-API-Key header against the configured
    internal API key. It's used to protect internal service endpoints like
    /logs/internal that should only be called from other microservices.
    
    Args:
        x_api_key: The API key from the X-API-Key header (optional parameter)
        
    Raises:
        HTTPException: 401 Unauthorized if the API key is invalid or missing
        
    Usage:
        @router.post("/internal")
        async def create_log(
            data: SomeDTO,
            _: None = Depends(verify_internal_service)
        ):
            # This endpoint now requires valid API key
    """
    if not x_api_key or x_api_key != settings.internal_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def verify_jwt_token(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))
) -> Dict[str, Any]:
    """
    Verify JWT token from Authorization header.
    
    This dependency extracts and validates a JWT token from the Authorization header.
    Returns the decoded token payload if valid.
    
    Args:
        credentials: HTTP Bearer credentials from Authorization header
        
    Returns:
        Decoded JWT payload (dict with 'sub' as user_id)
        
    Raises:
        HTTPException: 401 Unauthorized if token is invalid or expired
        
    Usage:
        @router.get("/endpoint")
        async def get_data(token: Dict = Depends(verify_jwt_token)):
            user_id = token['sub']
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_generator = JWTTokenGenerator()
    payload = token_generator.decode_access_token(credentials.credentials)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload


async def get_current_user_id(token: Dict[str, Any] = Depends(verify_jwt_token)) -> str:
    """
    Extract user_id from verified JWT token.
    
    This is a convenience dependency that extracts the user_id (from the 'sub' claim)
    from an already-verified JWT token.
    
    Args:
        token: Verified JWT token payload
        
    Returns:
        User ID (UUID as string)
        
    Raises:
        HTTPException: 401 Unauthorized if 'sub' claim missing
        
    Usage:
        @router.get("/my-logs")
        async def get_my_logs(user_id: str = Depends(get_current_user_id)):
            # user_id is the authenticated user's ID
    """
    user_id = token.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user_id",
        )
    return user_id


# ============ Basic Utility Dependencies (must come before complex ones) ============

def get_db():
    """FastAPI dependency: get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_password_hasher():
    """FastAPI dependency: get password hasher."""
    return ArgonPasswordHasher()


def get_token_generator():
    """FastAPI dependency: get JWT token generator."""
    return JWTTokenGenerator()


def get_totp_service():
    """FastAPI dependency: get TOTP service."""
    return TOTPService()


def get_refresh_token_store():
    """FastAPI dependency: get refresh token store."""
    return RefreshTokenStore()


def get_redis_service():
    """FastAPI dependency: get Redis service."""
    return RedisService()


def get_user_repository(db=None):
    """FastAPI dependency: get user repository."""
    if db is None:
        db = next(get_db())
    return PostgresUserRepository(db)


def get_recovery_token_repository(db: Session = Depends(get_db)):
    """FastAPI dependency: get recovery token repository."""
    return PostgresRecoveryTokenRepository(db)


def get_session_repository(db: Session = Depends(get_db)):
    """FastAPI dependency: get session repository."""
    return PostgresSessionRepository(db)


def get_log_repository(db=None):
    """FastAPI dependency: get log repository."""
    if db is None:
        db = next(get_db())
    return PostgresLogRepository(db)


def get_email_service():
    """FastAPI dependency: get email service."""
    from app.infrastructure.email.email import get_email_service as _get_email_service
    return _get_email_service()


# ============ Complex Dependencies (now safe to use get_db) ============

async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_db),
) -> User:
    """
    Get the current authenticated user entity.
    
    This dependency retrieves the User entity for the authenticated user
    by looking up their ID in the database.
    
    Args:
        user_id: Authenticated user's ID from JWT token
        db: Database session
        
    Returns:
        User entity
        
    Raises:
        HTTPException: 404 if user not found
        
    Usage:
        @router.get("/profile")
        async def get_profile(user: User = Depends(get_current_user)):
            # user is the authenticated User entity
    """
    user_repo = PostgresUserRepository(db)
    user = user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return user


def get_auth_service(
    db=None,
    user_repo=None,
    recovery_token_repo=None,
    password_hasher=None,
    token_generator=None,
    redis_service=None,
    log_repo=None,
):
    """FastAPI dependency: get fully configured AuthService.

    This wires together all the concrete implementations.
    FastAPI will inject each dependency automatically.
    """
    if db is None:
        db = next(get_db())

    user_repo = user_repo or PostgresUserRepository(db)
    recovery_token_repo = recovery_token_repo or PostgresRecoveryTokenRepository(db)
    password_hasher = password_hasher or ArgonPasswordHasher()
    token_generator = token_generator or JWTTokenGenerator()
    redis_service = redis_service or RedisService()
    log_repo = log_repo or PostgresLogRepository(db)

    return AuthService(
        user_repo=user_repo,
        recovery_token_repo=recovery_token_repo,
        password_hasher=password_hasher,
        token_generator=token_generator,
        redis_service=redis_service,
        log_repo=log_repo,
    )


def get_twofa_service(
    db: Session = Depends(get_db),
    user_repo: PostgresUserRepository = Depends(get_user_repository),
    recovery_token_repo: PostgresRecoveryTokenRepository = Depends(get_recovery_token_repository),
):
    """FastAPI dependency: get configured TwoFAService."""
    totp_service = TOTPService()
    return TwoFAService(
        user_repo=user_repo,
        recovery_token_repo=recovery_token_repo,
        totp_service=totp_service,
    )


def get_user_util_service(
    db=None,
    user_repo=None,
    password_hasher=None,
):
    """FastAPI dependency: get configured UserUtilService."""
    if db is None:
        db = next(get_db())

    user_repo = user_repo or PostgresUserRepository(db)
    password_hasher = password_hasher or ArgonPasswordHasher()

    return UserUtilService(
        user_repo=user_repo,
        password_hasher=password_hasher,
    )


def get_storage_quota_service(
    db=None,
    user_repo=None,
):
    """FastAPI dependency: get configured StorageQuotaService."""
    if db is None:
        db = next(get_db())

    user_repo = user_repo or PostgresUserRepository(db)

    return StorageQuotaService(user_repo=user_repo)


def get_oauth_service(
    db=None,
    user_repo=None,
    password_hasher=None,
):
    """FastAPI dependency: get configured OAuthService."""
    if db is None:
        db = next(get_db())

    user_repo = user_repo or PostgresUserRepository(db)
    password_hasher = password_hasher or ArgonPasswordHasher()

    return OAuthService(
        user_repository=user_repo,
        password_hasher=password_hasher,
    )

def get_user_service(
    db=None,
    user_repo=None,
    password_hasher=None,
):
    """FastAPI dependency: get configured UserService."""
    if db is None:
        db = next(get_db())

    user_repo = user_repo or PostgresUserRepository(db)
    password_hasher = password_hasher or ArgonPasswordHasher()

    return UserService(
        user_repo=user_repo,
        password_hasher=password_hasher,
    )