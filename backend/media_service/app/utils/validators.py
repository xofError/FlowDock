"""
Utility functions for file validation and error handling
"""

import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


def validate_file_type(content_type: Optional[str]) -> bool:
    """
    Validate if file MIME type is allowed
    
    Args:
        content_type: File content type
    
    Returns:
        True if allowed, False otherwise
    """
    if not content_type:
        return False
    return content_type in settings.ALLOWED_MIMES


def validate_file_size(file_size: int) -> tuple[bool, Optional[str]]:
    """
    Validate file size
    
    Args:
        file_size: File size in bytes
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if file_size < settings.MIN_FILE_SIZE:
        return False, "Empty file not allowed"
    
    if file_size > settings.MAX_FILE_SIZE:
        size_mb = file_size / (1024 * 1024)
        max_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
        return False, f"File too large: {size_mb:.2f}MB. Max: {max_mb:.0f}MB"
    
    return True, None


def format_file_size(size_bytes: int) -> str:
    """
    Format bytes to human readable size
    
    Args:
        size_bytes: Size in bytes
    
    Returns:
        Formatted size string (e.g., "5.2 MB")
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"


def get_allowed_mimes_description() -> str:
    """Get comma-separated list of allowed MIME types"""
    return ", ".join(settings.ALLOWED_MIMES)
