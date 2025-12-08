"""
Application Layer: Two-Factor Authentication Service

Business logic for TOTP setup, verification, and recovery codes.
"""

import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.domain.entities import User, RecoveryToken
from app.domain.interfaces import IUserRepository, IRecoveryTokenRepository
from app.infrastructure.security.totp import TOTPService


class TwoFAService:
    """Service for two-factor authentication operations."""

    def __init__(
        self,
        user_repo: IUserRepository,
        recovery_token_repo: IRecoveryTokenRepository,
        totp_service: TOTPService = None,
    ):
        self.user_repo = user_repo
        self.recovery_token_repo = recovery_token_repo
        self.totp_service = totp_service or TOTPService()

    # ============ TOTP Setup ============

    def initiate_totp_setup(self, email: str) -> tuple[str, str]:
        """Initiate TOTP setup for a user.

        Generates a new TOTP secret and returns it along with QR provisioning URI.

        Args:
            email: User's email

        Returns:
            (totp_secret, provisioning_uri)

        Raises:
            ValueError: If user not found
        """
        user = self.user_repo.get_by_email(email)
        if not user:
            raise ValueError("User not found")

        # Generate new TOTP secret
        secret = self.totp_service.generate_secret()

        # Get QR URI for scanning
        uri = self.totp_service.get_provisioning_uri(email, secret)

        return secret, uri

    def verify_totp_and_enable_2fa(
        self, email: str, totp_secret: str, totp_code: str, recovery_code_count: int = 10
    ) -> list[str]:
        """Verify TOTP code and enable 2FA for a user.

        Once verified, generates and stores one-time recovery codes.

        Args:
            email: User's email
            totp_secret: The TOTP secret to verify against
            totp_code: The 6-digit code from authenticator app
            recovery_code_count: Number of recovery codes to generate

        Returns:
            List of plaintext recovery codes (shown to user once)

        Raises:
            ValueError: If user not found or TOTP code invalid
        """
        user = self.user_repo.get_by_email(email)
        if not user:
            raise ValueError("User not found")

        # Verify the TOTP code
        if not self.totp_service.verify(totp_secret, totp_code):
            raise ValueError("Invalid TOTP code")

        # Update user: save secret and enable 2FA
        user.totp_secret = totp_secret
        user.twofa_enabled = True
        self.user_repo.update(user)

        # Generate recovery codes
        plaintext_codes = self._generate_recovery_codes(user.id, recovery_code_count)

        return plaintext_codes

    # ============ TOTP Verification (Login) ============

    def verify_totp_code(self, email: str, totp_code: str) -> bool:
        """Verify a TOTP code during login.

        Args:
            email: User's email
            totp_code: The 6-digit code from authenticator app

        Returns:
            True if code is valid, False otherwise
        """
        user = self.user_repo.get_by_email(email)
        if not user or not user.totp_secret:
            return False

        return self.totp_service.verify(user.totp_secret, totp_code)

    # ============ Recovery Codes ============

    def _generate_recovery_codes(self, user_id, count: int = 10) -> list[str]:
        """Generate and store recovery codes for 2FA.

        Args:
            user_id: User's ID
            count: Number of codes to generate

        Returns:
            List of plaintext recovery codes (for display to user)
        """
        plaintext_codes = []
        now = datetime.utcnow()
        expires = now + timedelta(days=3650)  # 10 years

        for _ in range(count):
            # Human-manageable code: 8 hex chars
            code = secrets.token_hex(4)
            hashed = hashlib.sha256(code.encode("utf-8")).hexdigest()

            # Create recovery token entity
            recovery_token = RecoveryToken(
                id=None,
                user_id=user_id,
                token=hashed,
                method="recovery_code",
                expires_at=expires,
                used=False,
            )

            # Persist
            self.recovery_token_repo.create(recovery_token)
            plaintext_codes.append(code)

        return plaintext_codes

    def verify_and_use_recovery_code(self, email: str, code: str) -> bool:
        """Verify and consume a recovery code.

        Args:
            email: User's email
            code: Plaintext recovery code

        Returns:
            True if code was valid and consumed, False otherwise
        """
        user = self.user_repo.get_by_email(email)
        if not user:
            return False

        hashed = hashlib.sha256(code.encode("utf-8")).hexdigest()

        # Try to find and use this recovery code
        recovery_token = self.recovery_token_repo.get_valid_by_user_and_token(
            user.id, hashed
        )
        if not recovery_token:
            return False

        # Mark as used
        self.recovery_token_repo.mark_as_used(recovery_token.id)
        return True

    # ============ TOTP Disable ============

    def disable_totp(self, email: str) -> User:
        """Disable TOTP/2FA for a user.

        Args:
            email: User's email

        Returns:
            Updated user entity

        Raises:
            ValueError: If user not found
        """
        user = self.user_repo.get_by_email(email)
        if not user:
            raise ValueError("User not found")

        user.twofa_enabled = False
        user.totp_secret = None
        return self.user_repo.update(user)
