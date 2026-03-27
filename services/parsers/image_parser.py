"""Image contract parser using OCR."""
from io import BytesIO

from PIL import Image
import pytesseract
from pytesseract import TesseractNotFoundError

from core.config import Settings
from services.parsers.base import DocumentParseError, DocumentParser, ParserResult


class ImageParser(DocumentParser):
    """Extract text from image contracts through Tesseract OCR."""

    supported_suffixes = (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp")

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        if settings.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd

    def parse(self, filename: str, content: bytes) -> ParserResult:
        try:
            image = Image.open(BytesIO(content))
            text = pytesseract.image_to_string(image, lang=self.settings.ocr_languages)
        except TesseractNotFoundError as exc:
            raise DocumentParseError(
                "Tesseract OCR is not installed or CONTRACT_AGENT_TESSERACT_CMD is not configured."
            ) from exc
        except Exception as exc:  # pragma: no cover - library errors vary
            raise DocumentParseError(f"Failed to OCR image: {filename}") from exc

        return ParserResult(text=text, content_type="image")

