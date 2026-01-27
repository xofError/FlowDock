"""
Application service orchestrating file operations.
Pure business logic - depends on interfaces, not implementations.
"""

import logging
import zipfile
import os
import tempfile
import aiofiles
from typing import AsyncGenerator, Optional, Tuple, List
from fastapi import UploadFile
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.domain.entities import File
from app.domain.interfaces import (
    IFileRepository,
    ICryptoService,
    IEventPublisher,
    IQuotaRepository,
    IActivityLogger,
    IFolderRepository,
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
        folder_repo: IFolderRepository = None,
        activity_logger: IActivityLogger = None,
    ):
        """
        Initialize service with dependencies (Dependency Injection).
        
        Args:
            repo: File repository implementation
            crypto: Crypto service implementation
            event_publisher: Event publisher implementation
            quota_repo: Quota repository for updating storage usage
            folder_repo: Optional folder repository for folder-related file operations
            activity_logger: Optional activity logger for audit trails
        """
        self.repo = repo
        self.crypto = crypto
        self.publisher = event_publisher
        self.quota_repo = quota_repo
        self.folder_repo = folder_repo
        self.activity_logger = activity_logger

    # ========================================================================
    # Helper Methods
    # ========================================================================

    async def _get_unique_filename(self, folder_id: str, filename: str) -> str:
        """
        Check for duplicate filenames in a folder and append counter if needed.
        
        If folder contains "report.pdf", returns "report (1).pdf"
        If folder contains both, returns "report (2).pdf", etc.
        
        Args:
            folder_id: ID of the folder to check
            filename: Original filename to check
            
        Returns:
            Unique filename (original or with counter appended)
        """
        try:
            # Get all files in the folder
            existing_files = await self.folder_repo.get_folder_contents(folder_id)
            existing_filenames = {f.filename for f in existing_files}
            
            # If filename doesn't exist, return as-is
            if filename not in existing_filenames:
                return filename
            
            # Extract base name and extension
            base_name, ext = os.path.splitext(filename)
            
            # Find next available counter
            counter = 1
            while True:
                new_filename = f"{base_name} ({counter}){ext}"
                if new_filename not in existing_filenames:
                    return new_filename
                counter += 1
                
        except Exception as e:
            logger.warning(f"Could not check for duplicate filenames: {e}. Using original: {filename}")
            return filename

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
        folder_id: Optional[str] = None,
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Upload an unencrypted file.
        
        Args:
            user_id: Owner of the file
            filename: Original filename
            file_content: File bytes
            content_type: MIME type
            ip_address: Optional client IP for logging
            folder_id: Optional folder ID for file placement
            
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
            # [FIX #3] Check for duplicate filenames in the folder and rename if needed
            if folder_id:
                filename = await self._get_unique_filename(folder_id, filename)
            
            # 2. Create domain entity
            file = File(
                filename=filename,
                content_type=content_type,
                size=len(file_content),
                owner_id=user_id,
                folder_id=folder_id,  # Include folder placement
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
        folder_id: Optional[str] = None,
    ) -> Tuple[bool, Optional[str], int, Optional[str]]:
        """
        Upload file with envelope encryption using streaming.
        
        Args:
            user_id: Owner of the file
            file: UploadFile object (streaming)
            ip_address: Optional client IP for logging
            folder_id: Optional folder ID for file placement
            
        Returns:
            Tuple of (success, file_id, original_size, error_message)
        """
        # 1. Validate
        if not validate_file_type(file.content_type):
            return False, None, 0, "Invalid file type"

        try:
            # [FIX #3] Check for duplicate filenames in the folder and rename if needed
            filename = file.filename
            if folder_id:
                filename = await self._get_unique_filename(folder_id, filename)

            # 2. Generate encryption keys
            file_key, nonce = self.crypto.generate_key_pair()
            encrypted_key = self.crypto.wrap_key(file_key)

            # 3. Create domain entity with encryption metadata
            file_entity = File(
                filename=filename,
                content_type=file.content_type,
                owner_id=user_id,
                folder_id=folder_id,  # NEW: Include folder placement
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
        folder_id: Optional[str] = None,
    ) -> Tuple[bool, Optional[List[dict]], Optional[str]]:
        """
        List all files owned by a user, optionally filtered by folder.
        When folder_id is None, returns only root-level files.
        
        [FIX FOR ISSUE 1 - Scope/Leaking Files]
        Explicitly filter by folder_id to prevent scoping leaks if repository
        returns all files when folder_id is None.
        
        Args:
            user_id: Owner identifier
            folder_id: Optional folder ID to filter by (None = root files only)
            
        Returns:
            Tuple of (success, files_list, error_message)
        """
        try:
            files = await self.repo.list_by_owner(user_id, folder_id=folder_id)
            
            logger.info(f"[list_user_files] Retrieved {len(files)} files from repo (folder_id={folder_id})")
            for f in files:
                logger.info(f"[list_user_files] File: '{f.filename}' | folder_id={repr(f.folder_id)} | type={type(f.folder_id)}")
            
            # Explicitly filter by folder_id to ensure proper scoping
            filtered_files = []
            for f in files:
                # If requesting root (None), ensure file has no folder_id
                if folder_id is None:
                    if not f.folder_id:
                        filtered_files.append(f)
                        logger.info(f"[list_user_files] Including (root): '{f.filename}'")
                    else:
                        logger.info(f"[list_user_files] Filtering out (has folder): '{f.filename}' with folder_id={f.folder_id}")
                # If requesting specific folder, ensure IDs match
                else:
                    if str(f.folder_id) == str(folder_id):
                        filtered_files.append(f)
            
            logger.info(f"[list_user_files] Filtered to {len(filtered_files)} files (folder_id={folder_id})")
            
            files_list = [
                {
                    "file_id": f.id,
                    "filename": f.filename,
                    "size": f.size,
                    "content_type": f.content_type,
                    "upload_date": f.upload_date,
                    "encrypted": f.encrypted,
                    "folder_id": f.folder_id,
                }
                for f in filtered_files
            ]
            return True, files_list, None

        except Exception as e:
            logger.error(f"List files failed: {e}")
            return False, None, str(e)

    # ========================================================================
    # Helper Methods for Folder Operations & Public Access
    # ========================================================================

    async def is_file_in_folder_tree(
        self,
        file_id: str,
        root_folder_id: str,
    ) -> bool:
        """
        Verify that a file is contained within a folder (at any depth).
        Used for security validation in public/shared access.
        
        Args:
            file_id: File to check
            root_folder_id: Root folder to check against
            
        Returns:
            True if file is inside root_folder_id tree, False otherwise
        """
        try:
            if not self.folder_repo:
                logger.warning("folder_repo not available for is_file_in_folder_tree")
                return False

            # Get file metadata
            file = await self.repo.get_file_metadata(file_id)
            if not file or not file.folder_id:
                return False

            # Traverse up from file's folder to check if we reach root
            current_folder_id = file.folder_id
            while current_folder_id:
                if current_folder_id == root_folder_id:
                    return True
                folder = await self.folder_repo.get_folder_by_id(current_folder_id)
                if not folder:
                    break
                current_folder_id = folder.parent_id
            return False
            
        except Exception as e:
            logger.error(f"Error checking file in folder tree: {e}")
            return False

    async def move_file(
        self,
        file_id: str,
        new_folder_id: str,
        user_id: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Move a file to a different folder.
        
        Args:
            file_id: The file to move
            new_folder_id: The destination folder
            user_id: The current user (for verification)
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            if not self.folder_repo:
                return False, "Folder service not available"

            # Get file metadata to verify ownership
            file = await self.repo.get_file_metadata(file_id)
            if not file or file.owner_id != user_id:
                return False, "File not found or access denied"

            # Verify new folder exists and is owned by user
            new_folder = await self.folder_repo.get_folder(new_folder_id, user_id)
            
            # [FIX #3] If not owner, check if user has EDIT permissions via sharing
            if not new_folder:
                # Check if folder exists and user has EDIT/ADMIN permissions
                new_folder = await self.folder_repo.get_folder_by_id(new_folder_id)
                if new_folder:
                    # Verify user has EDIT or ADMIN permission via folder sharing
                    # Access shares collection directly if available
                    if hasattr(self.folder_repo, 'db'):
                        share = await self.folder_repo.db["folder_shares"].find_one({
                            "folder_id": new_folder_id,
                            "target_id": user_id,
                            "permission": {"$in": ["edit", "admin"]}  # Only EDIT/ADMIN can add files
                        })
                        if not share:
                            logger.warning(f"User {user_id} lacks EDIT permission for folder {new_folder_id}")
                            return False, "Destination folder not found or access denied"
                    else:
                        logger.warning(f"Cannot check sharing permissions: folder_repo has no db attribute")
                        return False, "Destination folder not found or access denied"
                else:
                    return False, "Destination folder not found or access denied"

            # Update file's folder_id
            await self.repo.update_file_metadata(file_id, {"folder_id": new_folder_id})

            logger.info(f"✓ Moved file {file_id} to folder {new_folder_id}")
            return True, None

        except Exception as e:
            logger.error(f"Move file failed: {e}")
            return False, str(e)


class FolderService:
    """
    Application service for folder operations.
    Orchestrates folder management without knowing implementation details.
    """

    def __init__(
        self,
        folder_repo: "IFolderRepository",
        file_repo: "IGridFSRepository" = None,
        crypto: ICryptoService = None,
        quota_repo: IQuotaRepository = None,
    ):
        """
        Initialize service with folder and file repositories.
        
        Args:
            folder_repo: Folder repository implementation
            file_repo: Optional file repository for folder contents operations
            crypto: Optional crypto service for decryption during archive
            quota_repo: Optional quota repository for updating storage usage
        """
        self.folder_repo = folder_repo
        self.file_repo = file_repo
        self.crypto = crypto
        self.quota_repo = quota_repo

    # ========================================================================
    # Create Folder
    # ========================================================================
    async def create_folder(
        self,
        user_id: str,
        name: str,
        parent_id: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Create a new folder with validation.
        
        Args:
            user_id: Owner of the folder
            name: Folder name
            parent_id: Optional parent folder ID
            ip_address: Optional client IP for logging
            
        Returns:
            Tuple of (success, folder_id, error_message)
        """
        try:
            # Validate folder name
            if not name or len(name) > 255:
                return False, None, "Invalid folder name (1-255 characters)"

            # If parent_id provided, validate it exists and is owned by user
            if parent_id:
                parent = await self.folder_repo.get_folder(parent_id, user_id)
                if not parent:
                    return False, None, "Parent folder not found or not owned by user"
                # Note: No circular dependency check needed here because we're creating a new folder
                # with no existing children. Cycles only possible when moving folders.

            # Create domain entity
            from app.domain.entities import Folder
            folder = Folder(
                name=name,
                owner_id=user_id,
                parent_id=parent_id,
            )

            # Save folder
            folder_id = await self.folder_repo.create_folder(folder)
            
            logger.info(f"✓ Created folder {folder_id} for owner {user_id} (parent: {parent_id})")
            return True, folder_id, None

        except Exception as e:
            logger.error(f"Create folder failed: {e}")
            return False, None, str(e)

    # ========================================================================
    # Circular Dependency Detection
    # ========================================================================
    async def _has_circular_dependency(
        self,
        owner_id: str,
        current_folder_id: str,
        target_parent_id: str,
        visited: set = None,
    ) -> bool:
        """
        Check if assigning target_parent_id would create a circular reference.
        
        Example: If Folder A has parent B, and B has parent C, we cannot
        make C have parent A (circular).
        
        Args:
            owner_id: The owner
            current_folder_id: The folder being checked
            target_parent_id: The proposed parent folder
            visited: Set of already-visited folders (prevents infinite loops)
            
        Returns:
            True if would create circular dependency, False otherwise
        """
        if visited is None:
            visited = set()

        if current_folder_id in visited:
            return True

        visited.add(current_folder_id)

        if current_folder_id == target_parent_id:
            return True

        # Get the folder's parent
        current = await self.folder_repo.get_folder(current_folder_id, owner_id)
        if not current or not current.parent_id:
            return False

        # Recursively check the parent's ancestry
        return await self._has_circular_dependency(owner_id, current.parent_id, target_parent_id, visited)

    # ========================================================================
    # Delete Folder (with recursion)
    # ========================================================================
    async def delete_folder_recursive(
        self,
        user_id: str,
        folder_id: str,
        ip_address: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Delete a folder and all its contents (files and subfolders).
        
        Args:
            user_id: The owner (for verification)
            folder_id: The folder identifier
            ip_address: Optional client IP for logging
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Verify ownership
            folder = await self.folder_repo.get_folder(folder_id, user_id)
            if not folder:
                return False, "Folder not found or not owned by user"

            # [FIX #1] Calculate TOTAL tree size (all files in folder + subfolders)
            # Use the new get_folder_tree_size method for accurate calculation
            total_tree_size = 0
            if hasattr(self.folder_repo, 'get_folder_tree_size'):
                total_tree_size = await self.folder_repo.get_folder_tree_size(folder_id)
            
            # Use repository's recursive delete
            success = await self.folder_repo.delete_folder_recursive(folder_id, user_id)
            
            if not success:
                return False, "Failed to delete folder"

            # [FIX #1 & #2] After successful deletion, clean up orphaned records
            if hasattr(self.folder_repo, 'db'):
                try:
                    # Clean up folder shares
                    shares_deleted = await self.folder_repo.db["folder_shares"].delete_many({"folder_id": folder_id})
                    if shares_deleted.deleted_count > 0:
                        logger.info(f"✓ Cleaned up {shares_deleted.deleted_count} orphaned folder shares")
                    
                    # Clean up public links
                    links_deleted = await self.folder_repo.db["public_folder_links"].delete_many({"folder_id": folder_id})
                    if links_deleted.deleted_count > 0:
                        logger.info(f"✓ Cleaned up {links_deleted.deleted_count} orphaned public links")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup orphaned records: {cleanup_error}")
                    # Don't fail the deletion - cleanup is secondary

            # [FIX #1] Update Quota to reflect freed space (use total tree size)
            if self.quota_repo and total_tree_size > 0:
                await self.quota_repo.update_usage(user_id, -total_tree_size)
                logger.info(f"✓ Updated quota: freed {total_tree_size} bytes for user {user_id}")

            logger.info(f"✓ Recursively deleted folder {folder_id} and all contents (Freed {total_tree_size} bytes)")
            return True, None

        except Exception as e:
            logger.error(f"Delete folder failed: {e}")
            return False, str(e)

    # ========================================================================
    # Get Folder
    # ========================================================================
    async def get_folder(
        self,
        folder_id: str,
        user_id: str,
    ) -> Tuple[bool, Optional[dict], Optional[str]]:
        """
        Get folder metadata.
        
        Args:
            folder_id: The folder identifier
            user_id: The requesting user (for ownership verification)
            
        Returns:
            Tuple of (success, folder_dict, error_message)
        """
        try:
            folder = await self.folder_repo.get_folder(folder_id, user_id)
            
            if not folder:
                return False, None, "Folder not found"

            folder_dict = {
                "folder_id": folder.id,
                "name": folder.name,
                "parent_id": folder.parent_id,
                "created_at": folder.created_at,
                "updated_at": folder.updated_at,
            }
            
            return True, folder_dict, None

        except Exception as e:
            logger.error(f"Get folder failed: {e}")
            return False, None, str(e)

    # ========================================================================
    # Get Folder Contents (Files + Subfolders)
    # ========================================================================
    async def get_folder_contents(
        self,
        folder_id: str,
        user_id: str,
        allow_public: bool = False,
    ) -> Tuple[bool, Optional[dict], Optional[str]]:
        """
        Get folder contents (files and subfolders).
        
        Args:
            folder_id: The folder identifier
            user_id: The requesting user (for ownership verification)
            allow_public: If True, skip ownership verification (for public links)
            
        Returns:
            Tuple of (success, contents_dict, error_message)
            Where contents_dict has:
            {
                "folder": {folder_id, name, parent_id, created_at, updated_at},
                "files": [{file_id, name, size, created_at, ...}],
                "subfolders": [{folder_id, name, created_at, ...}]
            }
        """
        try:
            # Verify folder exists and user has access
            if allow_public:
                # For public access, just verify folder exists (no ownership check)
                folder = await self.folder_repo.get_folder_by_id(folder_id)
            else:
                # Try to get folder as owner first
                folder = await self.folder_repo.get_folder(folder_id, user_id)
                
                # If not owner, check if folder is shared with user
                if not folder:
                    try:
                        db = self.folder_repo.db if hasattr(self.folder_repo, 'db') else None
                        if db:
                            shares_coll = db["folder_shares"]
                            share = await shares_coll.find_one({
                                "folder_id": folder_id,
                                "target_id": user_id,
                            })
                            if share:
                                # User has shared access, get the folder without owner check
                                folder = await self.folder_repo.get_folder_by_id(folder_id)
                            else:
                                return False, None, "Folder not found or access denied"
                        else:
                            return False, None, "Folder not found or access denied"
                    except Exception as e:
                        logger.warning(f"Failed to check shared access: {e}")
                        return False, None, "Folder not found or access denied"
            
            if not folder:
                return False, None, "Folder not found"

            # [FIX #1] Determine if we should filter by owner_id
            # Only filter by owner if the user is the OWNER of this folder
            # If user is accessing via sharing or public link, don't filter
            is_owner = folder.owner_id == user_id
            
            # Get all files in this folder
            # [FIX #1] If not owner (i.e., accessed via sharing), don't filter by owner_id
            if is_owner or allow_public:
                # Owner or public access: filter by owner (owner only for owner, none for public)
                owner_filter = user_id if is_owner else None
            else:
                # Shared access: don't filter by owner - list all files in the folder
                owner_filter = None
            
            files = await self.file_repo.list_files_in_folder(folder_id, owner_id=owner_filter)
            
            files_list = [
                {
                    "file_id": f.id,
                    "name": f.filename,
                    "size": f.size,
                    "created_at": f.upload_date,
                    "is_infected": f.is_infected,
                }
                for f in files
            ]

            # Get direct subfolders only
            # [FIX #1] If not owner (i.e., accessed via sharing), don't filter by owner_id
            if is_owner or allow_public:
                # Owner or public access: filter by owner (owner only for owner, none for public)
                owner_filter = user_id if is_owner else None
            else:
                # Shared access: don't filter by owner - list all subfolders
                owner_filter = None
            
            subfolders = await self.folder_repo.list_subfolders(folder_id, owner_id=owner_filter)
            
            subfolders_list = [
                {
                    "folder_id": sf.id,
                    "name": sf.name,
                    "created_at": sf.created_at,
                }
                for sf in subfolders
            ]

            contents_dict = {
                "folder": {
                    "folder_id": folder.id,
                    "name": folder.name,
                    "parent_id": folder.parent_id,
                    "created_at": folder.created_at,
                    "updated_at": folder.updated_at,
                },
                "files": files_list,
                "subfolders": subfolders_list,
            }
            
            # Add breadcrumbs for navigation (unless public access)
            if not allow_public:
                try:
                    breadcrumbs = await self.get_breadcrumbs(folder_id, user_id)
                    contents_dict["breadcrumbs"] = breadcrumbs
                except Exception as e:
                    logger.warning(f"Failed to generate breadcrumbs: {e}")
                    contents_dict["breadcrumbs"] = []
            
            return True, contents_dict, None

        except Exception as e:
            logger.error(f"Get folder contents failed: {e}")
            return False, None, str(e)

    # ========================================================================
    # List Folders
    # ========================================================================
    async def list_folders(
        self,
        user_id: str,
        parent_id: Optional[str] = None,
    ) -> Tuple[bool, Optional[list], Optional[str]]:
        """
        List folders for a user.
        
        Args:
            user_id: The owner's identifier
            parent_id: Optional parent folder ID (None = root folders)
            
        Returns:
            Tuple of (success, folders_list, error_message)
        """
        try:
            folders = await self.folder_repo.list_folders(user_id, parent_id)

            folders_list = [
                {
                    "folder_id": f.id,
                    "name": f.name,
                    "parent_id": f.parent_id,
                    "created_at": f.created_at,
                    "updated_at": f.updated_at,
                }
                for f in folders
            ]
            
            return True, folders_list, None

        except Exception as e:
            logger.error(f"List folders failed: {e}")
            return False, None, str(e)

    # ========================================================================
    # Update Folder
    # ========================================================================
    async def update_folder(
        self,
        folder_id: str,
        user_id: str,
        name: Optional[str] = None,
        parent_id: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Update folder metadata and/or parent.
        
        Args:
            folder_id: The folder identifier
            user_id: The owner (for verification)
            name: New folder name
            parent_id: New parent folder ID (for moving)
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Get existing folder for verification
            folder = await self.folder_repo.get_folder(folder_id, user_id)
            if not folder:
                return False, "Folder not found"

            # Update name if provided
            if name:
                if len(name) > 255:
                    return False, "Folder name too long (max 255 characters)"
                folder.name = name

            # Handle parent_id change (move folder)
            if parent_id is not None:
                # Prevent moving folder into itself
                if parent_id == folder_id:
                    return False, "Cannot move folder into itself"
                
                # Prevent moving folder into its own descendant (circular dependency)
                if parent_id:  # None is valid (root)
                    is_descendant = await self.is_folder_descendant(parent_id, folder_id)
                    if is_descendant:
                        return False, "Cannot move folder into its own subfolder (circular dependency)"
                
                folder.parent_id = parent_id

            # Save changes
            success = await self.folder_repo.update_folder(folder)
            if not success:
                return False, "Update failed"

            logger.info(f"✓ Updated folder {folder_id}")
            return True, None

        except Exception as e:
            logger.error(f"Update folder failed: {e}")
            return False, str(e)

    # ========================================================================
    # Delete Folder
    # ========================================================================
    async def delete_folder(
        self,
        folder_id: str,
        user_id: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Delete a folder (only if empty).
        
        Args:
            folder_id: The folder identifier
            user_id: The owner (for verification)
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            success = await self.folder_repo.delete_folder(folder_id, user_id)
            
            if not success:
                return False, "Cannot delete folder (not found, not owned, or not empty)"

            logger.info(f"✓ Deleted folder {folder_id}")
            return True, None

        except Exception as e:
            logger.error(f"Delete folder failed: {e}")
            return False, str(e)

    # ========================================================================
    # Helper Methods for Folder Navigation & Public Access
    # ========================================================================

    async def get_breadcrumbs(
        self,
        folder_id: Optional[str],
        owner_id: str,
    ) -> List[dict]:
        """
        Build breadcrumb path from root to current folder.
        
        Optimized: Uses MongoDB $graphLookup to fetch entire ancestry chain in single query
        instead of iterative lookups (N+1 prevention).
        
        Args:
            folder_id: Current folder ID (None = root)
            owner_id: Owner for verification
            
        Returns:
            List of {folder_id, name} dicts representing path from root to folder
            Example: [{"folder_id": None, "name": "Home"}, {"folder_id": "123", "name": "Work"}]
        """
        breadcrumbs = [{"folder_id": None, "name": "Home"}]
        
        if not folder_id:
            return breadcrumbs
        
        try:
            # Use MongoDB $graphLookup to fetch entire ancestry chain in one query
            # This is much more efficient than the old while loop that made N queries
            from bson import ObjectId
            
            folder_oid = self.folder_repo._to_object_id(folder_id)
            if folder_oid is None:
                return breadcrumbs
            
            pipeline = [
                {"$match": {"_id": folder_oid, "owner_id": owner_id}},
                {
                    "$graphLookup": {
                        "from": "folders",
                        "startWith": "$parent_id",
                        "connectFromField": "parent_id",
                        "connectToField": "_id",
                        "as": "ancestors",
                        "maxDepth": 100,
                    }
                },
                {
                    "$project": {
                        "name": 1,
                        "_id": 1,
                        "ancestors": {
                            "_id": 1,
                            "name": 1,
                        }
                    }
                }
            ]
            
            result = await self.folder_repo.collection.aggregate(pipeline).to_list(1)
            
            if result:
                folder_data = result[0]
                # Add ancestors from root to parent (reverse order)
                if folder_data.get("ancestors"):
                    ancestors = folder_data["ancestors"]
                    # ancestors are already in order from immediate parent up to root
                    # reverse them to get from root down
                    for ancestor in reversed(ancestors):
                        breadcrumbs.append({
                            "folder_id": str(ancestor.get("_id", "")),
                            "name": ancestor.get("name", "")
                        })
                # Add current folder at the end
                breadcrumbs.append({
                    "folder_id": str(folder_data.get("_id", "")),
                    "name": folder_data.get("name", "")
                })
            
            return breadcrumbs
            
        except Exception as e:
            logger.error(f"Failed to get breadcrumbs for {folder_id}: {e}")
            # Fallback to simple path without parents
            try:
                folder = await self.folder_repo.get_folder(folder_id, owner_id)
                if folder:
                    breadcrumbs.append({"folder_id": folder.id, "name": folder.name})
            except:
                pass
            return breadcrumbs

    async def is_folder_descendant(
        self,
        target_folder_id: str,
        root_folder_id: str,
    ) -> bool:
        """
        Check if target_folder_id is a descendant of root_folder_id.
        Used for preventing circular dependencies and access validation.
        
        Args:
            target_folder_id: Folder to check
            root_folder_id: Parent folder to check against
            
        Returns:
            True if target is descendant of root, False otherwise
        """
        try:
            current_id = target_folder_id
            while current_id:
                if current_id == root_folder_id:
                    return True
                folder = await self.folder_repo.get_folder_by_id(current_id)
                if not folder:
                    return False
                current_id = folder.parent_id
            return False
        except Exception as e:
            logger.error(f"Error checking folder descendant: {e}")
            return False

    # ========================================================================
    # Move Operations
    # ========================================================================

    async def move_folder(
        self,
        folder_id: str,
        new_parent_id: Optional[str],
        user_id: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Move a folder to a different parent folder.
        Prevents circular dependencies (cannot move into descendant).
        
        Args:
            folder_id: The folder to move
            new_parent_id: The destination parent folder (None for root)
            user_id: The current user (for verification)
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Get folder to verify ownership
            folder = await self.folder_repo.get_folder(folder_id, user_id)
            if not folder:
                return False, "Folder not found or access denied"

            # Prevent moving into itself
            if new_parent_id == folder_id:
                return False, "Cannot move folder into itself"

            # If new_parent_id is not None, verify it exists and is owned by user
            if new_parent_id:
                parent_folder = await self.folder_repo.get_folder(new_parent_id, user_id)
                if not parent_folder:
                    return False, "Destination parent folder not found or access denied"

                # Prevent circular dependency (cannot move into descendant)
                is_descendant = await self.is_folder_descendant(new_parent_id, folder_id)
                if is_descendant:
                    return False, "Cannot move folder into its own subfolder (circular dependency)"

            # Update folder's parent_id
            folder.parent_id = new_parent_id
            success = await self.folder_repo.update_folder(folder)
            
            if not success:
                return False, "Move failed"

            logger.info(f"✓ Moved folder {folder_id} to parent {new_parent_id}")
            return True, None

        except Exception as e:
            logger.error(f"Move folder failed: {e}")
            return False, str(e)

    # ========================================================================
    # Zip Archive Operations
    # ========================================================================

    async def archive_folder(
        self,
        folder_id: str,
        user_id: str,
    ) -> Tuple[bool, Optional[AsyncGenerator], Optional[str], Optional[str]]:
        """
        Create a ZIP archive of the folder and its contents.
        Works for both owned and shared folders.
        
        Args:
            folder_id: The folder to archive
            user_id: The current user (for verification)
            
        Returns:
            Tuple of (success, file_stream, filename, error_message)
        """
        try:
            # 1. Verify access - try owned first, then check shared
            folder = await self.folder_repo.get_folder(folder_id, user_id)
            if not folder:
                # If not owned, try to get as shared folder
                folder = await self.folder_repo.get_folder_by_id(folder_id)
                if not folder:
                    return False, None, None, "Folder not found or access denied"
                # Note: Actual sharing permission was already checked at endpoint level

            # 2. Collect all files to zip
            # Format: [(file_entity, "path/inside/zip")]
            files_to_zip = []
            
            async def recurse_folder(current_fid, current_path):
                """Recursively collect files and folders for archiving."""
                # Get files in this folder (no owner filter for internal traversal)
                files = await self.file_repo.list_files_in_folder(current_fid, owner_id=None)
                for f in files:
                    # Only zip non-infected files
                    if not f.is_infected:
                        files_to_zip.append((f, f"{current_path}/{f.filename}"))
                
                # Get subfolders
                subs = await self.folder_repo.list_subfolders(current_fid, owner_id=None)
                for sub in subs:
                    await recurse_folder(sub.id, f"{current_path}/{sub.name}")

            # Start recursion from the root folder
            folder_name = folder.get('name', 'archive') if isinstance(folder, dict) else folder.name
            await recurse_folder(folder_id, folder_name)

            if not files_to_zip:
                return False, None, None, "Folder is empty"

            # 3. Create Zip (using temp file for memory safety)
            # [FIX: Async Blocking Issue] Move blocking zip operations to thread pool to avoid freezing event loop
            temp_dir = tempfile.mkdtemp()
            zip_filename = f"{folder_name}.zip"
            zip_path = os.path.join(temp_dir, zip_filename)

            try:
                # First collect all file streams asynchronously
                files_with_streams = []
                for file_entity, zip_entry_path in files_to_zip:
                    try:
                        _, stream = await self.file_repo.get_file_stream(file_entity.id)
                        if stream:
                            # Handle Decryption for encrypted files
                            if file_entity.encrypted and self.crypto:
                                try:
                                    file_key = self.crypto.unwrap_key(bytes.fromhex(file_entity.encrypted_key))
                                    nonce = bytes.fromhex(file_entity.nonce)
                                    stream = self.crypto.decrypt_stream(stream, file_key, nonce)
                                    logger.info(f"Decrypting file {file_entity.filename} for archive")
                                except Exception as decrypt_error:
                                    logger.error(f"Failed to decrypt {file_entity.filename} for zip: {decrypt_error}")
                                    logger.warning(f"Skipping encrypted file {file_entity.filename} - decryption failed")
                                    continue
                            
                            # Collect chunks from stream into memory (buffered)
                            chunks = []
                            async for chunk in stream:
                                chunks.append(chunk)
                            files_with_streams.append((file_entity, zip_entry_path, chunks))
                    except Exception as e:
                        logger.warning(f"Failed to prepare file {file_entity.filename} for zip: {e}")
                        continue
                
                # Now run the blocking zip operation in a thread pool
                # This prevents the entire event loop from freezing during zip creation
                loop = asyncio.get_event_loop()
                executor = ThreadPoolExecutor(max_workers=1)
                
                def create_zip_in_thread():
                    """Blocking operation - run in thread to avoid freezing event loop"""
                    try:
                        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                            for file_entity, zip_entry_path, chunks in files_with_streams:
                                try:
                                    with zipf.open(zip_entry_path, 'w') as zf_entry:
                                        for chunk in chunks:
                                            zf_entry.write(chunk)
                                except Exception as chunk_error:
                                    logger.warning(f"Failed to write {file_entity.filename} to zip: {chunk_error}")
                                    continue
                        return True
                    except Exception as e:
                        logger.error(f"Failed to create zip file in thread: {e}")
                        return False
                
                # Execute blocking operation in thread pool
                zip_success = await loop.run_in_executor(executor, create_zip_in_thread)
                executor.shutdown(wait=False)
                
                if not zip_success:
                    if os.path.exists(zip_path):
                        os.remove(zip_path)
                    if os.path.exists(temp_dir):
                        os.rmdir(temp_dir)
                    return False, None, None, "Failed to create zip file"
                    
            except Exception as e:
                logger.error(f"Failed to prepare zip creation: {e}")
                if os.path.exists(zip_path):
                    os.remove(zip_path)
                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
                return False, None, None, f"Failed to create zip: {str(e)}"

            # 4. Create async generator to stream the zip file back
            async def file_sender():
                """Stream zip file to client in chunks."""
                try:
                    async with aiofiles.open(zip_path, 'rb') as f:
                        while True:
                            chunk = await f.read(64 * 1024)  # 64KB chunks
                            if not chunk:
                                break
                            yield chunk
                finally:
                    # Cleanup temp files
                    try:
                        if os.path.exists(zip_path):
                            os.remove(zip_path)
                        if os.path.exists(temp_dir):
                            os.rmdir(temp_dir)
                    except Exception as cleanup_error:
                        logger.warning(f"Failed to cleanup temp files: {cleanup_error}")

            logger.info(f"✓ Created zip archive for folder {folder_id}")
            return True, file_sender(), zip_filename, None

        except Exception as e:
            logger.error(f"Archive folder failed: {e}")
            return False, None, None, str(e)

    async def archive_folder_public(
        self,
        folder_id: str,
    ) -> Tuple[bool, Optional[AsyncGenerator], Optional[str], Optional[str]]:
        """
        Create a ZIP archive of a public folder (no user ownership required).
        Used for public share links.
        
        Args:
            folder_id: The folder to archive
            
        Returns:
            Tuple of (success, file_stream, filename, error_message)
        """
        try:
            # 1. Verify folder exists (no ownership check for public)
            folder = await self.folder_repo.get_folder_by_id(folder_id)
            if not folder:
                return False, None, None, "Folder not found"

            # 2. Collect all files to zip
            files_to_zip = []
            
            async def recurse_folder(current_fid, current_path):
                """Recursively collect files and folders for archiving."""
                files = await self.file_repo.list_files_in_folder(current_fid, owner_id=None)
                for f in files:
                    if not f.is_infected:
                        files_to_zip.append((f, f"{current_path}/{f.filename}"))
                
                subs = await self.folder_repo.list_subfolders(current_fid, owner_id=None)
                for sub in subs:
                    await recurse_folder(sub.id, f"{current_path}/{sub.name}")

            folder_name = folder.get('name', 'archive') if isinstance(folder, dict) else folder.name
            await recurse_folder(folder_id, folder_name)

            if not files_to_zip:
                return False, None, None, "Folder is empty"

            # 3. Create Zip using temp file
            # [FIX: Async Blocking Issue] Move blocking zip operations to thread pool to avoid freezing event loop
            temp_dir = tempfile.mkdtemp()
            zip_filename = f"{folder_name}.zip"
            zip_path = os.path.join(temp_dir, zip_filename)

            try:
                # First collect all file streams asynchronously
                files_with_streams = []
                for file_entity, zip_entry_path in files_to_zip:
                    try:
                        _, stream = await self.file_repo.get_file_stream(file_entity.id)
                        if stream:
                            # Handle Decryption for encrypted files
                            if file_entity.encrypted and self.crypto:
                                try:
                                    file_key = self.crypto.unwrap_key(bytes.fromhex(file_entity.encrypted_key))
                                    nonce = bytes.fromhex(file_entity.nonce)
                                    stream = self.crypto.decrypt_stream(stream, file_key, nonce)
                                    logger.info(f"Decrypting file {file_entity.filename} for public archive")
                                except Exception as decrypt_error:
                                    logger.error(f"Failed to decrypt {file_entity.filename} for zip: {decrypt_error}")
                                    logger.warning(f"Skipping encrypted file {file_entity.filename} - decryption failed")
                                    continue
                            
                            # Collect chunks from stream into memory (buffered)
                            chunks = []
                            async for chunk in stream:
                                chunks.append(chunk)
                            files_with_streams.append((file_entity, zip_entry_path, chunks))
                    except Exception as e:
                        logger.warning(f"Failed to prepare file {file_entity.filename} for zip: {e}")
                        continue
                
                # Now run the blocking zip operation in a thread pool
                # This prevents the entire event loop from freezing during zip creation
                loop = asyncio.get_event_loop()
                executor = ThreadPoolExecutor(max_workers=1)
                
                def create_zip_in_thread():
                    """Blocking operation - run in thread to avoid freezing event loop"""
                    try:
                        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                            for file_entity, zip_entry_path, chunks in files_with_streams:
                                try:
                                    with zipf.open(zip_entry_path, 'w') as zf_entry:
                                        for chunk in chunks:
                                            zf_entry.write(chunk)
                                except Exception as chunk_error:
                                    logger.warning(f"Failed to write {file_entity.filename} to zip: {chunk_error}")
                                    continue
                        return True
                    except Exception as e:
                        logger.error(f"Failed to create zip file in thread: {e}")
                        return False
                
                # Execute blocking operation in thread pool
                zip_success = await loop.run_in_executor(executor, create_zip_in_thread)
                executor.shutdown(wait=False)
                
                if not zip_success:
                    if os.path.exists(zip_path):
                        os.remove(zip_path)
                    if os.path.exists(temp_dir):
                        os.rmdir(temp_dir)
                    return False, None, None, "Failed to create zip file"
                    
            except Exception as e:
                logger.error(f"Failed to prepare zip creation: {e}")
                if os.path.exists(zip_path):
                    os.remove(zip_path)
                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
                return False, None, None, f"Failed to create zip: {str(e)}"

            # 4. Create async generator to stream
            async def file_sender():
                try:
                    async with aiofiles.open(zip_path, 'rb') as f:
                        while True:
                            chunk = await f.read(64 * 1024)
                            if not chunk:
                                break
                            yield chunk
                finally:
                    try:
                        if os.path.exists(zip_path):
                            os.remove(zip_path)
                        if os.path.exists(temp_dir):
                            os.rmdir(temp_dir)
                    except Exception as cleanup_error:
                        logger.warning(f"Failed to cleanup temp files: {cleanup_error}")

            logger.info(f"✓ Created public zip archive for folder {folder_id}")
            return True, file_sender(), zip_filename, None

        except Exception as e:
            logger.error(f"Archive public folder failed: {e}")
            return False, None, None, str(e)


