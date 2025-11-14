from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from datetime import datetime

from app.database import Base


class RecoveryToken(Base):
    __tablename__ = "recovery_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    user_id = Column(UUID(as_uuid=True), nullable=False)

    token = Column(String(100), nullable=False)
    method = Column(String(20))  # email, telegram, phone

    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

    used = Column(Boolean, default=False)
