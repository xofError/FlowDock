"""
RabbitMQ message publishing for file events
"""

import json
import logging
import pika
from app.core.config import settings

logger = logging.getLogger(__name__)

# Global channel
rabbit_channel = None


async def connect_rabbitmq():
    """Connect to RabbitMQ on startup"""
    global rabbit_channel
    
    try:
        connection = pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))
        rabbit_channel = connection.channel()
        rabbit_channel.queue_declare(queue=settings.RABBITMQ_QUEUE, durable=True)
        logger.info(f"✓ Connected to RabbitMQ, queue '{settings.RABBITMQ_QUEUE}' declared")
    except Exception as e:
        logger.error(f"✗ Failed to connect to RabbitMQ: {e}")
        raise


async def close_rabbitmq():
    """Close RabbitMQ connection on shutdown"""
    global rabbit_channel
    
    if rabbit_channel and rabbit_channel.connection:
        rabbit_channel.connection.close()
        logger.info("✓ Closed RabbitMQ connection")


def publish_file_event(event_type: str, user_id: str, file_id: str, file_size: int) -> bool:
    """
    Publish file event to RabbitMQ for Core Service consumption
    
    Args:
        event_type: Event type (FILE_UPLOADED, FILE_DELETED)
        user_id: User ID
        file_id: File ObjectId
        file_size: File size in bytes
    
    Returns:
        True if published successfully
    """
    try:
        if not rabbit_channel:
            logger.error("RabbitMQ not connected")
            return False
        
        message = {
            "event": event_type,
            "user_id": user_id,
            "file_id": file_id,
            "file_size": file_size
        }
        
        rabbit_channel.basic_publish(
            exchange='',
            routing_key=settings.RABBITMQ_QUEUE,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            )
        )
        
        logger.info(f"✓ Published {event_type}: user={user_id}, file={file_id}, size={file_size}")
        return True
    
    except Exception as e:
        logger.error(f"✗ Failed to publish event: {e}")
        return False
