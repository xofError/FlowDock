"""
Domain interfaces (abstract contracts) for the media service.
Define WHAT needs to happen without specifying HOW.
Implementations are in the infrastructure layer.
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional, Tuple, List, Dict, Any
from app.domain.entities import File


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
