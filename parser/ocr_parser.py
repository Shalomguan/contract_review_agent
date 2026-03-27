"""
OCR解析器
使用Tesseract从图片中提取文本
"""
import pytesseract
from PIL import Image
from pathlib import Path
from typing import Optional
from .base import BaseParser, ParsedDocument


class OCRParser(BaseParser):
    """图片OCR解析器，支持扫描件合同"""

    def __init__(self, tesseract_cmd: Optional[str] = None):
        """
        初始化OCR解析器

        Args:
            tesseract_cmd: Tesseract可执行文件路径
                           Windows默认: C:\\Program Files\\Tesseract-OCR\\tesseract.exe
        """
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        self.supported_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif']

    def parse(self, file_path: str) -> ParsedDocument:
        """解析图片文件"""
        text = self.extract_text(file_path)

        return ParsedDocument(
            text=text,
            file_type='image',
            raw_metadata={'source': file_path}
        )

    def extract_text(self, file_path: str) -> str:
        """从图片提取文本"""
        image = Image.open(file_path)

        # 转换为RGB模式（OCR需要）
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # 使用Tesseract OCR提取文本
        # lang='chi_sim' 支持简体中文，'eng' 支持英文
        text = pytesseract.image_to_string(
            image,
            lang='chi_sim+eng',
            config='--psm 6'  # PSM模式：假设统一块段落
        )

        return text.strip()

    def extract_text_with_boxes(self, file_path: str) -> dict:
        """
        提取文本并返回字符位置信息
        用于高亮显示风险条款
        """
        image = Image.open(file_path)
        if image.mode != 'RGB':
            image = image.convert('RGB')

        data = pytesseract.image_to_data(
            image,
            lang='chi_sim+eng',
            output_type=pytesseract.Output.DICT
        )

        return data
