from sqlalchemy import Column, String, Text, Boolean, BigInteger, DateTime
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from datetime import datetime

from app.database import Base


class User(Base):
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
