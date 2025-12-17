"""
Domain entities for the media service.
Pure Python objects independent of technology choices (MongoDB, GridFS, encryption libs).
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class File:
    """
    Pure domain entity representing a file in the system.
    Contains only the essential attributes a file needs, agnostic of storage technology.
    """
    id: Optional[str] = None  # ObjectId from GridFS
    filename: str = ""
    content_type: str = ""
    size: int = 0
    owner_id: str = ""
    upload_date: Optional[datetime] = None
    
    # Encryption metadata
    encrypted: bool = False
    nonce: str = ""  # IV for CTR mode (hex string)
    encrypted_key: str = ""  # Wrapped file key (hex string)
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize datetime if not provided"""
        if self.upload_date is None:
            self.upload_date = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary"""
        return {
            "id": self.id,
            "filename": self.filename,
            "content_type": self.content_type,
            "size": self.size,
            "owner_id": self.owner_id,
            "upload_date": self.upload_date,
            "encrypted": self.encrypted,
            "nonce": self.nonce,
            "encrypted_key": self.encrypted_key,
            "metadata": self.metadata,
        }
