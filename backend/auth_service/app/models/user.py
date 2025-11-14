# Example user model placeholder

from dataclasses import dataclass


@dataclass
class User:
    id: int
    username: str
    email: str
    hashed_password: str
