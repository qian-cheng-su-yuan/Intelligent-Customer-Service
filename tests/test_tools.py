from intelligent_customer_service.database import initialize_database
from intelligent_customer_service.repositories import CustomerServiceRepository
from intelligent_customer_service.tools import CustomerServiceTools, build_tool_definitions


def test_tool_definitions_expose_expected_function_names():
    names = {item["function"]["name"] for item in build_tool_definitions()}

    assert names == {"query_order", "query_logistics", "create_repair_ticket", "request_refund"}


def test_query_order_returns_seeded_order(tmp_path):
    db_path = tmp_path / "service.db"
    initialize_database(db_path, seed=True)
    tools = CustomerServiceTools(CustomerServiceRepository(db_path))

    result = tools.execute("query_order", {"order_id": "ORD-1001", "customer_id": "CUST-001"})

    assert result["ok"] is True
    assert result["data"]["order_id"] == "ORD-1001"


def test_large_refund_is_suspended_for_human_approval(tmp_path):
    db_path = tmp_path / "service.db"
    initialize_database(db_path, seed=True)
    tools = CustomerServiceTools(CustomerServiceRepository(db_path), refund_review_threshold=500)

    result = tools.execute(
        "request_refund",
        {"order_id": "ORD-1001", "customer_id": "CUST-001", "amount": 899.0, "reason": "quality issue"},
    )

    assert result["ok"] is True
    assert result["requires_approval"] is True
    assert result["approval"]["status"] == "pending"
