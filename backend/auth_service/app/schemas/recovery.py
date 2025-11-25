from pydantic import BaseModel, EmailStr
from datetime import datetime
from uuid import UUID


class RequestPasswordReset(BaseModel):
    email: EmailStr


class VerifyResetToken(BaseModel):
    token: str
    new_password: str


class RecoveryTokenResponse(BaseModel):
    id: UUID
    user_id: UUID
    method: str
    created_at: datetime
    expires_at: datetime
    used: bool

    class Config:
        orm_mode = True
