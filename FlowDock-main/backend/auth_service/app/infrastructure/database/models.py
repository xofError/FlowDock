"""
Infrastructure Layer: SQLAlchemy ORM Models

These are the database representation of entities.
They map 1-to-1 to domain entities but include database-specific details.
"""

from sqlalchemy import Column, String, Text, Boolean, BigInteger, DateTime
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from datetime import datetime

from app.database import Base


class UserModel(Base):
    """SQLAlchemy User model - persisted to PostgreSQL."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    
    full_name = Column(String(100))
    telegram_id = Column(String(50))
    phone_number = Column(String(20))
    
    verified = Column(Boolean, default=False)
    twofa_enabled = Column(Boolean, default=False)
    totp_secret = Column(Text)
    
    recovery_phrase_hash = Column(Text)

    storage_used = Column(BigInteger, default=0)
    storage_limit = Column(BigInteger, default=10737418240)  # 10GB default
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_ip = Column(String(50))
    last_login_at = Column(DateTime)


class SessionModel(Base):
    """SQLAlchemy Session model - persisted to PostgreSQL."""
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    
    refresh_token_hash = Column(String(255), nullable=True)

    device_info = Column(String(255))
    browser_name = Column(String(100))
    ip_address = Column(String(50))

    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

    active = Column(Boolean, default=True)


class RecoveryTokenModel(Base):
    """SQLAlchemy RecoveryToken model - persisted to PostgreSQL."""
    __tablename__ = "recovery_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)

    token = Column(String(100), nullable=False)
    method = Column(String(20))  # email, telegram, phone, recovery_code

    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

    used = Column(Boolean, default=False)
