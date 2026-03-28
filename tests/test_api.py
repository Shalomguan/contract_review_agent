"""API integration tests for the MVP."""
from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from api.app import create_app
from core.config import Settings


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_CONTRACT = (PROJECT_ROOT / "docs" / "sample_contract.txt").read_text(encoding="utf-8")
SAFE_CONTRACT = """软件服务合同

第一条 服务内容
乙方按照双方确认的项目计划提供系统实施服务。

第二条 付款安排
甲方应在每个里程碑验收合格后五个工作日内支付对应价款。

第三条 保密义务
甲乙双方均应对履约过程中知悉的商业秘密承担保密义务，保密期限为合同终止后三年，但依法应披露或已公开的信息除外。

第四条 验收安排
甲方应在收到交付物后五个工作日内按照双方确认的验收标准完成验收，并就异议部分书面通知乙方整改。

第五条 争议解决
因本合同发生争议，双方协商不成的，可向被告住所地有管辖权的人民法院提起诉讼。
"""

GENERIC_RISKY_CONTRACT = """通用合作合同

第一条 自动续约
本合同到期后自动续约一年，如乙方未在到期前五日书面提出异议，视为同意续约。

第二条 价格调整
甲方有权随时调整价格、收费标准和服务规则，乙方应继续履行。

第三条 保密义务
仅乙方承担保密义务，且保密期限为永久。

第四条 验收
项目验收以甲方验收结果为准，甲方有权决定是否通过。

第五条 通知送达
甲方通过系统消息发送通知的，发送即视为送达并立即生效，无需乙方确认。
"""


def build_test_client(tmp_path: Path) -> TestClient:
    settings = Settings(
        data_dir=tmp_path / "data",
        database_path=tmp_path / "data" / "reviews.db",
        upload_dir=tmp_path / "data" / "uploads",
    )
    settings.ensure_directories()
    app = create_app(settings)
    return TestClient(app)


def create_review(client: TestClient, document_name: str, text: str = SAMPLE_CONTRACT) -> dict:
    response = client.post(
        "/api/review/analyze",
        json={"document_name": document_name, "text": text},
    )
    assert response.status_code == 200
    return response.json()


