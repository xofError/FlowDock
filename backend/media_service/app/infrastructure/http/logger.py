"""
Infrastructure Layer: HTTP-based Activity Logging and Quota Management

These implementations use HTTP to communicate with the Auth Service
for logging activities and updating storage quotas.
"""

import httpx
import logging
from typing import Dict, Any, Optional

from app.domain.interfaces import IActivityLogger, IQuotaRepository

logger = logging.getLogger(__name__)


class HttpActivityLogger(IActivityLogger):
    """
    HTTP implementation of activity logger.
    Sends logs to Auth Service via HTTP POST.
    """

    def __init__(self, auth_service_url: str, timeout: float = 2.0):
        """
        Initialize the HTTP activity logger.

        Args:
            auth_service_url: Base URL of Auth Service (e.g., "http://auth_service:8000")
            timeout: HTTP request timeout in seconds (default 2.0)
        """
        self.auth_service_url = auth_service_url.rstrip("/")
        self.timeout = timeout

    async def log_activity(
        self,
        user_id: str,
        action: str,
        details: Dict[str, Any] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """
        Log a user activity by sending an HTTP request to Auth Service.

        This is non-blocking - if logging fails, it won't crash the app.
        Exceptions are logged but not raised.

        Args:
            user_id: The user who performed the action
            action: Action type (e.g., "FILE_UPLOAD", "FILE_DELETE")
            details: Optional context data (filename, size, etc.)
            ip_address: Optional client IP address
        """
        async with httpx.AsyncClient() as client:
            try:
                payload = {
                    "user_id": user_id,
                    "action": action,
                    "details": details or {},
                    "ip_address": ip_address,
                }

                response = await client.post(
                    f"{self.auth_service_url}/logs/internal",
                    json=payload,
                    timeout=self.timeout,
                )

                if response.status_code == 201:
                    logger.debug(f"✅ Activity logged: {action} for user {user_id}")
                else:
                    logger.warning(
                        f"⚠️ Activity Log returned {response.status_code}: {response.text}"
                    )
            except httpx.TimeoutException:
                logger.warning(f"⏱️ Activity logging timeout for action: {action}")
            except httpx.RequestError as e:
                logger.error(f"❌ Failed to send Activity Log: {str(e)}")
            except Exception as e:
                # Catch all other exceptions to ensure logging failures don't crash the app
                logger.error(f"❌ Unexpected error during activity logging: {str(e)}")


class HttpQuotaRepository(IQuotaRepository):
    """
    HTTP implementation of quota repository.
    Updates storage quota in Auth Service via HTTP POST.
    """

    def __init__(self, auth_service_url: str, timeout: float = 5.0):
        """
        Initialize the HTTP quota repository.

        Args:
            auth_service_url: Base URL of Auth Service (e.g., "http://auth_service:8000")
            timeout: HTTP request timeout in seconds (default 5.0)
        """
        self.auth_service_url = auth_service_url.rstrip("/")
        self.timeout = timeout

    async def update_usage(self, user_id: str, size_delta: int) -> None:
        """
        Update the user's storage quota in Auth Service.

        This is non-blocking - if the update fails, it logs the error but doesn't crash.

        Args:
            user_id: The user whose quota should be updated
            size_delta: The change in storage (positive for upload, negative for delete)
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.auth_service_url}/users/internal/quota/update",
                    json={"user_id": user_id, "size_delta": size_delta},
                    timeout=self.timeout,
                )

                if response.status_code == 200:
                    logger.debug(f"✅ Updated quota for user {user_id}: {size_delta} bytes")
                else:
                    logger.warning(
                        f"⚠️ Quota update returned {response.status_code}: {response.text}"
                    )
            except httpx.TimeoutException:
                logger.warning(f"⏱️ Quota update timeout for user: {user_id}")
            except httpx.RequestError as e:
                logger.error(f"❌ Failed to update quota via HTTP: {str(e)}")
            except Exception as e:
                # Catch all other exceptions to ensure quota failures don't crash the app
                logger.error(f"❌ Unexpected error during quota update: {str(e)}")
