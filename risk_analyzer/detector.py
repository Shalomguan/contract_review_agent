"""
风险条款检测器
基于关键词和正则表达式检测潜在风险条款
"""
import re
from dataclasses import dataclass
from typing import List, Dict, Optional
from config import settings


@dataclass
class DetectedRisk:
    """检测到的风险"""
    clause_text: str  # 风险条款原文
    risk_type: str  # 风险类型
    risk_keywords: List[str]  # 匹配的关键词
    position: int  # 在文档中的位置
    confidence: float  # 置信度


class RiskDetector:
    """风险条款检测器"""

    # 风险类型与关键词映射（严格模式 - 需要真正的不利条款才触发）
    RISK_PATTERNS: Dict[str, List[str]] = {
        "违约金过高": [
            r"违约金[^\n]{0,20}(?:高于|超过|大于|不低于合同金额|每日|按日)",
            r"滞纳金[^\n]{0,10}(?:千分之|百分之|\d+%)",
            r"(?:赔偿|补偿)[^\n]{0,10}(?:高于|超过)[^\n]{0,20}损失",
        ],
        "保密条款不明确": [
            r"保密[^\n]{0,30}(?:无期限|永久|未约定|未明确|无明确)",
            r"保密范围[^\n]{0,20}(?:无|未|不限|所有)",
            r"机密信息[^\n]{0,20}(?:无|未|不限|所有)",
        ],
        "争议解决不利": [
            r"仅能在[^\n]{0,10}甲方所在地",
            r"管辖法院[^\n]{0,10}甲方",
            r"适用[^\n]{0,10}法律[^\n]{0,10}由[^\n]{0,5}甲方",
            r"仲裁[^\n]{0,10}仅在[^\n]{0,10}甲方",
        ],
        "责任边界模糊": [
            r"(?:免除|不承担)[^\n]{0,20}一切责任",
            r"(?:免除|不承担)[^\n]{0,20}全部责任",
            r"责任限制[^\n]{0,10}(?:无上限|无最高)",
            r"间接损失[^\n]{0,20}(?:免责|不承担|不赔偿)",
        ],
        "终止条款不合理": [
            r"甲方可[^\n]{0,10}单方面[^\n]{0,20}终止",
            r"甲方可[^\n]{0,10}随时[^\n]{0,20}解除",
            r"甲方可[^\n]{0,10}无条件[^\n]{0,20}终止",
            r"不得解除[^\n]{0,10}甲方",
        ],
        "支付条款风险": [
            r"预付款[^\n]{0,20}(?:不予退还|不可退还|不退还|不予返还)",
            r"预付款[^\n]{0,20}(?:违约|逾期)[^\n]{0,10}不予退还",
            r"单方面[^\n]{0,20}调整[^\n]{0,10}付款",
        ],
    }

    def __init__(self):
        self.risk_keywords = settings.RISK_KEYWORDS

    def detect(self, text: str, file_type: str = "contract") -> List[DetectedRisk]:
        """
        检测文本中的风险条款

        Args:
            text: 合同文本
            file_type: 文件类型

        Returns:
            检测到的风险列表
        """
        risks = []
        clauses = self._split_into_clauses(text)

        # 如果没有分割出条款，直接分析原文
        if not clauses:
            clauses = [text]

        for idx, clause in enumerate(clauses):
            if clause.strip():
                clause_risks = self._analyze_clause(clause, idx)
                risks.extend(clause_risks)

        return risks

    def _split_into_clauses(self, text: str) -> List[str]:
        """将文本分割成条款"""
        clauses = []

        # 先按双换行分割
        paragraphs = text.split('\n\n')

        # 如果没有双换行，按单换行分割
        if len(paragraphs) == 1:
            paragraphs = text.split('\n')

        for para in paragraphs:
            if not para.strip():
                continue

            # 按条款编号分割
            parts = re.split(r'(?:第[一二三四五六七八九十百\d]+条|第\d+条|^\d+\.|^[一二三四五六七八九十]+、)', para, flags=re.MULTILINE)
            for part in parts:
                part = part.strip()
                if part:
                    clauses.append(part)

        # 如果分割后只有一个很长的条款，按句子再分割
        if len(clauses) == 1 and len(clauses[0]) > 200:
            sentences = re.split(r'([。！？；\n])', clauses[0])
            new_clauses = []
            current = ""
            for s in sentences:
                current += s
                if s in '。！？；' and len(current) > 20:
                    new_clauses.append(current)
                    current = ""
            if current.strip():
                new_clauses.append(current)
            clauses = new_clauses

        return clauses

    def _analyze_clause(self, clause: str, position: int) -> List[DetectedRisk]:
        """分析单个条款"""
        risks = []

        # 各风险类型需要同时满足的关键词组合（严格模式）
        # 只有同时满足多个关键词才认为是风险
        strict_keywords = {
            "违约金过高": ["违约金", "滞纳金"],
            "保密条款不明确": ["保密", "机密"],
            "争议解决不利": ["仲裁", "诉讼", "管辖"],
            "责任边界模糊": ["免责", "不承担", "责任限制"],
            "终止条款不合理": ["单方面", "随时解除", "不得解除"],
            "支付条款风险": ["预付款"],
        }

        for risk_type, patterns in self.RISK_PATTERNS.items():
            matched_keywords = []

            # 检查正则模式
            for pattern in patterns:
                if re.search(pattern, clause):
                    matched_keywords.append(pattern)

            # 严格模式：必须匹配正则模式才算风险
            # 不再使用简单的关键词包含判断
            if matched_keywords:
                # 计算置信度
                confidence = min(0.5 + 0.1 * len(matched_keywords), 1.0)

                risks.append(DetectedRisk(
                    clause_text=clause[:500],  # 限制长度
                    risk_type=risk_type,
                    risk_keywords=list(set(matched_keywords)),
                    position=position,
                    confidence=confidence
                ))

        return risks

    def detect_in_clause(self, clause: str) -> List[str]:
        """
        快速检测条款中包含的风险类型

        Args:
            clause: 条款文本

        Returns:
            风险类型列表
        """
        risk_types = []
        for risk_type, keywords in self.risk_keywords.items():
            for keyword in keywords:
                if keyword in clause:
                    if risk_type not in risk_types:
                        risk_types.append(risk_type)
                    break
        return risk_types
