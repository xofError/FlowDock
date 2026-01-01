"""
MongoDB GridFS implementation of IFileRepository.
Handles all MongoDB/GridFS-specific logic.
"""

import logging
from typing import AsyncGenerator, Optional, Tuple, List
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorGridFSBucket, AsyncIOMotorDatabase
from datetime import datetime

from app.domain.entities import File, Folder
from app.domain.interfaces import IFileRepository, IFolderRepository

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


class MongoFolderRepository(IFolderRepository):
    """
    MongoDB implementation of folder storage.
    Uses a dedicated 'folders' collection for hierarchical folder structure.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize repository with MongoDB database.
        
        Args:
            db: AsyncIOMotorDatabase instance
        """
        self.db = db
        self.collection = db["folders"]

    async def create_folder(self, folder: Folder) -> str:
        """
        Create a new folder in MongoDB.
        
        Args:
            folder: Folder entity
            
        Returns:
            folder_id as string
        """
        try:
            doc = {
                "name": folder.name,
                "owner_id": folder.owner_id,
                "parent_id": folder.parent_id,
                "created_at": folder.created_at or datetime.utcnow(),
                "updated_at": folder.updated_at or datetime.utcnow(),
                "metadata": folder.metadata,
            }

            result = await self.collection.insert_one(doc)
            folder_id = str(result.inserted_id)
            logger.info(f"✓ Created folder {folder_id} for owner {folder.owner_id}")
            return folder_id

        except Exception as e:
            logger.error(f"Failed to create folder: {e}")
            raise

    async def get_folder(self, folder_id: str, owner_id: str) -> Optional[Folder]:
        """
        Get a folder by ID with ownership verification.
        
        Args:
            folder_id: The folder identifier
            owner_id: The owner (for verification)
            
        Returns:
            Folder entity or None
        """
        try:
            doc = await self.collection.find_one({
                "_id": ObjectId(folder_id),
                "owner_id": owner_id,
            })

            if not doc:
                return None

            return Folder(
                id=str(doc["_id"]),
                name=doc["name"],
                owner_id=doc["owner_id"],
                parent_id=doc.get("parent_id"),
                created_at=doc.get("created_at"),
                updated_at=doc.get("updated_at"),
                metadata=doc.get("metadata", {}),
            )

        except Exception as e:
            logger.error(f"Failed to get folder {folder_id}: {e}")
            return None

    async def list_folders(
        self,
        owner_id: str,
        parent_id: Optional[str] = None,
    ) -> List[Folder]:
        """
        List folders for a user.
        
        Args:
            owner_id: The owner's identifier
            parent_id: Optional parent folder ID (None = root folders)
            
        Returns:
            List of Folder entities
        """
        try:
            query = {"owner_id": owner_id}
            if parent_id is None:
                query["parent_id"] = None
            else:
                query["parent_id"] = parent_id

            cursor = self.collection.find(query)
            folders = []

            async for doc in cursor:
                folder = Folder(
                    id=str(doc["_id"]),
                    name=doc["name"],
                    owner_id=doc["owner_id"],
                    parent_id=doc.get("parent_id"),
                    created_at=doc.get("created_at"),
                    updated_at=doc.get("updated_at"),
                    metadata=doc.get("metadata", {}),
                )
                folders.append(folder)

            return folders

        except Exception as e:
            logger.error(f"Failed to list folders for {owner_id}: {e}")
            return []

    async def update_folder(self, folder: Folder) -> bool:
        """
        Update folder metadata.
        
        Args:
            folder: Folder entity with updated fields
            
        Returns:
            True if updated, False if not found
        """
        try:
            folder.updated_at = datetime.utcnow()
            result = await self.collection.update_one(
                {"_id": ObjectId(folder.id)},
                {
                    "$set": {
                        "name": folder.name,
                        "metadata": folder.metadata,
                        "updated_at": folder.updated_at,
                    }
                },
            )

            if result.matched_count == 0:
                return False

            logger.info(f"✓ Updated folder {folder.id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update folder {folder.id}: {e}")
            return False

    async def delete_folder(self, folder_id: str, owner_id: str) -> bool:
        """
        Delete a folder (only if empty).
        
        Args:
            folder_id: The folder identifier
            owner_id: The owner (for verification)
            
        Returns:
            True if deleted, False if not found/not owned/not empty
        """
        try:
            # Check if folder is empty
            # Need to check both files collection and subfolders
            file_count = await self.db["files"].count_documents({
                "folder_id": ObjectId(folder_id)
            })
            
            subfolder_count = await self.collection.count_documents({
                "parent_id": folder_id,
                "owner_id": owner_id,
            })

            if file_count > 0 or subfolder_count > 0:
                logger.warning(f"Cannot delete folder {folder_id}: not empty")
                return False

            result = await self.collection.delete_one({
                "_id": ObjectId(folder_id),
                "owner_id": owner_id,
            })

            if result.deleted_count == 0:
                return False

            logger.info(f"✓ Deleted folder {folder_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete folder {folder_id}: {e}")
            return False

    async def get_folder_contents_size(self, folder_id: str) -> int:
        """
        Get total size of all files in a folder.
        
        Args:
            folder_id: The folder identifier
            
        Returns:
            Total size in bytes
        """
        try:
            pipeline = [
                {"$match": {"folder_id": ObjectId(folder_id)}},
                {"$group": {"_id": None, "total": {"$sum": "$size"}}},
            ]

            result = await self.db["files"].aggregate(pipeline).to_list(1)
            if result:
                return int(result[0]["total"])
            return 0

        except Exception as e:
            logger.error(f"Failed to get folder size {folder_id}: {e}")
            return 0

