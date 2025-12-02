from typing import Optional, Dict
from datetime import timezone
import redis
import os
import json

from app.database import SessionLocal
from app.models.session import Session as DBSession
from app.models.user import User as DBUser


# Initialize Redis client
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)


def store_refresh_token(hashed: str, user_email: str, expiry) -> None:
    """Persist a refresh token into Redis with automatic expiry.
    
    Redis stores the token with the format:
    Key: refresh_token:{hashed}
    Value: JSON with user_email and expiry timestamp
    TTL: Set to token expiry time
    """
    # normalize expiry to UTC timestamp
    if hasattr(expiry, "timestamp"):
        expiry_timestamp = int(expiry.timestamp())
    else:
        expiry_timestamp = int(expiry.timestamp())
    
    # Calculate TTL (time to live) in seconds
    now_timestamp = int(timezone.utc.now().timestamp()) if not hasattr(timezone, "utc_now") else int(timezone.utc.now().timestamp())
    ttl = max(1, expiry_timestamp - now_timestamp)
    
    # Store token data in Redis with automatic expiry
    key = f"refresh_token:{hashed}"
    token_data = {
        "user_email": user_email,
        "expiry": expiry_timestamp
    }
    redis_client.setex(key, ttl, json.dumps(token_data))


def get_refresh_token(hashed: str) -> Optional[Dict]:
    """Retrieve a refresh token from Redis if it exists and is not revoked."""
    key = f"refresh_token:{hashed}"
    token_data = redis_client.get(key)
    
    if not token_data:
        return None
    
    try:
        data = json.loads(token_data)
        # Convert expiry timestamp back to timezone-aware UTC
        expiry = timezone.utc.localize(__import__("datetime").datetime.utcfromtimestamp(data["expiry"]))
        return {
            "user_email": data["user_email"],
            "expiry": expiry
        }
    except (json.JSONDecodeError, KeyError, ValueError):
        return None


def revoke_refresh_token(hashed: str) -> None:
    """Immediately revoke a refresh token by adding it to a blacklist."""
    key = f"refresh_token:{hashed}"
    blacklist_key = f"refresh_token_blacklist:{hashed}"
    
    # Get the token to find its expiry
    token_data = redis_client.get(key)
    
    # Delete from active tokens
    redis_client.delete(key)
    
    # Add to blacklist with same TTL as original token would have had
    if token_data:
        try:
            data = json.loads(token_data)
            now_timestamp = int(__import__("datetime").datetime.now(timezone.utc).timestamp())
            expiry_timestamp = data.get("expiry", now_timestamp + 86400)  # Default 1 day
            ttl = max(1, expiry_timestamp - now_timestamp)
            redis_client.setex(blacklist_key, ttl, "revoked")
        except (json.JSONDecodeError, KeyError):
            pass


def revoke_all_refresh_tokens_for_user(user_email: str) -> None:
    """Revoke all active refresh tokens for a user by adding to blacklist.
    
    This enforces single-session behavior by invalidating previous tokens
    when a user logs in.
    """
    # Scan all refresh tokens to find those belonging to this user
    pattern = "refresh_token:*"
    cursor = 0
    
    while True:
        cursor, keys = redis_client.scan(cursor, match=pattern, count=100)
        
        for key in keys:
            token_data = redis_client.get(key)
            if token_data:
                try:
                    data = json.loads(token_data)
                    if data.get("user_email") == user_email:
                        # Extract the hashed token from the key
                        hashed = key.replace("refresh_token:", "")
                        revoke_refresh_token(hashed)
                except (json.JSONDecodeError, KeyError):
                    pass
        
        if cursor == 0:
            break
