"""
GridFS file operations service
"""

import logging
from typing import Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
from app.database import get_fs
from app.utils.validators import validate_file_type, validate_file_size
from app.core.config import settings

logger = logging.getLogger(__name__)


class FileService:
    """Service for file operations using GridFS"""
    
    @staticmethod
    async def upload_file(
        filename: str,
        file_content: bytes,
        content_type: str,
        user_id: str
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Upload file to GridFS
        
        Args:
            filename: Original filename
            file_content: Binary file content
            content_type: MIME type
            user_id: User ID
        
        Returns:
            Tuple of (success, file_id_or_error, error_message)
        """
        # Validate MIME type
        if not validate_file_type(content_type):
            error = f"Invalid file type: {content_type}. Allowed: {', '.join(settings.ALLOWED_MIMES)}"
            return False, None, error
        
        # Validate file size
        file_size = len(file_content)
        is_valid, error_msg = validate_file_size(file_size)
        if not is_valid:
            return False, None, error_msg
        
        try:
            fs = get_fs()
            
            logger.info(f"Uploading {filename} ({file_size} bytes) for user {user_id}")
            
            # Open upload stream
            grid_in = await fs.open_upload_stream(
                filename,
                metadata={
                    "owner": user_id,
                    "contentType": content_type,
                    "originalFilename": filename
                }
            )
            
            # Write file content
            await grid_in.write(file_content)
            await grid_in.close()
            
            file_id = str(grid_in._id)
            logger.info(f"✓ File uploaded: {file_id}")
            
            return True, file_id, None
        
        except Exception as e:
            logger.error(f"✗ Upload failed: {e}")
            return False, None, str(e)
    
    @staticmethod
    async def download_file(file_id: str) -> tuple[bool, Optional[bytes], Optional[dict], Optional[str]]:
        """
        Download file from GridFS
        
        Args:
            file_id: MongoDB ObjectId
        
        Returns:
            Tuple of (success, file_content, metadata, error_message)
        """
        try:
            # Validate ObjectId
            try:
                oid = ObjectId(file_id)
            except Exception:
                return False, None, None, "Invalid file ID format"
            
            fs = get_fs()
            
            # Open download stream
            grid_out = await fs.open_download_stream(oid)
            
            # Get metadata
            metadata = {
                "filename": grid_out.filename,
                "size": grid_out.length,
                "content_type": grid_out.content_type,
                "upload_date": grid_out.upload_date
            }
            
            # Read file content
            file_content = await grid_out.read()
            await grid_out.close()
            
            logger.info(f"✓ Downloaded file: {file_id}")
            
            return True, file_content, metadata, None
        
        except Exception as e:
            logger.error(f"✗ Download failed: {e}")
            return False, None, None, "File not found"
    
    @staticmethod
    async def delete_file(file_id: str) -> tuple[bool, Optional[int], Optional[str]]:
        """
        Delete file from GridFS
        
        Args:
            file_id: MongoDB ObjectId
        
        Returns:
            Tuple of (success, file_size_or_none, error_message)
        """
        try:
            # Validate ObjectId
            try:
                oid = ObjectId(file_id)
            except Exception:
                return False, None, "Invalid file ID format"
            
            fs = get_fs()
            
            # Get file size before deletion
            try:
                grid_out = await fs.open_download_stream(oid)
                file_size = grid_out.length
                await grid_out.close()
            except Exception:
                return False, None, "File not found"
            
            # Delete file
            await fs.delete(oid)
            logger.info(f"✓ Deleted file: {file_id}")
            
            return True, file_size, None
        
        except Exception as e:
            logger.error(f"✗ Deletion failed: {e}")
            return False, None, str(e)
    
    @staticmethod
    async def get_file_metadata(file_id: str) -> tuple[bool, Optional[dict], Optional[str]]:
        """
        Get file metadata without downloading
        
        Args:
            file_id: MongoDB ObjectId
        
        Returns:
            Tuple of (success, metadata, error_message)
        """
        try:
            # Validate ObjectId
            try:
                oid = ObjectId(file_id)
            except Exception:
                return False, None, "Invalid file ID format"
            
            fs = get_fs()
            
            # Open stream to get metadata
            grid_out = await fs.open_download_stream(oid)
            
            metadata = {
                "file_id": file_id,
                "filename": grid_out.filename,
                "size": grid_out.length,
                "content_type": grid_out.content_type,
                "upload_date": grid_out.upload_date,
                "metadata": await grid_out.metadata
            }
            
            await grid_out.close()
            
            return True, metadata, None
        
        except Exception as e:
            logger.error(f"✗ Metadata retrieval failed: {e}")
            return False, None, "File not found"
