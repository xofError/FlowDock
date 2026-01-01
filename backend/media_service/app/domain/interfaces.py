"""
Domain interfaces (abstract contracts) for the media service.
Define WHAT needs to happen without specifying HOW.
Implementations are in the infrastructure layer.
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional, Tuple, List, Dict, Any
from app.domain.entities import File, Folder


class IFileRepository(ABC):
    """
    Abstract contract for file storage.
    Implementations can use GridFS, S3, local filesystem, etc.
    """

    @abstractmethod
    async def save_file_stream(
        self,
        file: File,
        stream: AsyncGenerator,
    ) -> str:
        """
        Save a file and its metadata to storage.
        
        Args:
            file: Domain entity with file metadata
            stream: Async generator yielding file chunks
            
        Returns:
            file_id (str): The identifier of the saved file
        """
        pass

    @abstractmethod
    async def get_file_metadata(self, file_id: str) -> Optional[File]:
        """
        Retrieve only file metadata (no content).
        
        Args:
            file_id: The file identifier
            
        Returns:
            File entity with metadata, or None if not found
        """
        pass

    @abstractmethod
    async def get_file_stream(
        self,
        file_id: str,
    ) -> Tuple[Optional[File], Optional[AsyncGenerator]]:
        """
        Retrieve file metadata and content stream.
        
        Args:
            file_id: The file identifier
            
        Returns:
            Tuple of (File entity, async generator of chunks) or (None, None) if not found
        """
        pass

    @abstractmethod
    async def delete(self, file_id: str) -> bool:
        """
        Delete a file.
        
        Args:
            file_id: The file identifier
            
        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def list_by_owner(self, owner_id: str) -> List[File]:
        """
        List all files owned by a user.
        
        Args:
            owner_id: The owner's identifier
            
        Returns:
            List of File entities
        """
        pass


class ICryptoService(ABC):
    """
    Abstract contract for file encryption/decryption.
    Implementations can use AES, ChaCha20, etc.
    """

    @abstractmethod
    def generate_key_pair(self) -> Tuple[bytes, bytes]:
        """
        Generate a new file key and nonce.
        
        Returns:
            Tuple of (file_key, nonce)
        """
        pass

    @abstractmethod
    def encrypt_stream(
        self,
        stream: AsyncGenerator,
        file_key: bytes,
        nonce: bytes,
    ) -> AsyncGenerator:
        """
        Create an async generator that encrypts chunks on-the-fly.
        
        Args:
            stream: Input async generator yielding plaintext chunks
            file_key: Key for encryption
            nonce: Nonce/IV for encryption
            
        Yields:
            Encrypted chunks
        """
        pass

    @abstractmethod
    def decrypt_stream(
        self,
        stream: AsyncGenerator,
        file_key: bytes,
        nonce: bytes,
    ) -> AsyncGenerator:
        """
        Create an async generator that decrypts chunks on-the-fly.
        
        Args:
            stream: Input async generator yielding ciphertext chunks
            file_key: Key for decryption
            nonce: Nonce/IV for decryption
            
        Yields:
            Decrypted chunks
        """
        pass

    @abstractmethod
    def wrap_key(self, file_key: bytes) -> bytes:
        """
        Encrypt a file key with the master key (key wrapping).
        
        Args:
            file_key: The file-specific key
            
        Returns:
            Encrypted key
        """
        pass

    @abstractmethod
    def unwrap_key(self, encrypted_key: bytes) -> bytes:
        """
        Decrypt a wrapped file key using the master key.
        
        Args:
            encrypted_key: The encrypted key
            
        Returns:
            Decrypted key
        """
        pass


