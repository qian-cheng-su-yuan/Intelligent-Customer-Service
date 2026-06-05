from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    customer_id: str = Field(min_length=1, max_length=64)
    conversation_id: str | None = None


class ToolCallRecord(BaseModel):
    name: str
    arguments: dict[str, Any]
    result: dict[str, Any]


class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)


class ApproveRequest(BaseModel):
    reviewer: str = Field(min_length=1, max_length=64)


class QueryOrderInput(BaseModel):
    order_id: str = Field(min_length=3, max_length=64)
    customer_id: str = Field(min_length=1, max_length=64)


class QueryLogisticsInput(QueryOrderInput):
    pass


class RepairTicketInput(QueryOrderInput):
    issue_type: str = Field(min_length=2, max_length=64)
    description: str = Field(min_length=5, max_length=500)
    contact: str = Field(min_length=1, max_length=128)

    @field_validator("contact")
    @classmethod
    def contact_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("contact is required")
        return value.strip()


class RefundRequestInput(QueryOrderInput):
    amount: float = Field(gt=0)
    reason: str = Field(min_length=3, max_length=300)


class Order(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    order_id: str
    customer_id: str
    product_name: str
    amount: float
    status: str
    paid_at: str


class Logistics(BaseModel):
    order_id: str
    carrier: str
    tracking_no: str
    status: str
    latest_event: str


class Ticket(BaseModel):
    id: int
    order_id: str
    customer_id: str
    issue_type: str
    description: str
    contact: str
    status: Literal["open", "processing", "closed"]
    created_at: str


class Refund(BaseModel):
    id: int
    order_id: str
    customer_id: str
    amount: float
    reason: str
    status: Literal["processing", "approved", "rejected"]
    created_at: str


class PendingApproval(BaseModel):
    id: int
    action: str
    payload: dict[str, Any]
    risk_reason: str
    status: Literal["pending", "approved", "rejected"]
    created_at: str
