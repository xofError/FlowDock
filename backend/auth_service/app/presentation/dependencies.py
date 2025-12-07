"""
Presentation Layer: Dependency Injection Setup

This wires together all the layers:
- Domain interfaces are implemented by infrastructure classes
- Application services use injected repositories
- API routes use injected services via FastAPI dependencies
"""

from app.database import SessionLocal
from app.application.services import AuthService, RedisService
from app.application.twofa_service import TwoFAService
from app.application.user_util_service import UserUtilService
from app.application.quota_service import StorageQuotaService
from app.application.oauth_service import OAuthService
from app.infrastructure.database.repositories import (
    PostgresUserRepository,
    PostgresRecoveryTokenRepository,
)
from app.infrastructure.security.security import (
    ArgonPasswordHasher,
    JWTTokenGenerator,
)
from app.infrastructure.security.totp import TOTPService
from app.infrastructure.security.token_store import RefreshTokenStore
from app.infrastructure.email.email import get_email_service


def get_db():
    """FastAPI dependency: get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_repository(db=None):
    """FastAPI dependency: get user repository."""
    if db is None:
        db = next(get_db())
    return PostgresUserRepository(db)


def get_recovery_token_repository(db=None):
    """FastAPI dependency: get recovery token repository."""
    if db is None:
        db = next(get_db())
    return PostgresRecoveryTokenRepository(db)


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


def get_email_service():
    """FastAPI dependency: get email service."""
    from app.infrastructure.email.email import get_email_service as _get_email_service
    return _get_email_service()


def get_auth_service(
    db=None,
    user_repo=None,
    recovery_token_repo=None,
    password_hasher=None,
    token_generator=None,
    redis_service=None,
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

    return AuthService(
        user_repo=user_repo,
        recovery_token_repo=recovery_token_repo,
        password_hasher=password_hasher,
        token_generator=token_generator,
        redis_service=redis_service,
    )


def get_twofa_service(
    db=None,
    user_repo=None,
    recovery_token_repo=None,
    totp_service=None,
):
    """FastAPI dependency: get configured TwoFAService."""
    if db is None:
        db = next(get_db())

    user_repo = user_repo or PostgresUserRepository(db)
    recovery_token_repo = recovery_token_repo or PostgresRecoveryTokenRepository(db)
    totp_service = totp_service or TOTPService()

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