class IEventPublisher(ABC):
    """
    Abstract contract for publishing file events (async messaging).
    Implementations can use RabbitMQ, Kafka, SNS, etc.
    """

    @abstractmethod
    async def publish_upload(self, user_id: str, file_id: str, file_size: int) -> None:
        """
        Publish a FILE_UPLOADED event.
        
        Args:
            user_id: Owner of the file
            file_id: The uploaded file identifier
            file_size: Size of the file in bytes
        """
        pass

    @abstractmethod
    async def publish_delete(self, user_id: str, file_id: str, file_size: int) -> None:
        """
        Publish a FILE_DELETED event.
        
        Args:
            user_id: Owner of the file
            file_id: The deleted file identifier
            file_size: Size of the file in bytes
        """
        pass

    @abstractmethod
    async def publish_download(self, user_id: str, file_id: str) -> None:
        """
        Publish a FILE_DOWNLOADED event.
        
        Args:
            user_id: User who downloaded
            file_id: The downloaded file identifier
        """
        pass


class IQuotaRepository(ABC):
    """
    Abstract contract for updating user storage quota.
    Implementations can use HTTP calls, direct DB access, messaging, etc.
    """

    @abstractmethod
    async def update_usage(self, user_id: str, size_delta: int) -> None:
        """
        Update the user's storage quota in the Auth Service.
        
        This is called whenever a file is uploaded or deleted to keep
        the user's storage_used counter in sync.
        
        Args:
            user_id: The user whose quota should be updated
            size_delta: The change in storage (positive for upload, negative for delete)
        """
        pass


class IActivityLogger(ABC):
    """
    Abstract contract for logging user activities to the Auth Service.
    Implementations can use HTTP calls, direct DB access, messaging, etc.
    """

    @abstractmethod
    async def log_activity(
        self,
        user_id: str,
        action: str,
        details: Dict[str, Any] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """
        Log a user activity to the Auth Service.
        
        This is called when important actions occur (file upload, delete, download).
        
        Args:
            user_id: The user who performed the action
            action: Action type (e.g., "FILE_UPLOAD", "FILE_DELETE")
            details: Optional context data (filename, size, etc.)
            ip_address: Optional client IP address
        """
        pass


class IFolderRepository(ABC):
    """
    Abstract contract for folder storage and management.
    Supports hierarchical folder structure with parent_id pattern.
    """

    @abstractmethod
    async def create_folder(self, folder: "Folder") -> str:
        """
        Create a new folder.
        
        Args:
            folder: Folder entity with name, owner_id, and optional parent_id
            
        Returns:
            folder_id (str): The identifier of the created folder
        """
        pass

    @abstractmethod
    async def get_folder(self, folder_id: str, owner_id: str) -> Optional["Folder"]:
        """
        Get a folder by ID (with ownership verification).
        
        Args:
            folder_id: The folder identifier
            owner_id: The owner (for verification)
            
        Returns:
            Folder entity or None if not found/not owned
        """
        pass

    @abstractmethod
    async def list_folders(
        self,
        owner_id: str,
        parent_id: Optional[str] = None,
    ) -> List["Folder"]:
        """
        List folders for a user.
        
        Args:
            owner_id: The owner's identifier
            parent_id: Optional parent folder ID (None = root folders)
            
        Returns:
            List of Folder entities
        """
        pass

    @abstractmethod
    async def update_folder(self, folder: "Folder") -> bool:
        """
        Update folder metadata.
        
        Args:
            folder: Folder entity with updated fields
            
        Returns:
            True if updated, False if not found
        """
        pass

    @abstractmethod
    async def delete_folder(self, folder_id: str, owner_id: str) -> bool:
        """
        Delete a folder (only if empty).
        
        Args:
            folder_id: The folder identifier
            owner_id: The owner (for verification)
            
        Returns:
            True if deleted, False if not found/not owned/not empty
        """
        pass

    @abstractmethod
    async def get_folder_contents_size(self, folder_id: str) -> int:
        """
        Get total size of all files in a folder (for deletion checks).
        
        Args:
            folder_id: The folder identifier
            
        Returns:
            Total size in bytes
        """
        pass

