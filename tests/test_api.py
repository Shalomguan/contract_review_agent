"""API integration tests for the MVP."""
from __future__ import annotations

import re
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


def authenticate(client: TestClient, username: str = "alice", password: str = "password123") -> dict[str, str]:
    response = client.post('/api/auth/register', json={'username': username, 'password': password})
    assert response.status_code == 200
    token = response.json()['access_token']
    return {'Authorization': f'Bearer {token}'}


def create_review(client: TestClient, headers: dict[str, str], document_name: str, text: str = SAMPLE_CONTRACT) -> dict:
    response = client.post(
        "/api/review/analyze",
        json={"document_name": document_name, "text": text},
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()


def test_register_login_and_me(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)

    register = client.post('/api/auth/register', json={'username': 'alice', 'password': 'password123'})
    assert register.status_code == 200
    token = register.json()['access_token']

    login = client.post('/api/auth/login', json={'username': 'alice', 'password': 'password123'})
    assert login.status_code == 200

    me = client.get('/api/auth/me', headers={'Authorization': f'Bearer {token}'})
    assert me.status_code == 200
    assert me.json()['username'] == 'alice'


def test_review_endpoints_require_authentication(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)

    response = client.get('/api/reviews')
    assert response.status_code == 401


def test_reviews_are_isolated_per_user(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    alice = authenticate(client, 'alice', 'password123')
    bob = authenticate(client, 'bob', 'password123')

    review = create_review(client, alice, 'alice_contract.txt')

    list_for_bob = client.get('/api/reviews', headers=bob)
    assert list_for_bob.status_code == 200
    assert list_for_bob.json()['items'] == []

    detail_for_bob = client.get(f"/api/review/{review['review_id']}", headers=bob)
    assert detail_for_bob.status_code == 404


def test_analyze_text_creates_review(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    headers = authenticate(client)
    payload = create_review(client, headers, "sample_contract.txt")

    assert re.fullmatch(r"contract\d{8}-\d{4}(?:-\d+)?", payload["document_name"])
    assert payload["review_id"]
    assert payload["risks"]
    assert {risk["risk_level"] for risk in payload["risks"]}.issubset({"high", "medium", "low"})
    assert payload["document_text"] == SAMPLE_CONTRACT.strip()
    assert payload["risks"][0]["references"]
    assert payload["risks"][0]["references"][0]["category"] in {"review_rule", "drafting_guidance", "balanced_clause", "legal_basis"}
    assert "???" not in payload["summary"]
    assert "???" not in payload["risks"][0]["risk_reason"]

    detail = client.get(f"/api/review/{payload['review_id']}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["review_id"] == payload["review_id"]
    assert detail.json()["document_text"] == SAMPLE_CONTRACT.strip()
    assert detail.json()["risks"][0]["references"]


def test_upload_txt_file_is_supported(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    headers = authenticate(client)
    response = client.post(
        "/api/review/upload",
        files={"file": ("sample_contract.txt", SAMPLE_CONTRACT.encode("utf-8"), "text/plain")},
        headers=headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert re.fullmatch(r"contract\d{8}-\d{4}(?:-\d+)?\.txt", payload["document_name"])
    assert len(payload["risks"]) >= 1
    assert payload["risks"][0]["references"]


def test_list_reviews_returns_history(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    headers = authenticate(client)
    first = create_review(client, headers, "contract_a.txt")
    create_review(client, headers, "contract_b.txt", SAFE_CONTRACT)

    response = client.get("/api/reviews", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    items = payload["items"]
    assert len(items) == 2
    assert all(item["document_name"].startswith("contract") for item in items)
    assert payload["total"] == 2
    assert payload["limit"] == 20
    assert payload["offset"] == 0


def test_list_reviews_supports_document_name_search(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    headers = authenticate(client)
    first = create_review(client, headers, "procurement_contract.docx")
    create_review(client, headers, "employment_contract.docx")

    response = client.get("/api/reviews", params={"document_name": "procurement"}, headers=headers)
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["review_id"] == first["review_id"]


def test_list_reviews_supports_risk_level_filter_and_pagination(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    headers = authenticate(client)
    create_review(client, headers, "risky_1.txt", GENERIC_RISKY_CONTRACT)
    create_review(client, headers, "risky_2.txt", SAMPLE_CONTRACT)
    create_review(client, headers, "safe.txt", SAFE_CONTRACT)

    high_only = client.get("/api/reviews", params={"risk_level": "high", "limit": 1, "offset": 0}, headers=headers)
    assert high_only.status_code == 200
    payload = high_only.json()
    assert payload["limit"] == 1
    assert payload["offset"] == 0
    assert payload["total"] == 2
    assert len(payload["items"]) == 1
    assert payload["items"][0]["risk_counts"]["high"] > 0


def test_list_reviews_uses_local_timezone_for_date_filters(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    headers = authenticate(client)
    payload = create_review(client, headers, "timezone_contract.txt")
    database_path = tmp_path / "data" / "reviews.db"

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "UPDATE reviews SET created_at = ?, review_payload = json_set(review_payload, '$.created_at', ?) WHERE review_id = ?",
            ("2026-03-28T16:30:00+00:00", "2026-03-28T16:30:00+00:00", payload["review_id"]),
        )
        connection.commit()

    response = client.get("/api/reviews", params={"date_from": "2026-03-29", "date_to": "2026-03-29"}, headers=headers)
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["review_id"] == payload["review_id"]


def test_list_reviews_supports_date_range_search(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    headers = authenticate(client)
    create_review(client, headers, "today_contract.txt")
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    include_today = client.get("/api/reviews", params={"date_from": today, "date_to": today}, headers=headers)
    assert include_today.status_code == 200
    assert len(include_today.json()["items"]) == 1

    exclude_today = client.get("/api/reviews", params={"date_to": yesterday}, headers=headers)
    assert exclude_today.status_code == 200
    assert exclude_today.json()["items"] == []


def test_list_reviews_rejects_invalid_date_range(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    headers = authenticate(client)
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
    headers = authenticate(client)
    review = create_review(client, headers, "deletable_contract.txt")

    delete_response = client.delete(f"/api/review/{review['review_id']}", headers=headers)
    assert delete_response.status_code == 200
    assert delete_response.json() == {"review_id": review["review_id"], "deleted": True}

    detail_response = client.get(f"/api/review/{review['review_id']}", headers=headers)
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
    headers = authenticate(client)
    response = client.post(
        "/api/review/upload",
        files={"file": ("table.xlsx", b"fake-binary", "application/octet-stream")},
        headers=headers,
    )
    assert response.status_code == 400
    assert "Unsupported document type" in response.json()["detail"]


def test_get_review_returns_404_for_missing_record(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    headers = authenticate(client)
    response = client.get("/api/review/not-found", headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Review not found."


def test_analyze_generic_risky_contract_returns_multiple_risk_types(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    headers = authenticate(client)
    payload = create_review(client, headers, "generic_risky.txt", GENERIC_RISKY_CONTRACT)

    risk_types = {item["risk_type"] for item in payload["risks"]}
    assert {"auto_renewal_trap", "unilateral_change_right", "confidentiality_imbalance", "acceptance_unfairness"} <= risk_types


def test_analyze_relatively_balanced_contract_returns_fewer_risks(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    headers = authenticate(client)
    risky_payload = create_review(client, headers, "generic_risky.txt", GENERIC_RISKY_CONTRACT)
    safe_payload = create_review(client, headers, "balanced_contract.txt", SAFE_CONTRACT)

    assert len(safe_payload["risks"]) <= len(risky_payload["risks"])


def test_duplicate_risk_hits_are_merged_per_clause(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    contract = """保密条款

仅乙方承担保密义务，且保密期限为永久，乙方应对全部保密信息承担保密责任。
"""

    headers = authenticate(client)
    payload = create_review(client, headers, "dedupe_contract.txt", contract)
    confidentiality_risks = [item for item in payload["risks"] if item["risk_type"] == "confidentiality_imbalance"]

    assert len(confidentiality_risks) == 1


def test_history_detail_returns_full_contract_text(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    headers = authenticate(client)
    payload = create_review(client, headers, "history_full_text.txt", GENERIC_RISKY_CONTRACT)

    response = client.get(f"/api/review/{payload['review_id']}", headers=headers)
    assert response.status_code == 200
    detail = response.json()
    assert detail["document_text"] == GENERIC_RISKY_CONTRACT.strip()


def test_history_detail_recovers_document_text_for_legacy_payload(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    headers = authenticate(client)
    payload = create_review(client, headers, "legacy_document_text.txt", GENERIC_RISKY_CONTRACT)
    database_path = tmp_path / "data" / "reviews.db"

    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            "SELECT review_payload FROM reviews WHERE review_id = ?",
            (payload["review_id"],),
        ).fetchone()
    import json
    payload_json = json.loads(row[0])
    payload_json.pop("document_text", None)

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "UPDATE reviews SET review_payload = ? WHERE review_id = ?",
            (json.dumps(payload_json, ensure_ascii=False), payload["review_id"]),
        )
        connection.commit()

    detail_response = client.get(f"/api/review/{payload['review_id']}", headers=headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["document_text"].startswith("历史记录缺少完整合同原文")
    assert "自动续约" in detail_response.json()["document_text"]


def test_history_read_keeps_summary_and_references_after_old_summary_cleanup(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    headers = authenticate(client)
    payload = create_review(client, headers, "legacy_summary.txt", GENERIC_RISKY_CONTRACT)
    database_path = tmp_path / "data" / "reviews.db"

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "UPDATE reviews SET summary = ? WHERE review_id = ?",
            ("锟斤拷锟斤拷??", payload["review_id"]),
        )
        connection.commit()

    list_response = client.get("/api/reviews", headers=headers)
    assert list_response.status_code == 200
    item = next(entry for entry in list_response.json()["items"] if entry["review_id"] == payload["review_id"])
    assert "???" not in item["summary"]

    detail_response = client.get(f"/api/review/{payload['review_id']}", headers=headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["risks"][0]["references"]
    assert detail_response.json()["document_text"] == GENERIC_RISKY_CONTRACT.strip()


def test_analyze_nested_headings_skips_empty_parent_clause(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    contract = """合同解除与争议解决

第五条 合同解除
5.1 甲方可随时单方解除合同。
5.2 乙方不得解除合同。

第六条 争议解决
6.1 所有争议由甲方所在地法院管辖。"""

    headers = authenticate(client)
    payload = create_review(client, headers, "nested_headings.txt", contract)

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


def test_export_review_as_markdown(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    headers = authenticate(client)
    review = create_review(client, headers, "export_contract.txt", GENERIC_RISKY_CONTRACT)

    response = client.get(
        f"/api/review/{review['review_id']}/export",
        params={"format": "markdown"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    assert "attachment;" in response.headers["content-disposition"]
    assert "合同审查报告" in response.text
    assert "## 合同原文" in response.text
    assert "## 风险条目" in response.text


def test_export_review_as_html(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    headers = authenticate(client)
    review = create_review(client, headers, "export_contract.txt", SAMPLE_CONTRACT)

    response = client.get(
        f"/api/review/{review['review_id']}/export",
        params={"format": "html"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert '<html lang="zh-CN">' in response.text
    assert "合同审查报告" in response.text
    assert "合同原文" in response.text


def test_analyze_returns_legal_basis_reference_when_available(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    headers = authenticate(client)
    payload = create_review(client, headers, "sample_contract.txt", SAMPLE_CONTRACT)

    categories = {
        reference['category']
        for risk in payload['risks']
        for reference in risk.get('references', [])
    }

    assert 'legal_basis' in categories
