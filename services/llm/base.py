"""LLM interfaces used by the MVP."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(slots=True)
class PromptPayload:
    """Normalized prompt input for structured analysis generation."""

    prompt: str
    clause_title: str
    clause_text: str
    risk_type: str
    risk_level: str
    references: list[str] = field(default_factory=list)


class StructuredLLMClient(Protocol):
    """Protocol for any client that returns structured analysis fields."""

    def analyze(self, payload: PromptPayload) -> dict[str, str]:
        """Generate a structured analysis response."""

