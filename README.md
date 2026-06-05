# Enterprise Intelligent Customer Service

基于 Tool Calling 的企业智能客服与工单路由引擎。项目面向订单查询、物流查询、售后报修、退款申请等企业客服场景，使用 FastAPI、Pydantic、SQLite 和 Qwen 百炼 OpenAI 兼容接口实现一个可本地演示、可测试、可扩展的客服 Agent 原型。

## 项目亮点

- Tool Calling 闭环：用户提问 -> 大模型选择工具 -> 参数校验 -> SQLite 数据查询/写入 -> 结构化结果返回。
- 真实 LLM 接入：默认使用 Qwen 百炼 OpenAI 兼容模式，可切换到 DeepSeek 或其他兼容服务。
- 强参数校验：Pydantic 对订单号、客户 ID、退款金额、联系方式等参数做类型和业务约束。
- Human-in-the-loop：大额退款会进入人工审核队列，审核通过后才执行退款。
- 工程化结构：标准 `src/` 布局、FastAPI 接口、Typer CLI、pytest 测试和详细文档。

## 技术栈

- Python 3.10+
- FastAPI + Uvicorn
- OpenAI Python SDK
- Pydantic + pydantic-settings
- SQLite
- Typer + Rich
- pytest + httpx

## 目录结构

```text
.
├── docs/
│   ├── api.md
│   ├── architecture.md
│   └── tool-calling-flow.md
├── scripts/
│   └── init_db.py
├── src/
│   └── intelligent_customer_service/
│       ├── agent.py
│       ├── api.py
│       ├── cli.py
│       ├── config.py
│       ├── database.py
│       ├── db.py
│       ├── llm_client.py
│       ├── repositories.py
│       ├── schemas.py
│       └── tools.py
├── tests/
├── .env.example
├── pyproject.toml
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
python -m pip install -e ".[dev]"
```

如果你的默认 Python 是预览版或 alpha 版本，建议使用稳定的 Python 3.10-3.12。

### 2. 配置环境变量

```bash
copy .env.example .env
```

编辑 `.env`：

```env
DASHSCOPE_API_KEY=your_dashscope_api_key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
DATABASE_PATH=data/customer_service.db
REFUND_REVIEW_THRESHOLD=500
```

Qwen 百炼 OpenAI 兼容接口参考官方文档：
[阿里云百炼 OpenAI 兼容说明](https://help.aliyun.com/zh/model-studio/compatibility-of-openai-with-dashscope)。

DeepSeek Function Calling 参考：
[DeepSeek Function Calling](https://api-docs.deepseek.com/guides/function_calling)。

### 3. 初始化 SQLite 数据库

```bash
python -m intelligent_customer_service.db init --seed
```

也可以使用脚本：

```bash
python scripts/init_db.py
```

### 4. 启动 API 服务

```bash
uvicorn intelligent_customer_service.api:app --reload
```

打开接口文档：

```text
http://127.0.0.1:8000/docs
```

### 5. CLI 演示

直接调用业务工具，不消耗 LLM token：

```bash
ics tool query_order --order-id ORD-1001 --customer-id CUST-001
ics tool query_logistics --order-id ORD-1001 --customer-id CUST-001
ics tool request_refund --order-id ORD-1001 --customer-id CUST-001 --amount 899 --reason "quality issue"
ics approvals
ics approve 1 --reviewer admin
```

使用真实 LLM Tool Calling：

```bash
ics chat "帮我查一下 ORD-1001 的物流" --customer-id CUST-001
```

## API 示例

### 健康检查

```bash
curl http://127.0.0.1:8000/health
```

响应：

```json
{"status":"ok"}
```

### 智能客服对话

```bash
curl -X POST http://127.0.0.1:8000/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"帮我查一下 ORD-1001 的物流\",\"customer_id\":\"CUST-001\"}"
```

典型响应：

```json
{
  "conversation_id": "conv-xxxx",
  "answer": "您的包裹已到达上海转运中心。",
  "tool_calls": [
    {
      "name": "query_logistics",
      "arguments": {"order_id": "ORD-1001", "customer_id": "CUST-001"},
      "result": {"ok": true, "data": {"carrier": "SF Express"}}
    }
  ]
}
```

### 人工审核大额退款

```bash
curl -X POST http://127.0.0.1:8000/approvals/1/approve ^
  -H "Content-Type: application/json" ^
  -d "{\"reviewer\":\"admin\"}"
```

## Tool Calling 设计

系统向大模型暴露 4 个标准工具：

| 工具名 | 功能 | 关键参数 |
| --- | --- | --- |
| `query_order` | 查询订单信息 | `order_id`, `customer_id` |
| `query_logistics` | 查询物流状态 | `order_id`, `customer_id` |
| `create_repair_ticket` | 创建售后报修工单 | `order_id`, `issue_type`, `description`, `contact` |
| `request_refund` | 申请退款 | `order_id`, `amount`, `reason` |

工具参数来自 Pydantic 的 JSON Schema，执行前再次通过 Pydantic 校验。这样即使模型输出缺字段、类型错误或非法金额，系统也会返回可解释错误，而不是直接执行失败。

## 数据库设计

- `orders`：订单模拟数据
- `logistics`：物流模拟数据
- `repair_tickets`：售后工单
- `refunds`：退款记录
- `pending_approvals`：高风险操作人工审核队列

初始化后内置演示数据：

- `ORD-1001` / `CUST-001`
- `ORD-1002` / `CUST-001`
- `ORD-2001` / `CUST-002`

## 安全审核机制

默认 `REFUND_REVIEW_THRESHOLD=500`。当退款金额大于或等于阈值时：

1. `request_refund` 不会直接创建退款记录。
2. 系统在 `pending_approvals` 中创建待审核记录。
3. 管理员调用 `/approvals/{id}/approve` 或 `ics approve`。
4. 审核通过后才写入 `refunds` 表。

这个流程模拟企业 Agent 中常见的 Human-in-the-loop 风控节点，避免模型直接执行敏感操作。

## 测试

```bash
python -m pytest
```

测试覆盖：

- 配置默认值和 API key 解析
- Pydantic 参数校验
- SQLite seed 数据和 repository 查询
- 业务工具执行
- 大额退款人工审核
- FastAPI `/chat`、`/health`、`/approvals/{id}/approve`

## 常见问题

### `/chat` 返回 503

说明没有配置 `DASHSCOPE_API_KEY` 或 `LLM_API_KEY`。复制 `.env.example` 为 `.env` 后填写真实 key。

### 想使用 DeepSeek

将 `.env` 改成兼容配置：

```env
LLM_API_KEY=your_deepseek_api_key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

### 不想消耗 LLM token

使用 CLI 的 `ics tool ...` 命令可以直接测试本地工具和数据库流程。

## 可扩展方向

- 接入企业真实订单系统、物流系统和 CRM。
- 增加 Redis 会话记忆和多轮上下文持久化。
- 增加 LangGraph 状态机编排复杂客服流程。
- 将人工审核节点扩展为后台管理页面。
- 接入向量库，实现客服知识库 RAG 问答。
