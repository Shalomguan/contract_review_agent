"""
嵌入模型
本地嵌入实现，使用sentence-transformers或OpenAI兼容API
"""
import numpy as np
from typing import List, Optional
from config import settings


class EmbeddingModel:
    """嵌入模型"""

    def __init__(self, model_name: Optional[str] = None):
        """
        初始化嵌入模型

        Args:
            model_name: 模型名称，默认使用配置中的模型
        """
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self._model = None
        self._dimension = settings.EMBEDDING_DIM

    def _load_model(self):
        """懒加载模型"""
        if self._model is None:
            try:
                # 尝试使用sentence-transformers（本地模型）
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
                self._dimension = 384  # MiniLM-L12-v2的维度
            except ImportError:
                # 如果没有sentence-transformers，使用简单的TF-IDF作为备选
                self._model = "tfidf"
                self._dimension = 5000

    def embed(self, texts: List[str]) -> np.ndarray:
        """
        生成文本嵌入

        Args:
            texts: 文本列表

        Returns:
            嵌入向量数组 (len(texts), dimension)
        """
        self._load_model()

        if self._model == "tfidf":
            return self._tfidf_embed(texts)
        else:
            return np.array(self._model.encode(texts))

    def _tfidf_embed(self, texts: List[str]) -> np.ndarray:
        """
        使用TF-IDF作为备选嵌入方法

        这是一个简化的实现，生产环境建议使用真正的嵌入模型
        """
        from sklearn.feature_extraction.text import TfidfVectorizer

        if len(texts) == 0:
            return np.random.randn(0, self._dimension)

        # 维护一个单一的 vectorizer
        if not hasattr(self, '_tfidf_vectorizer'):
            self._tfidf_vectorizer = TfidfVectorizer(max_features=5000)
            # 第一次：fit_transform
            try:
                embeddings = self._tfidf_vectorizer.fit_transform(texts).toarray()
                self._dimension = embeddings.shape[1]
                return embeddings
            except Exception:
                pass

        # 后续：只用 transform（用已学习的词汇表）
        try:
            embeddings = self._tfidf_vectorizer.transform(texts).toarray()
            return embeddings
        except Exception:
            # 如果transform失败，返回零向量
            return np.zeros((len(texts), self._dimension))

    @property
    def dimension(self) -> int:
        """返回嵌入向量维度"""
        return self._dimension
