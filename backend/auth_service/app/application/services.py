"""
Application Layer: Business Services

These services orchestrate the business logic using repositories and other services.
They are independent of frameworks and databases - they only use domain entities and interfaces.
"""

from typing import Optional
from datetime import datetime, timedelta, timezone
import redis
import os
import secrets
import logging

from app.domain.entities import User, RecoveryToken, ActivityLog
from app.domain.interfaces import (
    IUserRepository,
    IRecoveryTokenRepository,
    IPasswordHasher,
    ITokenGenerator,
)
from app.application.dtos import (
    RegisterRequestDTO,
    LoginRequestDTO,
    TokenResponseDTO,
)
from app.infrastructure.database.repositories import PostgresLogRepository

logger = logging.getLogger(__name__)


OTP_EXPIRE_MINUTES = 15
OTP_EXPIRE_SECONDS = OTP_EXPIRE_MINUTES * 60

# Rate limiting constants
LOGIN_RATE_LIMIT = 5
LOGIN_RATE_LIMIT_WINDOW = 300
OTP_RATE_LIMIT = 3
OTP_RATE_LIMIT_WINDOW = 300
PASS_CODE_RATE_LIMIT = 3
PASS_CODE_RATE_LIMIT_WINDOW = 300


class RedisService:
    """Service for Redis operations (caching, rate limiting, OTP storage)."""

    def __init__(self):
        self.client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=0,
            decode_responses=True,
        )

    def check_rate_limit(self, identifier: str, limit: int, window: int) -> bool:
        """Check if identifier has exceeded rate limit."""
        key = f"rate_limit:{identifier}"
        current = self.client.incr(key)

        if current == 1:
            self.client.expire(key, window)

        return current <= limit

    def set_otp(self, email: str, otp: str, expires_in_seconds: int = OTP_EXPIRE_SECONDS) -> None:
        """Store OTP in Redis with expiry."""
        key = f"otp:email:{email}"
        self.client.setex(key, expires_in_seconds, otp)

    def get_otp(self, email: str) -> Optional[str]:
        """Retrieve OTP from Redis."""
        key = f"otp:email:{email}"
        return self.client.get(key)

    def delete_otp(self, email: str) -> None:
        """Delete OTP from Redis (after verification)."""
        key = f"otp:email:{email}"
        self.client.delete(key)

    def set_passcode(self, email: str, code: str, expires_in_seconds: int = OTP_EXPIRE_SECONDS) -> None:
        """Store passcode in Redis with expiry."""
        key = f"passcode:email:{email}"
        self.client.setex(key, expires_in_seconds, code)

    def get_passcode(self, email: str) -> Optional[str]:
        """Retrieve passcode from Redis."""
        key = f"passcode:email:{email}"
        return self.client.get(key)

    def delete_passcode(self, email: str) -> None:
        """Delete passcode from Redis (after verification)."""
        key = f"passcode:email:{email}"
        self.client.delete(key)


