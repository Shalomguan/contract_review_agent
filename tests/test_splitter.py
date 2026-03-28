"""Contract splitter unit tests."""
from services.splitters.contract_splitter import ContractSplitter


splitter = ContractSplitter()


def test_splitter_keeps_parent_heading_title_but_excludes_it_from_body() -> None:
    text = """第一条 服务内容
乙方负责为甲方提供系统开发与部署服务。"""

    clauses = splitter.split(text)

    assert len(clauses) == 1
    assert clauses[0].title == "第一条 服务内容"
    assert clauses[0].text == "乙方负责为甲方提供系统开发与部署服务。"


def test_splitter_skips_empty_parent_heading_and_keeps_child_clauses() -> None:
    text = """第五条 合同解除
5.1 甲方可随时单方解除合同。
5.2 乙方不得解除合同。"""

    clauses = splitter.split(text)

    assert [clause.title for clause in clauses] == [
        "5.1 甲方可随时单方解除合同。",
        "5.2 乙方不得解除合同。",
    ]
    assert [clause.text for clause in clauses] == [
        "5.1 甲方可随时单方解除合同。",
        "5.2 乙方不得解除合同。",
    ]


def test_splitter_falls_back_to_paragraphs_without_headings() -> None:
    text = """甲方委托乙方提供服务。

双方应按约履行付款义务。"""

    clauses = splitter.split(text)

    assert len(clauses) == 2
    assert clauses[0].text == "甲方委托乙方提供服务。"
    assert clauses[1].text == "双方应按约履行付款义务。"


def test_splitter_does_not_mix_parent_heading_into_child_text() -> None:
    text = """第六条 争议解决
6.1 所有争议由甲方所在地法院管辖。"""

    clauses = splitter.split(text)

    assert len(clauses) == 1
    assert clauses[0].title == "6.1 所有争议由甲方所在地法院管辖。"
    assert clauses[0].text == "6.1 所有争议由甲方所在地法院管辖。"
