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
        references = "\n".join(f"- {item.title}: {item.content}" for item in knowledge_snippets) or "- 无"
        return (
            "你是一名合同审查助手，请输出结构化风险分析。\n"
            f"条款标题: {clause_title}\n"
            f"条款内容: {clause_text}\n"
            f"风险类型: {risk_type}\n"
            f"风险等级: {risk_level}\n"
            "相关法律提示:\n"
            f"{references}\n"
            "请生成 risk_reason、impact_analysis、suggestion、replacement_text 四个字段。"
        )

