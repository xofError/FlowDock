# app/models/share.py
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime
from app.database import Base

class Share(Base):
    __tablename__ = "shares"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Stores the GridFS 'file_id' or logical path
    file_id = Column(String, nullable=False, index=True)
    
    shared_with_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # permissions: 'read', 'write', 'full'
    permission = Column(String(20), default='read')
    
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ShareLink(Base):
    __tablename__ = "share_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    file_id = Column(String, nullable=False)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # The part that goes in the URL: flowdock.com/s/AbCd123...
    token = Column(String(128), unique=True, nullable=False, index=True)
    
    password_hash = Column(Text, nullable=True)
    
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    max_downloads = Column(Integer, default=0) # 0 = unlimited
    downloads_used = Column(Integer, default=0)
    active = Column(Boolean, default=True)