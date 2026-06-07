from typer.testing import CliRunner

from intelligent_customer_service.cli import app
from intelligent_customer_service.database import initialize_database
from intelligent_customer_service.repositories import CustomerServiceRepository


def test_cli_reject_command_rejects_pending_refund(tmp_path, monkeypatch):
    db_path = tmp_path / "service.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    initialize_database(db_path, seed=True)
    repo = CustomerServiceRepository(db_path)
    approval = repo.create_pending_approval(
        action="request_refund",
        payload={"order_id": "ORD-1001", "customer_id": "CUST-001", "amount": 899.0, "reason": "quality"},
        risk_reason="refund amount exceeds threshold",
    )
    runner = CliRunner()

    result = runner.invoke(app, ["reject", str(approval["id"]), "--reviewer", "admin"])

    assert result.exit_code == 0
    assert '"status": "rejected"' in result.output
    assert repo.list_refunds() == []
