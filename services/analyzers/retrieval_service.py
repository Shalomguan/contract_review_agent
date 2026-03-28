"""Retrieval service with vector search and lexical fallback."""
from __future__ import annotations

import logging
import re
from collections.abc import Iterable

from services.analyzers.legal_knowledge_provider import KnowledgeSnippet, LegalKnowledgeProvider
from services.rag.knowledge_index import KnowledgeVectorIndex


logger = logging.getLogger(__name__)


class RetrievalService:
    """Resolve legal context using vector retrieval with lexical fallback."""

    token_pattern = re.compile(r"[a-z0-9_]+|[一-鿿]+", re.IGNORECASE)

    def __init__(
        self,
        legal_knowledge_provider: LegalKnowledgeProvider,
        top_k: int = 3,
        retrieval_mode: str = 'vector_with_lexical_fallback',
        vector_index: KnowledgeVectorIndex | None = None,
    ) -> None:
        self.legal_knowledge_provider = legal_knowledge_provider
        self.top_k = top_k
        self.retrieval_mode = retrieval_mode
        self.vector_index = vector_index

        if self.vector_index is not None:
            self.vector_index.build_or_load(self.legal_knowledge_provider.get_all())

        logger.info(self.status_message)

    @property
    def using_vector_retrieval(self) -> bool:
        return self.retrieval_mode == 'vector_with_lexical_fallback' and self.vector_index is not None and self.vector_index.available

    @property
    def status_message(self) -> str:
        if self.using_vector_retrieval:
            return 'RAG retrieval mode: vector retrieval enabled with lexical fallback.'
        if self.vector_index is not None:
            return f'RAG retrieval mode: lexical fallback only. {self.vector_index.status_message}'
        return 'RAG retrieval mode: lexical retrieval only.'

    def retrieve(self, risk_type: str, clause_text: str) -> list[KnowledgeSnippet]:
        """Return top-k legal context relevant to the clause and risk type."""
        preferred = self.legal_knowledge_provider.get_for_risk(risk_type)
        fallback = [item for item in self.legal_knowledge_provider.get_all() if item.risk_type != risk_type]

        if self._use_vector_retrieval():
            ranked = self._rank_with_vectors(clause_text=clause_text, preferred=preferred, fallback=fallback)
            if ranked:
                return [item for _, item in ranked[: self.top_k]]

        ranked = self._rank_lexically(clause_text=clause_text, candidates=preferred + fallback, risk_type=risk_type)
        selected = [item for _, item in ranked[: self.top_k]]

        if len(selected) < self.top_k:
            for candidate in preferred + fallback:
                if candidate in selected:
                    continue
                selected.append(candidate)
                if len(selected) >= self.top_k:
                    break

        return selected

    def _use_vector_retrieval(self) -> bool:
        return self.using_vector_retrieval

    def _rank_with_vectors(
        self,
        clause_text: str,
        preferred: list[KnowledgeSnippet],
        fallback: list[KnowledgeSnippet],
    ) -> list[tuple[float, KnowledgeSnippet]]:
        if self.vector_index is None:
            return []

        preferred_ranked = self._blend_scores(clause_text, preferred, same_risk_type=True)
        if len(preferred_ranked) >= self.top_k:
            return preferred_ranked

        selected_ids = {item.id for _, item in preferred_ranked}
        fallback_ranked = [item for item in self._blend_scores(clause_text, fallback, same_risk_type=False) if item[1].id not in selected_ids]
        return (preferred_ranked + fallback_ranked)[: self.top_k]

    def _blend_scores(
        self,
        clause_text: str,
        candidates: list[KnowledgeSnippet],
        same_risk_type: bool,
    ) -> list[tuple[float, KnowledgeSnippet]]:
        if not candidates or self.vector_index is None:
            return []

        vector_scores = self.vector_index.rank(clause_text, candidates)
        lexical_scores = self._lexical_scores(clause_text, candidates)
        ranked: list[tuple[float, KnowledgeSnippet]] = []

        for candidate in candidates:
            vector_score = vector_scores.get(candidate.id)
            if vector_score is None:
                continue
            lexical_score = lexical_scores.get(candidate.id, 0.0)
            risk_bonus = 2.0 if same_risk_type else 0.0
            total = risk_bonus + vector_score * 10.0 + lexical_score
            ranked.append((total, candidate))

        ranked.sort(key=lambda item: (-item[0], item[1].title))
        return ranked

    def _rank_lexically(
        self,
        clause_text: str,
        candidates: Iterable[KnowledgeSnippet],
        risk_type: str,
    ) -> list[tuple[float, KnowledgeSnippet]]:
        clause_terms = self._extract_terms(clause_text)
        ranked: list[tuple[float, KnowledgeSnippet]] = []

        for snippet in candidates:
            snippet_terms = self._extract_terms(
                ' '.join([snippet.title, snippet.content, *snippet.keywords, snippet.source]).strip()
            )
            overlap = len(clause_terms & snippet_terms)
            keyword_hits = sum(1 for keyword in snippet.keywords if keyword and keyword in clause_text)
            risk_bonus = 2.0 if snippet.risk_type == risk_type else 0.0
            jaccard = self._jaccard(clause_terms, snippet_terms)
            score = risk_bonus + keyword_hits * 3.0 + overlap + jaccard
            if score > 0:
                ranked.append((score, snippet))

        ranked.sort(key=lambda item: (-item[0], item[1].title))
        return ranked

    def _lexical_scores(self, clause_text: str, candidates: Iterable[KnowledgeSnippet]) -> dict[str, float]:
        clause_terms = self._extract_terms(clause_text)
        scores: dict[str, float] = {}
        for snippet in candidates:
            snippet_terms = self._extract_terms(
                ' '.join([snippet.title, snippet.content, *snippet.keywords, snippet.source]).strip()
            )
            overlap = len(clause_terms & snippet_terms)
            keyword_hits = sum(1 for keyword in snippet.keywords if keyword and keyword in clause_text)
            jaccard = self._jaccard(clause_terms, snippet_terms)
            scores[snippet.id] = keyword_hits * 3.0 + overlap + jaccard
        return scores

    def _extract_terms(self, text: str) -> set[str]:
        normalized = text.lower()
        terms: set[str] = set()
        for token in self.token_pattern.findall(normalized):
            if self._contains_cjk(token):
                terms.update(self._ngrams(token))
            else:
                terms.add(token)
        return {item for item in terms if item}

    @staticmethod
    def _contains_cjk(text: str) -> bool:
        return any('一' <= char <= '鿿' for char in text)

    @staticmethod
    def _ngrams(token: str) -> set[str]:
        if len(token) <= 2:
            return {token}
        grams = {token}
        for size in (2, 3):
            if len(token) < size:
                continue
            for index in range(len(token) - size + 1):
                grams.add(token[index : index + size])
        return grams

    @staticmethod
    def _jaccard(left: set[str], right: set[str]) -> float:
        if not left or not right:
            return 0.0
        union = left | right
        return len(left & right) / len(union) if union else 0.0
