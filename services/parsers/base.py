"""Parser abstractions."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


class UnsupportedDocumentError(ValueError):
    """Raised when no parser can handle an uploaded document type."""


class DocumentParseError(RuntimeError):
    """Raised when a parser cannot extract readable text."""


@dataclass(slots=True)
class ParserResult:
    """Text extracted from an uploaded file."""

    text: str
    content_type: str
    metadata: dict[str, Any] = field(default_factory=dict)


class DocumentParser(ABC):
    """Base class for all file parsers."""

    supported_suffixes: tuple[str, ...] = ()

    def supports(self, suffix: str) -> bool:
        return suffix.lower() in self.supported_suffixes

    @abstractmethod
    def parse(self, filename: str, content: bytes) -> ParserResult:
        """Extract text from a file payload."""

