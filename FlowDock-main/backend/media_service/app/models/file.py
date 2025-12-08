"""
Database models for MongoDB
"""

from datetime import datetime
from typing import Optional, Dict, Any


class FileMetadata:
    """File metadata model for GridFS"""
    
    def __init__(
        self,
        file_id: str,
        filename: str,
        size: int,
        content_type: str,
        owner_id: str,
        upload_date: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.file_id = file_id
        self.filename = filename
        self.size = size
        self.content_type = content_type
        self.owner_id = owner_id
        self.upload_date = upload_date or datetime.utcnow()
        self.metadata = metadata or {}
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "file_id": self.file_id,
            "filename": self.filename,
            "size": self.size,
            "content_type": self.content_type,
            "owner_id": self.owner_id,
            "upload_date": self.upload_date,
            "metadata": self.metadata
        }
