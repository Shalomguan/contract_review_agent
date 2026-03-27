"""Deterministic rule engine for obvious contract risks."""
from __future__ import annotations

import re
from dataclasses import dataclass

from models.review import Clause, RiskDetection


@dataclass(frozen=True, slots=True)
class RegexRule:
    """Regex-based rule definition."""

    risk_type: str
    risk_level: str
    rule_name: str
    patterns: tuple[str, ...]


class RuleEngine:
    """Detect high-signal risks from contract clauses."""

    regex_rules = (
        RegexRule(
            risk_type="unilateral_exemption",
            risk_level="high",
            rule_name="single_party_exemption",
            patterns=(
                r"(甲方|一方).{0,20}(免责|无需承担责任|不承担责任)",
                r"除甲方外.*承担责任",
            ),
        ),
        RegexRule(
            risk_type="unilateral_termination",
            risk_level="high",
            rule_name="single_party_termination",
            patterns=(
                r"(甲方|一方).{0,20}(有权|可).{0,15}(单方解除|单方终止|随时解除)",
                r"(甲方|一方).{0,20}(无条件解除|无条件终止)",
            ),
        ),
        RegexRule(
            risk_type="unilateral_interpretation",
            risk_level="high",
            rule_name="single_party_interpretation",
            patterns=(r"(甲方|一方).{0,20}(最终解释权|单方解释权)",),
        ),
        RegexRule(
            risk_type="one_sided_ip_assignment",
            risk_level="medium",
            rule_name="one_sided_ip_assignment",
            patterns=(
                r"(知识产权|著作权|专利权).{0,30}(全部|永久).{0,20}(归甲方|归一方所有)",
                r"乙方.*开发成果.*全部归甲方所有",
            ),
        ),
        RegexRule(
            risk_type="biased_dispute_resolution",
            risk_level="medium",
            rule_name="biased_dispute_resolution",
            patterns=(
                r"(争议|诉讼|仲裁).{0,30}(甲方所在地|由甲方选择)",
                r"仅可向甲方所在地.*(法院|仲裁委员会)提起",
            ),
        ),
    )

    def detect(self, clause: Clause) -> list[RiskDetection]:
        """Return detected risks for a clause."""
        detections: dict[str, RiskDetection] = {}

        for rule in self.regex_rules:
            evidence = [pattern for pattern in rule.patterns if re.search(pattern, clause.text)]
            if evidence:
                detections[rule.risk_type] = RiskDetection(
                    risk_type=rule.risk_type,
                    risk_level=rule.risk_level,
                    rule_name=rule.rule_name,
                    evidence=evidence,
                )

        liquidated = self._detect_liquidated_damages(clause.text)
        if liquidated:
            detections[liquidated.risk_type] = liquidated

        return list(detections.values())

    def _detect_liquidated_damages(self, clause_text: str) -> RiskDetection | None:
        percentages = [int(item) for item in re.findall(r"(\d{1,3})\s*%", clause_text)]
        has_daily_rate = bool(re.search(r"(每日|每天|每逾期一日|按日)", clause_text))
        has_damages_keyword = bool(re.search(r"(违约金|滞纳金|罚金)", clause_text))

        if not has_damages_keyword:
            return None

        level = None
        evidence: list[str] = []
        if has_daily_rate and percentages:
            level = "high"
            evidence.append("daily_rate_detected")
        elif any(value >= 50 for value in percentages):
            level = "high"
            evidence.append("percentage_ge_50")
        elif any(value >= 20 for value in percentages):
            level = "medium"
            evidence.append("percentage_ge_20")
        elif percentages:
            level = "low"
            evidence.append("percentage_detected")

        if level is None:
            return None

        return RiskDetection(
            risk_type="excessive_liquidated_damages",
            risk_level=level,
            rule_name="liquidated_damages_threshold",
            evidence=evidence,
        )

