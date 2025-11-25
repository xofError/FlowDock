from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=32)
    full_name: Optional[str] = None


class UserVerifyEmail(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=4, max_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    totp_code: Optional[str] = None  # only required if 2FA enabled


class UserResponse(UserBase):
    id: UUID
    verified: bool
    twofa_enabled: bool
    storage_used: int
    storage_limit: int
    created_at: datetime
    last_login_at: Optional[datetime]
    last_login_ip: Optional[str]

    class Config:
        orm_mode = True


class Enable2FA(BaseModel):
    enable: bool
    totp_code: Optional[str] = None
