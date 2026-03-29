"""Application settings."""
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the MVP."""

    app_name: str = "Contract Review Risk Agent"
    app_version: str = "0.1.0"
    debug: bool = False
    app_timezone: str = "Asia/Shanghai"
    auth_secret_key: str = "dev-secret-change-me"
    auth_token_ttl_minutes: int = 480

    data_dir: Path = Path("data")
    database_path: Path = Path("data/reviews.db")
    upload_dir: Path = Path("data/uploads")
    knowledge_base_path: Path = Path("docs/legal_knowledge_base.json")
    retrieval_top_k: int = Field(default=3, ge=1, le=10)
    retrieval_mode: str = "vector_with_lexical_fallback"
    embedding_model_name: str = "BAAI/bge-small-zh-v1.5"
    embedding_cache_dir: Path = Path("data/embedding_cache")
    rag_index_dir: Path = Path("data/rag")
    rag_rebuild_on_start: bool = False
    embedding_local_files_only: bool = True

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
        self.knowledge_base_path.parent.mkdir(parents=True, exist_ok=True)
        self.embedding_cache_dir.mkdir(parents=True, exist_ok=True)
        self.rag_index_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    settings = Settings()
    settings.ensure_directories()
    return settings
