from typing import Dict, Optional
from datetime import datetime


_TOKENS: Dict[str, Dict] = {}


def store_refresh_token(hashed: str, user_email: str, expiry: datetime) -> None:
    _TOKENS[hashed] = {
        "user_email": user_email,
        "expiry": expiry,
    }


def get_refresh_token(hashed: str) -> Optional[Dict]:
    return _TOKENS.get(hashed)


def revoke_refresh_token(hashed: str) -> None:
    _TOKENS.pop(hashed, None)
