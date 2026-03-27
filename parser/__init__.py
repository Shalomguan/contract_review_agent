"""
合同解析模块
支持PDF、Word、图片(OCR)格式
"""
from .base import BaseParser, ParsedDocument
from .pdf_parser import PDFParser
from .docx_parser import DocxParser
from .ocr_parser import OCRParser

__all__ = ["BaseParser", "ParsedDocument", "PDFParser", "DocxParser", "OCRParser"]
