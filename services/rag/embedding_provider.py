"""Embedding provider abstractions for local RAG."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

import numpy as np


logger = logging.getLogger(__name__)


class EmbeddingProvider(Protocol):
    """Protocol for any embedding backend used by retrieval."""

    model_name: str

    @property
    def available(self) -> bool:
        """Whether the provider can currently produce embeddings."""

    @property
    def error_message(self) -> str | None:
        """Return initialization or runtime error details if unavailable."""

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        """Return normalized embeddings for knowledge texts."""

    def embed_query(self, text: str) -> np.ndarray:
        """Return a normalized embedding for one query text."""


@dataclass(slots=True)
class SentenceTransformerEmbeddingProvider:
    """Sentence-transformers embedding provider with lazy model loading."""

    model_name: str
    cache_dir: Path | None = None
    local_files_only: bool = True
    _model: object | None = field(init=False, default=None, repr=False)
    _error_message: str | None = field(init=False, default=None, repr=False)

    def __post_init__(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer  # noqa: F401
        except Exception as exc:  # pragma: no cover - depends on local environment
            self._error_message = str(exc)
            logger.warning('Embedding provider unavailable during import check: %s', self._error_message)

    @property
    def available(self) -> bool:
        return self._error_message is None

    @property
    def error_message(self) -> str | None:
        return self._error_message

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        model = self._get_model()
        embeddings = model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(embeddings, dtype=np.float32)

    def embed_query(self, text: str) -> np.ndarray:
        model = self._get_model()
        embedding = model.encode(
            [text],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )[0]
        return np.asarray(embedding, dtype=np.float32)

    def _get_model(self):
        if not self.available:
            raise RuntimeError(self._error_message or 'Embedding provider is unavailable.')
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(
                    self.model_name,
                    cache_folder=str(self.cache_dir) if self.cache_dir else None,
                    local_files_only=self.local_files_only,
                )
            except Exception as exc:  # pragma: no cover - depends on local environment
                self._error_message = str(exc)
                logger.warning('Failed to load embedding model %s: %s', self.model_name, self._error_message)
                raise RuntimeError(self._error_message) from exc
        return self._model


@dataclass(slots=True)
class UnavailableEmbeddingProvider:
    """Fallback provider used when embeddings are intentionally disabled."""

    model_name: str = 'unavailable'
    reason: str = 'Embedding provider is unavailable.'

    @property
    def available(self) -> bool:
        return False

    @property
    def error_message(self) -> str | None:
        return self.reason

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        raise RuntimeError(self.reason)

    def embed_query(self, text: str) -> np.ndarray:
        raise RuntimeError(self.reason)
