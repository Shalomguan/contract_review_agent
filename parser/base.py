"""
合同解析器基类
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class ParsedDocument:
    """解析后的文档对象"""
    text: str  # 完整文本
    title: Optional[str] = None  # 文档标题
    parties: Optional[List[str]] = None  # 合同当事人
    date: Optional[str] = None  # 合同日期
    file_type: Optional[str] = None  # 文件类型
    raw_metadata: Optional[dict] = None  # 原始元数据
    sections: Optional[List[dict]] = None  # 解析出的章节


class BaseParser(ABC):
    """解析器抽象基类"""

    @abstractmethod
    def parse(self, file_path: str) -> ParsedDocument:
        """解析文件并返回结构化文档"""
        pass

    @abstractmethod
    def extract_text(self, file_path: str) -> str:
        """提取纯文本内容"""
        pass

    def split_into_clauses(self, text: str) -> List[str]:
        """
        将合同文本分割成条款列表
        按章节编号、换行等分割
        """
        import re

        # 按常见章节格式分割
        patterns = [
            r'第[一二三四五六七八九十百]+条',  # 中文条款编号
            r'第\d+条',  # 数字条款编号
            r'^\d+\.',  # 数字编号（开头）
            r'^第\d+章',  # 章节
        ]

        combined_pattern = '|'.join(patterns)
        clauses = re.split(combined_pattern, text, flags=re.MULTILINE)

        # 过滤空条款
        return [c.strip() for c in clauses if c.strip()]
