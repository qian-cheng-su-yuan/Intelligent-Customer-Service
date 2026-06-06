# Enterprise Intelligent Customer Service

基于 Tool Calling 的企业智能客服与工单路由引擎。项目面向企业客服场景，支持订单查询、物流追踪、售后报修、退款申请和 Human-in-the-loop 大额退款审核，适合作为 AI Agent / 大模型应用开发 / Python 后端开发方向的面试演示项目。

项目包含专业客服工作台前端、FastAPI 后端、SQLite 演示数据、OpenAI-compatible Tool Calling、Pydantic 参数校验、CLI 命令、pytest 自动化测试和面试演示文档。填写真实模型 API Key 后，可以通过聊天框跑通真实 Qwen / DeepSeek 等 OpenAI 兼容模型的 Tool Calling；未填写 Key 时，右侧本地业务工具仍可完整演示订单、物流、工单、退款审核和退款记录闭环。

## 项目亮点

- 企业客服工作台：首屏展示 Runtime、LLM 状态、工单数、审核数、退款记录和 Agent Tool Chain。
- 真实 Tool Calling：使用 OpenAI Python SDK 对接 Qwen 百炼、DeepSeek 等 OpenAI 兼容接口。
- 参数强校验：使用 Pydantic 校验订单号、客户 ID、退款金额、原因和联系方式。
- 本地业务闭环：SQLite 内置订单、物流、工单、待审批和退款记录表。
- 风险控制：大额退款先进入人工审核队列，审批通过后才创建退款记录。
- 面试可演示：提供 README、交付指南、面试演示脚本、CLI 和测试命令。

## 技术栈

- Python 3.10 到 3.12
- FastAPI + Uvicorn
- OpenAI Python SDK
- Pydantic + pydantic-settings
- SQLite
- Typer + Rich
- 原生 HTML / CSS / JavaScript
- pytest + httpx

> 不建议使用 Python 3.13 / 3.14。部分二进制依赖可能在新版解释器上出现 `pydantic_core` DLL 加载失败。

## 项目结构

```text
.
├── docs/
│   ├── api.md
│   ├── architecture.md
│   ├── delivery-guide.md
│   ├── interview-demo.md
│   └── tool-calling-flow.md
├── scripts/
│   └── init_db.py
├── src/intelligent_customer_service/
│   ├── agent.py
│   ├── api.py
│   ├── cli.py
│   ├── config.py
│   ├── database.py
│   ├── db.py
│   ├── llm_client.py
│   ├── repositories.py
│   ├── schemas.py
│   ├── static/
│   │   ├── app.js
│   │   ├── index.html
│   │   └── styles.css
│   └── tools.py
├── tests/
├── .env.example
├── pyproject.toml
└── README.md
```

## 需要填写的信息

复制环境变量模板：

```powershell
copy .env.example .env
```

### 方案 A：Qwen 百炼

```env
DASHSCOPE_API_KEY=your_dashscope_api_key
LLM_API_KEY=
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
DATABASE_PATH=data/customer_service.db
REFUND_REVIEW_THRESHOLD=500
```

### 方案 B：DeepSeek 或其他 OpenAI 兼容模型

```env
DASHSCOPE_API_KEY=
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
DATABASE_PATH=data/customer_service.db
REFUND_REVIEW_THRESHOLD=500
```

说明：

- `DASHSCOPE_API_KEY` 和 `LLM_API_KEY` 任填一个即可。
- `LLM_API_KEY` 优先级高于 `DASHSCOPE_API_KEY`。
- 不填写 API Key 时，`/chat` 会返回配置提示；本地业务工具不依赖模型，仍可演示核心闭环。

## Windows 快速启动

建议显式使用 Python 3.11：

```powershell
py -3.11 -m pip install -e ".[dev]"
py -3.11 -m intelligent_customer_service.db init --seed
py -3.11 -m uvicorn intelligent_customer_service.api:app --reload
```

