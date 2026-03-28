"""Rule engine unit tests."""
from models.review import Clause
from services.analyzers.rule_engine import RuleEngine


def build_clause(text: str) -> Clause:
    return Clause(clause_id="clause_1", title="测试条款", text=text, source_index=1)


def detect_types(text: str) -> list[str]:
    engine = RuleEngine()
    detections = engine.detect(build_clause(text))
    return [item.risk_type for item in detections]


def test_rule_engine_detects_auto_renewal_trap() -> None:
    types = detect_types("合同到期后自动续约一年，如乙方未在到期前五日书面提出异议，视为同意续约。")
    assert "auto_renewal_trap" in types


def test_rule_engine_detects_unilateral_change_right() -> None:
    types = detect_types("甲方有权随时调整价格、收费标准和服务规则，乙方应继续履行。")
    assert "unilateral_change_right" in types


def test_rule_engine_detects_acceptance_unfairness() -> None:
    types = detect_types("项目验收以甲方验收结果为准，甲方有权决定是否通过。")
    assert "acceptance_unfairness" in types


def test_rule_engine_detects_payment_imbalance() -> None:
    types = detect_types("乙方应在签约后两个工作日内支付80%预付款，剩余款项由甲方单方确认后支付。")
    assert "payment_imbalance" in types


def test_rule_engine_detects_confidentiality_imbalance() -> None:
    types = detect_types("仅乙方承担保密义务，且保密期限为永久。")
    assert "confidentiality_imbalance" in types


def test_rule_engine_detects_non_compete_or_exclusivity() -> None:
    types = detect_types("合作期间及终止后两年内，乙方不得与任何第三方合作或从事同类业务，甲方享有独家合作权。")
    assert "non_compete_or_exclusivity" in types


def test_rule_engine_detects_delivery_or_notice_trap() -> None:
    types = detect_types("甲方通过系统消息发送通知的，发送即视为送达并立即生效，无需乙方确认。")
    assert "delivery_or_notice_trap" in types


def test_rule_engine_detects_termination_penalty_unfairness() -> None:
    types = detect_types("乙方提前解约的，应一次性支付全部剩余费用且已付款项不予退还。")
    assert "termination_penalty_unfairness" in types


def test_rule_engine_detects_liability_imbalance() -> None:
    types = detect_types("如发生任何损失，乙方承担全部责任并全额赔偿，甲方不承担责任。")
    assert "liability_imbalance" in types


def test_rule_engine_detects_missing_core_terms() -> None:
    types = detect_types("双方约定进行验收。")
    assert "missing_core_terms" in types


def test_rule_engine_detects_required_mvp_risks() -> None:
    types = detect_types("甲方有权随时单方解除本合同，乙方不得主张任何赔偿。")
    assert "unilateral_termination" in types


def test_rule_engine_does_not_flag_balanced_confidentiality_clause() -> None:
    types = detect_types("甲乙双方均应对履约过程中知悉的商业秘密承担保密义务，保密期限为合同终止后三年，但已公开信息除外。")
    assert "confidentiality_imbalance" not in types


def test_rule_engine_does_not_flag_standard_dispute_resolution() -> None:
    types = detect_types("因本合同引起的争议，双方协商不成的，可向被告住所地有管辖权的人民法院提起诉讼。")
    assert "biased_dispute_resolution" not in types


def test_rule_engine_does_not_flag_reasonable_liquidated_damages() -> None:
    types = detect_types("任何一方违约的，应按未履行部分价款的10%承担违约责任。")
    assert "excessive_liquidated_damages" not in types


def test_rule_engine_does_not_flag_balanced_acceptance_clause() -> None:
    types = detect_types("甲方应在收到交付物后五个工作日内按双方确认的标准完成验收，并就异议部分与乙方协商处理。")
    assert "acceptance_unfairness" not in types


def test_rule_engine_ignores_empty_shell_heading_clause() -> None:
    types = detect_types("第一条 服务内容")
    assert types == []
