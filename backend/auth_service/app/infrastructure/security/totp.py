"""
Infrastructure Layer: TOTP Service

Implementation of TOTP/2FA operations using pyotp library.
"""

import pyotp
from typing import Optional


class TOTPService:
    """TOTP (Time-based One-Time Password) service for 2FA."""

    @staticmethod
    def generate_secret() -> str:
        """Generate a base32 TOTP secret suitable for authenticator apps."""
        return pyotp.random_base32()

    @staticmethod
    def verify(totp_secret: str, code: str, window: int = 1) -> bool:
        """Verify a TOTP code against a secret.

        Args:
            totp_secret: The base32 TOTP secret
            code: The 6-digit code from authenticator app
            window: Clock skew tolerance (default 1 allows ±1 timestep)

        Returns:
            True if code is valid, False otherwise
        """
        try:
            totp = pyotp.TOTP(totp_secret)
            return bool(totp.verify(code, valid_window=window))
        except (TypeError, ValueError):
            return False

    @staticmethod
    def get_provisioning_uri(email: str, totp_secret: str, app_name: str = "FlowDock") -> str:
        """Get QR code provisioning URI for authenticator app enrollment.

        Args:
            email: User's email (label for the TOTP entry)
            totp_secret: The base32 TOTP secret
            app_name: App name to display in authenticator

        Returns:
            Provisioning URI that can be converted to QR code
        """
        totp = pyotp.TOTP(totp_secret)
        return totp.provisioning_uri(name=email, issuer_name=app_name)
