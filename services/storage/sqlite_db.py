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
                CREATE TABLE IF NOT EXISTS reviews (
                    review_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    document_name TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    risk_counts TEXT NOT NULL,
                    review_payload TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def connect(self) -> sqlite3.Connection:
        """Open a row-access SQLite connection."""
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

