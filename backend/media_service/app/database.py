"""
Database connections for both MongoDB (GridFS) and PostgreSQL (Sharing data)
"""

import logging
import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

logger = logging.getLogger(__name__)

# ============================================================================
# MongoDB Configuration (for GridFS file storage)
# ============================================================================
mongo_client: AsyncIOMotorClient = None
db = None
fs: AsyncIOMotorGridFSBucket = None


async def connect_to_mongo():
    """Connect to MongoDB on startup"""
    global mongo_client, db, fs
    
    try:
        mongo_client = AsyncIOMotorClient(settings.mongo_url)
        db = mongo_client[settings.mongo_db_name]
        fs = AsyncIOMotorGridFSBucket(db)
        
        # Test connection
        await db.command("ping")
        logger.info(f"✓ Connected to MongoDB: {settings.mongo_db_name}")
        
    except Exception as e:
        logger.error(f"✗ Failed to connect to MongoDB: {e}")
        raise


async def close_mongo_connection():
    """Close MongoDB connection on shutdown"""
    global mongo_client
    
    if mongo_client:
        mongo_client.close()
        logger.info("✓ Closed MongoDB connection")


def get_fs() -> AsyncIOMotorGridFSBucket:
    """Get GridFS bucket instance"""
    if fs is None:
        raise RuntimeError("GridFS not initialized. Did you call connect_to_mongo()?")
    return fs


def get_mongo_db():
    """Get MongoDB database instance"""
    if db is None:
        raise RuntimeError("Database not initialized. Did you call connect_to_mongo()?")
    return db


# ============================================================================
# PostgreSQL Configuration (for sharing permissions, sessions, etc.)
# ============================================================================
DATABASE_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
)

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency for PostgreSQL database session"""
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


def init_db():
    """Create all PostgreSQL tables"""
    Base.metadata.create_all(bind=engine)
