import logging
from typing import Optional, Tuple
from bson import ObjectId
from app.database import get_fs
from app.utils.validators import validate_file_type, validate_file_size
from app.core.config import settings

logger = logging.getLogger(__name__)

class FileService:
    
    @staticmethod
    async def upload_file(
        filename: str,
        file_content: bytes,
        content_type: str,
        user_id: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        
        # 1. Validation (Sync)
        if not validate_file_type(content_type):
            error = f"Invalid file type: {content_type}."
            return False, None, error
        
        file_size = len(file_content)
        # You confirmed this is Sync, so NO 'await' here
        is_valid, error_msg = validate_file_size(file_size) 
        if not is_valid:
            return False, None, error_msg
        
        try:
            fs = get_fs()
            
            # 2. Fix Motor Usage: open_upload_stream is SYNC
            # Do NOT use 'await' here.
            grid_in = fs.open_upload_stream(
                filename,
                metadata={
                    "owner": user_id,
                    "contentType": content_type,
                    "originalFilename": filename
                }
            )
            
            # 3. Write IS Async
            await grid_in.write(file_content)
            # close() is synchronous
            grid_in.close()
            
            file_id = str(grid_in._id)
            return True, file_id, None
        
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return False, None, str(e)

    @staticmethod
    async def download_file(file_id: str, requester_user_id: str) -> Tuple[bool, Optional[bytes], Optional[dict], Optional[str]]:
        try:
            oid = ObjectId(file_id)
            fs = get_fs()
            
            # 4. open_download_stream IS Async (fetches file doc)
            grid_out = await fs.open_download_stream(oid)
            # enforce ownership if present in metadata
            file_meta = grid_out.metadata or {}
            owner = file_meta.get("owner")
            if owner and owner != requester_user_id:
                grid_out.close()
                return False, None, None, "Access denied"

            metadata = {
                "filename": grid_out.filename,
                "content_type": grid_out.content_type,
            }

            file_content = await grid_out.read()
            # close stream
            grid_out.close()
            return True, file_content, metadata, None
        except Exception as e:
            return False, None, None, "File not found"

    @staticmethod
    async def delete_file(file_id: str, requester_user_id: str) -> Tuple[bool, Optional[int], Optional[str]]:
        try:
            oid = ObjectId(file_id)
            fs = get_fs()
            
            # Helper to get size before delete
            try:
                grid_out = await fs.open_download_stream(oid)
                file_meta = grid_out.metadata or {}
                owner = file_meta.get("owner")
                if owner and owner != requester_user_id:
                    grid_out.close()
                    return False, None, "Access denied"

                file_size = grid_out.length
            except Exception:
                return False, None, "File not found"
            await fs.delete(oid)
            return True, file_size, None
        except Exception as e:
            return False, None, str(e)

    @staticmethod
    async def get_file_metadata(file_id: str, requester_user_id: str) -> Tuple[bool, Optional[dict], Optional[str]]:
        try:
            try:
                oid = ObjectId(file_id)
            except Exception:
                return False, None, "Invalid file ID format"

            fs = get_fs()
            
            # Open the stream to fetch file details
            grid_out = await fs.open_download_stream(oid)
            
            # SAFEGUARD: metadata might be None if the file has no metadata
            file_metadata = grid_out.metadata or {}
            owner = file_metadata.get("owner")
            if owner and owner != requester_user_id:
                grid_out.close()
                return False, None, "Access denied"
            
            # RETRIEVE CONTENT_TYPE CORRECTLY:
            # You stored it in 'metadata.contentType', so we look there first.
            # Fallback to grid_out.content_type (root level) if not found.
            content_type = file_metadata.get("contentType") or grid_out.content_type

            metadata = {
                "file_id": file_id,
                "filename": grid_out.filename,
                "size": grid_out.length,
                "content_type": content_type, 
                "upload_date": grid_out.upload_date,
                "metadata": file_metadata
            }
            
            grid_out.close()
            return True, metadata, None
        
        except Exception as e:
            # LOG THE REAL ERROR so you can see it in your terminal
            logger.error(f"Metadata error for {file_id}: {e}")
            return False, None, "File not found"