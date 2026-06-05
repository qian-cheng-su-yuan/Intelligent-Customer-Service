from typing import Any

from pydantic import ValidationError

from .repositories import CustomerServiceRepository
from .schemas import QueryLogisticsInput, QueryOrderInput, RefundRequestInput, RepairTicketInput


def build_tool_definitions() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "query_order",
                "description": "Query order details for an authenticated customer.",
                "parameters": QueryOrderInput.model_json_schema(),
            },
        },
        {
            "type": "function",
            "function": {
                "name": "query_logistics",
                "description": "Query logistics status for an order.",
                "parameters": QueryLogisticsInput.model_json_schema(),
            },
        },
        {
            "type": "function",
            "function": {
                "name": "create_repair_ticket",
                "description": "Create an after-sales repair ticket.",
                "parameters": RepairTicketInput.model_json_schema(),
            },
        },
        {
            "type": "function",
            "function": {
                "name": "request_refund",
                "description": "Request a refund. High value refunds require human approval.",
                "parameters": RefundRequestInput.model_json_schema(),
            },
        },
    ]


class CustomerServiceTools:
    def __init__(self, repository: CustomerServiceRepository, refund_review_threshold: float = 500.0):
        self.repository = repository
        self.refund_review_threshold = refund_review_threshold

    def execute(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        handlers = {
            "query_order": self.query_order,
            "query_logistics": self.query_logistics,
            "create_repair_ticket": self.create_repair_ticket,
            "request_refund": self.request_refund,
        }
        handler = handlers.get(name)
        if handler is None:
            return {"ok": False, "error": f"unknown tool: {name}"}
        try:
            return handler(arguments)
        except ValidationError as exc:
            return {"ok": False, "error": "invalid tool arguments", "details": exc.errors()}
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}

    def query_order(self, arguments: dict[str, Any]) -> dict[str, Any]:
        payload = QueryOrderInput.model_validate(arguments)
        order = self.repository.get_order(payload.order_id, payload.customer_id)
        if order is None:
            return {"ok": False, "error": "order not found or customer mismatch"}
        return {"ok": True, "data": order}

    def query_logistics(self, arguments: dict[str, Any]) -> dict[str, Any]:
        payload = QueryLogisticsInput.model_validate(arguments)
        logistics = self.repository.get_logistics(payload.order_id, payload.customer_id)
        if logistics is None:
            return {"ok": False, "error": "logistics not found or customer mismatch"}
        return {"ok": True, "data": logistics}

    def create_repair_ticket(self, arguments: dict[str, Any]) -> dict[str, Any]:
        payload = RepairTicketInput.model_validate(arguments)
        if self.repository.get_order(payload.order_id, payload.customer_id) is None:
            return {"ok": False, "error": "order not found or customer mismatch"}
        ticket = self.repository.create_repair_ticket(payload.model_dump())
        return {"ok": True, "data": ticket}

    def request_refund(self, arguments: dict[str, Any]) -> dict[str, Any]:
        payload = RefundRequestInput.model_validate(arguments)
        order = self.repository.get_order(payload.order_id, payload.customer_id)
        if order is None:
            return {"ok": False, "error": "order not found or customer mismatch"}
        if payload.amount > order["amount"]:
            return {"ok": False, "error": "refund amount cannot exceed order amount"}
        if payload.amount >= self.refund_review_threshold:
            approval = self.repository.create_pending_approval(
                action="request_refund",
                payload=payload.model_dump(),
                risk_reason=f"refund amount {payload.amount} exceeds threshold {self.refund_review_threshold}",
            )
            return {"ok": True, "requires_approval": True, "approval": approval}
        refund = self.repository.create_refund(payload.model_dump())
        return {"ok": True, "requires_approval": False, "refund": refund}
