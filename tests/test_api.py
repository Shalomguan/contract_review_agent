"""API integration tests for the MVP."""
from pathlib import Path

from fastapi.testclient import TestClient

from api.app import create_app
from core.config import Settings


SAMPLE_CONTRACT = """软件开发服务合同

第一条 服务内容
乙方负责为甲方开发内部管理系统，并根据甲方要求完成部署与培训。

第二条 付款安排
甲方应在合同签订后三个工作日内支付全部预付款。如甲方逾期付款，每逾期一日，按合同总金额的 5% 向乙方支付滞纳金。

第三条 免责条款
如甲方认为项目延期或交付结果不符合预期，乙方无需承担任何责任。

第四条 单方解除
甲方有权在任何时候单方解除本合同，且无需说明理由，乙方应无条件配合。

第五条 知识产权
乙方在履行本合同过程中形成的全部软件代码、文档、模型、接口及相关知识产权永久归甲方所有。

第六条 争议解决
因本合同引起的任何争议，仅可向甲方所在地人民法院提起诉讼。
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


def test_analyze_text_creates_review(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)

    response = client.post(
        "/api/review/analyze",
        json={"document_name": "sample_contract.txt", "text": SAMPLE_CONTRACT},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["document_name"] == "sample_contract.txt"
    assert payload["review_id"]
    assert payload["risks"]
    assert {risk["risk_level"] for risk in payload["risks"]}.issubset({"high", "medium", "low"})

    detail = client.get(f"/api/review/{payload['review_id']}")
    assert detail.status_code == 200
    assert detail.json()["review_id"] == payload["review_id"]


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


def test_list_reviews_returns_history(tmp_path: Path) -> None:
    client = build_test_client(tmp_path)
    client.post(
        "/api/review/analyze",
        json={"document_name": "contract_a.txt", "text": SAMPLE_CONTRACT},
    )
    client.post(
        "/api/review/analyze",
        json={"document_name": "contract_b.txt", "text": "第一条 服务内容\n双方按照约定履行。"},
    )

    response = client.get("/api/reviews")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 2
    assert items[0]["document_name"] in {"contract_a.txt", "contract_b.txt"}


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
