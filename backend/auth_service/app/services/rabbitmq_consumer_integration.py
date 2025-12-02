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
from .rabbitmq_consumer import create_file_event_consumer

logger = logging.getLogger(__name__)


class StorageQuotaManager:
    """
    Manages user storage quotas in response to file events.
    This is an interface that should be implemented in the Core Service.
    """
    
    @staticmethod
    def deduct_quota(user_id: str, file_size: int) -> bool:
        """
        Deduct storage quota for a user after file upload.
        
        Args:
            user_id: User identifier
            file_size: File size in bytes
        
        Returns:
            True if quota deducted successfully, False otherwise
        """
        # TODO: Implement in Core Service
        # Example:
        # user = get_user(user_id)
        # if user.used_storage + file_size > user.storage_quota:
        #     logger.error(f"Insufficient quota for user {user_id}")
        #     return False
        # user.used_storage += file_size
        # save_user(user)
        # return True
        logger.info(f"[QUOTA] Deducted {file_size} bytes from user {user_id}")
        return True
    
    @staticmethod
    def restore_quota(user_id: str, file_size: int) -> bool:
        """
        Restore storage quota after file deletion.
        
        Args:
            user_id: User identifier
            file_size: File size in bytes
        
        Returns:
            True if quota restored successfully, False otherwise
        """
        # TODO: Implement in Core Service
        # Example:
        # user = get_user(user_id)
        # user.used_storage = max(0, user.used_storage - file_size)
        # save_user(user)
        # return True
        logger.info(f"[QUOTA] Restored {file_size} bytes to user {user_id}")
        return True


class FileEventHandler:
    """Handles file events from the Media Service"""
    
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
            
            if not all([user_id, file_size, file_id]):
                logger.error(f"Invalid FILE_UPLOADED event: {event}")
                return False
            
            logger.info(f"📤 FILE_UPLOADED: user={user_id}, file={file_id}, size={file_size} bytes")
            
            # Deduct quota
            success = StorageQuotaManager.deduct_quota(user_id, file_size)
            
            if success:
                logger.info(f"✓ Quota deducted for user {user_id}")
            else:
                logger.error(f"✗ Failed to deduct quota for user {user_id}")
            
            return success
        
        except Exception as e:
            logger.error(f"✗ Error handling FILE_UPLOADED event: {e}")
            return False
    
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
            
            if not all([user_id, file_size, file_id]):
                logger.error(f"Invalid FILE_DELETED event: {event}")
                return False
            
            logger.info(f"🗑️ FILE_DELETED: user={user_id}, file={file_id}, size={file_size} bytes")
            
            # Restore quota
            success = StorageQuotaManager.restore_quota(user_id, file_size)
            
            if success:
                logger.info(f"✓ Quota restored for user {user_id}")
            else:
                logger.error(f"✗ Failed to restore quota for user {user_id}")
            
            return success
        
        except Exception as e:
            logger.error(f"✗ Error handling FILE_DELETED event: {e}")
            return False


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
