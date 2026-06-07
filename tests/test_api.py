from fastapi.testclient import TestClient

from intelligent_customer_service.api import create_app
from intelligent_customer_service.config import get_settings
from intelligent_customer_service.database import initialize_database
from intelligent_customer_service.repositories import CustomerServiceRepository
from intelligent_customer_service.tools import CustomerServiceTools


class FakeAgent:
    def chat(self, message, customer_id, conversation_id=None):
        return {
            "conversation_id": conversation_id or "conv-test",
            "answer": f"handled {message}",
            "tool_calls": [
                {
                    "name": "query_order",
                    "arguments": {"order_id": "ORD-1001", "customer_id": customer_id},
                    "result": {"ok": True},
                }
            ],
        }


def test_chat_endpoint_uses_injected_agent(tmp_path):
    db_path = tmp_path / "service.db"
    initialize_database(db_path, seed=True)
    app = create_app(agent=FakeAgent(), tools=CustomerServiceTools(CustomerServiceRepository(db_path)))
    client = TestClient(app)

    response = client.post("/chat", json={"message": "check order ORD-1001", "customer_id": "CUST-001"})

    assert response.status_code == 200
    assert response.json()["conversation_id"] == "conv-test"
    assert response.json()["tool_calls"][0]["name"] == "query_order"


def test_orders_endpoint_returns_seeded_business_orders(tmp_path):
    db_path = tmp_path / "service.db"
    initialize_database(db_path, seed=True)
    app = create_app(agent=FakeAgent(), tools=CustomerServiceTools(CustomerServiceRepository(db_path)))
    client = TestClient(app)

    response = client.get("/orders")

    assert response.status_code == 200
    assert len(response.json()) == 3
    assert response.json()[0]["order_id"] == "ORD-1002"
    assert response.json()[0]["customer_id"] == "CUST-001"


def test_approval_endpoint_executes_pending_refund(tmp_path):
    db_path = tmp_path / "service.db"
    initialize_database(db_path, seed=True)
    repo = CustomerServiceRepository(db_path)
    tools = CustomerServiceTools(repo, refund_review_threshold=500)
    refund = tools.execute(
        "request_refund",
        {"order_id": "ORD-1001", "customer_id": "CUST-001", "amount": 899.0, "reason": "quality issue"},
    )
    app = create_app(agent=FakeAgent(), tools=tools)
    client = TestClient(app)

    response = client.post(f"/approvals/{refund['approval']['id']}/approve", json={"reviewer": "admin"})

    assert response.status_code == 200
    assert response.json()["status"] == "approved"


def test_approval_endpoint_rejects_pending_refund_without_creating_refund(tmp_path):
    db_path = tmp_path / "service.db"
    initialize_database(db_path, seed=True)
    repo = CustomerServiceRepository(db_path)
    tools = CustomerServiceTools(repo, refund_review_threshold=500)
    refund = tools.execute(
        "request_refund",
        {"order_id": "ORD-1001", "customer_id": "CUST-001", "amount": 899.0, "reason": "quality issue"},
    )
    app = create_app(agent=FakeAgent(), tools=tools)
    client = TestClient(app)

    response = client.post(f"/approvals/{refund['approval']['id']}/reject", json={"reviewer": "admin"})

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
    assert response.json()["approval"]["status"] == "rejected"
    assert client.get("/refunds").json() == []


def test_refunds_endpoint_returns_refund_history_after_approval(tmp_path):
    db_path = tmp_path / "service.db"
    initialize_database(db_path, seed=True)
    repo = CustomerServiceRepository(db_path)
    tools = CustomerServiceTools(repo, refund_review_threshold=500)
    refund = tools.execute(
        "request_refund",
        {"order_id": "ORD-1001", "customer_id": "CUST-001", "amount": 899.0, "reason": "quality issue"},
    )
    app = create_app(agent=FakeAgent(), tools=tools)
    client = TestClient(app)

    initial = client.get("/refunds")
    approved = client.post(f"/approvals/{refund['approval']['id']}/approve", json={"reviewer": "admin"})
    history = client.get("/refunds")

    assert initial.status_code == 200
    assert initial.json() == []
    assert approved.status_code == 200
    assert history.status_code == 200
    assert history.json()[0]["order_id"] == "ORD-1001"
    assert history.json()[0]["status"] == "processing"


def test_approval_endpoint_rejects_duplicate_approval_without_second_refund(tmp_path):
    db_path = tmp_path / "service.db"
    initialize_database(db_path, seed=True)
    repo = CustomerServiceRepository(db_path)
    tools = CustomerServiceTools(repo, refund_review_threshold=500)
    refund = tools.execute(
        "request_refund",
        {"order_id": "ORD-1001", "customer_id": "CUST-001", "amount": 899.0, "reason": "quality issue"},
    )
    app = create_app(agent=FakeAgent(), tools=tools)
    client = TestClient(app)
    approval_id = refund["approval"]["id"]

    first = client.post(f"/approvals/{approval_id}/approve", json={"reviewer": "admin"})
    second = client.post(f"/approvals/{approval_id}/approve", json={"reviewer": "admin"})

    assert first.status_code == 200
    assert second.status_code == 400
    assert "already been approved" in second.json()["detail"]
    assert len(client.get("/refunds").json()) == 1


def test_health_endpoint_reports_ready(tmp_path):
    db_path = tmp_path / "service.db"
    initialize_database(db_path, seed=True)
    app = create_app(agent=FakeAgent(), tools=CustomerServiceTools(CustomerServiceRepository(db_path)))
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_config_status_explains_missing_api_key(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    get_settings.cache_clear()
    db_path = tmp_path / "service.db"
    initialize_database(db_path, seed=True)
    app = create_app(agent=FakeAgent(), tools=CustomerServiceTools(CustomerServiceRepository(db_path)))
    client = TestClient(app)

    response = client.get("/config/status")

    assert response.status_code == 200
    assert response.json()["llm_ready"] is False
    assert "Configure DASHSCOPE_API_KEY or LLM_API_KEY" in response.json()["next_step"]
    get_settings.cache_clear()
