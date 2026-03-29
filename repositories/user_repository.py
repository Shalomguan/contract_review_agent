from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from models.user import User
from services.storage.sqlite_db import SQLiteDatabase


class UserRepository:
    """Persist and query application users."""

    def __init__(self, database: SQLiteDatabase) -> None:
        self.database = database

    def create(self, username: str, password_hash: str) -> User:
        user = User(
            user_id=uuid4().hex,
            username=username,
            password_hash=password_hash,
            created_at=datetime.utcnow(),
        )
        with self.database.connect() as connection:
            connection.execute(
                "INSERT INTO users (user_id, username, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (user.user_id, user.username, user.password_hash, user.created_at.isoformat()),
            )
            connection.commit()
        return user

    def get_by_username(self, username: str) -> User | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT user_id, username, password_hash, created_at FROM users WHERE username = ?",
                (username,),
            ).fetchone()
        return self._hydrate(row)

    def get_by_id(self, user_id: str) -> User | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT user_id, username, password_hash, created_at FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        return self._hydrate(row)

    def _hydrate(self, row) -> User | None:
        if row is None:
            return None
        return User(
            user_id=row['user_id'],
            username=row['username'],
            password_hash=row['password_hash'],
            created_at=datetime.fromisoformat(row['created_at']),
        )
