"""
Domain entities for the media service.
Pure Python objects independent of technology choices (MongoDB, GridFS, encryption libs).
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List


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
    folder_id: Optional[str] = None  # Folder containing this file (None = root)
    upload_date: Optional[datetime] = None
    
    # Encryption metadata
    encrypted: bool = False
    nonce: str = ""  # IV for CTR mode (hex string)
    encrypted_key: str = ""  # Wrapped file key (hex string)
    
    # Virus scan status
    is_infected: bool = False
    
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
            "folder_id": self.folder_id,
            "upload_date": self.upload_date,
            "encrypted": self.encrypted,
            "nonce": self.nonce,
            "encrypted_key": self.encrypted_key,
            "is_infected": self.is_infected,
            "metadata": self.metadata,
        }


@dataclass
class Folder:
    """
    Pure domain entity representing a folder in the file system.
    Supports hierarchical structure using parent_id pattern.
    """
    id: Optional[str] = None  # MongoDB ObjectId
    name: str = ""
    owner_id: str = ""
    parent_id: Optional[str] = None  # None for root folders
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    path: List[Dict[str, str]] = field(default_factory=list)  # Breadcrumb: [{"id": "...", "name": "..."}]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize timestamps if not provided"""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "owner_id": self.owner_id,
            "parent_id": self.parent_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "path": self.path,
            "metadata": self.metadata,
        }

    def is_root(self) -> bool:
        """Check if this is a root folder"""
        return self.parent_id is None
