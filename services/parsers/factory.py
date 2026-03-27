"""Document parser selection."""
from pathlib import Path

from services.parsers.base import DocumentParser, UnsupportedDocumentError


class DocumentParserFactory:
    """Select the appropriate parser for an uploaded document."""

    def __init__(self, parsers: list[DocumentParser]) -> None:
        self.parsers = parsers

    def parse(self, filename: str, content: bytes):
        suffix = Path(filename).suffix.lower()
        for parser in self.parsers:
            if parser.supports(suffix):
                return parser.parse(filename=filename, content=content)
        raise UnsupportedDocumentError(f"Unsupported document type: {suffix or 'unknown'}")

