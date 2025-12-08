import pyotp
from typing import Optional


def generate_totp_secret() -> str:
    """Generate a base32 TOTP secret suitable for use with authenticator apps."""
    return pyotp.random_base32()


def verify_totp(totp_secret: str, code: str, window: int = 1) -> bool:
    """Verify a TOTP `code` against `totp_secret`.

    The `window` parameter allows for clock skew; by default we accept the
    previous/current/next timestep (window=1). Returns False for invalid
    inputs or on verification failure.
    """
    try:
        totp = pyotp.TOTP(totp_secret)
        return bool(totp.verify(code, valid_window=window))
    except (TypeError, ValueError):
        # invalid secret or code format
        return False


def get_totp_qr_uri(email: str, totp_secret: str, app_name: str = "SecureCloud") -> str:
    """Return the provisioning URI which can be converted to a QR code.

    Example: pass the returned URI to a QR code generator and the user can
    scan it with Google Authenticator or similar apps.
    """
    totp = pyotp.TOTP(totp_secret)
    return totp.provisioning_uri(name=email, issuer_name=app_name)