def test_analyze_text_creates_review(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    payload = create_review(client, "sample_contract.txt")

    assert payload["document_name"] == "sample_contract.txt"
    assert payload["review_id"]
    assert payload["risks"]
    assert {risk["risk_level"] for risk in payload["risks"]}.issubset({"high", "medium", "low"})
    assert payload["risks"][0]["references"]
    assert "???" not in payload["summary"]
    assert "???" not in payload["risks"][0]["risk_reason"]

    detail = client.get(f"/api/review/{payload['review_id']}")
    assert detail.status_code == 200
    assert detail.json()["review_id"] == payload["review_id"]
    assert detail.json()["risks"][0]["references"]


def test_upload_txt_file_is_supported(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    response = client.post(
        "/api/review/upload",
        files={"file": ("sample_contract.txt", SAMPLE_CONTRACT.encode("utf-8"), "text/plain")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["document_name"] == "sample_contract.txt"
    assert len(payload["risks"]) >= 1
    assert payload["risks"][0]["references"]


def test_list_reviews_returns_history(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    create_review(client, "contract_a.txt")
    create_review(client, "contract_b.txt", SAFE_CONTRACT)

    response = client.get("/api/reviews")
    assert response.status_code == 200
    payload = response.json()
    items = payload["items"]
    assert len(items) == 2
    assert {item["document_name"] for item in items} == {"contract_a.txt", "contract_b.txt"}
    assert payload["total"] == 2
    assert payload["limit"] == 20
    assert payload["offset"] == 0


def test_list_reviews_supports_document_name_search(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    create_review(client, "procurement_contract.docx")
    create_review(client, "employment_contract.docx")

    response = client.get("/api/reviews", params={"document_name": "procurement"})
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["document_name"] == "procurement_contract.docx"


def test_list_reviews_supports_risk_level_filter_and_pagination(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    create_review(client, "risky_1.txt", GENERIC_RISKY_CONTRACT)
    create_review(client, "risky_2.txt", SAMPLE_CONTRACT)
    create_review(client, "safe.txt", SAFE_CONTRACT)

    high_only = client.get("/api/reviews", params={"risk_level": "high", "limit": 1, "offset": 0})
    assert high_only.status_code == 200
    payload = high_only.json()
    assert payload["limit"] == 1
    assert payload["offset"] == 0
    assert payload["total"] == 2
    assert len(payload["items"]) == 1
    assert payload["items"][0]["risk_counts"]["high"] > 0


def test_list_reviews_supports_date_range_search(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    create_review(client, "today_contract.txt")
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    include_today = client.get("/api/reviews", params={"date_from": today, "date_to": today})
    assert include_today.status_code == 200
    assert len(include_today.json()["items"]) == 1

    exclude_today = client.get("/api/reviews", params={"date_to": yesterday})
    assert exclude_today.status_code == 200
    assert exclude_today.json()["items"] == []


def test_list_reviews_rejects_invalid_date_range(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    response = client.get(
        "/api/reviews",
        params={
            "date_from": date.today().isoformat(),
            "date_to": (date.today() - timedelta(days=1)).isoformat(),
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "date_from must be earlier than or equal to date_to."


def test_delete_review_removes_history_record(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    review = create_review(client, "deletable_contract.txt")

    delete_response = client.delete(f"/api/review/{review['review_id']}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"review_id": review["review_id"], "deleted": True}

    detail_response = client.get(f"/api/review/{review['review_id']}")
    assert detail_response.status_code == 404


def test_analyze_text_rejects_empty_text(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    response = client.post(
        "/api/review/analyze",
        json={"document_name": "empty.txt", "text": ""},
    )
    assert response.status_code == 422


def test_upload_rejects_empty_file(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    response = client.post(
        "/api/review/upload",
        files={"file": ("empty.txt", b"", "text/plain")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded file is empty."


def test_upload_rejects_unsupported_file_type(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    response = client.post(
        "/api/review/upload",
        files={"file": ("table.xlsx", b"fake-binary", "application/octet-stream")},
    )
    assert response.status_code == 400
    assert "Unsupported document type" in response.json()["detail"]


def test_get_review_returns_404_for_missing_record(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    response = client.get("/api/review/not-found")
    assert response.status_code == 404
    assert response.json()["detail"] == "Review not found."


def test_analyze_generic_risky_contract_returns_multiple_risk_types(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    payload = create_review(client, "generic_risky.txt", GENERIC_RISKY_CONTRACT)

    risk_types = {item["risk_type"] for item in payload["risks"]}
    assert {"auto_renewal_trap", "unilateral_change_right", "confidentiality_imbalance", "acceptance_unfairness"} <= risk_types


def test_analyze_relatively_balanced_contract_returns_fewer_risks(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    risky_payload = create_review(client, "generic_risky.txt", GENERIC_RISKY_CONTRACT)
    safe_payload = create_review(client, "balanced_contract.txt", SAFE_CONTRACT)

    assert len(safe_payload["risks"]) <= len(risky_payload["risks"])


def test_duplicate_risk_hits_are_merged_per_clause(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    contract = """保密条款

仅乙方承担保密义务，且保密期限为永久，乙方应对全部保密信息承担保密责任。
"""

    payload = create_review(client, "dedupe_contract.txt", contract)
    confidentiality_risks = [item for item in payload["risks"] if item["risk_type"] == "confidentiality_imbalance"]

    assert len(confidentiality_risks) == 1


def test_history_read_keeps_summary_and_references_after_old_summary_cleanup(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    payload = create_review(client, "legacy_summary.txt", GENERIC_RISKY_CONTRACT)
    database_path = tmp_path / "data" / "reviews.db"

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "UPDATE reviews SET summary = ? WHERE review_id = ?",
            ("锟斤拷锟斤拷??", payload["review_id"]),
        )
        connection.commit()

    list_response = client.get("/api/reviews")
    assert list_response.status_code == 200
    item = next(entry for entry in list_response.json()["items"] if entry["review_id"] == payload["review_id"])
    assert "???" not in item["summary"]

    detail_response = client.get(f"/api/review/{payload['review_id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["risks"][0]["references"]


def test_analyze_nested_headings_skips_empty_parent_clause(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    contract = """合同解除与争议解决

第五条 合同解除
5.1 甲方可随时单方解除合同。
5.2 乙方不得解除合同。

第六条 争议解决
6.1 所有争议由甲方所在地法院管辖。"""

    payload = create_review(client, "nested_headings.txt", contract)

    clause_titles = {item["clause_title"] for item in payload["risks"]}
    clause_texts = {item["clause_text"] for item in payload["risks"]}

    assert "第五条 合同解除" not in clause_titles
    assert "第六条 争议解决" not in clause_titles
    assert "第五条 合同解除" not in clause_texts
    assert "第六条 争议解决" not in clause_texts
    assert any(title.startswith("5.1") for title in clause_titles)


def test_health_exposes_rag_mode(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)

    response = client.get('/health')

    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'ok'
    assert payload['rag_mode'] in {'vector', 'lexical_fallback'}
