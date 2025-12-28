"""
Application service orchestrating file operations.
Pure business logic - depends on interfaces, not implementations.
"""

import logging
from typing import AsyncGenerator, Optional, Tuple, List
from fastapi import UploadFile

from app.domain.entities import File
from app.domain.interfaces import (
    IFileRepository,
    ICryptoService,
    IEventPublisher,
    IQuotaRepository,
    IActivityLogger,
)
from app.utils.validators import validate_file_type, validate_file_size

logger = logging.getLogger(__name__)


class FileService:
    """
    Main application service for file operations.
    Orchestrates business logic without knowing implementation details.
    """

    def __init__(
        self,
        repo: IFileRepository,
        crypto: ICryptoService,
        event_publisher: IEventPublisher,
        quota_repo: IQuotaRepository,
        activity_logger: IActivityLogger = None,
    ):
        """
        Initialize service with dependencies (Dependency Injection).
        
        Args:
            repo: File repository implementation
            crypto: Crypto service implementation
            event_publisher: Event publisher implementation
            quota_repo: Quota repository for updating storage usage
            activity_logger: Optional activity logger for audit trails
        """
        self.repo = repo
        self.crypto = crypto
        self.publisher = event_publisher
        self.quota_repo = quota_repo
        self.activity_logger = activity_logger

    # ========================================================================
    # Upload Operations
    # ========================================================================

    async def upload_file_unencrypted(
        self,
        user_id: str,
        filename: str,
        file_content: bytes,
        content_type: str,
        ip_address: Optional[str] = None,
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Upload an unencrypted file.
        
        Args:
            user_id: Owner of the file
            filename: Original filename
            file_content: File bytes
            content_type: MIME type
            ip_address: Optional client IP for logging
            
        Returns:
            Tuple of (success, file_id, error_message)
        """
        # 1. Validate
        if not validate_file_type(content_type):
            return False, None, f"Invalid file type: {content_type}"

        is_valid, error_msg = validate_file_size(len(file_content))
        if not is_valid:
            return False, None, error_msg

        try:
            # 2. Create domain entity
            file = File(
                filename=filename,
                content_type=content_type,
                size=len(file_content),
                owner_id=user_id,
                encrypted=False,
            )

            # 3. Create stream from bytes
            async def byte_stream():
                yield file_content

            # 4. Save via repository
            file_id = await self.repo.save_file_stream(file, byte_stream())

            # 5. Update storage quota
            await self.quota_repo.update_usage(user_id, len(file_content))

            # 6. Log activity
            if self.activity_logger:
                await self.activity_logger.log_activity(
                    user_id,
                    "FILE_UPLOAD",
                    {
                        "file_id": file_id,
                        "filename": filename,
                        "size": len(file_content),
                        "content_type": content_type,
                    },
                    ip_address,
                )

            logger.info(f"✓ Uploaded unencrypted file {file_id}")
            return True, file_id, None

        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return False, None, str(e)

    async def upload_file_encrypted(
        self,
        user_id: str,
        file: UploadFile,
        ip_address: Optional[str] = None,
    ) -> Tuple[bool, Optional[str], int, Optional[str]]:
        """
        Upload file with envelope encryption using streaming.
        
        Args:
            user_id: Owner of the file
            file: UploadFile object (streaming)
            ip_address: Optional client IP for logging
            
        Returns:
            Tuple of (success, file_id, original_size, error_message)
        """
        # 1. Validate
        if not validate_file_type(file.content_type):
            return False, None, 0, "Invalid file type"

        try:
            # 2. Generate encryption keys
            file_key, nonce = self.crypto.generate_key_pair()
            encrypted_key = self.crypto.wrap_key(file_key)

            # 3. Create domain entity with encryption metadata
            file_entity = File(
                filename=file.filename,
                content_type=file.content_type,
                owner_id=user_id,
                encrypted=True,
                nonce=nonce.hex(),
                encrypted_key=encrypted_key.hex(),
            )

            # 4. Create encrypted stream
            original_size = 0
            chunk_size = 64 * 1024

            async def encrypt_and_track_stream():
                nonlocal original_size
                while True:
                    chunk = await file.read(chunk_size)
                    if not chunk:
                        break
                    original_size += len(chunk)
                    yield chunk

            # 5. Encrypt the stream
            encrypted_stream = self.crypto.encrypt_stream(
                encrypt_and_track_stream(),
                file_key,
                nonce,
            )

            # 6. Save encrypted stream
            file_id = await self.repo.save_file_stream(file_entity, encrypted_stream)
            file_entity.id = file_id

            # 7. Update storage quota
            await self.quota_repo.update_usage(user_id, original_size)

            # 8. Log activity
            if self.activity_logger:
                await self.activity_logger.log_activity(
                    user_id,
                    "FILE_UPLOAD",
                    {
                        "file_id": file_id,
                        "filename": file.filename,
                        "size": original_size,
                        "content_type": file.content_type,
                        "encrypted": True,
                    },
                    ip_address,
                )

            logger.info(f"✓ Uploaded encrypted file {file_id} (original: {original_size} bytes)")
            return True, file_id, original_size, None

        except Exception as e:
            logger.error(f"Encryption upload failed: {e}")
            return False, None, 0, str(e)

    async def _uploadfile_to_async_gen(self, upload_file: UploadFile) -> AsyncGenerator:
        """Convert UploadFile to async generator"""
        chunk_size = 64 * 1024
        while True:
            chunk = await upload_file.read(chunk_size)
            if not chunk:
                break
            yield chunk

    async def _save_encrypted_and_track_size(
        self,
        file_entity: File,
        encrypted_stream: AsyncGenerator,
        upload_file: UploadFile,
    ) -> int:
        """
        Save encrypted stream and track original size.
        
        Returns:
            Original file size
        """
        original_size = 0
        chunk_size = 64 * 1024

        async def size_tracking_stream():
            nonlocal original_size
            upload_file.file.seek(0)  # Reset to beginning
            while True:
                chunk = await upload_file.read(chunk_size)
                if not chunk:
                    break
                original_size += len(chunk)
                yield chunk

        # Re-create encrypted stream with size tracking
        encrypted_stream = self.crypto.encrypt_stream(
            size_tracking_stream(),
            bytes.fromhex(file_entity.encrypted_key.replace("encrypted_key", "")),
            bytes.fromhex(file_entity.nonce),
        )

        file_id = await self.repo.save_file_stream(file_entity, encrypted_stream)
        file_entity.id = file_id
        return original_size

    # ========================================================================
    # Download Operations
    # ========================================================================

    async def download_file(
        self,
        file_id: str,
        requester_user_id: str,
        allow_shared: bool = False,
    ) -> Tuple[bool, Optional[AsyncGenerator], Optional[dict], Optional[str]]:
        """
        Download and decrypt file if encrypted.
        
        Args:
            file_id: File to download
            requester_user_id: User requesting (for ownership check)
            
        Returns:
            Tuple of (success, file_stream, metadata, error_message)
        """
        try:
            # 1. Get file metadata
            file = await self.repo.get_file_metadata(file_id)
            if not file:
                return False, None, None, "File not found"

            # 2. Check ownership or allowed shared access
            if requester_user_id != "public_link" and file.owner_id != requester_user_id and not allow_shared:
                return False, None, None, "Access denied"

            # 3. Get file stream
            file, stream = await self.repo.get_file_stream(file_id)
            if not stream:
                return False, None, None, "Cannot open file"

            # 4. Decrypt if necessary
            if file.encrypted:
                try:
                    file_key = self.crypto.unwrap_key(bytes.fromhex(file.encrypted_key))
                    nonce = bytes.fromhex(file.nonce)
                    stream = self.crypto.decrypt_stream(stream, file_key, nonce)
                except Exception as e:
                    logger.error(f"Decryption setup failed: {e}")
                    return False, None, None, "Decryption error"

            # 5. Publish download event
            await self.publisher.publish_download(requester_user_id, file_id)

            # 6. Prepare metadata
            metadata = {
                "filename": file.filename,
                "content_type": file.content_type,
                "size": file.size,
            }

            logger.info(f"✓ Started download for file {file_id}")
            return True, stream, metadata, None

        except Exception as e:
            logger.error(f"Download failed: {e}")
            return False, None, None, "Download error"

    # ========================================================================
    # Delete Operations
    # ========================================================================

    async def delete_file(
        self,
        file_id: str,
        requester_user_id: str,
        ip_address: Optional[str] = None,
    ) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Delete a file.
        
        Args:
            file_id: File to delete
            requester_user_id: User requesting deletion
            ip_address: Optional client IP for logging
            
        Returns:
            Tuple of (success, file_size, error_message)
        """
        try:
            # 1. Get metadata to verify ownership
            file = await self.repo.get_file_metadata(file_id)
            if not file:
                return False, None, "File not found"

            if file.owner_id != requester_user_id:
                return False, None, "Access denied"

            # 2. Delete
            success = await self.repo.delete(file_id)
            if not success:
                return False, None, "Deletion failed"

            # 3. Update storage quota (negative delta for deletion)
            await self.quota_repo.update_usage(requester_user_id, -file.size)

            # 4. Log activity
            if self.activity_logger:
                await self.activity_logger.log_activity(
                    requester_user_id,
                    "FILE_DELETE",
                    {
                        "file_id": file_id,
                        "filename": file.filename,
                        "size": file.size,
                    },
                    ip_address,
                )

            logger.info(f"✓ Deleted file {file_id}")
            return True, file.size, None

        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False, None, str(e)

    # ========================================================================
    # Metadata & List Operations
    # ========================================================================

    async def get_file_metadata(
        self,
        file_id: str,
        requester_user_id: str,
    ) -> Tuple[bool, Optional[dict], Optional[str]]:
        """
        Get file metadata.
        
        Args:
            file_id: File to retrieve metadata for
            requester_user_id: User requesting
            
        Returns:
            Tuple of (success, metadata_dict, error_message)
        """
        try:
            file = await self.repo.get_file_metadata(file_id)
            if not file:
                return False, None, "File not found"

            if requester_user_id != "public_link" and file.owner_id != requester_user_id:
                return False, None, "Access denied"

            metadata = {
                "file_id": file.id,
                "filename": file.filename,
                "size": file.size,
                "content_type": file.content_type,
                "upload_date": file.upload_date,
                "encrypted": file.encrypted,
            }

            return True, metadata, None

        except Exception as e:
            logger.error(f"Metadata retrieval failed: {e}")
            return False, None, str(e)

    async def list_user_files(
        self,
        user_id: str,
    ) -> Tuple[bool, Optional[List[dict]], Optional[str]]:
        """
        List all files owned by a user.
        
        Args:
            user_id: Owner identifier
            
        Returns:
            Tuple of (success, files_list, error_message)
        """
        try:
            files = await self.repo.list_by_owner(user_id)
            files_list = [
                {
                    "file_id": f.id,
                    "filename": f.filename,
                    "size": f.size,
                    "content_type": f.content_type,
                    "upload_date": f.upload_date,
                    "encrypted": f.encrypted,
                }
                for f in files
            ]
            return True, files_list, None

        except Exception as e:
            logger.error(f"List files failed: {e}")
            return False, None, str(e)
