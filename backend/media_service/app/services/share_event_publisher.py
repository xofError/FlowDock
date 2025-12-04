"""
RabbitMQ publisher for sharing events.
Publishes share and sharelink events to sync with Auth Service.
"""

import json
import logging
import pika
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class ShareEventPublisher:
    """
    Publishes share and sharelink events to RabbitMQ.
    Used to sync sharing data with Auth Service and other services.
    """

    def __init__(self, rabbitmq_url: str):
        self.rabbitmq_url = rabbitmq_url
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.adapters.blocking_connection.BlockingChannel] = None

    def _open_connection(self):
        """Create a new connection to RabbitMQ."""
        params = pika.URLParameters(self.rabbitmq_url)
        params.heartbeat = 60
        params.blocked_connection_timeout = 30
        return pika.BlockingConnection(params)

    def connect(self):
        """Establish connection and declare exchange."""
        try:
            self.connection = self._open_connection()
            self.channel = self.connection.channel()

            # Declare the sharing events exchange
            self.channel.exchange_declare(
                exchange='sharing_events',
                exchange_type='topic',
                durable=True
            )

            logger.info("✓ Share Event Publisher connected to RabbitMQ")
            return True

        except Exception as e:
            logger.error(f"✗ Failed to connect Share Event Publisher: {e}")
            return False

    def publish_share_created(self, share_data: dict):
        """
        Publish a share.created event.

        Args:
            share_data: Dictionary with share information (id, file_id, shared_by_user_id, shared_with_user_id, permission, expires_at, created_at)
        """
        self._publish_event('share.created', share_data)

    def publish_share_updated(self, share_data: dict):
        """Publish a share.updated event."""
        self._publish_event('share.updated', share_data)

    def publish_share_deleted(self, share_id: str):
        """Publish a share.deleted event."""
        self._publish_event('share.deleted', {'id': share_id})

    def publish_sharelink_created(self, link_data: dict):
        """
        Publish a sharelink.created event.

        Args:
            link_data: Dictionary with sharelink information (id, file_id, created_by_user_id, token, has_password, expires_at, max_downloads, created_at, active)
        """
        self._publish_event('sharelink.created', link_data)

    def publish_sharelink_updated(self, link_data: dict):
        """Publish a sharelink.updated event."""
        self._publish_event('sharelink.updated', link_data)

    def publish_sharelink_deleted(self, link_id: str):
        """Publish a sharelink.deleted event."""
        self._publish_event('sharelink.deleted', {'id': link_id})

    def _publish_event(self, routing_key: str, data: dict):
        """
        Internal method to publish an event to RabbitMQ.

        Args:
            routing_key: The routing key (e.g., 'share.created', 'sharelink.updated')
            data: The event data as a dictionary
        """
        try:
            if not self.connection or not self.channel:
                if not self.connect():
                    logger.error(f"Cannot publish event {routing_key}: not connected")
                    return

            payload = json.dumps(data, default=str)  # default=str for datetime serialization

            self.channel.basic_publish(
                exchange='sharing_events',
                routing_key=routing_key,
                body=payload,
                properties=pika.BasicProperties(
                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,
                    content_type='application/json'
                )
            )

            logger.debug(f"✓ Published event: {routing_key}")

        except Exception as e:
            logger.error(f"✗ Failed to publish {routing_key}: {e}")

    def close(self):
        """Close the connection."""
        try:
            if self.connection:
                self.connection.close()
            logger.info("✓ Share Event Publisher closed")
        except Exception as e:
            logger.error(f"✗ Error closing publisher: {e}")


# Global publisher instance
_publisher: Optional[ShareEventPublisher] = None


def get_share_event_publisher() -> ShareEventPublisher:
    """
    Get or create the global share event publisher instance.
    Ensures only one connection is maintained.
    """
    global _publisher
    if _publisher is None:
        _publisher = ShareEventPublisher(settings.RABBITMQ_URL)
        _publisher.connect()
    return _publisher


def publish_share_created(share_data: dict):
    """Publish share.created event."""
    get_share_event_publisher().publish_share_created(share_data)


def publish_share_updated(share_data: dict):
    """Publish share.updated event."""
    get_share_event_publisher().publish_share_updated(share_data)


def publish_share_deleted(share_id: str):
    """Publish share.deleted event."""
    get_share_event_publisher().publish_share_deleted(share_id)


def publish_sharelink_created(link_data: dict):
    """Publish sharelink.created event."""
    get_share_event_publisher().publish_sharelink_created(link_data)


def publish_sharelink_updated(link_data: dict):
    """Publish sharelink.updated event."""
    get_share_event_publisher().publish_sharelink_updated(link_data)


def publish_sharelink_deleted(link_id: str):
    """Publish sharelink.deleted event."""
    get_share_event_publisher().publish_sharelink_deleted(link_id)
