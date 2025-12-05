from typing import Optional
import secrets
from datetime import datetime, timedelta, timezone
import redis
import os
from app.utils import security
from app.database import SessionLocal
from app.models.recovery_token import RecoveryToken as DBRecoveryToken
from app.models.user import User as DBUser
from app.utils import email as email_utils
from app.core.config import settings
from datetime import datetime

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


# --- DB-backed recovery token helpers ---------------------------------
def create_recovery_token(user_email: str) -> str:
    """Create a one-use recovery token stored in the DB and return the token string."""
    db = SessionLocal()
    try:
        user = db.query(DBUser).filter(DBUser.email == user_email).first()
        if not user:
            raise ValueError("user not found")

        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRE_MINUTES)

        rec = DBRecoveryToken(user_id=user.id, token=token, method="email", expires_at=expires_at)
        db.add(rec)
        db.commit()
        return token
    finally:
        db.close()


def verify_recovery_token(user_email: str, token: str) -> bool:
    """Verify a recovery token (DB). Marks it used and returns True on success."""
    db = SessionLocal()
    try:
        user = db.query(DBUser).filter(DBUser.email == user_email).first()
        if not user:
            return False

        now = datetime.now(timezone.utc)
        rec = (
            db.query(DBRecoveryToken)
            .filter(DBRecoveryToken.user_id == user.id)
            .filter(DBRecoveryToken.token == token)
            .filter(DBRecoveryToken.used == False)
            .filter(DBRecoveryToken.expires_at > now)
            .first()
        )
        if not rec:
            return False

        # mark used
        rec.used = True
        db.add(rec)
        db.commit()
        return True
    finally:
        db.close()


def check_recovery_token(user_email: str, token: str) -> bool:
    """Check if a recovery token is valid WITHOUT marking it as used.
    Used for verification before showing the reset form."""
    db = SessionLocal()
    try:
        user = db.query(DBUser).filter(DBUser.email == user_email).first()
        if not user:
            return False

        now = datetime.now(timezone.utc)
        rec = (
            db.query(DBRecoveryToken)
            .filter(DBRecoveryToken.user_id == user.id)
            .filter(DBRecoveryToken.token == token)
            .filter(DBRecoveryToken.used == False)
            .filter(DBRecoveryToken.expires_at > now)
            .first()
        )
        return rec is not None
    finally:
        db.close()
# 1. Request Reset
async def request_password_reset(email: str) -> bool:
    """Generates a DB-backed recovery token and sends a reset link to the user."""
    try:
        # Prefer a DB-backed recovery token so we can send a link to the frontend
        token = create_recovery_token(email)

        # Build reset link that points to the verification endpoint first
        backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        reset_link = f"{backend_url}/auth/verify-reset-token?token={token}&email={email}"

        subject = "Reset your FlowDock password"
        body = f"Click the link to reset your password:\n\n{reset_link}\n\nThis link expires in {OTP_EXPIRE_MINUTES} minutes."

        # Send email synchronously (falls back to console if SMTP not configured)
        email_utils.send_email(email, subject, body)
        return True
    except ValueError:
        # User not found: Return True anyway to prevent Email Enumeration attacks
        return True
    except Exception as e:
        print(f"Error requesting reset: {e}")
        return False

# 2. Confirm Reset
def confirm_password_reset(email: str, token: str, new_password: str) -> bool:
    """Verifies recovery token and updates the password."""
    # Verify DB-backed recovery token
    if not verify_recovery_token(email, token):
        return False
    
    db = SessionLocal()
    try:
        user = db.query(DBUser).filter(DBUser.email == email).first()
        if not user:
            return False
            
        # Hash new password and save
        user.password_hash = security.hash_password(new_password)
        db.add(user)
        db.commit()
        return True
    finally:
        db.close()