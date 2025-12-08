"""
Application Layer: Utility Services

Helper services for development and testing.
"""

from typing import Optional
from app.domain.entities import User
from app.domain.interfaces import IUserRepository, IPasswordHasher


class UserUtilService:
    """Utility service for user operations."""

    def __init__(self, user_repo: IUserRepository, password_hasher: IPasswordHasher):
        self.user_repo = user_repo
        self.password_hasher = password_hasher

    def create_test_user(
        self, email: str = "test@example.com", password: str = "password"
    ) -> User:
        """Create a test user if it doesn't already exist.

        Useful for local development.

        Args:
            email: Email of test user
            password: Password for test user

        Returns:
            The created or existing user entity
        """
        # Check if user already exists
        existing = self.user_repo.get_by_email(email)
        if existing:
            return existing

        # Hash password
        hashed_pw = self.password_hasher.hash(password)

        # Create user entity
        new_user = User(
            id=None,
            email=email,
            password_hash=hashed_pw,
            full_name="Test User",
            verified=True,  # Test user is already verified
        )

        # Persist
        return self.user_repo.save(new_user)

    def mark_user_verified(self, email: str) -> User:
        """Mark a user as email-verified.

        Args:
            email: User's email

        Returns:
            Updated user entity

        Raises:
            ValueError: If user not found
        """
        user = self.user_repo.get_by_email(email)
        if not user:
            raise ValueError("User not found")

        user.verified = True
        return self.user_repo.update(user)
