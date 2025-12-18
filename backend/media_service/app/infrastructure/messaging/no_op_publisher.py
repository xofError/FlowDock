"""
No-op (null object) implementation of IEventPublisher.
Used when we don't need to publish events (messaging disabled).
"""

import logging
from app.domain.interfaces import IEventPublisher

logger = logging.getLogger(__name__)


class NoOpEventPublisher(IEventPublisher):
    """
    A no-op implementation that discards all events.
    
    This is used in place of RabbitMQ when we want to simplify the architecture
    and don't need event publishing for download/delete operations.
    """

    async def publish_upload(self, user_id: str, file_id: str, file_size: int) -> None:
        """Discards upload events."""
        logger.debug(f"[NoOp] Would publish upload event for {file_id}")

    async def publish_delete(self, user_id: str, file_id: str, file_size: int) -> None:
        """Discards delete events."""
        logger.debug(f"[NoOp] Would publish delete event for {file_id}")

    async def publish_download(self, user_id: str, file_id: str) -> None:
        """Discards download events."""
        logger.debug(f"[NoOp] Would publish download event for {file_id}")
