"""
Data Transfer Objects (DTOs) for the application layer.
These are Pydantic schemas used in API requests/responses.
Moved here from schemas/ to follow Clean Architecture conventions.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


# ============================================================================
# FILE DTOs
# ============================================================================
class FileUploadResponse(BaseModel):
    """Response from file upload"""
    file_id: str = Field(..., description="MongoDB ObjectId of uploaded file")
    status: str = Field(default="uploaded", description="Upload status")
    size: int = Field(..., description="File size in bytes")
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type of file")


class FileMetadataResponse(BaseModel):
    """Response containing file metadata"""
    file_id: str = Field(..., description="MongoDB ObjectId")
    filename: str = Field(..., description="Original filename")
    size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME type")
    upload_date: datetime = Field(..., description="Upload timestamp")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class FileDeleteResponse(BaseModel):
    """Response from file deletion"""
    status: str = Field(default="deleted", description="Deletion status")
    file_id: str = Field(..., description="Deleted file ID")


class FileListResponse(BaseModel):
    """Response containing list of files"""
    files: list = Field(default_factory=list, description="List of file metadata")
    total: int = Field(..., description="Total number of files")


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(default="healthy", description="Service health status")
    service: str = Field(..., description="Service name")
    mongodb: str = Field(default="connected", description="MongoDB status")


class ErrorResponse(BaseModel):
    """Error response"""
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")


# ============================================================================
# SHARING DTOs (kept from original schemas/sharing.py)
# ============================================================================
class ShareCreate(BaseModel):
    """Request to share a file with another user"""
    file_id: str = Field(..., description="File ID to share")
    target_email: str = Field(..., description="Email of user to share with")
    permission: str = Field(default="view", description="Permission level (view, edit)")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")


class ShareLinkCreate(BaseModel):
    """Request to create a public share link"""
    file_id: str = Field(..., description="File ID to create link for")
    expires_at: Optional[datetime] = Field(None, description="Link expiration")
    password: Optional[str] = Field(None, description="Optional password protection")


class ShareLinkResponse(BaseModel):
    """Response containing a public share link"""
    share_id: str = Field(..., description="Unique share identifier")
    link: str = Field(..., description="Public share URL")
    expires_at: Optional[datetime] = Field(None)
    password_protected: bool = Field(default=False)


class AccessLinkRequest(BaseModel):
    """Request to access a shared link"""
    password: Optional[str] = Field(None, description="Password if link is protected")


class AccessLinkResponse(BaseModel):
    """Response granting access to shared file"""
    download_token: str = Field(..., description="JWT token for download")
    file_id: str = Field(..., description="File ID")
    filename: str = Field(..., description="File name")


class ShareFileResponse(BaseModel):
    """Response from file sharing"""
    status: str = Field(default="shared", description="Sharing status")
    file_id: str = Field(..., description="File ID")
    target: str = Field(..., description="Share target (email or link)")