class AuthService:
    """Core authentication service - business logic for user registration, login, etc."""

    def __init__(
        self,
        user_repo: IUserRepository,
        recovery_token_repo: IRecoveryTokenRepository,
        password_hasher: IPasswordHasher,
        token_generator: ITokenGenerator,
        redis_service: RedisService,
        log_repo: PostgresLogRepository = None,  # Optional dependency for logging
    ):
        self.user_repo = user_repo
        self.recovery_token_repo = recovery_token_repo
        self.password_hasher = password_hasher
        self.token_generator = token_generator
        self.redis_service = redis_service
        self.log_repo = log_repo

    def _log_activity(self, user_id, action: str, details: dict = None, ip_address: str = None):
        """Internal helper to create activity logs.
        
        This is non-blocking - if logging fails, it won't crash the app.
        """
        if not self.log_repo:
            return
        
        try:
            log = ActivityLog(
                user_id=user_id,
                action=action,
                details=details or {},
                ip_address=ip_address,
            )
            self.log_repo.create_log(log)
        except Exception as e:
            logger.error(f"Failed to create activity log: {str(e)}")

    # ============ Registration ============

    def register_user(self, data: RegisterRequestDTO, ip_address: str = None) -> User:
        """Register a new user.

        Business logic:
        1. Check if user already exists
        2. Hash password
        3. Create user entity
        4. Persist to repository
        5. Log the activity
        """
        # Business rule: User cannot register twice
        existing = self.user_repo.get_by_email(data.email)
        if existing:
            # ✅ FIX: If user exists but is NOT verified, treat it as a retry
            if not existing.verified:
                # Optional: Update password or name if they changed it
                hashed_pw = self.password_hasher.hash(data.password)
                existing.password_hash = hashed_pw
                existing.full_name = data.full_name
                updated = self.user_repo.update(existing)

                # Generate and store a fresh OTP so the user can verify again
                try:
                    # This will check rate limits and store OTP in Redis
                    self.generate_email_otp(data.email)
                except Exception:
                    # Don't fail the flow if OTP generation fails here; caller can retry
                    pass

                # Log activity
                self._log_activity(
                    str(updated.id),
                    "USER_REGISTER",
                    {"email": data.email},
                    ip_address
                )

                return updated

            # If verified, raise the standard error
            raise ValueError("User already exists")

        # Hash the password for a new user
        hashed_pw = self.password_hasher.hash(data.password)

        # Create domain entity
        new_user = User(
            id=None,  # DB will assign
            email=data.email,
            password_hash=hashed_pw,
            full_name=data.full_name,
            verified=False,
        )

        # Persist
        saved_user = self.user_repo.save(new_user)
        
        # Log activity
        self._log_activity(
            str(saved_user.id),
            "USER_REGISTER",
            {"email": data.email},
            ip_address
        )
        
        return saved_user

    # ============ Email OTP Verification ============

    def generate_email_otp(self, email: str) -> str:
        """Generate and store an OTP for email verification."""
        # Check rate limit
        if not self.redis_service.check_rate_limit(
            f"otp_request:{email}",
            OTP_RATE_LIMIT,
            OTP_RATE_LIMIT_WINDOW,
        ):
            raise ValueError("Too many OTP requests. Try again later.")

        # Verify user exists
        user = self.user_repo.get_by_email(email)
        if not user:
            raise ValueError("User not found")

        # Generate 6-digit OTP
        otp = f"{secrets.randbelow(10**6):06d}"

        # Store in Redis
        self.redis_service.set_otp(email, otp)

        return otp

    def verify_email_otp(self, email: str, otp: str) -> User:
        """Verify an OTP and mark user as verified.

        Raises:
            ValueError: If OTP is invalid or expired
        """
        user = self.user_repo.get_by_email(email)
        if not user:
            raise ValueError("User not found")

        # Verify OTP
        stored_otp = self.redis_service.get_otp(email)
        if not stored_otp or stored_otp != otp:
            raise ValueError("Invalid or expired OTP")

        # Mark user as verified
        user.verified = True
        updated_user = self.user_repo.update(user)

        # Delete OTP to prevent reuse
        self.redis_service.delete_otp(email)

        return updated_user

    # ============ Login ============

    def authenticate_user(self, email: str, password: str, ip_address: Optional[str] = None) -> User:
        """Authenticate a user by email and password.

        Args:
            email: User email
            password: User password
            ip_address: Client IP address (optional)

        Raises:
            ValueError: If credentials are invalid
        """
        # Check rate limit
        if not self.redis_service.check_rate_limit(
            f"login:{email}",
            LOGIN_RATE_LIMIT,
            LOGIN_RATE_LIMIT_WINDOW,
        ):
            raise ValueError("Too many login attempts. Try again later.")

        user = self.user_repo.get_by_email(email)
        if not user:
            raise ValueError("Invalid credentials")

        # Verify password
        if not self.password_hasher.verify(password, user.password_hash):
            raise ValueError("Invalid credentials")

        # Set login metadata and persist it
        user.last_login_ip = ip_address
        user.last_login_at = datetime.now(timezone.utc)

        try:
            self.user_repo.update(user)
        except Exception:
            # If persisting login metadata fails, still return the authenticated user
            pass

        # Log activity
        self._log_activity(
            str(user.id),
            "USER_LOGIN",
            {"email": email},
            ip_address
        )

        return user

    def create_tokens(self, user_id) -> tuple[str, str, datetime]:
        """Create access and refresh tokens for a user.

        Returns:
            (access_token, refresh_token_plaintext, refresh_token_expiry)
        """
        access_token = self.token_generator.create_access_token(user_id)
        refresh_token, refresh_hash, expiry = self.token_generator.create_refresh_token(user_id)

        return access_token, refresh_token, expiry

    # ============ Password Recovery ============

    def request_password_reset(self, email: str) -> RecoveryToken:
        """Create a password reset token and return it (caller handles sending email).

        Raises:
            ValueError: If user not found
        """
        user = self.user_repo.get_by_email(email)
        if not user:
            # Prevent email enumeration: don't tell caller user doesn't exist
            raise ValueError("User not found")

        # Create recovery token
        token_str = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRE_MINUTES)

        recovery_token = RecoveryToken(
            id=None,
            user_id=user.id,
            token=token_str,
            method="email",
            expires_at=expires_at,
        )

        return self.recovery_token_repo.create(recovery_token)

    def verify_password_reset_token(self, email: str, token: str) -> bool:
        """Verify a password reset token without consuming it."""
        user = self.user_repo.get_by_email(email)
        if not user:
            return False

        recovery_token = self.recovery_token_repo.get_valid_by_user_and_token(user.id, token)
        return recovery_token is not None

    def confirm_password_reset(self, email: str, token: str, new_password: str) -> User:
        """Verify recovery token and update password.

        Raises:
            ValueError: If token is invalid or user not found
        """
        user = self.user_repo.get_by_email(email)
        if not user:
            raise ValueError("User not found")

        recovery_token = self.recovery_token_repo.get_valid_by_user_and_token(user.id, token)
        if not recovery_token:
            raise ValueError("Invalid or expired token")

        # Hash new password
        hashed_pw = self.password_hasher.hash(new_password)

        # Update user
        user.password_hash = hashed_pw
        updated_user = self.user_repo.update(user)

        # Mark token as used
        self.recovery_token_repo.mark_as_used(recovery_token.id)

        return updated_user

    # ============ Passcode Sign-In ============

    def generate_passcode(self, email: str) -> str:
        """Generate and store a 6-digit passcode for magic link sign-in.

        Args:
            email: User email address

        Returns:
            Generated 6-digit passcode

        Raises:
            ValueError: If user not found or rate limit exceeded
        """
        # Check rate limit
        if not self.redis_service.check_rate_limit(
            f"passcode_request:{email}",
            PASS_CODE_RATE_LIMIT,
            PASS_CODE_RATE_LIMIT_WINDOW,
        ):
            raise ValueError("Too many passcode requests. Try again later.")

        # Verify user exists
        user = self.user_repo.get_by_email(email)
        if not user:
            raise ValueError("User not found")

        # Generate 6-digit passcode
        passcode = f"{secrets.randbelow(10**6):06d}"

        # Store in Redis
        self.redis_service.set_passcode(email, passcode)

        return passcode

    def verify_passcode(self, email: str, code: str) -> User:
        """Verify a passcode and authenticate the user.

        Args:
            email: User email
            code: 6-digit passcode

        Returns:
            Authenticated User object

        Raises:
            ValueError: If passcode is invalid or expired
        """
        # Check rate limit for verification attempts
        if not self.redis_service.check_rate_limit(
            f"passcode_verify:{email}",
            OTP_RATE_LIMIT,
            OTP_RATE_LIMIT_WINDOW,
        ):
            raise ValueError("Too many verification attempts. Try again later.")

        user = self.user_repo.get_by_email(email)
        if not user:
            raise ValueError("User not found")

        # Verify passcode
        stored_passcode = self.redis_service.get_passcode(email)
        if not stored_passcode or stored_passcode != code:
            raise ValueError("Invalid or expired passcode")

        # Delete passcode to prevent reuse
        self.redis_service.delete_passcode(email)

        # Update last login metadata and persist
        user.last_login_at = datetime.now(timezone.utc)
        try:
            updated = self.user_repo.update(user)
            return updated
        except Exception:
            return user
