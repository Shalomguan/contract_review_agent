"""Persistent vector index for legal knowledge snippets."""
from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

import numpy as np

from services.analyzers.legal_knowledge_provider import KnowledgeSnippet
from services.rag.embedding_provider import EmbeddingProvider


logger = logging.getLogger(__name__)


class KnowledgeVectorIndex:
    """Build, persist, and query a lightweight vector index."""

    def __init__(
        self,
        index_dir: Path,
        embedding_provider: EmbeddingProvider,
        rebuild_on_start: bool = False,
    ) -> None:
        self.index_dir = index_dir
        self.embedding_provider = embedding_provider
        self.rebuild_on_start = rebuild_on_start
        self.index_path = index_dir / 'knowledge_index.json'
        self.embeddings_path = index_dir / 'knowledge_embeddings.npy'
        self.meta_path = index_dir / 'index_meta.json'
        self._ids: list[str] = []
        self._positions: dict[str, int] = {}
        self._embeddings: np.ndarray | None = None
        self._fingerprint: str | None = None
        self._ready = False
        self._status_message = 'Vector index is not initialized.'

    @property
    def available(self) -> bool:
        return self.embedding_provider.available and self._ready and self._embeddings is not None

    @property
    def status_message(self) -> str:
        return self._status_message

    def build_or_load(self, snippets: list[KnowledgeSnippet]) -> None:
        self.index_dir.mkdir(parents=True, exist_ok=True)
        fingerprint = self._fingerprint_for(snippets)

        if (
            not self.rebuild_on_start
            and self.index_path.exists()
            and self.embeddings_path.exists()
            and self.meta_path.exists()
        ):
            try:
                meta = json.loads(self.meta_path.read_text(encoding='utf-8'))
                if meta.get('fingerprint') == fingerprint and meta.get('model_name') == self.embedding_provider.model_name:
                    self._load()
                    self._status_message = f"Loaded vector index from disk: {self.embeddings_path}"
                    logger.info(self._status_message)
                    return
            except Exception as exc:
                logger.warning('Failed to load vector index metadata, rebuilding index: %s', exc)

        if not self.embedding_provider.available:
            self._ready = False
            self._status_message = (
                'Vector retrieval disabled: embedding provider unavailable. '
                f"Reason: {self.embedding_provider.error_message or 'unknown error'}"
            )
            logger.warning(self._status_message)
            return

        try:
            texts = [self._compose_text(snippet) for snippet in snippets]
            embeddings = self.embedding_provider.embed_documents(texts)
            ids = [snippet.id for snippet in snippets]
            self.index_path.write_text(json.dumps(ids, ensure_ascii=False, indent=2), encoding='utf-8')
            np.save(self.embeddings_path, embeddings)
            self.meta_path.write_text(
                json.dumps(
                    {
                        'fingerprint': fingerprint,
                        'model_name': self.embedding_provider.model_name,
                        'count': len(ids),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding='utf-8',
            )
            self._ids = ids
            self._positions = {item: index for index, item in enumerate(ids)}
            self._embeddings = np.asarray(embeddings, dtype=np.float32)
            self._fingerprint = fingerprint
            self._ready = True
            self._status_message = f"Built vector index and persisted it to {self.embeddings_path}"
            logger.info(self._status_message)
        except Exception as exc:
            self._ready = False
            self._embeddings = None
            self._status_message = f'Vector retrieval disabled: failed to build index ({exc})'
            logger.warning(self._status_message)

    def rank(self, query_text: str, candidates: list[KnowledgeSnippet]) -> dict[str, float]:
        if not self.available or not candidates:
            return {}

        try:
            query_vector = self.embedding_provider.embed_query(query_text)
        except Exception as exc:
            logger.warning('Embedding query failed, falling back to lexical retrieval: %s', exc)
            return {}

        scores: dict[str, float] = {}
        for snippet in candidates:
            position = self._positions.get(snippet.id)
            if position is None or self._embeddings is None:
                continue
            vector = self._embeddings[position]
            scores[snippet.id] = float(np.dot(query_vector, vector))
        return scores

    def _load(self) -> None:
        self._ids = json.loads(self.index_path.read_text(encoding='utf-8'))
        self._positions = {item: index for index, item in enumerate(self._ids)}
        self._embeddings = np.load(self.embeddings_path).astype(np.float32)
        self._ready = True

    def _fingerprint_for(self, snippets: list[KnowledgeSnippet]) -> str:
        payload = [
            {
                'id': snippet.id,
                'category': snippet.category,
                'risk_type': snippet.risk_type,
                'title': snippet.title,
                'content': snippet.content,
                'source': snippet.source,
                'keywords': list(snippet.keywords),
                'jurisdiction': snippet.jurisdiction,
                'updated_at': snippet.updated_at,
            }
            for snippet in snippets
        ]
        body = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(body.encode('utf-8')).hexdigest()

    @staticmethod
    def _compose_text(snippet: KnowledgeSnippet) -> str:
        return ' '.join(
            part
            for part in (
                snippet.category,
                snippet.risk_type,
                snippet.title,
                snippet.content,
                snippet.source,
                ' '.join(snippet.keywords),
                snippet.jurisdiction,
            )
            if part
        )
