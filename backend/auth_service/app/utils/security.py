import os
import hmac
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict, Any
from uuid import UUID
from jose import jwt, JWTError
from passlib.context import CryptContext

JWT_SECRET = "secret"
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))

# Use Argon2 for password hashing: memory-hard, resistant to GPU attacks,
# and handles long passwords gracefully. Widely recommended for production.
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def _ensure_jwt_secret() -> None:
    if not JWT_SECRET:
        raise RuntimeError("JWT_SECRET environment variable is not set")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

def create_access_token(user_id: UUID, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token for a user.

    Returns a compact JWT string. The token contains `sub` (subject), `iat`
    and `exp` as unix timestamps (UTC).
    """
    _ensure_jwt_secret()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "access",
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(40)   # secure random string

def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_refresh_token(token: str, stored_hash: str) -> bool:
    # use compare_digest to avoid timing attacks
    candidate = hash_refresh_token(token)
    return hmac.compare_digest(candidate, stored_hash)



def decode_token(token: str) -> Optional[Dict[str, Any]]:
    _ensure_jwt_secret()
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def create_refresh_token(user_id: UUID) -> Tuple[str, str, datetime]:
    """Create a refresh token, return (plain_token, hashed_token, expiry).

    Caller should store the hashed token and expiry in a persistent store.
    """
    token = secrets.token_urlsafe(40)
    hashed = hash_refresh_token(token)
    expiry = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return token, hashed, expiry
