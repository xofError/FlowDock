"""
Infrastructure Layer: Refresh Token Store

Redis-based storage for refresh tokens with automatic expiry.
"""

from typing import Optional, Dict
from datetime import datetime, timezone
import redis
import os
import json


class RefreshTokenStore:
    """Redis-based refresh token storage."""

    def __init__(self, redis_client: redis.Redis = None):
        self.redis = redis_client or redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=0,
            decode_responses=True,
        )

    def store(self, hashed_token: str, user_email: str, expiry: datetime) -> None:
        """Store a refresh token in Redis with automatic expiry.

        Args:
            hashed_token: SHA256 hash of the refresh token
            user_email: Email of the user who owns this token
            expiry: Expiry datetime (timezone-aware UTC)
        """
        # Normalize expiry to UTC timestamp
        if hasattr(expiry, "timestamp"):
            expiry_timestamp = int(expiry.timestamp())
        else:
            expiry_timestamp = int(expiry.timestamp())

        # Calculate TTL in seconds
        now_timestamp = int(datetime.now(timezone.utc).timestamp())
        ttl = max(1, expiry_timestamp - now_timestamp)

        # Store in Redis with TTL
        key = f"refresh_token:{hashed_token}"
        token_data = {
            "user_email": user_email,
            "expiry": expiry_timestamp,
        }
        self.redis.setex(key, ttl, json.dumps(token_data))

    def get(self, hashed_token: str) -> Optional[Dict]:
        """Retrieve a refresh token from Redis.

        Returns:
            Dict with user_email and expiry, or None if not found/expired
        """
        key = f"refresh_token:{hashed_token}"
        token_data = self.redis.get(key)

        if not token_data:
            return None

        try:
            data = json.loads(token_data)
            expiry = datetime.fromtimestamp(data["expiry"], tz=timezone.utc)
            return {
                "user_email": data["user_email"],
                "expiry": expiry,
            }
        except (json.JSONDecodeError, KeyError, ValueError):
            return None

    def revoke(self, hashed_token: str) -> None:
        """Revoke a refresh token by moving it to blacklist.

        Args:
            hashed_token: SHA256 hash of the refresh token to revoke
        """
        key = f"refresh_token:{hashed_token}"
        blacklist_key = f"refresh_token_blacklist:{hashed_token}"

        # Get the token to find its original expiry
        token_data = self.redis.get(key)

        # Delete from active tokens
        self.redis.delete(key)

        # Add to blacklist with same TTL
        if token_data:
            try:
                data = json.loads(token_data)
                now_timestamp = int(datetime.now(timezone.utc).timestamp())
                expiry_timestamp = data.get("expiry", now_timestamp + 86400)
                ttl = max(1, expiry_timestamp - now_timestamp)
                self.redis.setex(blacklist_key, ttl, "revoked")
            except (json.JSONDecodeError, KeyError):
                pass

    def revoke_all_by_user(self, user_email: str) -> None:
        """Revoke all active refresh tokens for a user.

        Args:
            user_email: Email of the user whose tokens should be revoked
        """
        pattern = "refresh_token:*"
        cursor = 0

        while True:
            cursor, keys = self.redis.scan(cursor, match=pattern, count=100)

            for key in keys:
                token_data = self.redis.get(key)
                if token_data:
                    try:
                        data = json.loads(token_data)
                        if data.get("user_email") == user_email:
                            hashed = key.replace("refresh_token:", "")
                            self.revoke(hashed)
                    except (json.JSONDecodeError, KeyError):
                        pass

            if cursor == 0:
                break

    def is_blacklisted(self, hashed_token: str) -> bool:
        """Check if a token is blacklisted.

        Args:
            hashed_token: SHA256 hash of the refresh token

        Returns:
            True if token is blacklisted, False otherwise
        """
        blacklist_key = f"refresh_token_blacklist:{hashed_token}"
        return self.redis.exists(blacklist_key) > 0
