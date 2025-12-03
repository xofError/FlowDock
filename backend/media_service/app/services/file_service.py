import logging
from typing import AsyncGenerator, Optional, Tuple
from bson import ObjectId
from app.database import get_fs
from app.utils.validators import validate_file_type, validate_file_size
from app.core.config import settings
from app.utils.crypto import (
    generate_file_key, 
    generate_nonce, 
    encrypt_file_key, 
    decrypt_file_key, 
    create_stream_cipher
)
from fastapi import UploadFile

logger = logging.getLogger(__name__)
CHUNK_SIZE = 64 * 1024  # 64KB chunks

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
        


    @staticmethod
    async def upload_encrypted_file(
        user_id: str,
        file: UploadFile
    ) -> Tuple[bool, Optional[str], int, Optional[str]]:
        """
        Upload file with envelope encryption using streaming (does not load full file into RAM).
        
        Args:
            user_id: Owner of the file
            file: UploadFile object (streaming upload)
        
        Returns:
            Tuple[success, file_id, original_size, error_message]
        """
        
        # 1. Validation
        if not validate_file_type(file.content_type):
            return False, None, 0, "Invalid file type"
        
        try:
            fs = get_fs()
            
            # 2. Prepare Encryption
            file_key = generate_file_key()     # Unique key for this file
            nonce = generate_nonce()           # Random IV for CTR mode
            encrypted_key = encrypt_file_key(file_key) # Wrap with Master Key
            
            # Setup Cipher for streaming
            cipher = create_stream_cipher(file_key, nonce)
            encryptor = cipher.encryptor()

            # 3. Open GridFS Upload Stream
            grid_in = fs.open_upload_stream(
                file.filename,
                metadata={
                    "owner": user_id,
                    "contentType": file.content_type,
                    "originalFilename": file.filename,
                    "encryptedKey": encrypted_key.hex(),  # Encrypted file key
                    "nonce": nonce.hex(),                  # IV for decryption
                    "encrypted": True                      # Flag that file is encrypted
                }
            )

            # 4. Stream: Read -> Encrypt -> Write (processes chunks, no full file in RAM)
            original_size = 0
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                original_size += len(chunk)
                encrypted_chunk = encryptor.update(chunk)
                await grid_in.write(encrypted_chunk)
            
            # Finalize encryption
            final_chunk = encryptor.finalize()
            if final_chunk:
                await grid_in.write(final_chunk)
            
            # Close and finalize upload
            grid_in.close()
            
            logger.info(f"✓ Uploaded encrypted file {grid_in._id} (original size: {original_size} bytes)")
            return True, str(grid_in._id), original_size, None

        except Exception as e:
            logger.error(f"Encryption upload failed: {e}")
            return False, None, 0, str(e)

    @staticmethod
    async def download_encrypted_file(
        file_id: str,
        requester_user_id: str
    ) -> Tuple[bool, Optional[AsyncGenerator], Optional[dict], Optional[str]]:
        """
        Download and decrypt a file in a streaming fashion.
        
        Args:
            file_id: ObjectId of the file
            requester_user_id: User requesting the download (for ownership check)
        
        Returns:
            Tuple[success, file_stream_generator, file_info, error_message]
        """
        try:
            oid = ObjectId(file_id)
            fs = get_fs()
            
            # 1. Open Download Stream (fetches metadata)
            grid_out = await fs.open_download_stream(oid)
            
            meta = grid_out.metadata or {}
            
            # 2. Enforce ownership
            owner = meta.get("owner")
            if owner and owner != requester_user_id:
                grid_out.close()
                return False, None, None, "Access denied"
            
            stored_key_hex = meta.get("encryptedKey")
            nonce_hex = meta.get("nonce")

            if not stored_key_hex or not nonce_hex:
                grid_out.close()
                return False, None, None, "File is not encrypted or metadata corrupt"

            # 3. Prepare Decryption
            encrypted_key = bytes.fromhex(stored_key_hex)
            nonce = bytes.fromhex(nonce_hex)
            
            file_key = decrypt_file_key(encrypted_key)  # Unwrap with Master Key
            cipher = create_stream_cipher(file_key, nonce)
            decryptor = cipher.decryptor()

            # 4. Generator Function (streams decrypted chunks without loading full file into RAM)
            async def file_iterator():
                try:
                    while True:
                        chunk = await grid_out.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        yield decryptor.update(chunk)
                    # Finalize decryption
                    final_chunk = decryptor.finalize()
                    if final_chunk:
                        yield final_chunk
                finally:
                    grid_out.close()

            # 5. Prepare metadata
            file_info = {
                "filename": grid_out.filename,
                "content_type": meta.get("contentType", grid_out.content_type),
                "size": grid_out.length  # Encrypted size (different from original)
            }

            return True, file_iterator(), file_info, None

        except Exception as e:
            logger.error(f"Decryption download failed: {e}")
            return False, None, None, "File not found"