"""
MongoDB GridFS implementation of IFileRepository.
Handles all MongoDB/GridFS-specific logic.
"""

import logging
from typing import AsyncGenerator, Optional, Tuple, List
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorGridFSBucket

from app.domain.entities import File
from app.domain.interfaces import IFileRepository

logger = logging.getLogger(__name__)
CHUNK_SIZE = 64 * 1024  # 64KB chunks


class MongoGridFSRepository(IFileRepository):
    """
    MongoDB GridFS implementation of file storage.
    Handles ObjectId conversions and GridFS-specific operations.
    """

    def __init__(self, fs: AsyncIOMotorGridFSBucket):
        """
        Initialize repository with GridFS bucket.
        
        Args:
            fs: AsyncIOMotorGridFSBucket instance
        """
        self.fs = fs

    async def save_file_stream(
        self,
        file: File,
        stream: AsyncGenerator,
    ) -> str:
        """
        Save encrypted file to GridFS.
        
        Args:
            file: Domain File entity
            stream: Async generator yielding encrypted chunks
            
        Returns:
            ObjectId as string
        """
        try:
            # Prepare GridFS metadata
            metadata = {
                "owner": file.owner_id,
                "contentType": file.content_type,
                "originalFilename": file.filename,
                "encrypted": file.encrypted,
                "nonce": file.nonce,
                "encryptedKey": file.encrypted_key,
            }
            metadata.update(file.metadata)

            # Open GridFS upload stream
            grid_in = self.fs.open_upload_stream(
                file.filename,
                metadata=metadata,
            )

            # Stream encrypted chunks to GridFS
            async for chunk in stream:
                await grid_in.write(chunk)

            grid_in.close()

            file_id = str(grid_in._id)
            logger.info(f"✓ Saved file {file_id} for owner {file.owner_id}")
            return file_id

        except Exception as e:
            logger.error(f"GridFS save failed: {e}")
            raise

    async def get_file_metadata(self, file_id: str) -> Optional[File]:
        """
        Retrieve file metadata from GridFS.
        
        Args:
            file_id: ObjectId as string
            
        Returns:
            File entity or None if not found
        """
        try:
            oid = ObjectId(file_id)
            grid_out = await self.fs.open_download_stream(oid)
            meta = grid_out.metadata or {}

            file = File(
                id=str(grid_out._id),
                filename=grid_out.filename,
                content_type=meta.get("contentType", grid_out.content_type),
                size=grid_out.length,
                owner_id=meta.get("owner", ""),
                upload_date=grid_out.upload_date,
                encrypted=meta.get("encrypted", False),
                nonce=meta.get("nonce", ""),
                encrypted_key=meta.get("encryptedKey", ""),
                metadata=meta,
            )

            grid_out.close()
            return file

        except Exception as e:
            logger.error(f"Failed to get metadata for {file_id}: {e}")
            return None

    async def get_file_stream(
        self,
        file_id: str,
    ) -> Tuple[Optional[File], Optional[AsyncGenerator]]:
        """
        Retrieve file metadata and content stream from GridFS.
        
        Args:
            file_id: ObjectId as string
            
        Returns:
            Tuple of (File entity, async generator of chunks)
        """
        try:
            oid = ObjectId(file_id)
            grid_out = await self.fs.open_download_stream(oid)
            meta = grid_out.metadata or {}

            file = File(
                id=str(grid_out._id),
                filename=grid_out.filename,
                content_type=meta.get("contentType", grid_out.content_type),
                size=grid_out.length,
                owner_id=meta.get("owner", ""),
                upload_date=grid_out.upload_date,
                encrypted=meta.get("encrypted", False),
                nonce=meta.get("nonce", ""),
                encrypted_key=meta.get("encryptedKey", ""),
                metadata=meta,
            )

            async def stream_generator():
                try:
                    while True:
                        chunk = await grid_out.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        yield chunk
                finally:
                    grid_out.close()

            return file, stream_generator()

        except Exception as e:
            logger.error(f"Failed to get stream for {file_id}: {e}")
            return None, None

    async def delete(self, file_id: str) -> bool:
        """
        Delete file from GridFS.
        
        Args:
            file_id: ObjectId as string
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            oid = ObjectId(file_id)
            await self.fs.delete(oid)
            logger.info(f"✓ Deleted file {file_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete {file_id}: {e}")
            return False

    async def list_by_owner(self, owner_id: str) -> List[File]:
        """
        List all files owned by a user.
        
        Args:
            owner_id: Owner identifier
            
        Returns:
            List of File entities
        """
        try:
            cursor = self.fs.find({"metadata.owner": owner_id})
            files = []

            async for grid_out in cursor:
                meta = grid_out.metadata or {}
                file = File(
                    id=str(grid_out._id),
                    filename=grid_out.filename,
                    content_type=meta.get("contentType", grid_out.content_type),
                    size=grid_out.length,
                    owner_id=meta.get("owner", ""),
                    upload_date=grid_out.upload_date,
                    encrypted=meta.get("encrypted", False),
                    nonce=meta.get("nonce", ""),
                    encrypted_key=meta.get("encryptedKey", ""),
                    metadata=meta,
                )
                files.append(file)

            return files

        except Exception as e:
            logger.error(f"Failed to list files for {owner_id}: {e}")
            return []
