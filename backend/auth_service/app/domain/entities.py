"""
Domain Layer: Core Business Entities

These are pure Python dataclasses representing the core business objects.
They have NO dependencies on frameworks (FastAPI, SQLAlchemy) or external services.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class User:
    """Core User entity - represents a user in the system."""
    id: Optional[UUID]
    email: str
    password_hash: str
    full_name: Optional[str] = None
    telegram_id: Optional[str] = None
    phone_number: Optional[str] = None
    verified: bool = False
    twofa_enabled: bool = False
    totp_secret: Optional[str] = None
    recovery_phrase_hash: Optional[str] = None
    storage_used: int = 0
    storage_limit: int = 10737418240  # 10GB default
    created_at: Optional[datetime] = None
    last_login_ip: Optional[str] = None
    last_login_at: Optional[datetime] = None


@dataclass
class Session:
    """Session entity - represents a user session/login."""
    id: Optional[UUID]
    user_id: UUID
    refresh_token_hash: Optional[str]
    device_info: Optional[str] = None
    browser_name: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    active: bool = True


@dataclass
class RecoveryToken:
    """Recovery token entity - for password reset and recovery codes."""
    id: Optional[UUID]
    user_id: UUID
    token: str
    method: str  # "email", "telegram", "phone", "recovery_code"
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    used: bool = False
