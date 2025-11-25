from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None


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
