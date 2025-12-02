from typing import Optional
import secrets
from datetime import datetime, timedelta, timezone
import redis
import os

from app.database import SessionLocal
from app.models.recovery_token import RecoveryToken as DBRecoveryToken
from app.models.user import User as DBUser


OTP_EXPIRE_MINUTES = 15
OTP_EXPIRE_SECONDS = OTP_EXPIRE_MINUTES * 60

# Rate limiting constants
LOGIN_RATE_LIMIT = 5  # max 5 attempts
LOGIN_RATE_LIMIT_WINDOW = 300  # per 5 minutes (300 seconds)
OTP_RATE_LIMIT = 3  # max 3 OTP requests
OTP_RATE_LIMIT_WINDOW = 300  # per 5 minutes (300 seconds)

# Initialize Redis client
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)


def authenticate_user(username: str, password: str) -> Optional[DBUser]:
    # This function can be expanded to verify password hashes, etc.
    db = SessionLocal()
    try:
        user = db.query(DBUser).filter(DBUser.email == username).first()
        return user
    finally:
        db.close()


def create_email_otp(user_email: str) -> str:
    """Generate an OTP, store it in Redis with 15-minute expiry, and return the token string."""
    db = SessionLocal()
    try:
        user = db.query(DBUser).filter(DBUser.email == user_email).first()
        if not user:
            raise ValueError("user not found")

        # Generate 6-digit OTP
        otp = f"{secrets.randbelow(10**6):06d}"
        
        # Save to Redis with 15-minute expiry
        # Key format: otp:email:{user_email}
        key = f"otp:email:{user_email}"
        redis_client.setex(key, OTP_EXPIRE_SECONDS, otp)
        
        return otp
    finally:
        db.close()


def verify_email_otp(user_email: str, token: str) -> bool:
    """Verify an OTP from Redis. Marks user as verified in DB and returns True on success."""
    db = SessionLocal()
    try:
        user = db.query(DBUser).filter(DBUser.email == user_email).first()
        if not user:
            return False

        # Retrieve OTP from Redis
        key = f"otp:email:{user_email}"
        stored_otp = redis_client.get(key)
        
        # Verify OTP matches and hasn't expired (Redis handles expiry automatically)
        if stored_otp and stored_otp == token:
            # Delete OTP to prevent reuse
            redis_client.delete(key)
            
            # Mark user as verified in database
            user.verified = True
            db.add(user)
            db.commit()
            return True
        
        return False
    finally:
        db.close()


def check_rate_limit(identifier: str, limit: int, window: int) -> bool:
    """Check if an identifier (email/IP) has exceeded rate limit.
    
    Args:
        identifier: Unique identifier (e.g., email or IP address)
        limit: Maximum attempts allowed
        window: Time window in seconds
    
    Returns:
        True if within limit, False if limit exceeded
    """
    key = f"rate_limit:{identifier}"
    current = redis_client.incr(key)
    
    if current == 1:
        # First request, set expiry
        redis_client.expire(key, window)
    
    return current <= limit


def check_login_rate_limit(email: str) -> bool:
    """Check if login attempts for this email are within limit."""
    return check_rate_limit(f"login:{email}", LOGIN_RATE_LIMIT, LOGIN_RATE_LIMIT_WINDOW)


def check_otp_request_rate_limit(email: str) -> bool:
    """Check if OTP requests for this email are within limit."""
    return check_rate_limit(f"otp_request:{email}", OTP_RATE_LIMIT, OTP_RATE_LIMIT_WINDOW)
