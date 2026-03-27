"""Rule engine unit tests."""
from models.review import Clause
from services.analyzers.rule_engine import RuleEngine


def test_rule_engine_detects_multiple_high_signal_risks() -> None:
    engine = RuleEngine()
    clause = Clause(
        clause_id="clause_1",
        title="第四条 单方解除",
        text="甲方有权在任何时候单方解除本合同，且无需说明理由。",
        source_index=1,
    )

    detections = engine.detect(clause)
    assert any(item.risk_type == "unilateral_termination" for item in detections)


def test_rule_engine_scores_excessive_liquidated_damages() -> None:
    engine = RuleEngine()
    clause = Clause(
        clause_id="clause_2",
        title="违约责任",
        text="如乙方违约，应向甲方支付合同总金额 60% 的违约金。",
        source_index=2,
    )

    detections = engine.detect(clause)
    damages = next(item for item in detections if item.risk_type == "excessive_liquidated_damages")
    assert damages.risk_level == "high"
