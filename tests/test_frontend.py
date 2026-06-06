from fastapi.testclient import TestClient

from intelligent_customer_service.api import create_app
from intelligent_customer_service.database import initialize_database
from intelligent_customer_service.repositories import CustomerServiceRepository
from intelligent_customer_service.tools import CustomerServiceTools


class FakeAgent:
    def chat(self, message, customer_id, conversation_id=None):
        return {
            "conversation_id": conversation_id or "conv-ui",
            "answer": "frontend chat response",
            "tool_calls": [],
        }


def _client(tmp_path):
    db_path = tmp_path / "service.db"
    initialize_database(db_path, seed=True)
    tools = CustomerServiceTools(CustomerServiceRepository(db_path))
    return TestClient(create_app(agent=FakeAgent(), tools=tools))


def test_homepage_serves_customer_service_console(tmp_path):
    client = _client(tmp_path)

    response = client.get("/")

    assert response.status_code == 200
    assert "Enterprise Service Console" in response.text
    assert "app-shell" in response.text
    assert "Interview Demo Console" in response.text
    assert "Agent Tool Chain" in response.text
    assert "退款记录" in response.text
    assert "智能客服会话" in response.text
    assert "�" not in response.text
    assert "绯" not in response.text


def test_static_css_is_served(tmp_path):
    client = _client(tmp_path)

    response = client.get("/static/styles.css")

    assert response.status_code == 200
    assert "service-console" in response.text


def test_static_javascript_is_served_without_garbled_text(tmp_path):
    client = _client(tmp_path)

    response = client.get("/static/app.js")

    assert response.status_code == 200
    assert "Chat service is not available" in response.text
    assert "�" not in response.text


def test_tool_endpoint_executes_local_business_tool(tmp_path):
    client = _client(tmp_path)

    response = client.post(
        "/tools/query_order",
        json={"order_id": "ORD-1001", "customer_id": "CUST-001"},
    )

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert response.json()["data"]["order_id"] == "ORD-1001"


def test_config_status_endpoint_reports_llm_readiness(tmp_path):
    client = _client(tmp_path)

    response = client.get("/config/status")

    assert response.status_code == 200
    assert response.json()["provider"] == "OpenAI-compatible"
    assert "llm_ready" in response.json()
    assert "model" in response.json()
