"""
PDF解析器
使用PyPDF2和pdfplumber提取文本
"""
import PyPDF2
import pdfplumber
from pathlib import Path
from typing import Optional
from .base import BaseParser, ParsedDocument


class PDFParser(BaseParser):
    """PDF文档解析器"""

    def __init__(self):
        self.supported_extensions = ['.pdf']

    def parse(self, file_path: str) -> ParsedDocument:
        """解析PDF文件"""
        text = self.extract_text(file_path)
        metadata = self._extract_metadata(file_path)

        return ParsedDocument(
            text=text,
            title=metadata.get('title'),
            file_type='pdf',
            raw_metadata=metadata
        )

    def extract_text(self, file_path: str) -> str:
        """从PDF提取文本"""
        text_parts = []

        # 使用pdfplumber提取文本（保留布局）
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        # 如果pdfplumber失败，尝试PyPDF2
        if not text_parts:
            text_parts = self._extract_with_pypdf(file_path)

        return '\n\n'.join(text_parts)

    def _extract_with_pypdf(self, file_path: str) -> list:
        """使用PyPDF2作为备选"""
        text_parts = []
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
        return text_parts

    def _extract_metadata(self, file_path: str) -> dict:
        """提取PDF元数据"""
        metadata = {}
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                if reader.metadata:
                    metadata = {
                        'title': reader.metadata.get('/Title', ''),
                        'author': reader.metadata.get('/Author', ''),
                        'subject': reader.metadata.get('/Subject', ''),
                        'creator': reader.metadata.get('/Creator', ''),
                    }
        except Exception:
            pass
        return metadata
