from typing import Optional

from app.database import SessionLocal
from app.models.user import User as DBUser
from app.utils import security


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
            raise ValueError("user already exists")
        new = DBUser(email=email, full_name = full_name , password_hash=security.hash_password(password))
        db.add(new)
        db.commit()
        db.refresh(new)
        return new
    finally:
        db.close()
