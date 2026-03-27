"""
合同审查流程测试
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from parser import PDFParser, DocxParser
from risk_analyzer import RiskDetector, RiskClassifier, ImpactAnalyzer
from rag import VectorStore, Retriever
from generator import ClauseGenerator, ReportGenerator


def test_parser():
    """测试解析器"""
    print("[TEST] 测试解析器...")

    # 测试PDF解析器
    pdf_parser = PDFParser()
    assert pdf_parser is not None

    # 测试Docx解析器
    docx_parser = DocxParser()
    assert docx_parser is not None

    print("[PASS] 解析器测试通过")


def test_risk_detector():
    """测试风险检测"""
    print("[TEST] 测试风险检测...")

    detector = RiskDetector()

    # 测试高违约金风险
    test_text = "如甲方违约，应向乙方支付合同总金额50%的违约金，且每日按合同金额的1%计算滞纳金。"
    risks = detector.detect(test_text)

    assert len(risks) > 0, "应该检测到风险"
    assert any("违约金" in r.risk_type for r in risks), "应该识别违约金风险"

    print(f"[PASS] 检测到 {len(risks)} 个风险")

    # 测试保密条款
    test_text2 = "乙方应对甲方提供的商业资料保密，保密期限为永久。"
    risks2 = detector.detect(test_text2)
    assert len(risks2) > 0, "应该检测到保密条款风险"

    print("[PASS] 风险检测测试通过")


def test_risk_classifier():
    """测试风险分级"""
    print("[TEST] 测试风险分级...")

    classifier = RiskClassifier()

    # 测试高风险
    result = classifier.classify("违约金过高", "违约金为合同金额的100%")
    assert result.risk_level.value in ["red", "yellow"], "应该识别为中高风险"

    # 测试低风险
    result2 = classifier.classify("违约金过高", "违约金为合同金额的10%")
    assert result2.risk_level.value == "green", "应该识别为绿色风险"

    print(f"风险等级: {result.risk_level.value}")
    print("[PASS] 风险分级测试通过")


def test_impact_analyzer():
    """测试影响分析"""
    print("[TEST] 测试影响分析...")

    analyzer = ImpactAnalyzer()

    result = analyzer.analyze("违约金过高", "甲方违约应支付50%违约金")

    assert result.affected_party.value in ["甲方", "乙方", "双方", "中立"]
    assert result.impact_description, "应该有影响描述"
    assert result.recommendation, "应该有建议"

    print(f"受影响方: {result.affected_party.value}")
    print("[PASS] 影响分析测试通过")


def test_vector_store():
    """测试向量库"""
    print("[TEST] 测试向量库...")

    vector_store = VectorStore()
    vector_store.initialize(recreate=False)

    # 测试检索
    results = vector_store.search("违约金过高", top_k=3)
    assert len(results) > 0, "应该检索到相关条款"

    print(f"检索到 {len(results)} 条相关法律条款")
    print("[PASS] 向量库测试通过")


def test_clause_generator():
    """测试建议生成"""
    print("[TEST] 测试建议生成...")

    generator = ClauseGenerator()

    # 测试建议生成（使用fallback，因为可能没有API密钥）
    suggestion = generator._generate_fallback_suggestion(
        clause_text="甲方违约应支付合同金额100%的违约金",
        risk_type="违约金过高",
        legal_basis="《民法典》第585条"
    )

    assert suggestion.original_clause, "应该有原文"
    assert suggestion.suggested_clause, "应该有建议文本"
    assert "违约金" in suggestion.suggested_clause, "建议应该包含违约金"

    print("[PASS] 建议生成测试通过")


def test_report_generator():
    """测试报告生成"""
    print("[TEST] 测试报告生成...")

    generator = ReportGenerator()

    report = generator.create_report(
        file_name="test_contract.pdf",
        file_type="pdf",
        risks=[
            {
                "clause_text": "测试条款",
                "risk_type": "违约金过高",
                "level": "red",
                "description": "违约金过高",
                "impact_party": "甲方"
            }
        ],
        suggestions=[
            {
                "risk_type": "违约金过高",
                "reason": "建议调整",
                "suggested_clause": "违约金为合同金额的20%"
            }
        ],
        summary={"red": 1, "yellow": 0, "green": 0},
        overall_rating="建议修改后签"
    )

    assert report.title == "test_contract.pdf"
    assert report.summary["red"] == 1

    # 生成文本摘要
    summary_text = generator.generate_text_summary(report)
    assert "合同审查报告" in summary_text

    print("[PASS] 报告生成测试通过")


def test_full_pipeline():
    """测试完整流程"""
    print("[TEST] 测试完整审查流程...")

    # 模拟合同文本
    contract_text = """
    合同编号：2024-001
    甲方：北京科技有限公司
    乙方：上海贸易有限公司

    第一条 服务内容
    乙方向甲方提供软件开发服务，具体内容见附件。

    第二条 合同金额及支付
    合同总金额为人民币100万元，甲方应在签订合同后3日内支付全额定金。如甲方逾期付款，每逾期一日应按合同金额的5%向乙方支付滞纳金。

    第三条 保密义务
    乙方应对甲方的商业秘密负有保密义务，保密期限为永久。

    第四条 违约责任
    如任何一方违约，违约方应向守约方支付合同总金额200%的违约金。

    第五条 争议解决
    本合同引起的任何争议，由甲方所在地人民法院管辖。

    第六条 合同解除
    甲方有权在合同履行期间随时单方面解除本合同，解除通知到达乙方时合同即终止，乙方已收取的费用不予退还。
    """

    # 1. 风险检测
    detector = RiskDetector()
    risks = detector.detect(contract_text)

    print(f"检测到 {len(risks)} 个风险条款")

    # 2. 风险分级
    classifier = RiskClassifier()
    impact_analyzer = ImpactAnalyzer()

    analyzed_risks = []
    for risk in risks:
        classification = classifier.classify(risk.risk_type, risk.clause_text)
        impact = impact_analyzer.analyze(risk.risk_type, risk.clause_text)

        analyzed_risks.append({
            "clause_text": risk.clause_text[:200],
            "risk_type": risk.risk_type,
            "level": classification.risk_level.value,
            "description": classification.description,
            "impact_party": impact.affected_party.value
        })

    # 3. 统计
    summary = classifier.classify_batch([
        type('obj', (object,), {'risk_level': r['level']}) for r in analyzed_risks
    ])

    print(f"风险统计: 红={summary['red']}, 黄={summary['yellow']}, 绿={summary['green']}")

    # 4. 评级
    overall_rating = "建议签"
    if summary["red"] > 0:
        overall_rating = "建议修改后签"
    if summary["red"] >= 3:
        overall_rating = "不建议签"

    print(f"整体评级: {overall_rating}")

    print("[PASS] 完整流程测试通过")


if __name__ == "__main__":
    print("=" * 50)
    print("合同审查风险Agent - 测试套件")
    print("=" * 50)

    try:
        test_parser()
        test_risk_detector()
        test_risk_classifier()
        test_impact_analyzer()
        test_vector_store()
        test_clause_generator()
        test_report_generator()
        test_full_pipeline()

        print("\n" + "=" * 50)
        print("所有测试通过!")
        print("=" * 50)
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
