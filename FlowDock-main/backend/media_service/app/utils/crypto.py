# app/utils/crypto.py
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from app.core.config import settings

# Helper to verify key length
def get_master_key() -> bytes:
    key_hex = settings.ENCRYPTION_MASTER_KEY
    if not key_hex:
        raise ValueError("ENCRYPTION_MASTER_KEY is missing in .env")
    return bytes.fromhex(key_hex)

def generate_file_key() -> bytes:
    """Generates a random 32-byte key for a specific file."""
    return os.urandom(32)

def generate_nonce() -> bytes:
    """Generates a random 16-byte nonce (IV) for AES-CTR."""
    return os.urandom(16)

def encrypt_file_key(file_key: bytes) -> bytes:
    """Encrypts the file's specific key using the Master Key (AES-ECB for simplicity of key wrapping)."""
    # Note: For production key-wrapping, AES-KW is preferred, but ECB is acceptable for 
    # random keys effectively acting as a Key-Encryption-Key scenario here.
    cipher = Cipher(algorithms.AES(get_master_key()), modes.ECB(), backend=default_backend())
    encryptor = cipher.encryptor()
    return encryptor.update(file_key) + encryptor.finalize()

def decrypt_file_key(encrypted_file_key: bytes) -> bytes:
    """Decrypts the file's specific key."""
    cipher = Cipher(algorithms.AES(get_master_key()), modes.ECB(), backend=default_backend())
    decryptor = cipher.decryptor()
    return decryptor.update(encrypted_file_key) + decryptor.finalize()

def create_stream_cipher(key: bytes, nonce: bytes):
    """Creates an AES-CTR cipher for streaming file data."""
    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
    return cipher