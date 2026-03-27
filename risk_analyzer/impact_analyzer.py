"""
影响分析器
分析风险对甲方/乙方的影响
"""
import re
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


class AffectedParty(Enum):
    """受影响方"""
    PARTY_A = "甲方"  # 合同中的甲方
    PARTY_B = "乙方"  # 合同中的乙方
    BOTH = "双方"  # 双方都受影响
    NEUTRAL = "中立"  # 中立条款


@dataclass
class ImpactAnalysis:
    """影响分析结果"""
    affected_party: AffectedParty
    impact_description: str
    risk_exposure: str  # 风险敞口描述
    recommendation: str  # 建议


class ImpactAnalyzer:
    """甲方/乙方影响分析器"""

    # 用于识别甲方/乙方的模式
    PARTY_PATTERNS = {
        "甲方": [r"甲方[是为]?\s*([^\n，,]+)", r"（甲方）\s*([^\n，,]+)", r"甲方：\s*([^\n，,]+)"],
        "乙方": [r"乙方[是为]?\s*([^\n，,]+)", r"（乙方）\s*([^\n，,]+)", r"乙方：\s*([^\n，,]+)"],
    }

    # 风险类型与影响映射
    IMPACT_MAPPING = {
        "违约金过高": {
            AffectedParty.PARTY_A: "甲方需承担过高的违约成本，一旦违约将面临沉重的经济压力。",
            AffectedParty.PARTY_B: "乙方可获得较高的违约赔偿，但过高的违约金可能被认定为无效。",
            AffectedParty.BOTH: "双方都面临高额违约金风险，可能导致合同僵局。",
            AffectedParty.NEUTRAL: "违约金条款的合理性取决于具体金额和计算方式。",
        },
        "保密条款不明确": {
            AffectedParty.PARTY_A: "甲方的商业秘密可能得不到充分保护，泄露风险增加。",
            AffectedParty.PARTY_B: "乙方的保密义务范围不清晰，可能承担意外的保密责任。",
            AffectedParty.BOTH: "双方对保密义务的理解可能存在分歧，引发争议。",
            AffectedParty.NEUTRAL: "需要明确保密的范围、期限和违约责任。",
        },
        "争议解决不利": {
            AffectedParty.PARTY_A: "若甲方是外地企业，在乙方所在地诉讼可能面临地方保护主义风险。",
            AffectedParty.PARTY_B: "若乙方是外地企业，在甲方所在地诉讼可能处于不利地位。",
            AffectedParty.BOTH: "争议解决条款对双方的影响取决于实际选择。",
            AffectedParty.NEUTRAL: "建议选择中立机构仲裁或双方认可的法院管辖。",
        },
        "责任边界模糊": {
            AffectedParty.PARTY_A: "甲方的责任边界不清晰，可能承担超出预期的赔偿责任。",
            AffectedParty.PARTY_B: "乙方的免责范围不明确，可能无法有效规避风险。",
            AffectedParty.BOTH: "模糊的责任边界可能导致争议时双方各执一词。",
            AffectedParty.NEUTRAL: "需要明确约定责任边界和免责情形。",
        },
        "终止条款不合理": {
            AffectedParty.PARTY_A: "甲方可能被赋予过大的单方终止权，乙方权益缺乏保障。",
            AffectedParty.PARTY_B: "乙方可能被赋予过大的单方终止权，甲方投入可能无法收回。",
            AffectedParty.BOTH: "不平衡的终止条款可能导致合同关系不稳定。",
            AffectedParty.NEUTRAL: "终止条款应当平衡双方权益。",
        },
        "支付条款风险": {
            AffectedParty.PARTY_A: "预付款不予退还条款可能导致甲方资金被占用。",
            AffectedParty.PARTY_B: "付款期限过短可能导致乙方资金压力增大。",
            AffectedParty.BOTH: "不对等的支付条款可能影响合同正常履行。",
            AffectedParty.NEUTRAL: "支付条款应当公平合理。",
        },
    }

    def __init__(self):
        self.party_a_name: Optional[str] = None
        self.party_b_name: Optional[str] = None

    def extract_parties(self, text: str) -> tuple:
        """从文本中提取甲方乙方信息"""
        party_a = None
        party_b = None

        for party, patterns in self.PARTY_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    if party == "甲方":
                        party_a = match.group(1).strip() if match.lastindex else None
                    else:
                        party_b = match.group(1).strip() if match.lastindex else None

        self.party_a_name = party_a
        self.party_b_name = party_b

        return party_a, party_b

    def analyze(self, risk_type: str, clause_text: str, party_context: Optional[str] = None) -> ImpactAnalysis:
        """
        分析风险对各方的具体影响

        Args:
            risk_type: 风险类型
            clause_text: 风险条款文本
            party_context: 合同上下文，用于判断甲方乙方

        Returns:
            影响分析结果
        """
        # 判断受影响方
        affected_party = self._determine_affected_party(risk_type, clause_text, party_context)

        # 获取影响描述
        impact_map = self.IMPACT_MAPPING.get(risk_type, {})
        impact_description = impact_map.get(affected_party, "该条款的影响需要根据具体情况判断。")

        # 生成风险敞口描述
        risk_exposure = self._generate_risk_exposure(risk_type, clause_text)

        # 生成建议
        recommendation = self._generate_recommendation(risk_type, affected_party)

        return ImpactAnalysis(
            affected_party=affected_party,
            impact_description=impact_description,
            risk_exposure=risk_exposure,
            recommendation=recommendation
        )

    def _determine_affected_party(self, risk_type: str, clause_text: str, party_context: Optional[str]) -> AffectedParty:
        """判断哪个合同方受该风险影响最大"""
        # 检查条款中是否明确提到甲方乙方
        has_party_a = any(p in clause_text for p in ["甲方", "发包方", "委托方", "买方", "出租方"])
        has_party_b = any(p in clause_text for p in ["乙方", "承包方", "受托方", "卖方", "承租方"])

        # 基于风险类型的常见影响方
        party_association = {
            "违约金过高": AffectedParty.PARTY_A,  # 通常对甲方（付款方）影响更大
            "保密条款不明确": AffectedParty.PARTY_A,  # 通常甲方商业秘密更多
            "争议解决不利": AffectedParty.NEUTRAL,  # 取决于哪方是本地企业
            "责任边界模糊": AffectedParty.BOTH,
            "终止条款不合理": AffectedParty.PARTY_B,  # 乙方通常是被终止方
            "支付条款风险": AffectedParty.PARTY_A,  # 甲方通常是付款方
        }

        if has_party_a and not has_party_b:
            return AffectedParty.PARTY_A
        elif has_party_b and not has_party_a:
            return AffectedParty.PARTY_B
        elif has_party_a and has_party_b:
            return AffectedParty.BOTH
        else:
            return party_association.get(risk_type, AffectedParty.NEUTRAL)

    def _generate_risk_exposure(self, risk_type: str, clause_text: str) -> str:
        """生成风险敞口描述"""
        # 尝试提取具体金额或比例
        numbers = re.findall(r'\d+(?:\.\d+)?%?', clause_text)

        exposure_templates = {
            "违约金过高": f"可能面临{numbers[0] if numbers else '较高'}的违约金风险敞口。",
            "保密条款不明确": "保密义务的范围和期限不明确，存在潜在法律风险。",
            "争议解决不利": "争议解决成本可能较高，执行难度增加。",
            "责任边界模糊": "责任范围不清晰，可能承担超出预期的损失。",
            "终止条款不合理": "可能被单方面终止合作，已投入资源无法收回。",
            "支付条款风险": f"涉及金额{numbers[0] if numbers else '较大'}，资金安全存在风险。",
        }

        return exposure_templates.get(risk_type, "风险敞口需要进一步评估。")

    def _generate_recommendation(self, risk_type: str, affected_party: AffectedParty) -> str:
        """生成应对建议"""
        party_name = affected_party.value

        recommendations = {
            AffectedParty.PARTY_A: f"建议{party_name}要求对方修改该条款，增加合理的违约金上限或明确责任边界。",
            AffectedParty.PARTY_B: f"建议{party_name}审慎评估该条款的商业风险，必要时寻求专业法律意见。",
            AffectedParty.BOTH: "建议双方协商修改该条款，建立公平合理的风险分担机制。",
            AffectedParty.NEUTRAL: "建议聘请专业律师审查该条款，确保合同公平有效。",
        }

        return recommendations.get(affected_party, "建议咨询专业法律人士。")
