from fastapi.testclient import TestClient

from intelligent_customer_service.api import create_app
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


def test_health_endpoint_reports_ready(tmp_path):
    db_path = tmp_path / "service.db"
    initialize_database(db_path, seed=True)
    app = create_app(agent=FakeAgent(), tools=CustomerServiceTools(CustomerServiceRepository(db_path)))
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
