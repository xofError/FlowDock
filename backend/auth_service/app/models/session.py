from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from datetime import datetime

from app.database import Base


class Session(Base):
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
