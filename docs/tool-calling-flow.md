# Tool Calling Flow

## Tool Schema

Tool schemas are generated from Pydantic models with `model_json_schema()`. The same schema contract is used in two places:

- Sent to the LLM as OpenAI-compatible `tools`.
- Used locally to validate model-produced arguments before execution.

## Tools

### `query_order`

Finds an order by `order_id` and `customer_id`.

### `query_logistics`

Finds logistics status only when the order belongs to the requesting customer.

### `create_repair_ticket`

Creates an after-sales ticket. Contact information and description are required.

### `request_refund`

Creates a refund for small amounts. Large refunds are suspended for human approval.

## Human-in-the-loop

`request_refund` checks `REFUND_REVIEW_THRESHOLD`.

- Amount below threshold: create refund immediately.
- Amount greater than or equal to threshold: create a pending approval.

The administrator approves with:

```bash
ics approve 1 --reviewer admin
```

or:

```bash
curl -X POST http://127.0.0.1:8000/approvals/1/approve \
  -H "Content-Type: application/json" \
  -d '{"reviewer":"admin"}'
```
