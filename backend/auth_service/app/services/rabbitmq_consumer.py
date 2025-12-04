"""
RabbitMQ Consumer for File Events
Listens for messages from Media Service and updates user storage quotas.
This module should be integrated into the Core Service.
"""

import pika
import json
import logging
import time
import traceback
from typing import Callable, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class FileEventConsumer:
    """Robust RabbitMQ consumer for file events with reconnection and backoff.

    - Declares a durable queue (default: file_events)
    - Supports registering callbacks per event type
    - Acknowledges messages on success, nacks on failures
    - Reconnects with exponential backoff on connection errors
    """

    def __init__(self, rabbitmq_url: str, queue_name: str = 'file_events'):
        self.rabbitmq_url = rabbitmq_url
        self.queue_name = queue_name
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.adapters.blocking_connection.BlockingChannel] = None
        self.callbacks = {}
        self._stopped = False

    def register_callback(self, event_type: str, callback: Callable):
        self.callbacks[event_type] = callback
        logger.info(f"✓ Registered callback for event: {event_type}")

    def _open_connection(self):
        params = pika.URLParameters(self.rabbitmq_url)
        # sensible defaults
        params.heartbeat = 60
        params.blocked_connection_timeout = 30
        return pika.BlockingConnection(params)

    def connect(self):
        """Open connection and declare queue."""
        self.connection = self._open_connection()
        self.channel = self.connection.channel()
        # ensure durable queue — the media service publishes to this queue name
        self.channel.queue_declare(queue=self.queue_name, durable=True)
        logger.info(f"✓ Connected to RabbitMQ and declared queue '{self.queue_name}'")

    def disconnect(self):
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

    def _on_message(self, ch, method, properties, body):
        try:
            if isinstance(body, bytes):
                payload = body.decode('utf-8')
            else:
                payload = str(body)

            message = json.loads(payload)
            event_type = message.get('event')

            logger.info(f"📨 Received event: {event_type}")
            logger.debug(f"   Message: {message}")

            if event_type in self.callbacks:
                try:
                    success = self.callbacks[event_type](message)
                except Exception as e:
                    logger.error(f"✗ Callback raised for {event_type}: {e}\n{traceback.format_exc()}")
                    success = False

                if success:
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    logger.info(f"✓ Processed event: {event_type}")
                else:
                    # do not requeue infinitely; let the consumer decide — requeue once
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                    logger.warning(f"✗ Processing failed, message requeued: {event_type}")
            else:
                logger.warning(f"⚠ No callback registered for event: {event_type}; acking message")
                ch.basic_ack(delivery_tag=method.delivery_tag)

        except json.JSONDecodeError as e:
            logger.error(f"✗ JSON decode error: {e}; discarding message")
            try:
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            except Exception:
                pass
        except Exception as e:
            logger.error(f"✗ Unexpected error processing message: {e}\n{traceback.format_exc()}")
            try:
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            except Exception:
                pass

    def start_consuming(self, prefetch_count: int = 1, reconnect_delay: float = 1.0, max_delay: float = 30.0):
        """Start consuming in a resilient loop. This is blocking.

        Will attempt reconnects with exponential backoff when the connection/channel dies.
        Call `stop()` to request a graceful stop.
        """
        self._stopped = False
        delay = reconnect_delay

        while not self._stopped:
            try:
                if not self.connection or not getattr(self.connection, 'is_open', False):
                    logger.info(f"Attempting RabbitMQ connect to {self.rabbitmq_url}")
                    self.connect()

                # configure consumer
                if not self.channel:
                    raise RuntimeError("Channel is not available after connect")

                self.channel.basic_qos(prefetch_count=prefetch_count)
                self.channel.basic_consume(
                    queue=self.queue_name,
                    on_message_callback=self._on_message,
                    auto_ack=False,
                )

                logger.info("=" * 60)
                logger.info("🚀 File Event Consumer Started")
                logger.info(f"   Queue: {self.queue_name}")
                logger.info("   Waiting for events...")
                logger.info("=" * 60)

                # Reset delay after successful start
                delay = reconnect_delay

                # This will block until a network error or stop requested
                self.channel.start_consuming()

            except KeyboardInterrupt:
                logger.info("⏸ Consumer interrupted by user")
                self.stop()
            except Exception as e:
                logger.error(f"✗ Consumer error: {e}\n{traceback.format_exc()}")
                # Ensure connection closed and retry with backoff
                try:
                    self.disconnect()
                except Exception:
                    pass

                if self._stopped:
                    break

                logger.info(f"Reconnecting in {delay:.1f}s...")
                time.sleep(delay)
                delay = min(delay * 2, max_delay)

        # final cleanup
        try:
            self.disconnect()
        except Exception:
            pass

    def stop(self):
        """Request a graceful stop of the consumer."""
        self._stopped = True
        try:
            if self.channel and getattr(self.channel, 'is_open', False):
                try:
                    self.channel.stop_consuming()
                except Exception:
                    pass
        except Exception:
            pass


# ============================================================================
# INTEGRATION EXAMPLE FOR CORE SERVICE
# ============================================================================

def create_file_event_consumer(
    rabbitmq_url: str,
    on_file_uploaded: Callable,
    on_file_deleted: Callable,
    queue_name: str = 'file_events'
) -> FileEventConsumer:
    """
    Factory function to create and configure a file event consumer.
    
    Args:
        rabbitmq_url: RabbitMQ connection URL
        on_file_uploaded: Callback for FILE_UPLOADED event
        on_file_deleted: Callback for FILE_DELETED event
        queue_name: RabbitMQ queue name
    
    Returns:
        Configured FileEventConsumer instance
    
    Example:
    ```python
    # Define callbacks in your service
    def handle_file_uploaded(event: dict) -> bool:
        user_id = event['user_id']
        file_size = event['file_size']
        # Deduct quota logic here
        return True
    
    def handle_file_deleted(event: dict) -> bool:
        user_id = event['user_id']
        file_size = event['file_size']
        # Restore quota logic here
        return True
    
    # Create consumer
    consumer = create_file_event_consumer(
        rabbitmq_url="amqp://guest:guest@localhost:5672/",
        on_file_uploaded=handle_file_uploaded,
        on_file_deleted=handle_file_deleted
    )
    
    # Run in a separate thread/process
    consumer.start_consuming()
    ```
    """
    consumer = FileEventConsumer(rabbitmq_url, queue_name)
    consumer.register_callback('FILE_UPLOADED', on_file_uploaded)
    consumer.register_callback('FILE_DELETED', on_file_deleted)
    return consumer


@contextmanager
def file_event_consumer(rabbitmq_url: str, on_file_uploaded: Callable, on_file_deleted: Callable):
    """
    Context manager for file event consumer.
    
    Example:
    ```python
    with file_event_consumer(
        "amqp://guest:guest@localhost:5672/",
        handle_file_uploaded,
        handle_file_deleted
    ) as consumer:
        consumer.start_consuming()
    ```
    """
    consumer = create_file_event_consumer(rabbitmq_url, on_file_uploaded, on_file_deleted)
    try:
        yield consumer
    finally:
        consumer.disconnect()

