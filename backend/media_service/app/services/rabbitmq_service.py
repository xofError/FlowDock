"""Compatibility shim for legacy synchronous callers.

This module used to contain a synchronous pika-based publisher. During the
clean-architecture migration the canonical async publisher moved to
`app.infrastructure.messaging.rabbitmq_publisher`. To avoid breaking
existing imports that call `publish_file_event(...)`, we keep a tiny shim
that schedules the async publisher on the event loop.
"""

import asyncio
import logging
from typing import Optional

from app.infrastructure.messaging.rabbitmq_publisher import RabbitMQEventPublisher

logger = logging.getLogger(__name__)

# Single shared async publisher instance
_publisher: Optional[RabbitMQEventPublisher] = RabbitMQEventPublisher()


async def connect_rabbitmq():
    """Awaitable connection helper for startup."""
    if _publisher:
        await _publisher.connect()


async def close_rabbitmq():
    """Awaitable close helper for shutdown."""
    if _publisher:
        await _publisher.close()


def _schedule(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop: create a background loop in a new thread
        # fallback: run in a new loop so we don't block callers
        def _run_in_thread():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            new_loop.run_until_complete(coro)
            new_loop.close()

        import threading

        t = threading.Thread(target=_run_in_thread, daemon=True)
        t.start()
        return

    # If event loop running, schedule task
    loop.create_task(coro)


def publish_file_event(event_type: str, user_id: str, file_id: str, file_size: int) -> bool:
    """Schedule an async publish and return True if scheduled.

    This keeps the old synchronous API while moving the real work to the
    async publisher. Callers should switch to the new async publisher when
    possible.
    """
    if not _publisher:
        logger.error("No RabbitMQ publisher available")
        return False

    if event_type == "FILE_UPLOADED":
        coro = _publisher.publish_upload(user_id=user_id, file_id=file_id, size=file_size)
    elif event_type == "FILE_DELETED":
        coro = _publisher.publish_delete(user_id=user_id, file_id=file_id, file_size=file_size)
    elif event_type == "FILE_DOWNLOADED":
        coro = _publisher.publish_download(user_id=user_id, file_id=file_id)
    else:
        logger.warning("Unknown event type for publish_file_event: %s", event_type)
        return False

    _schedule(coro)
    return True
