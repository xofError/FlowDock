"""
Async RabbitMQ publisher using aio_pika.

This implements the IEventPublisher interface and publishes events to a
durable topic exchange. The publisher will connect on demand and retry
connecting if necessary.
"""

import json
import logging
import asyncio
from typing import Optional

import aio_pika

from app.core.config import settings
from app.domain.interfaces import IEventPublisher

logger = logging.getLogger(__name__)


class RabbitMQEventPublisher(IEventPublisher):
    def __init__(self):
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.RobustChannel] = None
        self.exchange_name = "flowdock.events"
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        """Connect to RabbitMQ and declare exchange."""
        if self.channel and not self.channel.is_closed:
            return

        async with self._lock:
            if self.channel and not self.channel.is_closed:
                return
            try:
                self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
                self.channel = await self.connection.channel()
                await self.channel.set_qos(prefetch_count=10)
                await self.channel.declare_exchange(self.exchange_name, aio_pika.ExchangeType.TOPIC, durable=True)
                logger.info("✓ Connected to RabbitMQ exchange %s", self.exchange_name)
            except Exception as e:
                logger.error("✗ Failed to connect to RabbitMQ: %s", e)
                # leave connection as None so subsequent publish attempts try again

    async def _publish(self, routing_key: str, payload: dict) -> None:
        if not self.channel or self.channel.is_closed:
            await self.connect()
        if not self.channel:
            logger.error("No RabbitMQ channel available to publish message")
            return

        try:
            exchange = await self.channel.get_exchange(self.exchange_name)
            message = aio_pika.Message(body=json.dumps(payload).encode(), delivery_mode=aio_pika.DeliveryMode.PERSISTENT)
            await exchange.publish(message, routing_key=routing_key)
            logger.info("Published event %s -> %s", payload.get("event"), routing_key)
        except Exception as e:
            logger.error("Failed to publish RabbitMQ message: %s", e)

    async def publish_upload(self, user_id: str, file_id: str, size: int) -> None:
        payload = {"event": "FILE_UPLOADED", "user_id": user_id, "file_id": file_id, "file_size": size}
        await self._publish("file_events", payload)

    async def publish_delete(self, user_id: str, file_id: str, file_size: int) -> None:
        payload = {"event": "FILE_DELETED", "user_id": user_id, "file_id": file_id, "file_size": file_size}
        await self._publish("file_events", payload)

    async def publish_download(self, user_id: str, file_id: str) -> None:
        payload = {"event": "FILE_DOWNLOADED", "user_id": user_id, "file_id": file_id, "file_size": 0}
        await self._publish("file_events", payload)

    async def close(self) -> None:
        try:
            if self.channel and not self.channel.is_closed:
                await self.channel.close()
            if self.connection and not self.connection.is_closed:
                await self.connection.close()
        except Exception as e:
            logger.warning("Error closing RabbitMQ connection: %s", e)
