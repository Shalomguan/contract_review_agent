"""PDF parser."""
from io import BytesIO

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - compatibility for existing environments
    from PyPDF2 import PdfReader

from services.parsers.base import DocumentParseError, DocumentParser, ParserResult


class PdfParser(DocumentParser):
    """Extract text from PDF contracts."""

    supported_suffixes = (".pdf",)

    def parse(self, filename: str, content: bytes) -> ParserResult:
        try:
            reader = PdfReader(BytesIO(content))
        except Exception as exc:  # pragma: no cover - library errors vary
            raise DocumentParseError(f"Failed to open PDF: {filename}") from exc

        texts: list[str] = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                texts.append(page_text.strip())

        return ParserResult(
            text="\n\n".join(texts),
            content_type="application/pdf",
            metadata={"page_count": len(reader.pages)},
        )

