"""
FlowDock Media Service - Main Application
Handles file uploads, downloads, and metadata storage.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.presentation.api import files as files_router
from app.presentation.api import folders as folders_router
from app.presentation.api import public as public_router
from app.presentation.api import folder_sharing as folder_sharing_router
from app.presentation.api import public_folder_links as public_folder_links_router
from app.database import connect_to_mongo, close_mongo_connection, init_db
from app.core.config import settings
# Import models to register them with SQLAlchemy Base
from app.models import share

# Configure logging
logging.basicConfig(
    level=settings.log_level,
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
        
        # Initialize PostgreSQL tables
        init_db()
        logger.info("✓ PostgreSQL tables initialized")
        
        # Connect to MongoDB
        await connect_to_mongo()
        
        logger.info("=" * 70)
        logger.info(f"✓ {settings.service_name} v{settings.service_version}")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"✗ Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    try:
        logger.info("🛑 Shutting down Media Service...")
        await close_mongo_connection()
        logger.info("✓ Shutdown complete")
    except Exception as e:
        logger.error(f"✗ Shutdown error: {e}")


# ============================================================================
# FASTAPI APP SETUP
# ============================================================================

app = FastAPI(
    title=settings.service_name,
    description="Handles file uploads, downloads, and metadata storage with async communication",
    version=settings.service_version,
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
app.include_router(files_router.router, prefix=settings.api_prefix, tags=["files"])
app.include_router(folders_router.router, prefix=settings.api_prefix, tags=["folders"])
app.include_router(folder_sharing_router.router, prefix=settings.api_prefix, tags=["folder-sharing"])
app.include_router(public_folder_links_router.router, prefix=settings.api_prefix, tags=["public-folder-links"])
app.include_router(public_router.router, tags=["public"])  # No prefix for public endpoint


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.service_name,
        "version": settings.service_version,
        "status": "running"
    }
