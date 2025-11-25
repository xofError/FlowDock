from typing import Optional
import secrets
from datetime import datetime, timedelta, timezone

from app.database import SessionLocal
from app.models.recovery_token import RecoveryToken as DBRecoveryToken
from app.models.user import User as DBUser


OTP_EXPIRE_MINUTES = 15


def authenticate_user(username: str, password: str) -> Optional[DBUser]:
    # This function can be expanded to verify password hashes, etc.
    db = SessionLocal()
    try:
        user = db.query(DBUser).filter(DBUser.email == username).first()
        return user
    finally:
        db.close()


def create_email_otp(user_email: str) -> str:
    """Generate an OTP, store it in recovery_tokens and return the token string."""
    db = SessionLocal()
    try:
        user = db.query(DBUser).filter(DBUser.email == user_email).first()
        if not user:
            raise ValueError("user not found")

        otp = f"{secrets.randbelow(10**6):06d}"  # 6-digit zero-padded
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=OTP_EXPIRE_MINUTES)
        # store naive UTC for DB
        expires_naive = expires_at.astimezone(timezone.utc).replace(tzinfo=None)

        rec = DBRecoveryToken(user_id=user.id, token=otp, method="email", expires_at=expires_naive)
        db.add(rec)
        db.commit()
        return otp
    finally:
        db.close()


def verify_email_otp(user_email: str, token: str) -> bool:
    """Verify a previously created email OTP. Marks it used and returns True on success."""
    db = SessionLocal()
    try:
        user = db.query(DBUser).filter(DBUser.email == user_email).first()
        if not user:
            return False

        now = datetime.now(timezone.utc).astimezone(timezone.utc).replace(tzinfo=None)
        rec = (
            db.query(DBRecoveryToken)
            .filter(DBRecoveryToken.user_id == user.id, DBRecoveryToken.token == token, DBRecoveryToken.used == False)
            .order_by(DBRecoveryToken.created_at.desc())
            .first()
        )
        if not rec:
            return False
        if rec.expires_at < now:
            return False
        rec.used = True
        db.add(rec)
        # mark user verified
        user.verified = True
        db.add(user)
        db.commit()
        return True
    finally:
        db.close()
