"""Deterministic rule engine for common contract risks."""
from __future__ import annotations

import re
from dataclasses import dataclass

from models.review import Clause, RiskDetection


@dataclass(frozen=True, slots=True)
class KeywordRule:
    """Keyword-based rule definition."""

    risk_type: str
    risk_level: str
    rule_name: str
    groups: tuple[tuple[str, ...], ...]
    exclusion_groups: tuple[tuple[str, ...], ...] = ()


@dataclass(frozen=True, slots=True)
class MissingTermRule:
    """Rule definition for missing or weak core clauses."""

    risk_type: str
    risk_level: str
    rule_name: str
    topic_keywords: tuple[str, ...]
    required_keywords: tuple[str, ...]


class RuleEngine:
    """Detect high-signal risks from contract clauses."""

    keyword_rules = (
        KeywordRule(
            risk_type="unilateral_exemption",
            risk_level="high",
            rule_name="single_party_exemption",
            groups=(("甲方", "买方", "委托方", "平台方"), ("无需承担责任", "不承担任何责任", "免责", "全部免责")),
        ),
        KeywordRule(
            risk_type="unilateral_termination",
            risk_level="high",
            rule_name="single_party_termination",
            groups=(("甲方", "买方", "委托方", "平台方"), ("单方解除", "随时解除", "有权解除", "无条件解除")),
        ),
        KeywordRule(
            risk_type="unilateral_interpretation",
            risk_level="high",
            rule_name="single_party_interpretation",
            groups=(("甲方", "平台", "主办方", "运营方"), ("最终解释权", "单方解释", "解释权归")),
        ),
        KeywordRule(
            risk_type="one_sided_ip_assignment",
            risk_level="medium",
            rule_name="one_sided_ip_assignment",
            groups=(("知识产权", "著作权", "源代码", "成果"), ("归甲方所有", "全部归", "永久归", "无偿转让"), ("甲方", "委托方", "买方")),
        ),
        KeywordRule(
            risk_type="biased_dispute_resolution",
            risk_level="high",
            rule_name="biased_dispute_resolution",
            groups=(("争议", "诉讼", "仲裁"), ("甲方所在地法院", "甲方所在地人民法院", "甲方住所地", "由甲方指定仲裁机构")),
        ),
        KeywordRule(
            risk_type="auto_renewal_trap",
            risk_level="low",
            rule_name="auto_renewal_trap",
            groups=(("自动续约", "自动延续", "期满自动顺延"), ("未提出书面异议", "未通知终止", "视为同意续约", "默认续约")),
        ),
        KeywordRule(
            risk_type="unilateral_change_right",
            risk_level="high",
            rule_name="unilateral_change_right",
            groups=(("甲方", "平台", "卖方", "服务方"), ("有权调整", "有权变更", "可随时修改", "单方变更", "自行变更", "调整", "修改"), ("价格", "服务规则", "收费标准", "履约标准", "通知方式")),
        ),
        KeywordRule(
            risk_type="payment_imbalance",
            risk_level="medium",
            rule_name="payment_imbalance_unilateral_decision",
            groups=(("付款", "结算", "费用", "价款"), ("以甲方确认为准", "以平台认定为准", "由甲方单方确认", "由平台单方决定")),
            exclusion_groups=(("双方确认", "共同确认", "对账确认"),),
        ),
        KeywordRule(
            risk_type="acceptance_unfairness",
            risk_level="medium",
            rule_name="acceptance_unfairness_unilateral",
            groups=(("验收",), ("以甲方验收结果为准", "由甲方单方认定", "甲方有权决定是否通过", "甲方认定为准")),
            exclusion_groups=(("双方确认", "共同验收", "协商确认"),),
        ),
        KeywordRule(
            risk_type="acceptance_unfairness",
            risk_level="medium",
            rule_name="acceptance_unfairness_deemed",
            groups=(("验收",), ("视为验收合格", "默认验收", "逾期未反馈视为合格", "逾期未提出异议视为验收通过")),
        ),
        KeywordRule(
            risk_type="confidentiality_imbalance",
            risk_level="medium",
            rule_name="confidentiality_imbalance_scope",
            groups=(("甲方", "乙方", "一方"), ("保密义务", "保密责任", "保密信息", "保密")),
        ),
        KeywordRule(
            risk_type="confidentiality_imbalance",
            risk_level="medium",
            rule_name="confidentiality_imbalance_duration",
            groups=(("保密",), ("永久", "无限期", "长期有效")),
            exclusion_groups=(("法律另有规定", "公开信息", "非因违约已公开"),),
        ),
        KeywordRule(
            risk_type="non_compete_or_exclusivity",
            risk_level="high",
            rule_name="non_compete_or_exclusivity",
            groups=(("独家", "排他", "竞业限制", "不得与第三方合作"), ("不得", "禁止", "唯一", "排除")),
        ),
        KeywordRule(
            risk_type="delivery_or_notice_trap",
            risk_level="medium",
            rule_name="delivery_or_notice_trap",
            groups=(("通知", "送达", "邮件", "短信", "系统消息"), ("发出即视为送达", "发送即视为送达", "系统通知即生效", "无需确认")),
        ),
        KeywordRule(
            risk_type="termination_penalty_unfairness",
            risk_level="medium",
            rule_name="termination_penalty_unfairness",
            groups=(("解除", "终止", "提前解约"), ("支付全部剩余费用", "一次性支付全部费用", "不予退还", "承担全部损失")),
        ),
        KeywordRule(
            risk_type="liability_imbalance",
            risk_level="medium",
            rule_name="liability_imbalance",
            groups=(("赔偿", "违约责任", "损失"), ("乙方承担全部责任", "乙方承担全部损失", "甲方不承担责任", "由乙方全额赔偿")),
        ),
    )

    missing_term_rules = (
        MissingTermRule(
            risk_type="missing_core_terms",
            risk_level="low",
            rule_name="missing_acceptance_standard",
            topic_keywords=("验收", "交付"),
            required_keywords=("标准", "条件", "时间", "流程"),
        ),
        MissingTermRule(
            risk_type="missing_core_terms",
            risk_level="low",
            rule_name="missing_payment_cycle",
            topic_keywords=("付款", "结算", "费用"),
            required_keywords=("时间", "金额", "节点", "方式"),
        ),
        MissingTermRule(
            risk_type="missing_core_terms",
            risk_level="low",
            rule_name="missing_delivery_schedule",
            topic_keywords=("交付", "履行", "服务"),
            required_keywords=("期限", "时间", "节点", "里程碑"),
        ),
    )

    percentage_pattern = re.compile(r"(\d+(?:\.\d+)?)\s*%")
    amount_pattern = re.compile(r"(\d+(?:\.\d+)?)\s*(?:元|万元|万|人民币)")

    def detect(self, clause: Clause) -> list[RiskDetection]:
        """Detect all known risks from a single clause."""
        text = self._normalize(clause.text)
        if not self._is_substantive_text(text):
            return []

        detections: list[RiskDetection] = []
        seen: set[tuple[str, str]] = set()

        for rule in self.keyword_rules:
            evidence = self._match_keyword_rule(text, rule)
            if not evidence:
                continue
            key = (rule.risk_type, rule.rule_name)
            if key in seen:
                continue
            seen.add(key)
            detections.append(
                RiskDetection(
                    risk_type=rule.risk_type,
                    risk_level=rule.risk_level,
                    rule_name=rule.rule_name,
                    evidence=evidence,
                )
            )

        excessive = self._detect_excessive_liquidated_damages(text)
        if excessive:
            detections.append(excessive)

        detections.extend(self._detect_missing_core_terms(text))
        detections.extend(self._detect_payment_imbalance_by_ratio(text, seen))
        detections.extend(self._detect_confidentiality_scope_imbalance(text, seen))

        return detections

    def _match_keyword_rule(self, text: str, rule: KeywordRule) -> list[str]:
        if rule.exclusion_groups and any(self._contains_any(text, group) for group in rule.exclusion_groups):
            return []

        evidence: list[str] = []
        for group in rule.groups:
            token = self._find_first(text, group)
            if not token:
                return []
            evidence.append(token)
        return evidence

    def _detect_excessive_liquidated_damages(self, text: str) -> RiskDetection | None:
        if not self._contains_any(text, ("违约金", "滞纳金", "罚金", "违约责任")):
            return None

        percentages = [float(value) for value in self.percentage_pattern.findall(text)]
        if any(value >= 30 for value in percentages):
            return RiskDetection(
                risk_type="excessive_liquidated_damages",
                risk_level="high",
                rule_name="excessive_penalty_percentage",
                evidence=[f"{value}%" for value in percentages if value >= 30],
            )

        if self._contains_any(text, ("按日", "每日", "每逾期一日")) and any(value >= 5 for value in percentages):
            return RiskDetection(
                risk_type="excessive_liquidated_damages",
                risk_level="high",
                rule_name="excessive_daily_penalty_percentage",
                evidence=[f"{value}%" for value in percentages if value >= 5],
            )

        amounts = [float(value) for value in self.amount_pattern.findall(text)]
        if self._contains_any(text, ("固定违约金", "一次性违约金")) and amounts:
            return RiskDetection(
                risk_type="excessive_liquidated_damages",
                risk_level="medium",
                rule_name="fixed_penalty_amount",
                evidence=[str(amounts[0])],
            )

        return None

    def _detect_missing_core_terms(self, text: str) -> list[RiskDetection]:
        detections: list[RiskDetection] = []
        for rule in self.missing_term_rules:
            if not self._contains_any(text, rule.topic_keywords):
                continue
            if any(keyword in text for keyword in rule.required_keywords):
                continue
            detections.append(
                RiskDetection(
                    risk_type=rule.risk_type,
                    risk_level=rule.risk_level,
                    rule_name=rule.rule_name,
                    evidence=[rule.topic_keywords[0]],
                )
            )
        return detections

    def _detect_payment_imbalance_by_ratio(
        self,
        text: str,
        seen: set[tuple[str, str]],
    ) -> list[RiskDetection]:
        if not self._contains_any(text, ("预付款", "预付", "首付款")):
            return []

        percentages = [float(value) for value in self.percentage_pattern.findall(text)]
        if not any(value >= 70 for value in percentages):
            return []

        key = ("payment_imbalance", "payment_imbalance_high_prepayment")
        if key in seen:
            return []

        seen.add(key)
        return [
            RiskDetection(
                risk_type="payment_imbalance",
                risk_level="medium",
                rule_name="payment_imbalance_high_prepayment",
                evidence=[f"{value}%" for value in percentages if value >= 70],
            )
        ]

    def _detect_confidentiality_scope_imbalance(
        self,
        text: str,
        seen: set[tuple[str, str]],
    ) -> list[RiskDetection]:
        if "保密" not in text:
            return []
        if not self._contains_any(text, ("仅乙方", "乙方应", "乙方承担", "仅由乙方")):
            return []
        if self._contains_any(text, ("双方", "甲乙双方", "双方均应")):
            return []

        key = ("confidentiality_imbalance", "confidentiality_one_sided_obligation")
        if key in seen:
            return []
        seen.add(key)
        return [
            RiskDetection(
                risk_type="confidentiality_imbalance",
                risk_level="medium",
                rule_name="confidentiality_one_sided_obligation",
                evidence=["仅乙方承担保密义务"],
            )
        ]

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"\s+", "", text)

    @staticmethod
    def _is_substantive_text(text: str) -> bool:
        if len(text) < 8:
            return False
        return re.fullmatch(r"第[一二三四五六七八九十百零\d]+条[\w\u4e00-\u9fff：:、.)）-]*", text) is None

    @staticmethod
    def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
        return any(keyword in text for keyword in keywords)

    @staticmethod
    def _find_first(text: str, keywords: tuple[str, ...]) -> str | None:
        for keyword in keywords:
            if keyword in text:
                return keyword
        return None