打开前端工作台：

```text
http://127.0.0.1:8000/
```

打开 Swagger API 文档：

```text
http://127.0.0.1:8000/docs
```

## 面试演示流程

1. 打开 `http://127.0.0.1:8000/`，展示 Runtime、LLM 状态、指标卡和 Agent Tool Chain。
2. 点击 `订单查询`，展示 `ORD-1001` 的订单金额、商品名和客户归属。
3. 点击 `物流追踪`，展示承运商、运单号和最新物流事件。
4. 点击 `售后报修`，创建售后工单，观察 Tickets 指标和售后工单列表变化。
5. 点击 `大额退款`，系统返回 `requires_approval = true`，人工审核列表出现待审批记录。
6. 点击 `Approve`，待审批记录清空，退款记录列表新增一条 `processing` 状态退款。
7. 如果已填写真实 API Key，在聊天框输入 `帮我查询一下订单 ORD-1001`，展示模型选择工具、后端校验参数、查询 SQLite 并返回结果的完整链路。

更详细的讲解脚本见 [docs/interview-demo.md](docs/interview-demo.md)。

## CLI 演示

本地业务工具不消耗 LLM token：

```powershell
py -3.11 -m intelligent_customer_service.cli tool query_order --order-id ORD-1001 --customer-id CUST-001
py -3.11 -m intelligent_customer_service.cli tool query_logistics --order-id ORD-1001 --customer-id CUST-001
py -3.11 -m intelligent_customer_service.cli tool create_repair_ticket --order-id ORD-1001 --customer-id CUST-001 --issue-type hardware --description "Noise cancelling is unstable" --contact 19838622783
py -3.11 -m intelligent_customer_service.cli tool request_refund --order-id ORD-1001 --customer-id CUST-001 --amount 899 --reason "quality issue"
py -3.11 -m intelligent_customer_service.cli approvals
```

真实 LLM Tool Calling：

```powershell
py -3.11 -m intelligent_customer_service.cli chat "帮我查询一下订单 ORD-1001" --customer-id CUST-001
```

## API 摘要

- `GET /`：前端工作台。
- `GET /health`：服务健康检查。
- `GET /config/status`：模型配置状态，不暴露密钥。
- `POST /chat`：真实 LLM Agent 对话。
- `POST /tools/{tool_name}`：本地业务工具调用。
- `GET /tickets`：售后工单列表。
- `GET /approvals`：待审批高风险操作。
- `POST /approvals/{approval_id}/approve`：审批大额退款。
- `GET /refunds`：退款记录列表。

## 测试与验收

```powershell
py -3.11 -m pytest -q
```

验收标准：

- 测试全部通过。
- 首页 `/` 可访问，页面中文无乱码。
- `/docs` 可访问 Swagger 文档。
- 不配置 API Key 时，本地业务工具链路能完整跑通。
- 配置 API Key 后，`/chat` 能调用真实模型并触发 Tool Calling。
- 大额退款必须先进入人工审核，审批通过后才出现在退款记录中。

## 常见问题

### `/chat` 返回 503

说明没有配置 `DASHSCOPE_API_KEY` 或 `LLM_API_KEY`。复制 `.env.example` 为 `.env` 后填写真实 Key，再重启服务。

### 本地工具能用，但聊天框不可用

这是正常情况。聊天框依赖真实 LLM API Key；右侧业务工具直接调用本地 FastAPI 和 SQLite，不依赖模型。

### Python 3.14 下测试报 DLL 错误

请切换到 Python 3.10 到 3.12。Windows 推荐命令：

```powershell
py -3.11 -m pytest -q
```

## 可扩展方向

- 接入真实订单、物流和 CRM 系统。
- 增加 Redis 会话记忆和多轮上下文持久化。
- 使用 LangGraph 编排更复杂的客服状态机。
- 接入向量库，实现客服知识库 RAG 问答。
- 增加管理员后台、审计日志和权限控制。
