from intelligent_customer_service.database import initialize_database
from intelligent_customer_service.repositories import CustomerServiceRepository


def test_initialize_database_reset_clears_operational_records(tmp_path):
    db_path = tmp_path / "service.db"
    initialize_database(db_path, seed=True)
    repo = CustomerServiceRepository(db_path)
    repo.create_repair_ticket(
        {
            "order_id": "ORD-1001",
            "customer_id": "CUST-001",
            "issue_type": "hardware",
            "description": "Noise cancelling function is unstable.",
            "contact": "19838622783",
        }
    )
    approval = repo.create_pending_approval(
        action="request_refund",
        payload={"order_id": "ORD-1001", "customer_id": "CUST-001", "amount": 899.0, "reason": "quality"},
        risk_reason="refund amount exceeds threshold",
    )
    repo.approve_pending_refund(approval["id"], reviewer="admin")

    initialize_database(db_path, seed=True, reset=True)
    reset_repo = CustomerServiceRepository(db_path)

    assert len(reset_repo.list_orders()) == 3
    assert reset_repo.list_tickets() == []
    assert reset_repo.list_pending_approvals() == []
    assert reset_repo.list_refunds() == []
