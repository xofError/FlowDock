"""
Application Layer: Storage Quota Service

Manages user storage quotas in response to file events from RabbitMQ.
"""

from app.domain.entities import User
from app.domain.interfaces import IUserRepository


class StorageQuotaService:
    """Service for managing user storage quotas."""

    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    def deduct_quota(self, user_id, file_size: int) -> bool:
        """
        Deduct storage quota for a user after file upload.

        Args:
            user_id: User UUID
            file_size: Size of uploaded file in bytes

        Returns:
            True if quota was deducted, False if would exceed limit
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return False

        # Check if deduction would exceed limit
        if user.storage_used + file_size > user.storage_limit:
            return False

        # Deduct quota
        user.storage_used += file_size
        self.user_repo.update(user)
        return True

    def add_quota(self, user_id, file_size: int) -> bool:
        """
        Add back storage quota when file is deleted.

        Args:
            user_id: User UUID
            file_size: Size of deleted file in bytes

        Returns:
            True if quota was added back, False if user not found
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return False

        # Add back quota (but don't exceed limit)
        user.storage_used = max(0, user.storage_used - file_size)
        self.user_repo.update(user)
        return True

    def get_quota_info(self, user_id) -> dict:
        """
        Get storage quota information for a user.

        Args:
            user_id: User UUID

        Returns:
            Dict with storage_used, storage_limit, remaining
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return None

        return {
            "storage_used": user.storage_used,
            "storage_limit": user.storage_limit,
            "storage_remaining": user.storage_limit - user.storage_used,
            "usage_percentage": (user.storage_used / user.storage_limit * 100) if user.storage_limit > 0 else 0,
        }
