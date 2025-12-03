"""
Example: Core Service Integration with RabbitMQ Consumer
This module demonstrates how to integrate file event handling into the Core Service.

To integrate:
1. Add this module to your Core Service
2. Call start_file_event_consumer() during service startup
3. Implement quota management in your Core Service database layer
"""

import logging
import os
from threading import Thread
from typing import Optional

from app.database import SessionLocal
from app.models.user import User
from .rabbitmq_consumer import create_file_event_consumer

logger = logging.getLogger(__name__)

# Track failed message attempts to prevent infinite requeue loops
FAILED_MESSAGES = {}
MAX_RETRIES = 3


class StorageQuotaManager:
    """
    Manages user storage quotas in response to file events.
    This is an interface that should be implemented in the Core Service.
    """
    
    @staticmethod
    def deduct_quota(user_id: str, file_size: int) -> bool:
        """Deduct storage quota for a user"""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.error(f"User not found: {user_id}")
                return False
            
            # Check quota
            if user.storage_used + file_size > user.storage_limit:
                logger.error(f"Quota exceeded for user {user_id}: {user.storage_used} + {file_size} > {user.storage_limit}")
                return False
            
            # Deduct quota
            user.storage_used += file_size
            db.commit()
            logger.info(f"✓ Deducted {file_size} bytes from {user_id}; new total: {user.storage_used} / {user.storage_limit}")
            return True
        
        except Exception as e:
            logger.error(f"Database error: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    @staticmethod
    def restore_quota(user_id: str, file_size: int) -> bool:
        """Restore storage quota after file deletion"""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.storage_used = max(0, user.storage_used - file_size)
                db.commit()
                logger.info(f"✓ Restored {file_size} bytes to {user_id}")
                return True
            return False
        
        except Exception as e:
            logger.error(f"Database error: {e}")
            db.rollback()
            return False
        finally:
            db.close()


class FileEventHandler:
    """Handles file events from the Media Service"""
    
    @staticmethod
    def _should_retry(message_id: str) -> bool:
        """Check if a message should be retried or permanently rejected"""
        attempt = FAILED_MESSAGES.get(message_id, 0)
        if attempt >= MAX_RETRIES:
            logger.error(f"Message {message_id} failed {MAX_RETRIES} times, permanently rejecting")
            del FAILED_MESSAGES[message_id]
            return False
        
        FAILED_MESSAGES[message_id] = attempt + 1
        logger.warning(f"Message {message_id} failed, attempt {FAILED_MESSAGES[message_id]}/{MAX_RETRIES}")
        return True
    
    @staticmethod
    def on_file_uploaded(event: dict) -> bool:
        """
        Handle FILE_UPLOADED event from Media Service.
        Deducts storage quota from the user.
        
        Event structure:
        {
            "event": "FILE_UPLOADED",
            "user_id": "user123",
            "file_id": "ObjectId",
            "file_size": 1024000
        }
        """
        try:
            user_id = event.get('user_id')
            file_size = event.get('file_size')
            file_id = event.get('file_id')
            message_id = f"{file_id}_{user_id}"
            
            if not all([user_id, file_size, file_id]):
                logger.error(f"Invalid FILE_UPLOADED event: {event}")
                return False
            
            logger.info(f"📤 FILE_UPLOADED: user={user_id}, file={file_id}, size={file_size} bytes")
            
            # Deduct quota
            success = StorageQuotaManager.deduct_quota(user_id, file_size)
            
            if success:
                logger.info(f"✓ Quota deducted for user {user_id}")
                # Clear from failed attempts on success
                FAILED_MESSAGES.pop(message_id, None)
            else:
                # Retry logic for transient failures
                if FileEventHandler._should_retry(message_id):
                    return False  # Requeue
                else:
                    logger.error(f"✗ Permanently rejecting FILE_UPLOADED for user {user_id}")
                    return True  # Ack and discard
            
            return success
        
        except Exception as e:
            logger.error(f"✗ Error handling FILE_UPLOADED event: {e}")
            message_id = f"{event.get('file_id')}_{event.get('user_id')}"
            if FileEventHandler._should_retry(message_id):
                return False  # Requeue
            return True  # Give up and ack
    
    @staticmethod
    def on_file_deleted(event: dict) -> bool:
        """
        Handle FILE_DELETED event from Media Service.
        Restores storage quota to the user.
        
        Event structure:
        {
            "event": "FILE_DELETED",
            "user_id": "user123",
            "file_id": "ObjectId",
            "file_size": 1024000
        }
        """
        try:
            user_id = event.get('user_id')
            file_size = event.get('file_size')
            file_id = event.get('file_id')
            message_id = f"{file_id}_{user_id}"
            
            if not all([user_id, file_size, file_id]):
                logger.error(f"Invalid FILE_DELETED event: {event}")
                return False
            
            logger.info(f"🗑️ FILE_DELETED: user={user_id}, file={file_id}, size={file_size} bytes")
            
            # Restore quota
            success = StorageQuotaManager.restore_quota(user_id, file_size)
            
            if success:
                logger.info(f"✓ Quota restored for user {user_id}")
                # Clear from failed attempts on success
                FAILED_MESSAGES.pop(message_id, None)
            else:
                # Retry logic for transient failures
                if FileEventHandler._should_retry(message_id):
                    return False  # Requeue
                else:
                    logger.error(f"✗ Permanently rejecting FILE_DELETED for user {user_id}")
                    return True  # Ack and discard
            
            return success
        
        except Exception as e:
            logger.error(f"✗ Error handling FILE_DELETED event: {e}")
            message_id = f"{event.get('file_id')}_{event.get('user_id')}"
            if FileEventHandler._should_retry(message_id):
                return False  # Requeue
            return True  # Give up and ack


def start_file_event_consumer_background():
    """
    Start the file event consumer in a background thread.
    
    Call this during Core Service initialization.
    
    Example in main.py:
    ```python
    from app.services.rabbitmq_consumer_integration import start_file_event_consumer_background
    
    app = FastAPI()
    
    @app.on_event("startup")
    async def startup():
        # ... other startup code ...
        start_file_event_consumer_background()
    ```
    """
    try:
        rabbitmq_url = os.getenv(
            "RABBITMQ_URL",
            "amqp://guest:guest@rabbitmq:5672/"
        )
        
        consumer = create_file_event_consumer(
            rabbitmq_url=rabbitmq_url,
            on_file_uploaded=FileEventHandler.on_file_uploaded,
            on_file_deleted=FileEventHandler.on_file_deleted
        )
        
        # Start consumer in background thread
        thread = Thread(target=consumer.start_consuming, daemon=True)
        thread.start()
        
        logger.info("✓ File event consumer started in background thread")
        
    except Exception as e:
        logger.error(f"✗ Failed to start file event consumer: {e}")
        # Don't raise - service should continue even if consumer fails
        logger.warning("⚠ Core Service will continue without file event consumer")
