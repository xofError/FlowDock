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

from app.domain.entities import User, RecoveryToken
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


OTP_EXPIRE_MINUTES = 15
OTP_EXPIRE_SECONDS = OTP_EXPIRE_MINUTES * 60

# Rate limiting constants
LOGIN_RATE_LIMIT = 5
LOGIN_RATE_LIMIT_WINDOW = 300
OTP_RATE_LIMIT = 3
OTP_RATE_LIMIT_WINDOW = 300


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


class AuthService:
    """Core authentication service - business logic for user registration, login, etc."""

    def __init__(
        self,
        user_repo: IUserRepository,
        recovery_token_repo: IRecoveryTokenRepository,
        password_hasher: IPasswordHasher,
        token_generator: ITokenGenerator,
        redis_service: RedisService,
    ):
        self.user_repo = user_repo
        self.recovery_token_repo = recovery_token_repo
        self.password_hasher = password_hasher
        self.token_generator = token_generator
        self.redis_service = redis_service

    # ============ Registration ============

    def register_user(self, data: RegisterRequestDTO) -> User:
        """Register a new user.

        Business logic:
        1. Check if user already exists
        2. Hash password
        3. Create user entity
        4. Persist to repository
        """
        # Business rule: User cannot register twice
        existing = self.user_repo.get_by_email(data.email)
        if existing and existing.verified:
            raise ValueError("User already exists")

        # Hash the password
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
        return self.user_repo.save(new_user)

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

    def authenticate_user(self, email: str, password: str) -> User:
        """Authenticate a user by email and password.

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
