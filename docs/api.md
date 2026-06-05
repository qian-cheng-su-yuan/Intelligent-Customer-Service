# API Reference

## GET `/`

Serves the built-in service console frontend. This page can be used for a full local demo:

- chat with the LLM-backed customer service Agent
- run local business tools without using LLM tokens
- inspect tool results
- approve high-risk refund requests

## GET `/health`

Returns service health.

```json
{"status":"ok"}
```

## GET `/config/status`

Returns runtime configuration status without exposing secrets.

```json
{
  "provider": "OpenAI-compatible",
  "llm_ready": true,
  "model": "qwen-plus",
  "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
  "database_path": "data/customer_service.db",
  "refund_review_threshold": 500,
  "next_step": "LLM chat is ready."
}
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

## POST `/tools/{tool_name}`

Executes a local business tool directly. This is useful for frontend demos and offline validation because it does not call the LLM.

Request for `/tools/query_order`:

```json
{
  "order_id": "ORD-1001",
  "customer_id": "CUST-001"
}
```

Response:

```json
{
  "ok": true,
  "data": {
    "order_id": "ORD-1001",
    "customer_id": "CUST-001",
    "product_name": "AI Noise Cancelling Headphones",
    "amount": 899.0,
    "status": "paid",
    "paid_at": "2026-05-20 10:15:00"
  }
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
