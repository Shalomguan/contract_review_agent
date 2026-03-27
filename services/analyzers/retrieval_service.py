"""Retrieval service abstraction for future RAG expansion."""
from services.analyzers.legal_knowledge_provider import KnowledgeSnippet, StaticLegalKnowledgeProvider


class RetrievalService:
    """Resolve legal context for detected risks."""

    def __init__(self, legal_knowledge_provider: StaticLegalKnowledgeProvider) -> None:
        self.legal_knowledge_provider = legal_knowledge_provider

    def retrieve(self, risk_type: str, clause_text: str) -> list[KnowledgeSnippet]:
        """Return legal context relevant to the given risk type and clause text."""
        _ = clause_text
        return self.legal_knowledge_provider.get_for_risk(risk_type)

