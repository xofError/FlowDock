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


# ============================================================================
# FOLDER DTOs
# ============================================================================
class FolderCreateRequest(BaseModel):
    """Request to create a folder"""
    name: str = Field(..., min_length=1, max_length=255, description="Folder name")
    parent_id: Optional[str] = Field(None, description="Parent folder ID (None for root)")


class FolderResponse(BaseModel):
    """Response containing folder metadata"""
    folder_id: str = Field(..., description="MongoDB ObjectId of folder")
    name: str = Field(..., description="Folder name")
    parent_id: Optional[str] = Field(None, description="Parent folder ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last updated timestamp")


class FolderListResponse(BaseModel):
    """Response containing list of folders"""
    folders: list = Field(default_factory=list, description="List of folder metadata")
    total: int = Field(..., description="Total number of folders")


class FolderUpdateRequest(BaseModel):
    """Request to update folder metadata"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="New folder name")


class FolderDeleteResponse(BaseModel):
    """Response from folder deletion"""
    status: str = Field(default="deleted", description="Deletion status")
    folder_id: str = Field(..., description="Deleted folder ID")


class FolderUploadResponse(BaseModel):
    """Response from folder upload"""
    status: str = Field(default="uploaded", description="Upload status")
    folder_id: str = Field(..., description="Created root folder ID")
    files_uploaded: int = Field(..., description="Number of files uploaded")
    total_size: int = Field(..., description="Total size in bytes")
    failed_files: int = Field(default=0, description="Number of failed uploads")


class FolderContentsResponse(BaseModel):
    """Response containing folder contents (files and subfolders)"""
    folder: dict = Field(..., description="Folder metadata")
    files: list = Field(default_factory=list, description="Files in this folder")
    subfolders: list = Field(default_factory=list, description="Subfolders in this folder")


# ============================================================================
# FOLDER SHARING DTOs
# ============================================================================
class FolderShareRequest(BaseModel):
    """Request to share a folder with user(s) or group(s)"""
    folder_id: str = Field(..., description="Folder ID to share")
    targets: list = Field(..., description="List of email addresses or group IDs to share with")
    permission: str = Field(default="view", description="Permission level (view, edit, admin)")
    cascade: bool = Field(default=True, description="Apply permissions to subfolders")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration date for share")


class FolderShareResponse(BaseModel):
    """Response from folder sharing"""
    status: str = Field(default="shared", description="Sharing status")
    folder_id: str = Field(..., description="Folder ID")
    targets_count: int = Field(..., description="Number of targets shared with")


class FolderShareListResponse(BaseModel):
    """Response containing list of users/groups a folder is shared with"""
    folder_id: str = Field(..., description="Folder ID")
    shared_with: list = Field(default_factory=list, description="List of shares")


class FolderUnshareRequest(BaseModel):
    """Request to remove sharing from a folder"""
    folder_id: str = Field(..., description="Folder ID")
    target: str = Field(..., description="Email or group ID to revoke access from")
    cascade: bool = Field(default=True, description="Remove from subfolders too")


# ============================================================================
# PUBLIC FOLDER LINK DTOs
# ============================================================================
class PublicFolderLinkCreate(BaseModel):
    """Request to create a public link for a folder"""
    folder_id: str = Field(..., description="Folder ID to create link for")
    expires_at: Optional[datetime] = Field(None, description="Link expiration")
    password: Optional[str] = Field(None, description="Optional password protection")
    max_downloads: Optional[int] = Field(None, description="Maximum download count")


class PublicFolderLinkResponse(BaseModel):
    """Response containing a public folder link"""
    link_id: str = Field(..., description="Unique link identifier")
    link: str = Field(..., description="Public folder URL")
    folder_id: str = Field(..., description="Folder ID")
    expires_at: Optional[datetime] = Field(None)
    password_protected: bool = Field(default=False)
    created_at: datetime = Field(..., description="Creation timestamp")


class PublicFolderAccessRequest(BaseModel):
    """Request to access a public folder link"""
    password: Optional[str] = Field(None, description="Password if link is protected")


class PublicFolderAccessResponse(BaseModel):
    """Response granting access to public folder"""
    access_token: str = Field(..., description="JWT token for folder access")
    folder_id: str = Field(..., description="Folder ID")
    folder_name: str = Field(..., description="Folder name")
    expires_in: int = Field(..., description="Token expiration in seconds")


