# app/models/share.py
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from datetime import datetime, timezone
from app.database import Base

class Share(Base):
    __tablename__ = "shares"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Stores the GridFS 'file_id' or logical path
    file_id = Column(String, nullable=False, index=True)
    
    # User ID from auth_service - the user who owns the file
    # Stored as UUID without foreign key constraint since users table
    # doesn't exist in media_service database
    shared_by_user_id = Column(UUID(as_uuid=True), nullable=False)
    
    # User ID from auth_service - the user receiving access
    shared_with_user_id = Column(UUID(as_uuid=True), nullable=False)
    
    # permissions: 'read', 'write', 'full'
    permission = Column(String(20), default='read')
    
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class ShareLink(Base):
    __tablename__ = "share_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    file_id = Column(String, nullable=False)
    # User ID from auth_service - stored as UUID without foreign key constraint
    created_by_user_id = Column(UUID(as_uuid=True), nullable=False)
    
    # The part that goes in the URL: flowdock.com/s/AbCd123...
    token = Column(String(128), unique=True, nullable=False, index=True)
    
    password_hash = Column(Text, nullable=True)
    
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    max_downloads = Column(Integer, default=0) # 0 = unlimited
    downloads_used = Column(Integer, default=0)
    active = Column(Boolean, default=True)