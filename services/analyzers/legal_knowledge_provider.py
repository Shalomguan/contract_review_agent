"""Static legal knowledge provider for MVP extensibility."""
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class KnowledgeSnippet:
    """A lightweight legal knowledge reference."""

    risk_type: str
    title: str
    content: str


class StaticLegalKnowledgeProvider:
    """Provide built-in legal guidance snippets keyed by risk type."""

    def __init__(self) -> None:
        self._knowledge = {
            "unilateral_exemption": [
                KnowledgeSnippet(
                    risk_type="unilateral_exemption",
                    title="公平原则",
                    content="免责条款不应完全免除一方因故意或重大过失造成损失的责任。",
                )
            ],
            "unilateral_termination": [
                KnowledgeSnippet(
                    risk_type="unilateral_termination",
                    title="解除权平衡",
                    content="解除权触发条件应明确、合理，并给予对方补救或通知期限。",
                )
            ],
            "excessive_liquidated_damages": [
                KnowledgeSnippet(
                    risk_type="excessive_liquidated_damages",
                    title="违约金调整",
                    content="违约金明显过高时，存在被法院或仲裁机构调减的风险。",
                )
            ],
            "unilateral_interpretation": [
                KnowledgeSnippet(
                    risk_type="unilateral_interpretation",
                    title="格式条款解释",
                    content="合同不宜赋予一方单方最终解释权，应以双方书面确认的补充协议为准。",
                )
            ],
            "one_sided_ip_assignment": [
                KnowledgeSnippet(
                    risk_type="one_sided_ip_assignment",
                    title="知识产权归属",
                    content="知识产权归属应结合委托成果、既有技术和许可范围作明确区分。",
                )
            ],
            "biased_dispute_resolution": [
                KnowledgeSnippet(
                    risk_type="biased_dispute_resolution",
                    title="争议解决中立性",
                    content="争议解决地点应考虑双方履约地、证据取得便利性和执行成本。",
                )
            ],
        }

    def get_for_risk(self, risk_type: str) -> list[KnowledgeSnippet]:
        """Return legal snippets relevant to a risk type."""
        return list(self._knowledge.get(risk_type, []))

