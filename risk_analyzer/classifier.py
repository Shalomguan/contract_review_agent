"""
风险分级器
根据风险严重性进行分级
"""
import re
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum
from config import settings


class RiskLevel(Enum):
    """风险等级"""
    RED = "red"  # 重大风险
    YELLOW = "yellow"  # 中等风险
    GREEN = "green"  # 建议优化


@dataclass
class RiskClassification:
    """风险分级结果"""
    risk_type: str
    risk_level: RiskLevel
    description: str
    legal_basis: Optional[str] = None  # 法律依据
    severity_score: float = 0.0  # 严重程度评分 0-1


class RiskClassifier:
    """风险分级器"""

    # 重大风险关键词（RED级）- 需要真正的不公平条款
    RED_INDICATORS = [
        r"\d+%",  # 百分比需要进一步检查
        r"无需承担",  # 无需承担责任
        r"单方面",  # 单方面权利
        r"永久",  # 永久保密/永久归属
        r"放弃",  # 放弃权利
        r"\d+万元",  # 高额赔偿
        r"不得.*解除",  # 不得解除
        r"甲方所在地",  # 不利管辖
        r"均由乙方承担",  # 单方承担费用
    ]

    def __init__(self):
        self.red_threshold = settings.RED_THRESHOLD
        self.yellow_threshold = settings.YELLOW_THRESHOLD

    def classify(self, risk_type: str, clause_text: str) -> RiskClassification:
        """
        对检测到的风险进行分级

        Args:
            risk_type: 风险类型
            clause_text: 风险条款文本

        Returns:
            分级结果
        """
        score = self._calculate_severity(risk_type, clause_text)
        level = self._score_to_level(score)
        description = self._generate_description(risk_type, level, clause_text)
        legal_basis = self._find_legal_basis(risk_type)

        return RiskClassification(
            risk_type=risk_type,
            risk_level=level,
            description=description,
            legal_basis=legal_basis,
            severity_score=score
        )

    def _calculate_severity(self, risk_type: str, clause_text: str) -> float:
        """计算风险严重程度评分"""
        import re

        # 基础分 - 提高阈值，避免简单条款也被标记
        score = 0.2

        # 检查违约金比例 - 必须有明确的百分比且过高才算风险
        if "违约金" in clause_text or "滞纳金" in clause_text:
            percentages = re.findall(r"(\d+)%", clause_text)
            if percentages:
                for p in percentages:
                    p = int(p)
                    if p >= 100:
                        score = 0.95  # >=100% 极高风险
                        break
                    elif p >= 50:
                        score = 0.8  # >=50% 高风险
                        break
                    elif p >= 30:
                        score = max(score, 0.65)  # >=30% 中高风险
                        break
                    elif p >= 20:
                        score = max(score, 0.5)  # >=20% 中等风险
                        break
                    else:
                        score = max(score, 0.3)  # <20% 轻度风险
            else:
                # 有"违约金"字样但无百分比，给低分
                score = max(score, 0.25)

        # 检查按日计算（这是极高风险）
        if any(k in clause_text for k in ["每延迟", "每逾期", "每日", "每天"]):
            score = max(score, 0.9)

        # 检查"无需承担责任"（甲方免责）
        if "无需承担" in clause_text or "不承担" in clause_text:
            # 必须同时有"责任"相关的词才算
            if "责任" in clause_text or "赔偿" in clause_text:
                score = max(score, 0.9)

        # 检查单方权利过大 - 必须同时有"甲方"和"单方面"
        if "单方面" in clause_text and "甲方" in clause_text:
            if any(k in clause_text for k in ["终止", "解除", "决定", "调整"]):
                score = max(score, 0.8)

        # 检查永久保密/归属 - 必须同时有"永久"和具体敏感词
        if "永久" in clause_text:
            if "保密" in clause_text or "归" in clause_text or "归属" in clause_text:
                score = max(score, 0.7)

        # 检查高额赔偿金额 - 金额必须与赔偿/违约金相关
        if any(k in clause_text for k in ["赔偿", "违约金", "补偿"]):
            amounts = re.findall(r"(\d+)\s*万元", clause_text)
            for amt in amounts:
                amt = int(amt)
                if amt >= 100:
                    score = max(score, 0.9)
                    break
                elif amt >= 50:
                    score = max(score, 0.75)
                    break
                elif amt >= 10:
                    score = max(score, 0.55)
                    break

        # 检查不得解除（约束单方）- 必须同时有"不得"和"甲方"
        if "不得" in clause_text and "解除" in clause_text:
            if "乙方" in clause_text or "对方" in clause_text:
                score = max(score, 0.75)

        # 检查不利管辖/律师费条款 - 必须有明确的不利指向
        if "甲方所在地" in clause_text and "管辖" in clause_text:
            score = max(score, 0.65)
        if "律师费" in clause_text and ("乙方" in clause_text or "对方" in clause_text):
            score = max(score, 0.65)

        # 检查预付款风险 - 必须同时有预付款和不予退还
        if "预付款" in clause_text:
            if any(k in clause_text for k in ["不予退还", "不可退还", "不退还", "不予返还"]):
                score = max(score, 0.7)

        return min(score, 1.0)

    def _score_to_level(self, score: float) -> RiskLevel:
        """根据评分确定风险等级"""
        if score >= self.red_threshold:
            return RiskLevel.RED
        elif score >= self.yellow_threshold:
            return RiskLevel.YELLOW
        else:
            return RiskLevel.GREEN

    def _generate_description(self, risk_type: str, level: RiskLevel, clause_text: str) -> str:
        """生成风险描述"""
        level_desc = {
            RiskLevel.RED: "重大风险",
            RiskLevel.YELLOW: "中等风险",
            RiskLevel.GREEN: "建议优化"
        }

        type_descriptions = {
            "违约金过高": "该条款约定的违约金金额或计算方式可能违反公平原则，建议调整为合理范围。",
            "保密条款不明确": "保密条款的范围、期限或违约责任约定不明确，可能导致争议。",
            "争议解决不利": "争议解决条款可能对一方不利，建议选择中立且便于执行的争议解决方式。",
            "责任边界模糊": "责任边界约定不清晰，可能导致意外的责任承担或免责范围争议。",
            "终止条款不合理": "终止条款赋予一方过大的单方解除权，建议增加合理的终止条件和程序。",
            "支付条款风险": "支付条款存在不对称风险，建议明确各方的付款义务和违约后果。",
        }

        base_desc = type_descriptions.get(risk_type, f"检测到{risk_type}相关风险。")

        if level == RiskLevel.RED:
            return f"【{level_desc[level]}】{base_desc}建议立即修改。"
        elif level == RiskLevel.YELLOW:
            return f"【{level_desc[level]}】{base_desc}建议审慎评估后修改。"
        else:
            return f"【{level_desc[level]}】{base_desc}可根据商业需要酌情优化。"

    def _find_legal_basis(self, risk_type: str) -> Optional[str]:
        """查找相关法律依据"""
        legal_basis = {
            "违约金过高": "《民法典》第五百八十五条：约定的违约金过分高于造成的损失的，人民法院或者仲裁机构可以根据当事人的请求予以适当减少。",
            "保密条款不明确": "《民法典》第四百六十九条：合同的权利义务终止，不影响合同中结算和清理条款的效力。保密义务应明确约定。",
            "争议解决不利": "《民事诉讼法》第三十四条：合同或者其他财产权益纠纷的当事人可以书面协议选择被告住所地等人民法院管辖。",
            "责任边界模糊": "《民法典》第五百八十四条：当事人一方不履行合同义务或者履行合同义务不符合约定，造成对方损失的，损失赔偿额应当相当于因违约所造成的损失。",
            "终止条款不合理": "《民法典》第五百六十二条：当事人协商一致，可以解除合同。",
            "支付条款风险": "《民法典》第六百七十四条：借款人应当按照约定的期限支付利息。",
        }
        return legal_basis.get(risk_type)

    def classify_batch(self, classifications: List[RiskClassification]) -> dict:
        """
        批量分级统计

        Returns:
            统计结果 {"red": count, "yellow": count, "green": count}
        """
        stats = {"red": 0, "yellow": 0, "green": 0}
        for c in classifications:
            level = c.risk_level
            # 支持字符串或枚举
            if hasattr(level, 'value'):
                level = level.value
            if level in stats:
                stats[level] += 1
        return stats
