"""
Configuration management for Media Service
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings and environment variables"""
    
    # Service info
    service_name: str = "FlowDock Media Service"
    service_version: str = "2.0.0"

    # JWT configuration - must match Auth Service
    jwt_secret: str = "secret"
    jwt_algorithm: str = "HS256"
    
    # Internal Service Authentication - must match Auth Service internal_api_key
    internal_api_key: str = "internal-api-key-change-in-production"
    
    # New: 32-byte Hex Key
    encryption_master_key: str = "a2d446b1587fd0afbf338055123deb317193c3406794b451296b6b3c16f85166"

    # MongoDB
    mongo_url: str = "mongodb://root:mongopass@mongo_meta:27017"
    mongo_db_name: str = "flowdock_media"
    
    # Auth Service (for activity logging and quota updates)
    auth_service_url: str = "http://auth_service:8000"
    
    # File validation
    allowed_mimes: List[str] = [
        # Images
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "image/svg+xml",
        "image/bmp",
        "image/tiff",

        # Documents
        "application/pdf",
        "text/plain",
        "application/rtf",
        "application/json",
        "application/xml",
        "text/csv",
        "application/epub+zip",

        # Microsoft / Office formats
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.oasis.opendocument.text",

        # Archives
        "application/zip",
        "application/x-tar",
        "application/gzip",
        "application/x-7z-compressed",
        "application/vnd.rar",
        "application/x-rar-compressed",

        # Audio
        "audio/mpeg",
        "audio/ogg",
        "audio/wav",
        "audio/webm",

        # Video
        "video/mp4",
        "video/webm",
        "video/quicktime",
        "video/x-msvideo"
    ]
    
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    min_file_size: int = 1  # 1 byte
    
    # GridFS
    gridfs_chunk_size: int = 262144  # 256KB (MongoDB default)
    
    # Logging
    log_level: str = "INFO"
    
    # API
    api_prefix: str = "/media"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
