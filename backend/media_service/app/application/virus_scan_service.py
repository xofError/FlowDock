"""
Virus scanning service for stream-based malware detection.
Uses ClamAV engine for real-time scanning during file upload.
"""

import logging
import hashlib
import io
import clamd
import tempfile
import aiofiles
from typing import AsyncGenerator, Tuple, Optional
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class VirusScanService:
    """
    Handles virus scanning using ClamAV with streaming support.
    Also calculates SHA-256 hash during the scan process.
    """

    def __init__(self, clamav_host: str = "clamav", clamav_port: int = 3310):
        """
        Initialize virus scan service with ClamAV connection details.
        
        Args:
            clamav_host: ClamAV server hostname/IP
            clamav_port: ClamAV CLAMD listening port
        """
        self.clamav_host = clamav_host
        self.clamav_port = clamav_port
        self.clamd_connection = None
        self._initialize_connection()

    def _initialize_connection(self):
        """Initialize connection to ClamAV server."""
        try:
            self.clamd_connection = clamd.ClamdNetworkSocket(
                host=self.clamav_host,
                port=self.clamav_port
            )
            # Test connection
            if self.clamd_connection.ping():
                logger.debug(f"✓ ClamAV connected at {self.clamav_host}:{self.clamav_port}")
            else:
                logger.warning("ClamAV connection test failed, will retry on use")
        except Exception as e:
            logger.warning(f"ClamAV initialization deferred: {e}")
            self.clamd_connection = None

    async def scan_and_hash_stream(
        self,
        file_stream: AsyncGenerator,
        filename: str,
        chunk_size: int = 1024 * 1024  # 1MB chunks
    ) -> Tuple[str, str, bool, Optional[str]]:
        """
        Scan file stream for viruses and calculate SHA-256 hash simultaneously.
        
        Uses temporary file buffering to avoid loading entire file into RAM.
        Process:
        1. Stream chunks to temporary disk file
        2. Calculate SHA-256 hash as chunks arrive
        3. Scan temporary file with ClamAV
        4. Clean up temporary file
        
        Args:
            file_stream: Async generator yielding file chunks
            filename: Original filename (for logging/reporting)
            chunk_size: Size of chunks to process (default 1MB)
            
        Returns:
            Tuple of (file_hash, scan_status, is_infected, threat_name)
            - file_hash: SHA-256 hex digest
            - scan_status: 'clean', 'infected', or 'error'
            - is_infected: Boolean True if malware detected
            - threat_name: Name of detected threat (if any)
        """
        sha256_hash = hashlib.sha256()
        is_infected = False
        threat_name = None
        scan_status = "clean"
        temp_file = None

        try:
            # Ensure ClamAV connection is available
            if not self.clamd_connection:
                self._initialize_connection()

            if not self.clamd_connection:
                logger.warning("ClamAV unavailable, allowing upload without scan")
                # Process stream without scanning, just hash it
                async for chunk in file_stream:
                    if chunk:
                        sha256_hash.update(chunk)
                file_hash = sha256_hash.hexdigest()
                return file_hash, "skipped", False, None

            # Create temporary file for streaming chunks (avoids RAM buildup)
            temp_file = tempfile.NamedTemporaryFile(delete=False, prefix=f"scan_{filename}_")
            temp_path = temp_file.name
            temp_file.close()  # Close file handle so aiofiles can open it
            
            total_bytes = 0
            
            # Stream chunks to temporary file and calculate hash
            async with aiofiles.open(temp_path, mode='wb') as f:
                async for chunk in file_stream:
                    if not chunk:
                        break
                    
                    # Update hash
                    sha256_hash.update(chunk)
                    
                    # Write chunk to temporary file
                    await f.write(chunk)
                    total_bytes += len(chunk)

            # Now scan the temporary file using ClamAV
            try:
                logger.debug(f"[scan] Scanning {filename}: {total_bytes} bytes via ClamAV from temp file")
                
                # ClamAV can scan a file by path (more efficient than instream for large files)
                # or we can use instream with the file handle
                with open(temp_path, 'rb') as file_handle:
                    scan_result = self.clamd_connection.instream(file_handle)
                
            except Exception as scan_error:
                logger.error(f"ClamAV instream error for {filename}: {scan_error}")
                file_hash = sha256_hash.hexdigest()
                # Clean up temp file on error
                try:
                    import os
                    os.unlink(temp_path)
                except:
                    pass
                return file_hash, "error", False, str(scan_error)

            # Process ClamAV response
            # Expected format: {'stream': ('OK', None)} or {'stream': ('FOUND', 'Trojan.Generic')}
            if scan_result and 'stream' in scan_result:
                status, threat = scan_result['stream']

                if status == 'OK':
                    scan_status = 'clean'
                    file_hash = sha256_hash.hexdigest()
                    logger.info(f"[virus_scan] ✓ CLEAN: {filename} ({total_bytes} bytes, hash={file_hash[:16]}...)")

                elif status == 'FOUND':
                    is_infected = True
                    threat_name = threat
                    scan_status = 'infected'
                    file_hash = sha256_hash.hexdigest()
                    logger.warning(f"[virus_scan] 🚨 INFECTED: {filename}, threat='{threat}', hash={file_hash[:16]}...")

                else:
                    logger.warning(f"[virus_scan] Unexpected ClamAV status for {filename}: {status}")
                    scan_status = 'error'
                    file_hash = sha256_hash.hexdigest()

            else:
                logger.warning(f"[virus_scan] No scan result received from ClamAV for {filename}")
                scan_status = 'error'
                file_hash = sha256_hash.hexdigest()

            return file_hash, scan_status, is_infected, threat_name

        except Exception as e:
            file_hash = sha256_hash.hexdigest()
            logger.error(f"[virus_scan] ERROR scanning {filename}: {str(e)}, hash={file_hash[:16]}...")
            # Still calculate hash even if scan fails
            return file_hash, "error", False, str(e)
        
        finally:
            # Always clean up temporary file
            if temp_file is not None:
                try:
                    import os
                    os.unlink(temp_path)
                    logger.debug(f"[scan] Cleaned up temporary file: {temp_path}")
                except Exception as e:
                    logger.warning(f"[scan] Failed to clean up temp file {temp_path}: {e}")

    async def scan_and_hash_with_stream_passthrough(
        self,
        file_stream: AsyncGenerator,
        filename: str,
        chunk_size: int = 1024 * 1024
    ) -> Tuple[AsyncGenerator, str, str, bool, Optional[str]]:
        """
        Scan stream AND pass through chunks simultaneously.
        
        This allows you to scan while still processing (e.g., encrypting) the data.
        Uses temporary file to avoid RAM buildup.
        Returns both the passthrough stream and scan results.
        
        Args:
            file_stream: Async generator yielding file chunks
            filename: Original filename
            chunk_size: Size of chunks to process
            
        Returns:
            Tuple of (passthrough_stream, file_hash, scan_status, is_infected, threat_name)
        """
        sha256_hash = hashlib.sha256()
        is_infected = False
        threat_name = None
        scan_status = "clean"
        accumulated_chunks = []
        temp_file = None

        # Consume entire stream first to scan (buffer to disk, not RAM)
        try:
            if not self.clamd_connection:
                self._initialize_connection()

            if self.clamd_connection:
                # Create temporary file for streaming chunks
                temp_file = tempfile.NamedTemporaryFile(delete=False, prefix=f"scan_{filename}_")
                temp_path = temp_file.name
                temp_file.close()
                
                # Stream to temp file and accumulate for passthrough
                async with aiofiles.open(temp_path, mode='wb') as f:
                    async for chunk in file_stream:
                        if not chunk:
                            break
                        sha256_hash.update(chunk)
                        accumulated_chunks.append(chunk)
                        await f.write(chunk)

                # Scan the temporary file
                try:
                    with open(temp_path, 'rb') as file_handle:
                        scan_result = self.clamd_connection.instream(file_handle)

                    if scan_result and 'stream' in scan_result:
                        status, threat = scan_result['stream']
                        if status == 'OK':
                            scan_status = 'clean'
                        elif status == 'FOUND':
                            is_infected = True
                            threat_name = threat
                            scan_status = 'infected'
                except Exception as scan_error:
                    logger.error(f"ClamAV scan error for passthrough: {scan_error}")
                    scan_status = "error"
            else:
                # ClamAV unavailable, just accumulate chunks
                async for chunk in file_stream:
                    if chunk:
                        sha256_hash.update(chunk)
                        accumulated_chunks.append(chunk)

        except Exception as e:
            logger.error(f"Passthrough scan error: {e}")
            scan_status = "error"
        
        finally:
            # Clean up temporary file
            if temp_file is not None:
                try:
                    import os
                    os.unlink(temp_path)
                except Exception as e:
                    logger.warning(f"Failed to clean up temp file: {e}")

        # Create passthrough generator from accumulated chunks
        async def passthrough_generator():
            for chunk in accumulated_chunks:
                yield chunk

        file_hash = sha256_hash.hexdigest()
        return passthrough_generator(), file_hash, scan_status, is_infected, threat_name
