"""Prompt-oriented structured analyzer."""
from models.review import Clause, RiskAnalysis, RiskDetection, RiskReference
from services.analyzers.legal_knowledge_provider import KnowledgeSnippet
from services.llm.base import PromptPayload, StructuredLLMClient
from services.llm.prompt_builder import PromptBuilder


class PromptAnalyzer:
    """Generate structured analysis output from a prompt payload."""

    def __init__(self, prompt_builder: PromptBuilder, llm_client: StructuredLLMClient) -> None:
        self.prompt_builder = prompt_builder
        self.llm_client = llm_client

    def analyze(
        self,
        clause: Clause,
        detection: RiskDetection,
        knowledge_snippets: list[KnowledgeSnippet],
    ) -> RiskAnalysis:
        """Turn a rule hit into a structured risk analysis record."""
        prompt = self.prompt_builder.build(
            clause_title=clause.title,
            clause_text=clause.text,
            risk_type=detection.risk_type,
            risk_level=detection.risk_level,
            knowledge_snippets=knowledge_snippets,
        )
        payload = PromptPayload(
            prompt=prompt,
            clause_title=clause.title,
            clause_text=clause.text,
            risk_type=detection.risk_type,
            risk_level=detection.risk_level,
            references=[item.content for item in knowledge_snippets],
        )
        result = self.llm_client.analyze(payload)

        references = [
            RiskReference(
                title=item.title,
                source=item.source,
                content=item.content,
                category=item.category,
            )
            for item in knowledge_snippets
        ]

        return RiskAnalysis(
            clause_id=clause.clause_id,
            clause_title=clause.title,
            clause_text=clause.text,
            risk_type=detection.risk_type,
            risk_level=detection.risk_level,
            risk_reason=result["risk_reason"],
            impact_analysis=result["impact_analysis"],
            suggestion=result["suggestion"],
            replacement_text=result["replacement_text"],
            references=references,
        )
