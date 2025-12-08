"""
Application Layer: OAuth Service

Handles OAuth provider integration and user authentication via third-party providers.
This service is provider-agnostic and handles business logic for OAuth flows.
"""

import logging
from typing import Optional, Dict, Any
import httpx

from app.domain.entities import User
from app.domain.interfaces import IUserRepository, IPasswordHasher

logger = logging.getLogger(__name__)


class OAuthService:
    """Service for handling OAuth authentication flows."""

    def __init__(self, user_repository: IUserRepository, password_hasher: IPasswordHasher):
        """
        Initialize OAuth service with repository and password hasher.
        
        Args:
            user_repository: Repository for user data access
            password_hasher: Password hasher for secure password generation
        """
        self.user_repository = user_repository
        self.password_hasher = password_hasher

    async def get_google_userinfo(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Fetch user information from Google using access token.
        
        Args:
            access_token: Google OAuth access token
            
        Returns:
            User info dict from Google or None if failed
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://www.googleapis.com/oauth2/v1/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10.0,
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch Google user info: {e}")
            return None

    def get_or_create_user_from_oauth(
        self,
        email: str,
        name: str,
        oauth_provider: str,
        oauth_sub: str,
    ) -> User:
        """
        Get existing user or create new user from OAuth provider info.
        
        Args:
            email: User email from OAuth provider
            name: User full name from OAuth provider
            oauth_provider: Provider name (e.g., 'google')
            oauth_sub: Subject ID from OAuth provider
            
        Returns:
            User entity (new or existing)
            
        Raises:
            ValueError: If email is not provided or other validation fails
        """
        if not email:
            raise ValueError("Email not provided by OAuth provider")

        # Check if user exists
        existing_user = self.user_repository.get_by_email(email)
        if existing_user:
            logger.info(f"Existing user found for email: {email}")
            return existing_user

        # Create new user from OAuth info
        logger.info(f"Creating new user from {oauth_provider} OAuth: {email}")
        
        # Generate a secure password hash (user won't use password)
        generated_password = self.password_hasher.hash(f"oauth_{oauth_provider}_{oauth_sub}")
        
        # Create new user without ID (will be generated on save)
        user = User(
            id=None,
            email=email,
            full_name=name or email.split("@")[0],  # Fallback to email prefix if no name
            password_hash=generated_password,
            verified=True,  # OAuth emails are verified by provider
        )
        
        return user

    def save_user(self, user: User) -> User:
        """
        Persist user to database.
        
        Args:
            user: User entity to persist
            
        Returns:
            Persisted user with ID from database
        """
        return self.user_repository.save(user)

