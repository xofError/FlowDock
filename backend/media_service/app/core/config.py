"""
Configuration management for Media Service
"""

import os
from typing import List


class Settings:
    """Application settings and environment variables"""
    
    # Service info
    SERVICE_NAME: str = "FlowDock Media Service"
    SERVICE_VERSION: str = "2.0.0"
    
    # MongoDB
    MONGO_URL: str = os.getenv(
        "MONGO_URL",
        "mongodb://root:mongopass@mongo_meta:27017"
    )
    MONGO_DB_NAME: str = "flowdock_media"
    
    # RabbitMQ
    RABBITMQ_URL: str = os.getenv(
        "RABBITMQ_URL",
        "amqp://guest:guest@rabbitmq:5672/"
    )
    RABBITMQ_QUEUE: str = "file_events"
    
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
