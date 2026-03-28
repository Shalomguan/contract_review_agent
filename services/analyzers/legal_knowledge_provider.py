"""Legal knowledge provider backed by a local JSON knowledge base."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class KnowledgeSnippet:
    """A lightweight legal knowledge reference."""

    id: str
    category: str
    risk_type: str
    title: str
    content: str
    source: str = ""
    keywords: tuple[str, ...] = field(default_factory=tuple)
    jurisdiction: str = ""
    updated_at: str = ""


class LegalKnowledgeProvider:
    """Load legal knowledge snippets from a local JSON file."""

    def __init__(self, knowledge_base_path: Path) -> None:
        self.knowledge_base_path = knowledge_base_path
        self._knowledge = self._load_knowledge(knowledge_base_path)

    def get_for_risk(self, risk_type: str) -> list[KnowledgeSnippet]:
        """Return knowledge snippets for a given risk type."""
        return [item for item in self._knowledge if item.risk_type == risk_type]

    def get_all(self) -> list[KnowledgeSnippet]:
        """Return all available legal knowledge snippets."""
        return list(self._knowledge)

    def _load_knowledge(self, knowledge_base_path: Path) -> list[KnowledgeSnippet]:
        if not knowledge_base_path.exists():
            return []

        payload = json.loads(knowledge_base_path.read_text(encoding='utf-8-sig'))
        return [
            KnowledgeSnippet(
                id=item['id'],
                category=item.get('category', 'general_contract_review'),
                risk_type=item['risk_type'],
                title=item['title'],
                content=item['content'],
                source=item.get('source', ''),
                keywords=tuple(item.get('keywords', [])),
                jurisdiction=item.get('jurisdiction', ''),
                updated_at=item.get('updated_at', ''),
            )
            for item in payload
        ]
