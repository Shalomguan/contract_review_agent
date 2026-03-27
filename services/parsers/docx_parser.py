"""DOCX parser."""
from io import BytesIO

from docx import Document

from services.parsers.base import DocumentParseError, DocumentParser, ParserResult


class DocxParser(DocumentParser):
    """Extract text from DOCX contracts."""

    supported_suffixes = (".docx",)

    def parse(self, filename: str, content: bytes) -> ParserResult:
        try:
            document = Document(BytesIO(content))
        except Exception as exc:  # pragma: no cover - library errors vary
            raise DocumentParseError(f"Failed to open DOCX: {filename}") from exc

        paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
        return ParserResult(
            text="\n\n".join(paragraphs),
            content_type=(
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ),
            metadata={"paragraph_count": len(paragraphs)},
        )

