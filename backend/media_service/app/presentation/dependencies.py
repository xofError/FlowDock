"""
Dependency Injection setup for FastAPI.
Constructs the service object graph for endpoints to use.
"""

import logging
from fastapi import Depends

from app.core.config import settings
from app.database import get_fs, get_mongo_db
from app.application.services import FileService, FolderService
from app.application.public_folder_links_service import PublicFolderLinksService
from app.infrastructure.database.mongo_repository import MongoGridFSRepository, MongoFolderRepository
from app.infrastructure.security.encryption import AESCryptoService
from app.infrastructure.messaging.no_op_publisher import NoOpEventPublisher
from app.infrastructure.http.auth_client import HttpQuotaRepository
from app.infrastructure.http.logger import HttpActivityLogger

logger = logging.getLogger(__name__)


async def get_file_service() -> FileService:
    """
    Factory function for FastAPI dependency injection.
    Builds the complete FileService with all dependencies.
    
    Usage in endpoint:
        @router.post("/upload")
        async def upload(file: UploadFile, service: FileService = Depends(get_file_service)):
            ...
    """
    try:
        # Infrastructure layer implementations
        fs = get_fs()
        db = get_mongo_db()
        repo = MongoGridFSRepository(fs, db)
        crypto = AESCryptoService()
        publisher = NoOpEventPublisher()  # No-op since we removed RabbitMQ
        quota_repo = HttpQuotaRepository(settings.auth_service_url)
        activity_logger = HttpActivityLogger(settings.auth_service_url, settings.internal_api_key)

        # Infrastructure for folder operations
        mongo_db = get_mongo_db()
        folder_repo = MongoFolderRepository(mongo_db)
        
        # Application service with injected dependencies
        service = FileService(
            repo=repo,
            crypto=crypto,
            event_publisher=publisher,
            quota_repo=quota_repo,
            folder_repo=folder_repo,
            activity_logger=activity_logger,
        )

        return service

    except Exception as e:
        logger.error(f"Failed to build FileService: {e}")
        raise


async def get_folder_service() -> FolderService:
    """
    Factory function for FolderService dependency injection.
    Builds the complete FolderService with all dependencies.
    
    Usage in endpoint:
        @router.post("/folders")
        async def create_folder(service: FolderService = Depends(get_folder_service)):
            ...
    """
    try:
        # Infrastructure layer implementations
        mongo_db = get_mongo_db()
        folder_repo = MongoFolderRepository(mongo_db)
        fs = get_fs()
        file_repo = MongoGridFSRepository(fs, mongo_db)
        
        # [FIX] Inject crypto and quota services
        crypto = AESCryptoService()
        quota_repo = HttpQuotaRepository(settings.auth_service_url)

        # Application service with injected dependencies
        service = FolderService(
            folder_repo=folder_repo,
            file_repo=file_repo,
            crypto=crypto,          # For decryption in archive_folder
            quota_repo=quota_repo,  # For quota updates in delete_folder_recursive
        )

        return service

    except Exception as e:
        logger.error(f"Failed to build FolderService: {e}")
        raise


def get_public_folder_link_service() -> PublicFolderLinksService:
    """
    Factory function for PublicFolderLinksService dependency injection.
    Builds the PublicFolderLinksService with all dependencies.
    
    Usage in endpoint:
        @router.get("/public-link/{token}")
        async def access_link(token: str, service: PublicFolderLinksService = Depends(get_public_folder_link_service)):
            ...
    """
    try:
        # Infrastructure layer implementations
        mongo_db = get_mongo_db()
        folder_repo = MongoFolderRepository(mongo_db)

        # Application service with injected dependencies
        service = PublicFolderLinksService(
            folder_repo=folder_repo,
            mongo_db=mongo_db,
        )

        return service

    except Exception as e:
        logger.error(f"Failed to build PublicFolderLinksService: {e}")
        raise

