"""
FAISS向量库管理
"""
import json
import faiss
import numpy as np
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass
from config import settings


@dataclass
class LegalClause:
    """法律条款"""
    id: str
    category: str  # 条款类别
    title: str  # 条款标题
    content: str  # 条款内容
    law_name: str  # 法律法规名称
    article: str  # 条款编号


class VectorStore:
    """FAISS向量存储管理"""

    def __init__(self, dimension: int = 384):
        """
        初始化向量存储

        Args:
            dimension: 嵌入向量维度，默认384（可根据模型调整）
        """
        self.dimension = dimension
        self.index: Optional[faiss.Index] = None
        self.clauses: List[LegalClause] = []
        self.embeddings: Optional[np.ndarray] = None
        self._initialized = False

    def initialize(self, recreate: bool = False):
        """初始化向量库"""
        if self._initialized and not recreate:
            return

        index_path = settings.VECTOR_STORE_PATH / "index.faiss"
        clauses_path = settings.VECTOR_STORE_PATH / "clauses.json"

        if not recreate and index_path.exists() and clauses_path.exists():
            self._load()
        else:
            self._create_from_knowledge_base()

        self._initialized = True

    def _create_from_knowledge_base(self):
        """从知识库创建向量库"""
        from .embedding import EmbeddingModel

        self._embedding_model = EmbeddingModel()

        # 加载内置法律条款
        kb_path = settings.KNOWLEDGE_BASE_DIR / "legal_clauses.json"
        if kb_path.exists():
            with open(kb_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._load_clauses(data.get('clauses', []))

        # 如果没有内置条款，加载默认条款
        if not self.clauses:
            self._load_default_clauses()

        # 生成嵌入向量
        texts = [c.content for c in self.clauses]
        self.embeddings = self._embedding_model.embed(texts)

        # 获取实际维度
        actual_dimension = self.embeddings.shape[1]
        self.dimension = actual_dimension

        # 创建FAISS索引
        self.index = faiss.IndexFlatL2(actual_dimension)
        self.index.add(self.embeddings.astype('float32'))

        # 保存
        self._save()

    def _load_default_clauses(self):
        """加载默认法律条款库"""
        default_clauses = [
            # 民法典 - 合同编
            {
                "category": "违约金",
                "title": "违约金过高调整",
                "content": "约定的违约金低于造成的损失的，当事人可以请求人民法院或者仲裁机构予以增加；约定的违约金过分高于造成的损失的，当事人可以请求人民法院或者仲裁机构予以适当减少。",
                "law_name": "《中华人民共和国民法典》",
                "article": "第五百八十五条"
            },
            {
                "category": "违约金",
                "title": "违约金与其他责任的并存",
                "content": "当事人既约定违约金，又约定定金的，一方违约时，对方可以选择适用违约金或者定金条款。",
                "law_name": "《中华人民共和国民法典》",
                "article": "第五百八十八条"
            },
            {
                "category": "保密义务",
                "title": "合同保密义务",
                "content": "当事人应当遵循诚信原则，根据合同的性质、目的和交易习惯履行保密义务。",
                "law_name": "《中华人民共和国民法典》",
                "article": "第五百零一条"
            },
            {
                "category": "争议解决",
                "title": "协议管辖",
                "content": "合同或者其他财产权益纠纷的当事人可以书面协议选择被告住所地、合同履行地、合同签订地、原告住所地、标的物所在地等与争议有实际联系地点的人民法院管辖。",
                "law_name": "《中华人民共和国民事诉讼法》",
                "article": "第三十四条"
            },
            {
                "category": "不可抗力",
                "title": "不可抗力免责",
                "content": "因不可抗力致使不能实现合同目的，当事人可以解除合同。不可抗力是指不能预见、不能避免且不能克服的客观情况。",
                "law_name": "《中华人民共和国民法典》",
                "article": "第一百八十条、第五百六十三条"
            },
            {
                "category": "合同解除",
                "title": "协商解除",
                "content": "当事人协商一致，可以解除合同。",
                "law_name": "《中华人民共和国民法典》",
                "article": "第五百六十二条第一款"
            },
            {
                "category": "责任限制",
                "title": "违约责任",
                "content": "当事人一方不履行合同义务或者履行合同义务不符合约定的，应当承担继续履行、采取补救措施或者赔偿损失等违约责任。",
                "law_name": "《中华人民共和国民法典》",
                "article": "第五百七十七条"
            },
            {
                "category": "赔偿范围",
                "title": "损失赔偿额",
                "content": "当事人一方不履行合同义务或者履行合同义务不符合约定，造成对方损失的，损失赔偿额应当相当于因违约所造成的损失，包括合同履行后可以获得的利益。",
                "law_name": "《中华人民共和国民法典》",
                "article": "第五百八十四条"
            },
            {
                "category": "格式条款",
                "title": "格式条款无效情形",
                "content": "格式条款中造成对方人身伤害的、因故意或者重大过失造成对方财产损失的免责条款无效。",
                "law_name": "《中华人民共和国民法典》",
                "article": "第四百九十七条"
            },
            {
                "category": "支付条款",
                "title": "付款期限",
                "content": "买受人应当按照约定的时间支付价款。对支付时间没有约定或者约定不明确的，依据本法第五百一十条的规定仍不能确定的，买受人应当在收到标的物或者提取标的物单证的同时支付。",
                "law_name": "《中华人民共和国民法典》",
                "article": "第六百二十八条"
            },
        ]

        self._load_clauses(default_clauses)

    def _load_clauses(self, clauses_data: List[Dict]):
        """加载法律条款"""
        for idx, c in enumerate(clauses_data):
            clause = LegalClause(
                id=str(idx),
                category=c.get('category', '其他'),
                title=c.get('title', ''),
                content=c.get('content', ''),
                law_name=c.get('law_name', ''),
                article=c.get('article', '')
            )
            self.clauses.append(clause)

    def _save(self):
        """保存向量库到磁盘"""
        settings.VECTOR_STORE_PATH.mkdir(parents=True, exist_ok=True)

        # 保存FAISS索引
        index_path = settings.VECTOR_STORE_PATH / "index.faiss"
        if self.index is not None:
            faiss.write_index(self.index, str(index_path))

        # 保存条款数据
        clauses_path = settings.VECTOR_STORE_PATH / "clauses.json"
        clauses_data = [
            {
                "id": c.id,
                "category": c.category,
                "title": c.title,
                "content": c.content,
                "law_name": c.law_name,
                "article": c.article
            }
            for c in self.clauses
        ]
        with open(clauses_path, 'w', encoding='utf-8') as f:
            json.dump({"clauses": clauses_data}, f, ensure_ascii=False, indent=2)

    def _load(self):
        """从磁盘加载向量库"""
        index_path = settings.VECTOR_STORE_PATH / "index.faiss"
        clauses_path = settings.VECTOR_STORE_PATH / "clauses.json"

        if index_path.exists():
            self.index = faiss.read_index(str(index_path))

        if clauses_path.exists():
            with open(clauses_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._load_clauses(data.get('clauses', []))

    def search(self, query: str, top_k: int = 5) -> List[LegalClause]:
        """
        搜索最相关的法律条款

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            最相关的法律条款列表
        """
        from .embedding import EmbeddingModel

        if self.index is None or not self.clauses:
            self.initialize()

        # 使用保存的 embedding model
        if not hasattr(self, '_embedding_model'):
            self._embedding_model = EmbeddingModel()

        query_embedding = self._embedding_model.embed([query]).astype('float32')

        # 搜索
        distances, indices = self.index.search(query_embedding.reshape(1, -1), min(top_k, len(self.clauses)))

        results = []
        for idx in indices[0]:
            if idx < len(self.clauses):
                results.append(self.clauses[idx])

        return results

    def add_clause(self, clause: LegalClause, embedding: np.ndarray):
        """添加新条款"""
        self.clauses.append(clause)
        if self.embeddings is None:
            self.embeddings = embedding.reshape(1, -1)
        else:
            self.embeddings = np.vstack([self.embeddings, embedding.reshape(1, -1)])

        if self.index is None:
            self.index = faiss.IndexFlatL2(self.dimension)

        self.index.add(embedding.reshape(1, -1).astype('float32'))
