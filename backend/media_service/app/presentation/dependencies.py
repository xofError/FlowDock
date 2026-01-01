"""
Dependency Injection setup for FastAPI.
Constructs the service object graph for endpoints to use.
"""

import logging
from fastapi import Depends

from app.core.config import settings
from app.database import get_fs
from app.application.services import FileService
from app.infrastructure.database.mongo_repository import MongoGridFSRepository
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
        repo = MongoGridFSRepository(fs)
        crypto = AESCryptoService()
        publisher = NoOpEventPublisher()  # No-op since we removed RabbitMQ
        quota_repo = HttpQuotaRepository(settings.auth_service_url, settings.internal_api_key)
        activity_logger = HttpActivityLogger(settings.auth_service_url, settings.internal_api_key)

        # Application service with injected dependencies
        service = FileService(
            repo=repo,
            crypto=crypto,
            event_publisher=publisher,
            quota_repo=quota_repo,
            activity_logger=activity_logger,
        )

        return service

    except Exception as e:
        logger.error(f"Failed to build FileService: {e}")
        raise
