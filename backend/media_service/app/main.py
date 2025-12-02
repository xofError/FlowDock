"""
FlowDock Media Service - Main Application
Handles file uploads, downloads, and metadata storage with async communication.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import files as files_router
from app.database import connect_to_mongo, close_mongo_connection
from app.services import rabbitmq_service
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# LIFESPAN MANAGEMENT
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle: startup and shutdown events
    """
    # Startup
    try:
        logger.info("🚀 Starting Media Service...")
        
        # Connect to MongoDB
        await connect_to_mongo()
        
        # Connect to RabbitMQ
        await rabbitmq_service.connect_rabbitmq()
        
        logger.info("=" * 70)
        logger.info(f"✓ {settings.SERVICE_NAME} v{settings.SERVICE_VERSION}")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"✗ Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    try:
        logger.info("🛑 Shutting down Media Service...")
        await close_mongo_connection()
        await rabbitmq_service.close_rabbitmq()
        logger.info("✓ Shutdown complete")
    except Exception as e:
        logger.error(f"✗ Shutdown error: {e}")


# ============================================================================
# FASTAPI APP SETUP
# ============================================================================

app = FastAPI(
    title=settings.SERVICE_NAME,
    description="Handles file uploads, downloads, and metadata storage with async communication",
    version=settings.SERVICE_VERSION,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(files_router.router, prefix=settings.API_PREFIX, tags=["files"])


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "status": "running"
    }
