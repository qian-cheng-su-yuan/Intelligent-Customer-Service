import pytest
from pydantic import ValidationError

from intelligent_customer_service.schemas import RefundRequestInput, RepairTicketInput


def test_refund_request_rejects_negative_amount():
    with pytest.raises(ValidationError) as exc_info:
        RefundRequestInput(order_id="ORD-1001", customer_id="CUST-001", amount=-1, reason="mistake")

    assert "greater than 0" in str(exc_info.value)


def test_repair_ticket_requires_contact_information():
    with pytest.raises(ValidationError) as exc_info:
        RepairTicketInput(
            order_id="ORD-1001",
            customer_id="CUST-001",
            issue_type="screen",
            description="Screen is broken",
            contact="",
        )

    assert "contact" in str(exc_info.value)
