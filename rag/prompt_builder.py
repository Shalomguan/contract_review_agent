"""
提示词构建器
"""
from typing import List, Optional
from .vector_store import LegalClause


class PromptBuilder:
    """提示词构建器"""

    # 系统提示词
    SYSTEM_PROMPT = """你是一位专业的中国法律顾问，擅长合同审查和风险评估。你的任务是：
1. 识别合同中的潜在法律风险
2. 评估风险对合同双方的影响
3. 提供符合中国法律规定的修改建议

请始终遵循以下原则：
- 以事实和法律为依据
- 保护委托方的合法权益
- 提供明确、可操作的建议"""

    def __init__(self):
        pass

    def build_risk_detection_prompt(self, clause_text: str, context: Optional[str] = None) -> str:
        """
        构建风险识别提示词

        Args:
            clause_text: 合同条款文本
            context: 可选的合同上下文

        Returns:
            完整的提示词
        """
        prompt = f"""请分析以下合同条款，识别潜在的法律风险：

---
{clause_text}
---

"""
        if context:
            prompt += f"合同背景：{context}\n\n"

        prompt += """请以JSON格式返回分析结果：
{
  "risk_type": "风险类型",
  "risk_level": "red/yellow/green",
  "description": "风险描述",
  "impact_party": "甲方/乙方/双方",
  "confidence": 0.0-1.0之间的置信度
}

风险类型包括：
- 违约金过高
- 保密条款不明确
- 争议解决不利
- 责任边界模糊
- 终止条款不合理
- 支付条款风险
- 格式条款无效风险

如果条款没有明显风险，请返回：
{
  "risk_type": "无",
  "risk_level": "green",
  "description": "该条款未发现明显法律风险",
  "impact_party": "中立",
  "confidence": 1.0
}"""
        return prompt

    def build_suggestion_prompt(self, clause_text: str, risk_type: str,
                                 retrieved_laws: Optional[str] = None,
                                 party_info: Optional[str] = None) -> str:
        """
        构建修改建议生成提示词

        Args:
            clause_text: 风险条款文本
            risk_type: 风险类型
            retrieved_laws: 检索到的相关法律条文
            party_info: 甲方乙方信息

        Returns:
            完整的提示词
        """
        prompt = f"""基于以下合同条款和相关法律条文，请生成专业的修改建议：

---
合同条款：
{clause_text}
---

风险类型：{risk_type}
"""
        if party_info:
            prompt += f"\n合同当事人：{party_info}\n"

        if retrieved_laws:
            prompt += f"\n相关法律条文：\n{retrieved_laws}\n"

        prompt += """
请提供一个符合中国法律规定的修改建议，回复格式如下：

**修改理由**：{简要说明为什么需要修改}

**示范条款**：
{可直接使用的修改后条款文本}

**法律依据**：{引用的法律条款}
"""
        return prompt

    def format_retrieved_laws(self, clauses: List[LegalClause]) -> str:
        """
        格式化检索到的法律条款

        Args:
            clauses: 法律条款列表

        Returns:
            格式化后的文本
        """
        if not clauses:
            return "未检索到相关法律条款"

        formatted = []
        for i, clause in enumerate(clauses, 1):
            text = f"""【{clause.category}】{clause.title}
法条：{clause.law_name} {clause.article}
内容：{clause.content}"""
            formatted.append(text)

        return "\n\n".join(formatted)

    def build_summary_prompt(self, review_results: List[dict]) -> str:
        """
        构建审查总结提示词

        Args:
            review_results: 审查结果列表

        Returns:
            完整的提示词
        """
        results_text = "\n".join([
            f"- {r['risk_type']}（{r['risk_level']}）：{r['description']}"
            for r in review_results
        ])

        return f"""请对以下合同审查结果进行总结：

{results_text}

请提供：
1. 整体风险评估概述
2. 需要重点关注的重大风险
3. 修改优先级建议
"""
