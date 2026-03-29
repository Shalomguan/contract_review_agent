"""Lightweight SQLite database wrapper."""
from pathlib import Path
import sqlite3


class SQLiteDatabase:
    """Manage SQLite connections and schema initialization."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def initialize(self) -> None:
        """Create the required tables if they do not exist."""
        with self.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS reviews (
                    review_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    document_id TEXT NOT NULL,
                    document_name TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    risk_counts TEXT NOT NULL,
                    review_payload TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )
                """
            )
            review_columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(reviews)").fetchall()
            }
            if "user_id" not in review_columns:
                connection.execute("ALTER TABLE reviews ADD COLUMN user_id TEXT")
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_reviews_user_created_at ON reviews(user_id, created_at DESC)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)"
            )
            connection.commit()

    def connect(self) -> sqlite3.Connection:
        """Open a row-access SQLite connection."""
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

