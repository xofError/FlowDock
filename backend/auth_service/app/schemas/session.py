from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class SessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    device_info: str
    browser_name: str
    ip_address: str
    created_at: datetime
    expires_at: datetime
    active: bool

    class Config:
        orm_mode = True
