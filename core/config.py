"""Application settings."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the MVP."""

    app_name: str = "Contract Review Risk Agent"
    app_version: str = "0.1.0"
    debug: bool = False

    data_dir: Path = Path("data")
    database_path: Path = Path("data/reviews.db")
    upload_dir: Path = Path("data/uploads")

    ocr_languages: str = "chi_sim+eng"
    tesseract_cmd: str | None = None

    model_config = SettingsConfigDict(
        env_prefix="CONTRACT_AGENT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def ensure_directories(self) -> None:
        """Create required runtime directories."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    settings = Settings()
    settings.ensure_directories()
    return settings

