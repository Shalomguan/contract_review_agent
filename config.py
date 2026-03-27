"""
合同审查风险Agent - 配置管理
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """应用配置"""

    # 项目路径
    PROJECT_ROOT: Path = Path(__file__).parent
    KNOWLEDGE_BASE_DIR: Path = PROJECT_ROOT / "knowledge_base"
    DB_PATH: Path = PROJECT_ROOT / "data" / "reviews.db"
    VECTOR_STORE_PATH: Path = PROJECT_ROOT / "data" / "faiss_index"

    # MiniMax API配置（Anthropic兼容）
    MINIMAX_API_KEY: str = Field(default="", description="MiniMax API密钥")
    MINIMAX_BASE_URL: str = "https://api.minimaxi.com/anthropic"
    MINIMAX_MODEL: str = "MiniMax-M2.7"

    # 向量库配置
    EMBEDDING_MODEL: str = "text-embedding-ada-002"  # OpenAI兼容格式
    EMBEDDING_DIM: int = 1536

    # 风险识别配置
    RISK_KEYWORDS: dict = {
        "违约金": ["违约金", "滞纳金", "罚金", "赔偿额"],
        "保密条款": ["保密", "机密", "泄露", "信息披露"],
        "争议解决": ["仲裁", "诉讼", "管辖", "法院"],
        "责任边界": ["免责", "不承担", "责任限制", "赔偿上限"],
        "不可抗力": ["不可抗力", "自然灾害", "战争", "疫情"],
        "终止条款": ["终止", "解除", "违约", "单方面"],
    }

    # 风险等级阈值
    RED_THRESHOLD: float = 0.8
    YELLOW_THRESHOLD: float = 0.5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 全局配置实例
settings = Settings()


def ensure_directories():
    """确保必要的目录存在"""
    settings.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    settings.VECTOR_STORE_PATH.mkdir(parents=True, exist_ok=True)
    settings.KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
