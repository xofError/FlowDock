"""
RabbitMQ Consumer for File Events
Listens for messages from Media Service and updates user storage quotas.
This module should be integrated into the Core Service.
"""

import pika
import json
import logging
from typing import Callable, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class FileEventConsumer:
    """
    Consumes file events from RabbitMQ and executes callbacks.
    
    Handles:
    - FILE_UPLOADED: Deduct storage quota
    - FILE_DELETED: Restore storage quota
    """
    
    def __init__(self, rabbitmq_url: str, queue_name: str = 'file_events'):
        """
        Initialize the consumer.
        
        Args:
            rabbitmq_url: RabbitMQ connection URL (e.g., amqp://guest:guest@localhost:5672/)
            queue_name: RabbitMQ queue name to consume from
        """
        self.rabbitmq_url = rabbitmq_url
        self.queue_name = queue_name
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.adapters.blocking_connection.BlockingChannel] = None
        self.callbacks = {}
    
    def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            self.connection = pika.BlockingConnection(pika.URLParameters(self.rabbitmq_url))
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=self.queue_name, durable=True)
            logger.info(f"✓ Connected to RabbitMQ, queue '{self.queue_name}' declared")
        except Exception as e:
            logger.error(f"✗ Failed to connect to RabbitMQ: {e}")
            raise
    
    def disconnect(self):
        """Close connection to RabbitMQ"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("✓ Disconnected from RabbitMQ")
    
    def register_callback(self, event_type: str, callback: Callable):
        """
        Register a callback for a specific event type.
        
        Args:
            event_type: Event type (e.g., 'FILE_UPLOADED', 'FILE_DELETED')
            callback: Async callback function(event_data) -> bool (True if successful)
        """
        self.callbacks[event_type] = callback
        logger.info(f"✓ Registered callback for event: {event_type}")
    
    def _on_message(self, ch, method, properties, body):
        """
        Message callback handler.
        
        Args:
            ch: Channel
            method: Method frame
            properties: Message properties
            body: Message body (JSON)
        """
        try:
            # Parse message
            message = json.loads(body.decode('utf-8'))
            event_type = message.get('event')
            
            logger.info(f"📨 Received event: {event_type}")
            logger.debug(f"   Message: {message}")
            
            # Execute callback if registered
            if event_type in self.callbacks:
                callback = self.callbacks[event_type]
                success = callback(message)
                
                if success:
                    # Acknowledge message
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    logger.info(f"✓ Processed event: {event_type}")
                else:
                    # Requeue message on failure
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                    logger.warning(f"✗ Event processing failed, requeued: {event_type}")
            else:
                logger.warning(f"⚠ No callback registered for event: {event_type}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
        
        except json.JSONDecodeError as e:
            logger.error(f"✗ Failed to parse message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logger.error(f"✗ Error processing message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def start_consuming(self, prefetch_count: int = 1):
        """
        Start consuming messages from the queue.
        This is a blocking call.
        
        Args:
            prefetch_count: Number of messages to prefetch from the queue
        """
        if not self.connection:
            self.connect()
        
        try:
            self.channel.basic_qos(prefetch_count=prefetch_count)
            self.channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=self._on_message,
                auto_ack=False
            )
            
            logger.info("=" * 70)
            logger.info("🚀 File Event Consumer Started")
            logger.info(f"   Queue: {self.queue_name}")
            logger.info(f"   Waiting for events...")
            logger.info("=" * 70)
            
            self.channel.start_consuming()
        
        except KeyboardInterrupt:
            logger.info("⏸ Consumer interrupted by user")
            self.channel.stop_consuming()
        except Exception as e:
            logger.error(f"✗ Consumer error: {e}")
            raise
        finally:
            self.disconnect()


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
