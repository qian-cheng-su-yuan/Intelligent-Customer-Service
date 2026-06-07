# Enterprise Intelligent Customer Service

基于 Tool Calling 的企业智能客服与工单路由引擎。项目面向企业客服与售后运营场景，支持订单查询、物流追踪、售后报修、退款申请、人工审核和退款记录追踪，是一份可交付项目，具备清晰的运行配置、业务闭环和验收标准。

系统由 FastAPI 后端、SQLite 业务数据、OpenAI-compatible 大模型调用、Pydantic 参数校验、原生 Web 运营工作台和自动化测试组成。填写真实模型 API Key 后，客服会话可以调用 Qwen / DeepSeek 等兼容 OpenAI SDK 的模型并触发 Tool Calling；未填写 API Key 时，订单、物流、工单、审批和退款记录等本地业务能力仍可完整运行，便于交付验收和故障排查。

## 项目能力

- 运营工作台：展示服务状态、模型配置、订单、工单、待审核、退款记录和 Agent 工作流。
- 真实 Tool Calling：大模型返回工具调用后，后端解析参数、校验参数并执行业务工具。
- 参数安全边界：使用 Pydantic 对订单号、客户 ID、金额、退款原因和联系方式做强校验。
- 业务数据闭环：SQLite 管理订单、物流、售后工单、待审核操作和退款记录。
- Human-in-the-loop：大额退款必须先进入人工审核，可审批通过或拒绝。
- 工程化交付：提供 API 文档、运行指南、交付验收步骤、CLI 命令和 pytest 测试。

## 技术栈

- Python 3.10 到 3.12
- FastAPI + Uvicorn
- OpenAI Python SDK
- Pydantic + pydantic-settings
- SQLite
- Typer + Rich
- 原生 HTML / CSS / JavaScript
- pytest + httpx

> 建议使用 Python 3.10 到 3.12。不要使用 Python 3.13 / 3.14 作为交付运行环境，部分二进制依赖可能出现 `pydantic_core` DLL 加载问题。

## 需要填写的信息

复制配置模板：

```powershell
copy .env.example .env
```

### Qwen 百炼

```env
DASHSCOPE_API_KEY=your_dashscope_api_key
LLM_API_KEY=
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
DATABASE_PATH=data/customer_service.db
REFUND_REVIEW_THRESHOLD=500
```

### DeepSeek 或其他 OpenAI 兼容模型

```env
DASHSCOPE_API_KEY=
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
DATABASE_PATH=data/customer_service.db
REFUND_REVIEW_THRESHOLD=500
```

配置说明：

- `DASHSCOPE_API_KEY` 和 `LLM_API_KEY` 任填一个即可。
- 如果两个都填写，系统优先使用 `LLM_API_KEY`。
- `DATABASE_PATH` 是 SQLite 数据库路径。
- `REFUND_REVIEW_THRESHOLD` 是退款人工审核阈值，默认 `500`。

## Windows 快速启动

```powershell
py -3.11 -m pip install -e ".[dev]"
py -3.11 -m intelligent_customer_service.db init --reset --seed
py -3.11 -m uvicorn intelligent_customer_service.api:app --reload
```

`--reset` 会删除并重建本地 SQLite 文件，适合首次验收或重新跑通完整流程；如果数据库里已经有需要保留的业务数据，请只执行 `init --seed` 或直接启动服务。

打开运营工作台：

```text
http://127.0.0.1:8000/
```

打开 Swagger API 文档：

```text
http://127.0.0.1:8000/docs
```

## 运行验收流程

1. 打开首页，确认 Runtime 为 `Online`。
2. 查看订单记录，确认系统已加载内置订单数据。
3. 点击 `订单查询`，结果面板返回订单结构化数据。
4. 点击 `物流追踪`，返回承运商、运单号和最新物流事件。
5. 点击 `售后报修`，创建工单后 `Tickets` 指标和售后工单列表刷新。
6. 点击 `大额退款`，系统创建待审核记录，不直接创建退款。
7. 在人工审核区域点击 `Approve`，退款记录列表新增 `processing` 退款。
8. 再次触发大额退款后点击 `Reject`，审核状态变为 rejected，退款记录不新增。
9. 填写真实 API Key 后，在会话框输入 `帮我查询一下订单 ORD-1001`，验证真实 LLM Tool Calling。

更完整的交付运行说明见 [docs/operation-guide.md](docs/operation-guide.md)。

## API 摘要

- `GET /`：运营工作台。
- `GET /health`：服务健康检查。
- `GET /config/status`：模型配置状态，不暴露密钥。
- `POST /chat`：真实 LLM Agent 对话。
- `POST /tools/{tool_name}`：本地业务工具调用。
- `GET /orders`：订单列表。
- `GET /tickets`：售后工单列表。
- `GET /approvals`：待审批高风险操作。
- `POST /approvals/{approval_id}/approve`：审批通过大额退款。
- `POST /approvals/{approval_id}/reject`：拒绝大额退款。
- `GET /refunds`：退款记录列表。

## CLI 命令

```powershell
py -3.11 -m intelligent_customer_service.cli tool query_order --order-id ORD-1001 --customer-id CUST-001
py -3.11 -m intelligent_customer_service.cli tool query_logistics --order-id ORD-1001 --customer-id CUST-001
py -3.11 -m intelligent_customer_service.cli tool create_repair_ticket --order-id ORD-1001 --customer-id CUST-001 --issue-type hardware --description "Noise cancelling is unstable" --contact 19838622783
py -3.11 -m intelligent_customer_service.cli tool request_refund --order-id ORD-1001 --customer-id CUST-001 --amount 899 --reason "quality issue"
py -3.11 -m intelligent_customer_service.cli approvals
```

真实 LLM 对话：

```powershell
py -3.11 -m intelligent_customer_service.cli chat "帮我查询一下订单 ORD-1001" --customer-id CUST-001
```

## 测试

```powershell
py -3.11 -m pytest -q
```

验收标准：

- 测试全部通过。
- 首页中文正常显示，无乱码。
- `/docs` 可访问并展示接口。
- 不填写 API Key 时，本地业务接口可完整运行。
- 填写 API Key 后，`/chat` 可触发真实 Tool Calling。
- 大额退款必须经人工审核，通过才创建退款，拒绝不创建退款。

## 常见问题

### `/chat` 返回 503

说明没有配置 `DASHSCOPE_API_KEY` 或 `LLM_API_KEY`。填写 `.env` 后重启服务。

### 本地业务按钮可以用，但聊天不可用

聊天能力依赖真实模型 API Key；订单、物流、工单、审批、退款记录等业务接口不依赖模型。

### 默认 Python 跑测试失败

请确认使用 Python 3.10 到 3.12。Windows 推荐：

```powershell
py -3.11 -m pytest -q
```

## 生产化延展

- 接入真实订单系统、物流系统和 CRM。
- 增加用户登录、角色权限、审计日志和审批备注。
- 使用 Redis 或数据库保存多轮会话上下文。
- 使用 LangGraph 编排复杂客服状态流。
- 接入向量库，增加客服知识库 RAG 问答。
