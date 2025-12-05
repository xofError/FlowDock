from pydantic import BaseModel, EmailStr , Field
from typing import Optional


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    # Optional TOTP code for combined login+TOTP flow
    totp_code: Optional[str] = None


class TokenResponse(BaseModel):
    """Response containing an access token and user info.

    Refresh tokens should not be returned in JSON responses for
    production; they are set as HttpOnly cookies instead.
    """
    access_token: str
    token_type: str = "bearer"
    user_id: str
    totp_required: bool = False


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class TotpSetupRequest(BaseModel):
    email: EmailStr


class TotpVerifyRequest(BaseModel):
    email: EmailStr
    code: str


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str


class VerifyEmailOTPRequest(BaseModel):
    email: EmailStr
    token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    token: str = Field(..., min_length=6, max_length=6, description="The 6-digit OTP")
    new_password: str = Field(..., min_length=8, description="New strong password")
# from pydantic import BaseModel
# from uuid import UUID


# class Token(BaseModel):
#     access_token: str
#     refresh_token: str
#     token_type: str = "bearer"


# class TokenPayload(BaseModel):
#     user_id: UUID
#     exp: int  # expiration timestamp


# class RefreshTokenSchema(BaseModel):
#     refresh_token: str
