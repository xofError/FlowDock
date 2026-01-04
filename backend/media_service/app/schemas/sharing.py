from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# --- Direct Sharing ---
class ShareCreate(BaseModel):
    file_id: str
    target_email: EmailStr  # User enters email, backend looks up ID
    permission: str = "read"
    expires_at: Optional[datetime] = Field(
        None,
        description="Expiration date (leave empty for 30-day default)",
        example=None
    )


# --- Link Sharing ---
class ShareLinkCreate(BaseModel):
    file_id: str
    password: Optional[str] = None
    expires_at: Optional[datetime] = Field(
        None,
        description="Expiration date (leave empty for 30-day default)",
        example=None
    )
    max_downloads: int = 0


class ShareLinkResponse(BaseModel):
    short_code: str
    link_url: str
    expires_at: Optional[datetime]
    has_password: bool


class AccessLinkRequest(BaseModel):
    password: Optional[str] = None


class AccessLinkResponse(BaseModel):
    """Response when public link access is granted"""
    status: str = "authorized"
    download_url: str
    
    class Config:
        example = {
            "status": "authorized",
            "download_url": "https://api.flowdock.com/media/download/507f1f77bcf86cd799439011?token=eyJ0eXAiOiJKV1QiLCJhbGc..."
        }


class ShareFileResponse(BaseModel):
    """Response when file is shared with a user"""
    message: str = "File shared successfully"
    share_id: Optional[str] = None