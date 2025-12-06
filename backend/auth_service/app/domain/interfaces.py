"""
Domain Layer: Repository Interfaces

These are abstract contracts that define how the application layer
interacts with persistence. The infrastructure layer implements these.
"""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID
from app.domain.entities import User, Session, RecoveryToken


class IUserRepository(ABC):
    """Contract for user persistence operations."""

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by email. Returns None if not found."""
        pass

    @abstractmethod
    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get a user by ID. Returns None if not found."""
        pass

    @abstractmethod
    def save(self, user: User) -> User:
        """Create or update a user. Returns the persisted entity with ID set."""
        pass

    @abstractmethod
    def update(self, user: User) -> User:
        """Update an existing user. Returns the updated entity."""
        pass


class ISessionRepository(ABC):
    """Contract for session persistence operations."""

    @abstractmethod
    def create(self, session: Session) -> Session:
        """Create a new session. Returns the persisted entity with ID set."""
        pass

    @abstractmethod
    def get_by_id(self, session_id: UUID) -> Optional[Session]:
        """Get a session by ID."""
        pass

    @abstractmethod
    def get_active_by_user(self, user_id: UUID) -> Optional[Session]:
        """Get the active session for a user."""
        pass

    @abstractmethod
    def update(self, session: Session) -> Session:
        """Update a session."""
        pass

    @abstractmethod
    def revoke_all_by_user(self, user_id: UUID) -> None:
        """Revoke all sessions for a user."""
        pass


class IRecoveryTokenRepository(ABC):
    """Contract for recovery token persistence operations."""

    @abstractmethod
    def create(self, token: RecoveryToken) -> RecoveryToken:
        """Create a new recovery token."""
        pass

    @abstractmethod
    def get_valid_by_user_and_token(self, user_id: UUID, token: str) -> Optional[RecoveryToken]:
        """Get a valid (unused, not expired) recovery token by user and token."""
        pass

    @abstractmethod
    def mark_as_used(self, token_id: UUID) -> None:
        """Mark a recovery token as used."""
        pass


class IPasswordHasher(ABC):
    """Contract for password hashing operations."""

    @abstractmethod
    def hash(self, password: str) -> str:
        """Hash a password."""
        pass

    @abstractmethod
    def verify(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash."""
        pass


class ITokenGenerator(ABC):
    """Contract for JWT token generation."""

    @abstractmethod
    def create_access_token(self, user_id: UUID) -> str:
        """Generate an access token."""
        pass

    @abstractmethod
    def decode_access_token(self, token: str) -> Optional[dict]:
        """Decode and validate an access token."""
        pass

    @abstractmethod
    def create_refresh_token(self, user_id: UUID) -> tuple[str, str, object]:
        """Create a refresh token. Returns (plaintext, hashed, expiry)."""
        pass

    @abstractmethod
    def verify_refresh_token(self, token: str, stored_hash: str) -> bool:
        """Verify a refresh token."""
        pass
