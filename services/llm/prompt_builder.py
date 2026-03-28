"""Prompt builder for future real LLM integration."""
from services.analyzers.legal_knowledge_provider import KnowledgeSnippet


class PromptBuilder:
    """Build a normalized prompt string from rule hits and legal references."""

    def build(
        self,
        clause_title: str,
        clause_text: str,
        risk_type: str,
        risk_level: str,
        knowledge_snippets: list[KnowledgeSnippet],
    ) -> str:
        references = "\n".join(
            f"- {item.title} ({item.source or 'knowledge_base'}): {item.content}"
            for item in knowledge_snippets
        ) or "暂无参考依据"
        return (
            "请基于合同条款和参考依据输出结构化风险审查结果。\n"
            + f"条款标题: {clause_title}\n"
            + f"条款内容: {clause_text}\n"
            + f"风险类型: {risk_type}\n"
            + f"风险等级: {risk_level}\n"
            + "参考依据如下:\n"
            + f"{references}\n"
            + "请返回 risk_reason、impact_analysis、suggestion、replacement_text 四个字段。"
        )
