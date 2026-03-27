"""Plain-text contract parser."""
from services.parsers.base import DocumentParseError, DocumentParser, ParserResult


class TextParser(DocumentParser):
    """Parse TXT-style contract uploads."""

    supported_suffixes = (".txt", ".md")

    def parse(self, filename: str, content: bytes) -> ParserResult:
        encodings = ("utf-8", "utf-8-sig", "gb18030", "gbk")
        for encoding in encodings:
            try:
                text = content.decode(encoding)
                return ParserResult(text=text, content_type="text/plain")
            except UnicodeDecodeError:
                continue

        raise DocumentParseError(f"Unable to decode text file: {filename}")

