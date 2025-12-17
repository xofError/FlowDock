"""
AES encryption service implementing ICryptoService.
Handles envelope encryption with AES-CTR mode.
"""

import os
import logging
from typing import AsyncGenerator, Tuple
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

from app.domain.interfaces import ICryptoService
from app.core.config import settings

logger = logging.getLogger(__name__)
CHUNK_SIZE = 64 * 1024  # 64KB chunks


class AESCryptoService(ICryptoService):
    """
    AES encryption implementation with envelope encryption pattern.
    Each file gets a unique key, which is encrypted with a master key.
    """

    def __init__(self):
        """Initialize with master key from config"""
        self.master_key = self._get_master_key()

    def _get_master_key(self) -> bytes:
        """
        Retrieve master key from environment.
        
        Returns:
            32-byte key for AES-256
        """
        key_hex = settings.ENCRYPTION_MASTER_KEY
        if not key_hex:
            raise ValueError("ENCRYPTION_MASTER_KEY is missing in .env")
        return bytes.fromhex(key_hex)

    def generate_key_pair(self) -> Tuple[bytes, bytes]:
        """
        Generate a unique file key and nonce for CTR mode.
        
        Returns:
            Tuple of (32-byte file_key, 16-byte nonce)
        """
        file_key = os.urandom(32)  # AES-256 key
        nonce = os.urandom(16)  # CTR mode IV
        return file_key, nonce

    def encrypt_stream(
        self,
        stream: AsyncGenerator,
        file_key: bytes,
        nonce: bytes,
    ) -> AsyncGenerator:
        """
        Create async generator that encrypts chunks with AES-CTR.
        
        Args:
            stream: Input async generator yielding plaintext chunks
            file_key: File-specific encryption key
            nonce: Nonce for CTR mode
            
        Yields:
            Encrypted chunks
        """
        cipher = Cipher(
            algorithms.AES(file_key),
            modes.CTR(nonce),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()

        async def _encrypt_gen():
            try:
                async for chunk in stream:
                    yield encryptor.update(chunk)
                # Finalize
                final = encryptor.finalize()
                if final:
                    yield final
            except Exception as e:
                logger.error(f"Encryption error: {e}")
                raise

        return _encrypt_gen()

    def decrypt_stream(
        self,
        stream: AsyncGenerator,
        file_key: bytes,
        nonce: bytes,
    ) -> AsyncGenerator:
        """
        Create async generator that decrypts chunks with AES-CTR.
        
        Args:
            stream: Input async generator yielding ciphertext chunks
            file_key: File-specific decryption key
            nonce: Nonce for CTR mode
            
        Yields:
            Decrypted chunks
        """
        cipher = Cipher(
            algorithms.AES(file_key),
            modes.CTR(nonce),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()

        async def _decrypt_gen():
            try:
                async for chunk in stream:
                    yield decryptor.update(chunk)
                # Finalize
                final = decryptor.finalize()
                if final:
                    yield final
            except Exception as e:
                logger.error(f"Decryption error: {e}")
                raise

        return _decrypt_gen()

    def wrap_key(self, file_key: bytes) -> bytes:
        """
        Encrypt file key with master key using AES-ECB (key wrapping).
        
        Args:
            file_key: File-specific key to wrap
            
        Returns:
            Encrypted key
        """
        cipher = Cipher(
            algorithms.AES(self.master_key),
            modes.ECB(),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        return encryptor.update(file_key) + encryptor.finalize()

    def unwrap_key(self, encrypted_key: bytes) -> bytes:
        """
        Decrypt wrapped file key using master key.
        
        Args:
            encrypted_key: Encrypted file key
            
        Returns:
            Decrypted file key
        """
        cipher = Cipher(
            algorithms.AES(self.master_key),
            modes.ECB(),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        return decryptor.update(encrypted_key) + decryptor.finalize()
