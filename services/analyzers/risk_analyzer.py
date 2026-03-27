"""High-level risk analyzer service."""
from models.review import ParsedDocument, RiskAnalysis
from services.analyzers.prompt_analyzer import PromptAnalyzer
from services.analyzers.retrieval_service import RetrievalService
from services.analyzers.rule_engine import RuleEngine


class RiskAnalyzer:
    """Combine rules, retrieval, and prompt analysis into final risk results."""

    def __init__(
        self,
        rule_engine: RuleEngine,
        retrieval_service: RetrievalService,
        prompt_analyzer: PromptAnalyzer,
    ) -> None:
        self.rule_engine = rule_engine
        self.retrieval_service = retrieval_service
        self.prompt_analyzer = prompt_analyzer

    def analyze(self, document: ParsedDocument) -> list[RiskAnalysis]:
        """Analyze a parsed contract document."""
        risks: list[RiskAnalysis] = []
        for clause in document.clauses:
            detections = self.rule_engine.detect(clause)
            for detection in detections:
                knowledge_snippets = self.retrieval_service.retrieve(
                    risk_type=detection.risk_type,
                    clause_text=clause.text,
                )
                risks.append(
                    self.prompt_analyzer.analyze(
                        clause=clause,
                        detection=detection,
                        knowledge_snippets=knowledge_snippets,
                    )
                )

        risks.sort(key=lambda item: {"high": 0, "medium": 1, "low": 2}[item.risk_level])
        return risks

