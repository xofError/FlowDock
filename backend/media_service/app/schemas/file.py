"""
Request and response schemas for file operations
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


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


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(default="healthy", description="Service health status")
    service: str = Field(..., description="Service name")
    mongodb: str = Field(default="connected", description="MongoDB status")
    rabbitmq: str = Field(default="connected", description="RabbitMQ status")


class ErrorResponse(BaseModel):
    """Error response"""
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
