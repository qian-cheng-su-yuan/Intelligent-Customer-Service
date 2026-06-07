from intelligent_customer_service.database import initialize_database
from intelligent_customer_service.repositories import CustomerServiceRepository


def test_seeded_order_and_logistics_can_be_loaded(tmp_path):
    db_path = tmp_path / "service.db"
    initialize_database(db_path, seed=True)
    repo = CustomerServiceRepository(db_path)

    order = repo.get_order("ORD-1001", "CUST-001")
    logistics = repo.get_logistics("ORD-1001", "CUST-001")

    assert order is not None
    assert order["status"] == "paid"
    assert logistics is not None
    assert logistics["carrier"] == "SF Express"


def test_seeded_orders_can_be_listed_for_operations_console(tmp_path):
    db_path = tmp_path / "service.db"
    initialize_database(db_path, seed=True)
    repo = CustomerServiceRepository(db_path)

    orders = repo.list_orders()

    assert [order["order_id"] for order in orders] == ["ORD-1002", "ORD-1001", "ORD-2001"]


def test_approve_pending_refund_creates_refund_record(tmp_path):
    db_path = tmp_path / "service.db"
    initialize_database(db_path, seed=True)
    repo = CustomerServiceRepository(db_path)

    approval = repo.create_pending_approval(
        action="request_refund",
        payload={"order_id": "ORD-1001", "customer_id": "CUST-001", "amount": 899.0, "reason": "quality"},
        risk_reason="refund amount exceeds threshold",
    )
    result = repo.approve_pending_refund(approval["id"], reviewer="admin")

    assert result["status"] == "approved"
    assert result["refund"]["status"] == "processing"


def test_reject_pending_refund_does_not_create_refund_record(tmp_path):
    db_path = tmp_path / "service.db"
    initialize_database(db_path, seed=True)
    repo = CustomerServiceRepository(db_path)

    approval = repo.create_pending_approval(
        action="request_refund",
        payload={"order_id": "ORD-1001", "customer_id": "CUST-001", "amount": 899.0, "reason": "quality"},
        risk_reason="refund amount exceeds threshold",
    )
    result = repo.reject_pending_refund(approval["id"], reviewer="admin")

    assert result["status"] == "rejected"
    assert result["approval"]["status"] == "rejected"
    assert repo.list_refunds() == []
