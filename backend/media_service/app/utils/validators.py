"""
Utility functions for file validation and error handling
"""

import logging
from typing import Optional, AsyncGenerator, Tuple
from app.core.config import settings

logger = logging.getLogger(__name__)

# Magic bytes (file signatures) for common file types
# Format: (file_signature_bytes, mime_type, description)
MAGIC_BYTES = {
    b'\xff\xd8\xff': ('image/jpeg', 'JPEG'),
    b'\x89\x50\x4e\x47': ('image/png', 'PNG'),
    b'\x47\x49\x46\x38': ('image/gif', 'GIF'),
    b'\x25\x50\x44\x46': ('application/pdf', 'PDF'),
    b'\x50\x4b\x03\x04': ('application/zip', 'ZIP'),
    b'\x7f\x45\x4c\x46': ('application/x-executable', 'ELF Executable'),
    b'\x4d\x5a': ('application/x-msdownload', 'Windows Executable'),
    b'\xca\xfe\xba\xbe': ('application/x-java-applet', 'Java Class'),
    b'\xd0\xcf\x11\xe0': ('application/vnd.ms-office', 'MS Office'),
    b'\xff\xfb': ('audio/mpeg', 'MP3'),
    b'\x49\x49\x2a\x00': ('image/tiff', 'TIFF'),
    b'\x4d\x4d\x00\x2a': ('image/tiff', 'TIFF'),
}


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
    return content_type in settings.allowed_mimes


async def validate_file_type_by_magic_bytes(
    file_stream: AsyncGenerator,
    declared_mime: Optional[str],
    filename: str
) -> Tuple[bool, Optional[str]]:
    """
    Validate file type by reading magic bytes (file signature).
    This prevents malicious users from uploading .exe as image/png.
    
    Args:
        file_stream: Async generator yielding file chunks
        declared_mime: The MIME type declared by the client
        filename: Original filename for fallback validation
    
    Returns:
        Tuple of (is_valid, error_message)
        
    Example:
        is_valid, error = await validate_file_type_by_magic_bytes(stream, 'image/png', 'photo.png')
    """
    try:
        # Read first few bytes to check magic signature
        magic_buffer = b''
        async for chunk in file_stream:
            magic_buffer += chunk
            if len(magic_buffer) >= 4:  # Most magic bytes are 1-4 bytes
                break
        
        if not magic_buffer:
            return False, "Empty file"
        
        # Check against known magic bytes
        detected_mime = None
        for signature_bytes, mime_type, description in [(sig, mime, desc) for sig, mime, desc in [
            (b'\xff\xd8\xff', 'image/jpeg', 'JPEG'),
            (b'\x89\x50\x4e\x47', 'image/png', 'PNG'),
            (b'\x47\x49\x46\x38', 'image/gif', 'GIF'),
            (b'\x25\x50\x44\x46', 'application/pdf', 'PDF'),
            (b'\x50\x4b\x03\x04', 'application/zip', 'ZIP'),
            (b'\x7f\x45\x4c\x46', 'application/x-executable', 'ELF'),
            (b'\x4d\x5a', 'application/x-msdownload', 'Windows EXE'),
            (b'\xca\xfe\xba\xbe', 'application/x-java-applet', 'Java'),
            (b'\xd0\xcf\x11\xe0', 'application/vnd.ms-office', 'MS Office'),
            (b'\xff\xfb', 'audio/mpeg', 'MP3'),
        ]]:
            if magic_buffer.startswith(signature_bytes):
                detected_mime = mime_type
                logger.warning(f"[Magic Bytes] Detected {description} ({mime_type}) from file {filename}")
                break
        
        # If we detected a MIME type, verify it matches declared type
        if detected_mime:
            # Check if declared MIME matches detected
            if declared_mime and declared_mime != detected_mime:
                logger.error(f"[Magic Bytes] MIME mismatch: declared {declared_mime}, detected {detected_mime} for {filename}")
                return False, f"File type mismatch: declared as {declared_mime} but is {detected_mime}"
            
            # Check if detected type is allowed
            if detected_mime not in settings.allowed_mimes:
                logger.error(f"[Magic Bytes] Blocked dangerous file type {detected_mime}: {filename}")
                return False, f"File type not allowed: {detected_mime}"
            
            return True, None
        
        # If we couldn't detect magic bytes, fall back to MIME type validation
        # (Some legitimate files may not have recognizable magic bytes)
        if declared_mime and declared_mime in settings.allowed_mimes:
            return True, None
        
        return False, f"Could not verify file type (declared: {declared_mime})"
        
    except Exception as e:
        logger.error(f"[Magic Bytes] Validation error for {filename}: {e}")
        # In case of error, allow the file through but log it
        # Better to allow legitimate files than block everything
        if declared_mime and declared_mime in settings.allowed_mimes:
            return True, None
        return False, "File type validation error"


def validate_file_size(file_size: int) -> tuple[bool, Optional[str]]:
    """
    Validate file size
    
    Args:
        file_size: File size in bytes
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if file_size < settings.min_file_size:
        return False, "Empty file not allowed"
    
    if file_size > settings.max_file_size:
        size_mb = file_size / (1024 * 1024)
        max_mb = settings.max_file_size / (1024 * 1024)
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
    return ", ".join(settings.allowed_mimes)
