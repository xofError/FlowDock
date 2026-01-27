"""
Virus scanning service for stream-based malware detection.
Uses ClamAV engine for real-time scanning during file upload.
"""

import logging
import hashlib
import io
import clamd
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
                logger.info(f"✓ ClamAV connected at {self.clamav_host}:{self.clamav_port}")
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
        
        This is a stream-based pipeline that processes chunks in real-time:
        1. Read chunk from upload stream
        2. Update SHA-256 hash
        3. Send chunk to ClamAV scanner
        
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

        try:
            # Ensure ClamAV connection is available
            if not self.clamd_connection:
                self._initialize_connection()

            if not self.clamd_connection:
                logger.warning("ClamAV unavailable, allowing upload without scan")
                # Process stream without scanning, just hash it
                async for chunk in file_stream:
                    sha256_hash.update(chunk)
                file_hash = sha256_hash.hexdigest()
                return file_hash, "skipped", False, None

            # Collect chunks for scanning
            chunks = []
            total_bytes = 0
            
            async for chunk in file_stream:
                if not chunk:
                    break
                
                # Update hash immediately
                sha256_hash.update(chunk)
                chunks.append(chunk)
                total_bytes += len(chunk)

            # Now scan the collected data using instream()
            # instream() takes a file-like object with chunks
            try:
                # Create a BytesIO-like object from chunks for scanning
                file_buffer = io.BytesIO(b''.join(chunks))
                
                # Call instream with the buffer
                scan_result = self.clamd_connection.instream(file_buffer)
                
            except Exception as scan_error:
                logger.error(f"ClamAV instream error for {filename}: {scan_error}")
                file_hash = sha256_hash.hexdigest()
                return file_hash, "error", False, str(scan_error)

            # Process ClamAV response
            # Expected format: {'stream': ('OK', None)} or {'stream': ('FOUND', 'Trojan.Generic')}
            if scan_result and 'stream' in scan_result:
                status, threat = scan_result['stream']

                if status == 'OK':
                    scan_status = 'clean'
                    logger.info(f"✓ File {filename} scanned clean ({total_bytes / 1024 / 1024:.2f}MB)")

                elif status == 'FOUND':
                    is_infected = True
                    threat_name = threat
                    scan_status = 'infected'
                    logger.warning(f"⚠ Virus detected in {filename}: {threat}")

                else:
                    logger.warning(f"Unexpected ClamAV status: {status}")
                    scan_status = 'error'

            else:
                logger.warning("No scan result received from ClamAV")
                scan_status = 'error'

            file_hash = sha256_hash.hexdigest()
            return file_hash, scan_status, is_infected, threat_name

        except Exception as e:
            logger.error(f"Virus scan error for {filename}: {e}")
            # Still calculate hash even if scan fails
            file_hash = sha256_hash.hexdigest()
            return file_hash, "error", False, str(e)

    async def scan_and_hash_with_stream_passthrough(
        self,
        file_stream: AsyncGenerator,
        filename: str,
        chunk_size: int = 1024 * 1024
    ) -> Tuple[AsyncGenerator, str, str, bool, Optional[str]]:
        """
        Scan stream AND pass through chunks simultaneously.
        
        This allows you to scan while still processing (e.g., encrypting) the data.
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

        # Consume entire stream first to scan
        try:
            if not self.clamd_connection:
                self._initialize_connection()

            if self.clamd_connection:
                # Accumulate all chunks first
                async for chunk in file_stream:
                    if not chunk:
                        break
                    sha256_hash.update(chunk)
                    accumulated_chunks.append(chunk)

                # Create buffer and scan
                file_buffer = io.BytesIO(b''.join(accumulated_chunks))
                scan_result = self.clamd_connection.instream(file_buffer)

                if scan_result and 'stream' in scan_result:
                    status, threat = scan_result['stream']
                    if status == 'OK':
                        scan_status = 'clean'
                    elif status == 'FOUND':
                        is_infected = True
                        threat_name = threat
                        scan_status = 'infected'
            else:
                # ClamAV unavailable, just accumulate chunks
                async for chunk in file_stream:
                    if chunk:
                        sha256_hash.update(chunk)
                        accumulated_chunks.append(chunk)

        except Exception as e:
            logger.error(f"Passthrough scan error: {e}")
            scan_status = "error"

        # Create passthrough generator from accumulated chunks
        async def passthrough_generator():
            for chunk in accumulated_chunks:
                yield chunk

        file_hash = sha256_hash.hexdigest()
        return passthrough_generator(), file_hash, scan_status, is_infected, threat_name
