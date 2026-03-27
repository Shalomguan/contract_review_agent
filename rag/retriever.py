"""
法律条款检索器
"""
from typing import List, Optional
from .vector_store import VectorStore, LegalClause
from .prompt_builder import PromptBuilder


class Retriever:
    """法律条款检索器"""

    def __init__(self):
        self.vector_store = VectorStore()
        self.prompt_builder = PromptBuilder()
        self._initialized = False

    def initialize(self):
        """初始化检索器"""
        if not self._initialized:
            self.vector_store.initialize()
            self._initialized = True

    def retrieve(self, query: str, risk_type: Optional[str] = None, top_k: int = 3) -> str:
        """
        检索与风险相关的法律条款

        Args:
            query: 查询文本（风险条款内容）
            risk_type: 风险类型（可选，用于过滤）
            top_k: 返回数量

        Returns:
            格式化后的法律条款文本
        """
        self.initialize()

        # 搜索相关条款
        clauses = self.vector_store.search(query, top_k=top_k)

        # 如果指定了风险类型，过滤相关类别
        if risk_type:
            category_map = {
                "违约金过高": ["违约金"],
                "保密条款不明确": ["保密义务"],
                "争议解决不利": ["争议解决"],
                "责任边界模糊": ["责任限制", "赔偿范围"],
                "终止条款不合理": ["合同解除"],
                "支付条款风险": ["支付条款"],
            }
            relevant_categories = category_map.get(risk_type, [])
            if relevant_categories:
                clauses = [c for c in clauses if c.category in relevant_categories] or clauses[:top_k]

        # 构建检索结果文本
        return self.prompt_builder.format_retrieved_laws(clauses)

    def retrieve_for_suggestion(self, clause_text: str, risk_type: str) -> dict:
        """
        检索用于生成修改建议的法律依据

        Args:
            clause_text: 风险条款文本
            risk_type: 风险类型

        Returns:
            包含检索结果的字典
        """
        clauses = self.vector_store.search(clause_text, top_k=5)

        # 按风险类型过滤
        category_map = {
            "违约金过高": ["违约金"],
            "保密条款不明确": ["保密义务"],
            "争议解决不利": ["争议解决"],
            "责任边界模糊": ["责任限制", "赔偿范围"],
            "终止条款不合理": ["合同解除"],
            "不可抗力": ["不可抗力"],
            "支付条款风险": ["支付条款"],
        }

        relevant_categories = category_map.get(risk_type, [])
        filtered_clauses = [c for c in clauses if c.category in relevant_categories] if relevant_categories else clauses

        return {
            "clauses": filtered_clauses,
            "formatted_text": self.prompt_builder.format_retrieved_laws(filtered_clauses)
        }
