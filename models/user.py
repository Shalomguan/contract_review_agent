from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class User:
    """Authenticated application user."""

    user_id: str
    username: str
    password_hash: str
    created_at: datetime
