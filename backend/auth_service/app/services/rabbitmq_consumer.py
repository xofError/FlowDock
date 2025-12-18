"""
Simple RabbitMQ consumer for file events.

Listens to `file_events` queue and invokes StorageQuotaService to update
`storage_used` on FILE_UPLOADED / FILE_DELETED events.

This runs in a background thread using pika BlockingConnection so it
doesn't interfere with FastAPI event loop.
"""
import json
import logging
import threading
import pika
import time
from typing import Optional

from app.core.config import settings
from app.infrastructure.database.repositories import PostgresUserRepository
from app.application.quota_service import StorageQuotaService
from app.database import SessionLocal

logger = logging.getLogger(__name__)


class RabbitMQConsumer:
    def __init__(self, rabbitmq_url: str, queue_name: str = "file_events"):
        self.url = rabbitmq_url
        self.queue = queue_name
        self._connection: Optional[pika.BlockingConnection] = None
        self._channel = None
        self._thread: Optional[threading.Thread] = None
        self._stopping = threading.Event()

    def _connect(self) -> bool:
        try:
            params = pika.URLParameters(self.url)
            params.heartbeat = 60
            self._connection = pika.BlockingConnection(params)
            self._channel = self._connection.channel()
            
            # Declare queue
            self._channel.queue_declare(queue=self.queue, durable=True)
            logger.info(f"✓ Declared queue '{self.queue}'")
            
            # Bind queue to exchange with routing key
            # The publisher publishes to 'flowdock.events' exchange with routing_key 'file_events'
            exchange_name = "flowdock.events"
            self._channel.exchange_declare(exchange=exchange_name, exchange_type="topic", durable=True)
            logger.info(f"✓ Declared exchange '{exchange_name}'")
            
            self._channel.queue_bind(exchange=exchange_name, queue=self.queue, routing_key="file_events")
            logger.info(f"✓ Bound queue '{self.queue}' to exchange '{exchange_name}' with routing_key 'file_events'")
            
            logger.info("✓ RabbitMQ consumer connected and ready")
            return True
        except Exception as e:
            logger.error(f"✗ RabbitMQ consumer connect failed: {e}")
            self._connection = None
            self._channel = None
            return False

    def _process_message(self, ch, method, properties, body):
        try:
            logger.debug(f"Raw message received: {body}")
            payload = json.loads(body)
            logger.debug(f"Parsed payload: {payload}")
            
            event = payload.get("event") or payload.get("event_type") or payload.get("type")
            user_id_raw = payload.get("user_id")
            file_size = int(payload.get("file_size", 0))

            logger.info(f"📨 Processing: event={event}, user_id={user_id_raw}, size={file_size}")

            # Normalize user_id to UUID instance if possible (repositories expect UUID)
            import uuid
            user_id = None
            if user_id_raw:
                try:
                    user_id = uuid.UUID(str(user_id_raw))
                except Exception:
                    logger.warning(f"Invalid user_id in message, passing raw value: {user_id_raw}")
                    user_id = user_id_raw

            # Create repo+service per message to ensure new DB session
            db = SessionLocal()
            try:
                user_repo = PostgresUserRepository(db)
                quota = StorageQuotaService(user_repo)

                if event == "FILE_UPLOADED":
                    logger.info(f"💾 FILE_UPLOADED: deducting {file_size} bytes from user {user_id}")
                    result = quota.deduct_quota(user_id, file_size)
                    logger.info(f"✓ Deduction result: {result}")
                elif event == "FILE_DELETED":
                    logger.info(f"🗑️  FILE_DELETED: adding back {file_size} bytes to user {user_id}")
                    result = quota.add_quota(user_id, file_size)
                    logger.info(f"✓ Addition result: {result}")
                else:
                    logger.warning(f"⚠️  Ignoring unknown event type: {event}")
            except Exception as db_error:
                logger.error(f"✗ Database operation failed: {db_error}", exc_info=True)
            finally:
                db.close()

            # Acknowledge message
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"✓ Message acknowledged")

        except Exception as e:
            logger.error(f"Error processing rabbitmq message: {e}", exc_info=True)
            # On error, reject and requeue (so it can be retried)
            try:
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            except Exception:
                pass

    def _run(self):
        # Connect with retries
        backoff = 1.0
        while not self._stopping.is_set():
            if not self._connect():
                time.sleep(backoff)
                backoff = min(backoff * 2, 30)
                continue

            try:
                # Start consuming - this will block until connection closed
                self._channel.basic_qos(prefetch_count=1)
                self._channel.basic_consume(queue=self.queue, on_message_callback=self._process_message)
                logger.info("✓ RabbitMQ consumer started consuming")
                self._channel.start_consuming()
            except Exception as e:
                logger.error(f"RabbitMQ consumer error: {e}")
                try:
                    if self._connection:
                        self._connection.close()
                except Exception:
                    pass
                self._connection = None
                self._channel = None
                # Short wait then reconnect
                time.sleep(2)

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stopping.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stopping.set()
        try:
            if self._channel:
                try:
                    self._channel.stop_consuming()
                except Exception:
                    pass
            if self._connection:
                try:
                    self._connection.close()
                except Exception:
                    pass
        finally:
            self._channel = None
            self._connection = None


# Global consumer instance
_consumer: Optional[RabbitMQConsumer] = None


def start_consumer():
    global _consumer
    if _consumer:
        return
    _consumer = RabbitMQConsumer(settings.RABBITMQ_URL, settings.RABBITMQ_QUEUE)
    _consumer.start()


def stop_consumer():
    global _consumer
    if not _consumer:
        return
    _consumer.stop()
    _consumer = None
