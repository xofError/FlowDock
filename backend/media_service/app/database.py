"""
MongoDB database connection and management
"""

import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from app.core.config import settings

logger = logging.getLogger(__name__)

# Global state
mongo_client: AsyncIOMotorClient = None
db = None
fs: AsyncIOMotorGridFSBucket = None


async def connect_to_mongo():
    """Connect to MongoDB on startup"""
    global mongo_client, db, fs
    
    try:
        mongo_client = AsyncIOMotorClient(settings.MONGO_URL)
        db = mongo_client[settings.MONGO_DB_NAME]
        fs = AsyncIOMotorGridFSBucket(db)
        
        # Test connection
        await db.command("ping")
        logger.info(f"✓ Connected to MongoDB: {settings.MONGO_DB_NAME}")
        
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


def get_db():
    """Get database instance"""
    if db is None:
        raise RuntimeError("Database not initialized. Did you call connect_to_mongo()?")
    return db
