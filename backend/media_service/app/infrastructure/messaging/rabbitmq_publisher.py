"""
RabbitMQ implementation of IEventPublisher.
Publishes file events asynchronously via RabbitMQ.
"""

import json
import logging
from typing import Optional

from app.domain.interfaces import IEventPublisher
from app.services.rabbitmq_service import publish_file_event

logger = logging.getLogger(__name__)


class RabbitMQEventPublisher(IEventPublisher):
    """
    RabbitMQ implementation for publishing file events.
    Wraps the existing synchronous rabbitmq_service.publish_file_event().
    """

    async def publish_upload(self, user_id: str, file_id: str, file_size: int) -> None:
        """
        Publish FILE_UPLOADED event.
        
        Args:
            user_id: Owner of the file
            file_id: Uploaded file ID
            file_size: Size in bytes
        """
        success = publish_file_event(
            event_type="FILE_UPLOADED",
            user_id=user_id,
            file_id=file_id,
            file_size=file_size,
        )
        if not success:
            logger.warning(f"Failed to publish FILE_UPLOADED for {file_id}")

    async def publish_delete(self, user_id: str, file_id: str, file_size: int) -> None:
        """
        Publish FILE_DELETED event.
        
        Args:
            user_id: Owner of the file
            file_id: Deleted file ID
            file_size: Size in bytes
        """
        success = publish_file_event(
            event_type="FILE_DELETED",
            user_id=user_id,
            file_id=file_id,
            file_size=file_size,
        )
        if not success:
            logger.warning(f"Failed to publish FILE_DELETED for {file_id}")

    async def publish_download(self, user_id: str, file_id: str) -> None:
        """
        Publish FILE_DOWNLOADED event.
        
        Args:
            user_id: User who downloaded
            file_id: Downloaded file ID
        """
        success = publish_file_event(
            event_type="FILE_DOWNLOADED",
            user_id=user_id,
            file_id=file_id,
            file_size=0,  # Size not needed for download events
        )
        if not success:
            logger.warning(f"Failed to publish FILE_DOWNLOADED for {file_id}")
