from pydantic import BaseModel
from uuid import UUID


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    user_id: UUID
    exp: int  # expiration timestamp


class RefreshTokenSchema(BaseModel):
    refresh_token: str
