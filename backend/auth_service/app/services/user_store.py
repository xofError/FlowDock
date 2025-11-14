from typing import Optional, Dict
from uuid import UUID, uuid4
from datetime import datetime

from app.utils import security


class InMemoryUser:
    def __init__(self, email: str, password: str, twofa_enabled: bool = False):
        self.id: UUID = uuid4()
        self.email = email
        self.password_hash = security.hash_password(password)
        self.twofa_enabled = twofa_enabled
        self.totp_secret = None
        self.created_at = datetime.utcnow()


_USERS: Dict[str, InMemoryUser] = {}


def create_test_user(email: str = "test@example.com", password: str = "password") -> InMemoryUser:
    user = InMemoryUser(email=email, password=password)
    _USERS[email] = user
    return user


def get_user_by_email(email: str) -> Optional[InMemoryUser]:
    return _USERS.get(email)


# create a default test user
create_test_user()
