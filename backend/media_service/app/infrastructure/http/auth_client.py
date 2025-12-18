"""
HTTP client for communicating with the Auth Service.
Implements IQuotaRepository using direct HTTP calls instead of messaging.
"""

import httpx
import logging
from app.domain.interfaces import IQuotaRepository

logger = logging.getLogger(__name__)


class HttpQuotaRepository(IQuotaRepository):
    """
    Updates user storage quota via HTTP calls to the Auth Service.
    
    This is a synchronous, simpler alternative to RabbitMQ messaging.
    Requests fail fast if the Auth Service is unreachable.
    """

    def __init__(self, auth_service_url: str):
        """
        Initialize the HTTP quota client.
        
        Args:
            auth_service_url: Base URL of the Auth Service (e.g., http://auth_service:8000)
        """
        self.url = auth_service_url

    async def update_usage(self, user_id: str, size_delta: int) -> None:
        """
        Update the user's storage quota in the Auth Service via HTTP.
        
        Args:
            user_id: The user whose quota should be updated
            size_delta: The change in storage (positive for upload, negative for delete)
            
        Note:
            - Does not raise exceptions on failure, only logs them
            - This prevents upload/delete failures from cascade failures in Auth Service
        """
        try:
            async with httpx.AsyncClient() as client:
                # POST to the internal quota endpoint
                response = await client.post(
                    f"{self.url}/internal/quota/update",
                    json={"user_id": user_id, "size_delta": size_delta},
                    timeout=5.0,  # Fail fast if auth service is down
                )
                response.raise_for_status()
                logger.info(f"✅ Updated quota for user {user_id}: {size_delta:+d} bytes")

        except httpx.TimeoutException:
            logger.error(
                f"❌ Timeout updating quota for user {user_id}: "
                f"Auth Service did not respond within 5 seconds"
            )
        except httpx.HTTPError as e:
            logger.error(
                f"❌ Failed to update quota for user {user_id}: HTTP error {e}"
            )
        except Exception as e:
            logger.error(
                f"❌ Unexpected error updating quota for user {user_id}: {str(e)}"
            )
