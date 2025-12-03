from typing import Optional

from app.database import SessionLocal
from app.models.user import User as DBUser
from app.utils import security
from app.models.recovery_token import RecoveryToken as DBRecoveryToken
import secrets
import hashlib
from datetime import datetime, timedelta


def create_test_user(email: str = "test@example.com", password: str = "password") -> DBUser:
    """Create a default test user in the DB if it doesn't already exist.

    Useful for local development. Returns the DB user instance.
    """
    db = SessionLocal()
    try:
        user = db.query(DBUser).filter(DBUser.email == email).first()
        if user:
            return user
        new = DBUser(email=email, password_hash=security.hash_password(password))
        db.add(new)
        db.commit()
        db.refresh(new)
        return new
    finally:
        db.close()


def get_user_by_email(email: str) -> Optional[DBUser]:
    db = SessionLocal()
    try:
        return db.query(DBUser).filter(DBUser.email == email).first()
    finally:
        db.close()


def create_user(email: str, full_name: str, password: str) -> DBUser:
    """Create a new user in the database. Raises ValueError if user exists."""
    db = SessionLocal()
    try:
        existing = db.query(DBUser).filter(DBUser.email == email).first()
        if existing:
            if existing.verified == False:
                return existing
            else:
                raise ValueError("user already exists")
        new = DBUser(email=email, full_name = full_name , password_hash=security.hash_password(password))
        db.add(new)
        db.commit()
        db.refresh(new)
        return new
    finally:
        db.close()


def set_totp_secret(email: str, secret: str) -> DBUser:
    """Persist a TOTP secret for the user. Returns updated DBUser."""
    db = SessionLocal()
    try:
        user = db.query(DBUser).filter(DBUser.email == email).first()
        if not user:
            raise ValueError("user not found")
        user.totp_secret = secret
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def enable_twofa_and_generate_recovery_codes(email: str, count: int = 10) -> list:
    """Enable 2FA for the user and generate `count` single-use recovery codes.

    Stores only hashed recovery codes in `recovery_tokens` and returns the
    plaintext codes so the caller can show them to the user exactly once.
    """
    db = SessionLocal()
    try:
        user = db.query(DBUser).filter(DBUser.email == email).first()
        if not user:
            raise ValueError("user not found")

        user.twofa_enabled = True
        db.add(user)

        now = datetime.utcnow()
        # recovery codes validity: long-lived (e.g. 10 years)
        expires = now + timedelta(days=3650)
        plaintext_codes = []
        for _ in range(count):
            # human-manageable code: 8 hex chars
            code = secrets.token_hex(4)
            hashed = hashlib.sha256(code.encode("utf-8")).hexdigest()
            rec = DBRecoveryToken(user_id=user.id, token=hashed, method="recovery_code", expires_at=expires)
            db.add(rec)
            plaintext_codes.append(code)

        db.commit()
        return plaintext_codes
    finally:
        db.close()


def verify_and_consume_recovery_code(email: str, code: str) -> bool:
    """Verify a recovery code for the user. Marks the code used on success.

    Returns True if the code is valid and consumed, False otherwise.
    """
    db = SessionLocal()
    try:
        user = db.query(DBUser).filter(DBUser.email == email).first()
        if not user:
            return False
        hashed = hashlib.sha256(code.encode("utf-8")).hexdigest()
        now = datetime.utcnow()
        rec = (
            db.query(DBRecoveryToken)
            .filter(DBRecoveryToken.user_id == user.id, DBRecoveryToken.token == hashed, DBRecoveryToken.used == False)
            .order_by(DBRecoveryToken.created_at.desc())
            .first()
        )
        if not rec:
            return False
        if rec.expires_at < now:
            return False
        rec.used = True
        db.add(rec)
        db.commit()
        return True
    finally:
        db.close()


def mark_user_verified(email: str) -> None:
    """Mark a user as email-verified."""
    db = SessionLocal()
    try:
        user = db.query(DBUser).filter(DBUser.email == email).first()
        if not user:
            raise ValueError("user not found")
        user.verified = True
        db.add(user)
        db.commit()
    finally:
        db.close()
