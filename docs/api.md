# API Reference

## GET `/health`

Returns service health.

```json
{"status":"ok"}
```

## POST `/chat`

Runs the customer service Agent.

Request:

```json
{
  "message": "帮我查一下 ORD-1001 的物流",
  "customer_id": "CUST-001",
  "conversation_id": "optional-conversation-id"
}
```

Response:

```json
{
  "conversation_id": "conv-xxxx",
  "answer": "客服回复",
  "tool_calls": [
    {
      "name": "query_logistics",
      "arguments": {
        "order_id": "ORD-1001",
        "customer_id": "CUST-001"
      },
      "result": {
        "ok": true,
        "data": {
          "carrier": "SF Express"
        }
      }
    }
  ]
}
```

## GET `/tickets`

Returns after-sales repair tickets.

## GET `/approvals`

Returns pending high-risk operations.

## POST `/approvals/{approval_id}/approve`

Approves a pending refund.

Request:

```json
{"reviewer":"admin"}
```

Response:

```json
{
  "status": "approved",
  "approval": {},
  "refund": {}
}
```
