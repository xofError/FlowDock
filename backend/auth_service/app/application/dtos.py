"""
Application Layer: Data Transfer Objects (DTOs)

These are Pydantic models for input/output validation.
They transfer data between the presentation layer (API) and application logic.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID


# ============ Authentication DTOs ============

class RegisterRequestDTO(BaseModel):
    """DTO for user registration."""
    email: EmailStr
    full_name: str
    password: str = Field(..., min_length=8, description="Strong password required")


class LoginRequestDTO(BaseModel):
    """DTO for user login."""
    email: EmailStr
    password: str
    totp_code: Optional[str] = None


class TokenResponseDTO(BaseModel):
    """DTO for token response."""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    totp_required: bool = False


class RefreshRequestDTO(BaseModel):
    """DTO for token refresh."""
    refresh_token: str


class LogoutRequestDTO(BaseModel):
    """DTO for logout."""
    refresh_token: str


# ============ Email Verification DTOs ============

class VerifyEmailOTPRequestDTO(BaseModel):
    """DTO for email OTP verification."""
    email: EmailStr
    token: str = Field(..., min_length=6, max_length=6, description="6-digit OTP")


class SendEmailOTPRequestDTO(BaseModel):
    """DTO for requesting email OTP (can be same as register or for sending another code)."""
    email: EmailStr


# ============ TOTP/2FA DTOs ============

class TotpSetupRequestDTO(BaseModel):
    """DTO for initiating TOTP setup."""
    email: EmailStr


class TotpSetupResponseDTO(BaseModel):
    """DTO for TOTP setup response."""
    secret: str
    qr_code: Optional[str] = None
    recovery_codes: list[str]


class TotpVerifyRequestDTO(BaseModel):
    """DTO for TOTP verification.
    
    Can be used for two flows:
    1. Setup verification: email, code, and totp_secret provided
    2. Login verification: email and code only (secret retrieved from database)
    """
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6, description="6-digit TOTP code")
    totp_secret: Optional[str] = Field(None, description="TOTP secret from setup phase (optional for login)")


# ============ Password Recovery DTOs ============

class ForgotPasswordRequestDTO(BaseModel):
    """DTO for requesting password reset."""
    email: EmailStr


class ResetPasswordRequestDTO(BaseModel):
    """DTO for resetting password."""
    email: EmailStr
    token: str = Field(..., min_length=10, description="Password reset token")
    new_password: str = Field(..., min_length=8, description="Strong password required")


class VerifyResetTokenRequestDTO(BaseModel):
    """DTO for verifying password reset token."""
    email: EmailStr
    token: str


# ============ User DTOs ============

class UserResponseDTO(BaseModel):
    """DTO for user profile response."""
    id: str
    email: str
    full_name: Optional[str] = None
    verified: bool = False
    twofa_enabled: bool = False
    storage_used: int
    storage_limit: int
    created_at: Optional[str] = None


class UpdateProfileRequestDTO(BaseModel):
    """DTO for updating user profile."""
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
