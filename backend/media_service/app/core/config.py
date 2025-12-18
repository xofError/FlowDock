"""
Configuration management for Media Service
"""

import os
from typing import List


class Settings:
    """Application settings and environment variables"""
    JWT_SECRET= "secret"
    # Service info
    SERVICE_NAME: str = "FlowDock Media Service"
    SERVICE_VERSION: str = "2.0.0"

    # New: 32-byte Hex Key
    ENCRYPTION_MASTER_KEY: str = os.getenv("ENCRYPTION_MASTER_KEY" , "a2d446b1587fd0afbf338055123deb317193c3406794b451296b6b3c16f85166")

    # MongoDB
    MONGO_URL: str = os.getenv(
        "MONGO_URL",
        "mongodb://root:mongopass@mongo_meta:27017"
    )
    MONGO_DB_NAME: str = "flowdock_media"
    
    # Auth Service (for quota updates)
    AUTH_SERVICE_URL: str = os.getenv(
        "AUTH_SERVICE_URL",
        "http://auth_service:8000"
    )
    
    # File validation
    ALLOWED_MIMES: List[str] = [
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
    
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    MIN_FILE_SIZE: int = 1  # 1 byte
    
    # GridFS
    GRIDFS_CHUNK_SIZE: int = 262144  # 256KB (MongoDB default)
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # API
    API_PREFIX: str = "/media"
    
    @classmethod
    def get_settings(cls):
        """Get settings instance"""
        return cls()


settings = Settings.get_settings()
