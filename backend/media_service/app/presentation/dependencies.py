"""
Dependency Injection setup for FastAPI.
Constructs the service object graph for endpoints to use.
"""

import logging
from fastapi import Depends

from app.database import get_fs
from app.application.services import FileService
from app.infrastructure.database.mongo_repository import MongoGridFSRepository
from app.infrastructure.security.encryption import AESCryptoService
from app.infrastructure.messaging.rabbitmq_publisher import RabbitMQEventPublisher

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
        publisher = RabbitMQEventPublisher()

        # Application service with injected dependencies
        service = FileService(
            repo=repo,
            crypto=crypto,
            event_publisher=publisher,
        )

        return service

    except Exception as e:
        logger.error(f"Failed to build FileService: {e}")
        raise
