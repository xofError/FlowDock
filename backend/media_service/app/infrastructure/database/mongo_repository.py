"""
MongoDB GridFS implementation of IFileRepository.
Handles all MongoDB/GridFS-specific logic.
"""

import logging
from typing import AsyncGenerator, Optional, Tuple, List
from bson import ObjectId
from bson.errors import InvalidId
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

    def __init__(self, fs: AsyncIOMotorGridFSBucket, db: AsyncIOMotorDatabase = None):
        """
        Initialize repository with GridFS bucket and optional database.
        
        Args:
            fs: AsyncIOMotorGridFSBucket instance
            db: Optional AsyncIOMotorDatabase for querying fs.files collection
        """
        self.fs = fs
        self.db = db

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
                "folder_id": file.folder_id,  # Added folder support - snake_case to match queries
                "encrypted": file.encrypted,
                "nonce": file.nonce,
                "encryptedKey": file.encrypted_key,
                "isInfected": file.is_infected,  # Added virus scan status
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
            logger.info(f"✓ Saved file {file_id} for owner {file.owner_id} (folder: {file.folder_id})")
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
                folder_id=meta.get("folder_id"),  # Added folder support - snake_case to match queries
                upload_date=grid_out.upload_date,
                encrypted=meta.get("encrypted", False),
                nonce=meta.get("nonce", ""),
                encrypted_key=meta.get("encryptedKey", ""),
                is_infected=meta.get("isInfected", False),  # Added virus scan status
                is_deleted=meta.get("is_deleted", False),  # Soft delete status
                deleted_at=meta.get("deleted_at"),  # Deletion timestamp
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
                is_deleted=meta.get("is_deleted", False),  # Soft delete status
                deleted_at=meta.get("deleted_at"),  # Deletion timestamp
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

    async def delete_file_from_gridfs(self, file_id: str) -> bool:
        """
        Permanently delete file from GridFS (hard delete).
        This is used for permanent deletion from trash.
        
        Args:
            file_id: ObjectId as string
            
        Returns:
            True if deleted, False otherwise
        """
        return await self.delete(file_id)

    async def list_by_owner(self, owner_id: str, folder_id: Optional[str] = None) -> List[File]:
        """
        List all files owned by a user, optionally filtered by folder.
        Automatically excludes deleted files (soft delete).
        
        Args:
            owner_id: Owner identifier
            folder_id: Optional folder ID to filter by (None = root files only)
            
        Returns:
            List of File entities
        """
        try:
            # Build query: always filter by owner and exclude deleted files
            # CRITICAL FIX: When folder_id is None, only get root files
            # When folder_id is provided, get files in that folder
            if folder_id is None:
                # Root files: folder_id must not be set OR be None/empty, AND not deleted
                # Use $and to ensure both owner and root-level conditions are met
                query = {
                    "$and": [
                        {"metadata.owner": owner_id},
                        {"$or": [
                            {"metadata.folder_id": {"$exists": False}},
                            {"metadata.folder_id": None},
                            {"metadata.folder_id": ""}
                        ]},
                        {"$or": [
                            {"metadata.is_deleted": {"$exists": False}},
                            {"metadata.is_deleted": False}
                        ]}
                    ]
                }
            else:
                # Files in specific folder (not deleted)
                query = {
                    "$and": [
                        {"metadata.owner": owner_id},
                        {"metadata.folder_id": folder_id},
                        {"$or": [
                            {"metadata.is_deleted": {"$exists": False}},
                            {"metadata.is_deleted": False}
                        ]}
                    ]
                }
            
            cursor = self.fs.find(query)
            files = []

            async for grid_out in cursor:
                meta = grid_out.metadata or {}
                file = File(
                    id=str(grid_out._id),
                    filename=grid_out.filename,
                    content_type=meta.get("contentType", grid_out.content_type),
                    size=grid_out.length,
                    owner_id=meta.get("owner", ""),
                    folder_id=meta.get("folder_id"),
                    upload_date=grid_out.upload_date,
                    encrypted=meta.get("encrypted", False),
                    nonce=meta.get("nonce", ""),
                    encrypted_key=meta.get("encryptedKey", ""),
                    is_deleted=meta.get("is_deleted", False),  # Soft delete status
                    deleted_at=meta.get("deleted_at"),  # Deletion timestamp
                    metadata=meta,
                )
                files.append(file)

            return files

        except Exception as e:
            logger.error(f"Failed to list files for {owner_id}: {e}")
            return []

    async def list_files_in_folder(
        self,
        folder_id: Optional[str],
        owner_id: Optional[str] = None,
    ) -> List[File]:
        """
        List all files in a specific folder (root if folder_id is None).
        Automatically excludes deleted files (soft delete).
        
        Args:
            folder_id: The folder identifier (None = root)
            owner_id: Optional owner identifier (None for public/shared lists)
            
        Returns:
            List of File entities
        """
        try:
            if self.db is None:
                logger.error("Database not initialized for file queries")
                return []

            fs = self.db.get_collection("fs.files")
            query = {}
            
            # Only filter by owner if owner_id is provided
            if owner_id:
                query["metadata.owner"] = owner_id
            
            # Always exclude deleted files
            query["$or"] = [
                {"metadata.is_deleted": {"$exists": False}},
                {"metadata.is_deleted": False}
            ]
            
            if folder_id is None:
                # Root files have no folder_id
                query["metadata.folder_id"] = {"$in": [None, ""]}
            else:
                # Files in specific folder
                query["metadata.folder_id"] = folder_id

            cursor = fs.find(query).sort("uploadDate", -1)
            files = []

            async for doc in cursor:
                meta = doc.get("metadata", {})
                file = File(
                    id=str(doc["_id"]),
                    filename=doc.get("filename", ""),
                    content_type=meta.get("contentType", ""),
                    size=doc.get("length", 0),
                    owner_id=meta.get("owner", ""),
                    folder_id=meta.get("folderId"),
                    upload_date=doc.get("uploadDate"),
                    encrypted=meta.get("encrypted", False),
                    nonce=meta.get("nonce", ""),
                    encrypted_key=meta.get("encryptedKey", ""),
                    is_infected=meta.get("isInfected", False),
                    is_deleted=meta.get("is_deleted", False),
                    deleted_at=meta.get("deleted_at"),
                    metadata=meta,
                )
                files.append(file)

            return files

        except Exception as e:
            logger.error(f"Failed to list files in folder {folder_id}: {e}")
            return []

    async def update_file_metadata(self, file_id: str, updates: dict) -> bool:
        """
        Update file metadata (e.g., moving to a new folder, soft delete).
        
        Args:
            file_id: ObjectId as string
            updates: Dict of fields to update (e.g., {"folder_id": "new_folder_id", "is_deleted": True})
            
        Returns:
            True if updated, False otherwise
        """
        try:
            if self.db is None:
                logger.error("Database not initialized for updates")
                return False

            oid = ObjectId(file_id)
            mongo_updates = {}
            
            # Map domain fields to MongoDB metadata fields
            if "folder_id" in updates:
                mongo_updates["metadata.folderId"] = updates["folder_id"]
            
            # Soft delete fields
            if "is_deleted" in updates:
                mongo_updates["metadata.is_deleted"] = updates["is_deleted"]
            if "deleted_at" in updates:
                mongo_updates["metadata.deleted_at"] = updates["deleted_at"]
            
            # Add other fields as needed
            if not mongo_updates:
                return False

            result = await self.db["fs.files"].update_one(
                {"_id": oid},
                {"$set": mongo_updates}
            )
            
            logger.info(f"✓ Updated metadata for file {file_id}: {mongo_updates}")
            return True  # Return True even if modified_count is 0 (idempotent)
            
        except Exception as e:
            logger.error(f"Failed to update metadata for {file_id}: {e}")
            return False


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

    @staticmethod
    def _to_object_id(id_str: Optional[str]) -> Optional[ObjectId]:
        """
        Safely convert a string to ObjectId.
        
        Args:
            id_str: String to convert
            
        Returns:
            ObjectId or None if invalid format
        """
        if not id_str:
            return None
        try:
            return ObjectId(id_str)
        except InvalidId:
            return None

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
            # Validate folder_id is a valid ObjectId
            oid = self._to_object_id(folder_id)
            if oid is None:
                logger.error(f"Invalid folder ID format: {folder_id}")
                return None

            doc = await self.collection.find_one({
                "_id": oid,
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

    async def get_folder_by_id(self, folder_id: str) -> Optional[Folder]:
        """
        Get a folder by ID without ownership verification (for public access).
        
        Args:
            folder_id: The folder identifier
            
        Returns:
            Folder entity or None
        """
        try:
            # Validate folder_id is a valid ObjectId
            oid = self._to_object_id(folder_id)
            if oid is None:
                logger.error(f"Invalid folder ID format: {folder_id}")
                return None

            doc = await self.collection.find_one({"_id": oid})

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
            oid = self._to_object_id(folder.id)
            if oid is None:
                logger.error(f"Invalid folder ID format: {folder.id}")
                return False

            folder.updated_at = datetime.utcnow()
            result = await self.collection.update_one(
                {"_id": oid},
                {
                    "$set": {
                        "name": folder.name,
                        "parent_id": folder.parent_id,
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
            oid = self._to_object_id(folder_id)
            if oid is None:
                logger.error(f"Invalid folder ID format: {folder_id}")
                return False

            # Check if folder is empty
            # Need to check both files collection and subfolders
            file_count = await self.db["files"].count_documents({
                "folder_id": oid
            })
            
            subfolder_count = await self.collection.count_documents({
                "parent_id": folder_id,
                "owner_id": owner_id,
            })

            if file_count > 0 or subfolder_count > 0:
                logger.warning(f"Cannot delete folder {folder_id}: not empty")
                return False

            result = await self.collection.delete_one({
                "_id": oid,
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
            oid = self._to_object_id(folder_id)
            if oid is None:
                logger.error(f"Invalid folder ID format: {folder_id}")
                return 0

            pipeline = [
                {"$match": {"folder_id": oid}},
                {"$group": {"_id": None, "total": {"$sum": "$size"}}},
            ]

            result = await self.db["files"].aggregate(pipeline).to_list(1)
            if result:
                return int(result[0]["total"])
            return 0

        except Exception as e:
            logger.error(f"Failed to get folder size {folder_id}: {e}")
            return 0

    # ========================================================================
    # RECURSIVE DELETE HELPERS
    # ========================================================================

    async def get_all_children_folders(self, folder_id: str) -> List[str]:
        """
        Recursively get all descendant folder IDs.
        
        Args:
            folder_id: The parent folder identifier
            
        Returns:
            List of all descendant folder IDs
        """
        children = []
        try:
            # Get direct children
            cursor = self.collection.find({"parent_id": folder_id})
            async for doc in cursor:
                child_id = str(doc["_id"])
                children.append(child_id)
                # Recursively get descendants
                descendants = await self.get_all_children_folders(child_id)
                children.extend(descendants)
            return children
        except Exception as e:
            logger.error(f"Failed to get children for {folder_id}: {e}")
            return []

    async def get_folder_tree_size(self, folder_id: str) -> int:
        """
        Calculate the total size of all files in the folder AND its subfolders.
        Uses MongoDB aggregation pipeline with $graphLookup for efficiency.
        
        Args:
            folder_id: The folder identifier
            
        Returns:
            Total size in bytes of all files in the folder tree
        """
        try:
            # Convert to ObjectId for matching
            oid = self._to_object_id(folder_id)
            if not oid:
                return 0

            # 1. Use $graphLookup to find all descendant folders efficiently
            pipeline = [
                {"$match": {"_id": oid}},
                {
                    "$graphLookup": {
                        "from": "folders",
                        "startWith": "$_id",
                        "connectFromField": "_id",
                        "connectToField": "parent_id",
                        "as": "descendants"
                    }
                },
                {
                    "$project": {
                        "all_ids": {
                            "$map": {
                                "input": {"$concatArrays": [["$$ROOT"], "$descendants"]},
                                "as": "item",
                                "in": {"$toString": "$$item._id"}  # Convert to string to match metadata.folderId
                            }
                        }
                    }
                }
            ]
            
            cursor = self.collection.aggregate(pipeline)
            result = await cursor.to_list(1)
            if not result:
                return 0
                
            all_folder_ids = result[0]['all_ids']

            # 2. Sum file sizes in all these folders
            fs_files = self.db["fs.files"]
            size_cursor = fs_files.aggregate([
                {"$match": {"metadata.folderId": {"$in": all_folder_ids}}},
                {"$group": {"_id": None, "total": {"$sum": "$length"}}}
            ])
            
            size_result = await size_cursor.to_list(1)
            total_size = size_result[0]['total'] if size_result else 0
            
            logger.info(f"✓ Calculated folder tree size: {folder_id} = {total_size} bytes")
            return total_size
            
        except Exception as e:
            logger.error(f"Failed to calculate tree size for {folder_id}: {e}")
            return 0

    async def delete_folder_recursive(self, folder_id: str, owner_id: str) -> bool:
        """
        Delete folder and all its contents (files and subfolders).
        Optimized with batch operations to avoid N+1 database calls.
        
        Args:
            folder_id: The folder identifier
            owner_id: The owner (for verification)
            
        Returns:
            True if deleted, False if not found/not owned
        """
        try:
            # Verify ownership
            folder = await self.get_folder(folder_id, owner_id)
            if not folder:
                return False

            # 1. Get all descendant folders
            all_folders_to_delete = [folder_id]
            descendants = await self.get_all_children_folders(folder_id)
            all_folders_to_delete.extend(descendants)

            # 2. Delete all files in these folders (BATCH operation with $in)
            # Instead of deleting files one by one, delete all matching in single query
            fs = self.db.get_collection("fs.files")
            if all_folders_to_delete:
                result = await fs.delete_many({"metadata.folderId": {"$in": all_folders_to_delete}})
                logger.info(f"✓ Deleted {result.deleted_count} files from {len(all_folders_to_delete)} folders")

            # 3. Delete all folders (BATCH operation with $in)
            # Convert to ObjectIds once
            folder_oids = [self._to_object_id(fid) for fid in all_folders_to_delete if self._to_object_id(fid)]
            if folder_oids:
                result = await self.collection.delete_many({"_id": {"$in": folder_oids}})
                logger.info(f"✓ Deleted {result.deleted_count} folders")

            logger.info(f"✓ Recursively deleted folder {folder_id} and all contents")
            return True

        except Exception as e:
            logger.error(f"Recursive delete failed for {folder_id}: {e}")
            return False

    # ========================================================================
    # FILE QUERIES BY FOLDER
    # ========================================================================

    async def list_files_in_folder(
        self,
        folder_id: Optional[str],
        owner_id: Optional[str] = None,
    ) -> List[File]:
        """
        List all files in a specific folder (root if folder_id is None).
        
        Args:
            folder_id: The folder identifier (None = root)
            owner_id: The owner identifier (None = no owner restriction)
            
        Returns:
            List of File entities
        """
        try:
            fs = self.db.get_collection("fs.files")
            query = {}
            
            if owner_id:
                query["metadata.owner"] = owner_id
            
            if folder_id is None:
                # Root files have no folder_id
                query["metadata.folder_id"] = {"$in": [None, ""]}
            else:
                # Files in specific folder
                query["metadata.folder_id"] = folder_id

            cursor = fs.find(query).sort("uploadDate", -1)
            files = []

            async for doc in cursor:
                meta = doc.get("metadata", {})
                file = File(
                    id=str(doc["_id"]),
                    filename=doc.get("filename", ""),
                    content_type=meta.get("contentType", "application/octet-stream"),
                    size=doc.get("length", 0),
                    owner_id=meta.get("owner", ""),
                    folder_id=meta.get("folderId"),
                    upload_date=doc.get("uploadDate"),
                    encrypted=meta.get("encrypted", False),
                    nonce=meta.get("nonce", ""),
                    encrypted_key=meta.get("encryptedKey", ""),
                    is_infected=meta.get("isInfected", False),
                    is_deleted=meta.get("is_deleted", False),  # Soft delete status
                    deleted_at=meta.get("deleted_at"),  # Deletion timestamp
                    metadata=meta,
                )
                files.append(file)

            return files

        except Exception as e:
            logger.error(f"Failed to list files in folder {folder_id}: {e}")
            return []

    async def list_subfolders(
        self,
        parent_id: Optional[str],
        owner_id: Optional[str] = None,
    ) -> List[Folder]:
        """
        List direct subfolders (not recursive).
        
        Args:
            parent_id: The parent folder ID (None = root)
            owner_id: The owner identifier (None = no owner restriction)
            
        Returns:
            List of Folder entities
        """
        try:
            query = {}
            if owner_id:
                query["owner_id"] = owner_id
                
            if parent_id is None:
                query["parent_id"] = {"$in": [None]}
            else:
                query["parent_id"] = parent_id

            cursor = self.collection.find(query).sort("created_at", -1)
            folders = []

            async for doc in cursor:
                folder = Folder(
                    id=str(doc["_id"]),
                    name=doc.get("name", ""),
                    owner_id=doc.get("owner_id", ""),
                    parent_id=doc.get("parent_id"),
                    created_at=doc.get("created_at"),
                    updated_at=doc.get("updated_at"),
                    metadata=doc.get("metadata", {}),
                )
                folders.append(folder)

            return folders

        except Exception as e:
            logger.error(f"Failed to list subfolders for {parent_id}: {e}")
            return []

