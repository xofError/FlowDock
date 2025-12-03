"""
RabbitMQ message publishing for file events with connection resilience.
"""

import json
import logging
import pika
import time
import threading
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class RabbitMQPublisher:
    """
    Resilient RabbitMQ publisher with connection pooling and reconnect logic.
    Handles temporary connection losses and retries publishing.
    """

    def __init__(self, rabbitmq_url: str, queue_name: str = 'file_events'):
        self.rabbitmq_url = rabbitmq_url
        self.queue_name = queue_name
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.adapters.blocking_connection.BlockingChannel] = None
        self._lock = threading.Lock()

    def _open_connection(self):
        """Create a new connection with sensible defaults."""
        params = pika.URLParameters(self.rabbitmq_url)
        params.heartbeat = 60
        params.blocked_connection_timeout = 30
        return pika.BlockingConnection(params)

    def connect(self):
        """Establish or re-establish connection to RabbitMQ."""
        with self._lock:
            try:
                # Close old connection if exists
                if self.connection:
                    try:
                        self.connection.close()
                    except Exception:
                        pass
                    self.connection = None
                    self.channel = None

                # Open new connection
                self.connection = self._open_connection()
                self.channel = self.connection.channel()
                self.channel.queue_declare(queue=self.queue_name, durable=True)
                logger.info(f"✓ Connected to RabbitMQ, queue '{self.queue_name}' declared")
                return True

            except Exception as e:
                logger.error(f"✗ Failed to connect to RabbitMQ: {e}")
                self.connection = None
                self.channel = None
                return False

    def is_connected(self) -> bool:
        """Check if connection is alive."""
        return (
            self.connection is not None
            and getattr(self.connection, 'is_open', False)
            and self.channel is not None
            and getattr(self.channel, 'is_open', False)
        )

    def disconnect(self):
        """Close RabbitMQ connection."""
        with self._lock:
            try:
                if self.channel and getattr(self.channel, 'is_open', False):
                    try:
                        self.channel.close()
                    except Exception:
                        pass
                if self.connection and getattr(self.connection, 'is_open', False):
                    try:
                        self.connection.close()
                    except Exception:
                        pass
            finally:
                self.channel = None
                self.connection = None
                logger.info("✓ RabbitMQ connection closed")

    def publish(
        self,
        event_type: str,
        user_id: str,
        file_id: str,
        file_size: int,
        max_retries: int = 3,
        retry_delay: float = 0.5,
    ) -> bool:
        """
        Publish a file event to RabbitMQ with automatic reconnect and retry.

        Args:
            event_type: Event type (FILE_UPLOADED, FILE_DELETED)
            user_id: User ID (UUID)
            file_id: File ObjectId / ID
            file_size: File size in bytes
            max_retries: Number of retries on transient failures
            retry_delay: Initial delay between retries (seconds)

        Returns:
            True if published successfully, False otherwise
        """
        message = {
            "event": event_type,
            "user_id": user_id,
            "file_id": file_id,
            "file_size": file_size,
        }

        for attempt in range(max_retries):
            try:
                # Ensure connection exists
                if not self.is_connected():
                    logger.warning(f"Connection not ready (attempt {attempt + 1}/{max_retries}), reconnecting...")
                    if not self.connect():
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay * (2 ** attempt))  # exponential backoff
                        continue

                # Publish message
                self.channel.basic_publish(
                    exchange='',
                    routing_key=self.queue_name,
                    body=json.dumps(message),
                    properties=pika.BasicProperties(
                        delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
                    ),
                )

                logger.info(
                    f"✓ Published {event_type}: user={user_id}, file={file_id}, size={file_size}"
                )
                return True

            except pika.exceptions.AMQPConnectionError as e:
                logger.warning(f"Connection error on attempt {attempt + 1}/{max_retries}: {e}")
                # Force reconnect
                with self._lock:
                    self.connection = None
                    self.channel = None
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))

            except pika.exceptions.AMQPChannelError as e:
                logger.warning(f"Channel error on attempt {attempt + 1}/{max_retries}: {e}")
                with self._lock:
                    self.channel = None
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))

            except Exception as e:
                logger.error(f"Unexpected error publishing event (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))

        logger.error(f"✗ Failed to publish {event_type} after {max_retries} attempts")
        return False


# Global publisher instance
_publisher: Optional[RabbitMQPublisher] = None


async def connect_rabbitmq():
    """Connect to RabbitMQ on startup"""
    global _publisher
    try:
        _publisher = RabbitMQPublisher(settings.RABBITMQ_URL, settings.RABBITMQ_QUEUE)
        _publisher.connect()
        logger.info("✓ RabbitMQ publisher initialized")
    except Exception as e:
        logger.error(f"✗ Failed to initialize RabbitMQ publisher: {e}")
        # Don't raise - service should continue; publishing will retry lazily


async def close_rabbitmq():
    """Close RabbitMQ connection on shutdown"""
    global _publisher
    if _publisher:
        _publisher.disconnect()


def publish_file_event(event_type: str, user_id: str, file_id: str, file_size: int) -> bool:
    """
    Publish file event to RabbitMQ for Core Service consumption.
    
    Uses the global publisher instance with automatic reconnect and retry.
    
    Args:
        event_type: Event type (FILE_UPLOADED, FILE_DELETED)
        user_id: User ID (UUID string)
        file_id: File ObjectId / ID
        file_size: File size in bytes
    
    Returns:
        True if published successfully, False otherwise
    """
    global _publisher
    if not _publisher:
        logger.error("RabbitMQ publisher not initialized")
        return False
    
    return _publisher.publish(event_type, user_id, file_id, file_size)
