"""
Infrastructure Layer: Repository Implementations

These concrete classes implement the domain interfaces using SQLAlchemy.
They handle the conversion between domain entities and database models.
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.domain.entities import User, Session as SessionEntity, RecoveryToken
from app.domain.interfaces import IUserRepository, ISessionRepository, IRecoveryTokenRepository
from app.infrastructure.database.models import UserModel, SessionModel, RecoveryTokenModel


class PostgresUserRepository(IUserRepository):
    """PostgreSQL implementation of user repository."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by email."""
        db_user = self.db.query(UserModel).filter(UserModel.email == email).first()
        return self._to_entity(db_user) if db_user else None

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get a user by ID."""
        db_user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        return self._to_entity(db_user) if db_user else None

    def save(self, user: User) -> User:
        """Create a new user."""
        db_user = UserModel(
            email=user.email,
            password_hash=user.password_hash,
            full_name=user.full_name,
            telegram_id=user.telegram_id,
            phone_number=user.phone_number,
            verified=user.verified,
            twofa_enabled=user.twofa_enabled,
            totp_secret=user.totp_secret,
            recovery_phrase_hash=user.recovery_phrase_hash,
            storage_used=user.storage_used,
            storage_limit=user.storage_limit,
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return self._to_entity(db_user)

    def update(self, user: User) -> User:
        """Update an existing user."""
        db_user = self.db.query(UserModel).filter(UserModel.id == user.id).first()
        if not db_user:
            raise ValueError(f"User with id {user.id} not found")

        # Update fields
        db_user.email = user.email
        db_user.password_hash = user.password_hash
        db_user.full_name = user.full_name
        db_user.telegram_id = user.telegram_id
        db_user.phone_number = user.phone_number
        db_user.verified = user.verified
        db_user.twofa_enabled = user.twofa_enabled
        db_user.totp_secret = user.totp_secret
        db_user.recovery_phrase_hash = user.recovery_phrase_hash
        db_user.storage_used = user.storage_used
        db_user.storage_limit = user.storage_limit
        db_user.last_login_ip = user.last_login_ip
        db_user.last_login_at = user.last_login_at

        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return self._to_entity(db_user)

    @staticmethod
    def _to_entity(db_user: UserModel) -> User:
        """Convert DB model to domain entity."""
        return User(
            id=db_user.id,
            email=db_user.email,
            password_hash=db_user.password_hash,
            full_name=db_user.full_name,
            telegram_id=db_user.telegram_id,
            phone_number=db_user.phone_number,
            verified=db_user.verified,
            twofa_enabled=db_user.twofa_enabled,
            totp_secret=db_user.totp_secret,
            recovery_phrase_hash=db_user.recovery_phrase_hash,
            storage_used=db_user.storage_used,
            storage_limit=db_user.storage_limit,
            created_at=db_user.created_at,
            last_login_ip=db_user.last_login_ip,
            last_login_at=db_user.last_login_at,
        )


class PostgresSessionRepository(ISessionRepository):
    """PostgreSQL implementation of session repository."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, session: SessionEntity) -> SessionEntity:
        """Create a new session."""
        db_session = SessionModel(
            user_id=session.user_id,
            refresh_token_hash=session.refresh_token_hash,
            device_info=session.device_info,
            browser_name=session.browser_name,
            ip_address=session.ip_address,
            expires_at=session.expires_at,
            active=session.active,
        )
        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)
        return self._to_entity(db_session)

    def get_by_id(self, session_id: UUID) -> Optional[SessionEntity]:
        """Get a session by ID."""
        db_session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
        return self._to_entity(db_session) if db_session else None

    def get_active_by_user(self, user_id: UUID) -> Optional[SessionEntity]:
        """Get the active session for a user."""
        db_session = (
            self.db.query(SessionModel)
            .filter(SessionModel.user_id == user_id, SessionModel.active == True)
            .order_by(SessionModel.created_at.desc())
            .first()
        )
        return self._to_entity(db_session) if db_session else None

    def update(self, session: SessionEntity) -> SessionEntity:
        """Update a session."""
        db_session = self.db.query(SessionModel).filter(SessionModel.id == session.id).first()
        if not db_session:
            raise ValueError(f"Session with id {session.id} not found")

        db_session.user_id = session.user_id
        db_session.refresh_token_hash = session.refresh_token_hash
        db_session.device_info = session.device_info
        db_session.browser_name = session.browser_name
        db_session.ip_address = session.ip_address
        db_session.expires_at = session.expires_at
        db_session.active = session.active

        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)
        return self._to_entity(db_session)

    def revoke_all_by_user(self, user_id: UUID) -> None:
        """Revoke all sessions for a user."""
        self.db.query(SessionModel).filter(
            SessionModel.user_id == user_id,
            SessionModel.active == True
        ).update({"active": False})
        self.db.commit()

    @staticmethod
    def _to_entity(db_session: SessionModel) -> SessionEntity:
        """Convert DB model to domain entity."""
        return SessionEntity(
            id=db_session.id,
            user_id=db_session.user_id,
            refresh_token_hash=db_session.refresh_token_hash,
            device_info=db_session.device_info,
            browser_name=db_session.browser_name,
            ip_address=db_session.ip_address,
            created_at=db_session.created_at,
            expires_at=db_session.expires_at,
            active=db_session.active,
        )


class PostgresRecoveryTokenRepository(IRecoveryTokenRepository):
    """PostgreSQL implementation of recovery token repository."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, token: RecoveryToken) -> RecoveryToken:
        """Create a new recovery token."""
        db_token = RecoveryTokenModel(
            user_id=token.user_id,
            token=token.token,
            method=token.method,
            expires_at=token.expires_at,
            used=token.used,
        )
        self.db.add(db_token)
        self.db.commit()
        self.db.refresh(db_token)
        return self._to_entity(db_token)

    def get_valid_by_user_and_token(self, user_id: UUID, token: str) -> Optional[RecoveryToken]:
        """Get a valid (unused, not expired) recovery token."""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        db_token = (
            self.db.query(RecoveryTokenModel)
            .filter(
                RecoveryTokenModel.user_id == user_id,
                RecoveryTokenModel.token == token,
                RecoveryTokenModel.used == False,
                RecoveryTokenModel.expires_at > now,
            )
            .first()
        )
        return self._to_entity(db_token) if db_token else None

    def mark_as_used(self, token_id: UUID) -> None:
        """Mark a recovery token as used."""
        db_token = self.db.query(RecoveryTokenModel).filter(RecoveryTokenModel.id == token_id).first()
        if db_token:
            db_token.used = True
            self.db.add(db_token)
            self.db.commit()

    @staticmethod
    def _to_entity(db_token: RecoveryTokenModel) -> RecoveryToken:
        """Convert DB model to domain entity."""
        return RecoveryToken(
            id=db_token.id,
            user_id=db_token.user_id,
            token=db_token.token,
            method=db_token.method,
            created_at=db_token.created_at,
            expires_at=db_token.expires_at,
            used=db_token.used,
        )
