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
