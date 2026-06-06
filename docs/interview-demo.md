# Interview Demo Guide

这份脚本用于把项目演示给面试官看。建议先运行项目，再按页面顺序讲解。

## 1. 开场介绍

可以这样讲：

```text
这是一个基于 Tool Calling 的企业智能客服与工单路由原型。
用户可以用自然语言咨询订单、物流、售后和退款问题。
模型负责识别意图并选择工具，后端使用 Pydantic 校验参数，再调用 SQLite 模拟业务系统。
对于大额退款这类高风险操作，系统不会直接执行，而是进入人工审核队列。
```

重点强调：

- 不是单纯聊天页面，而是一个能调用业务工具的 Agent。
- 工具调用、参数校验、数据库查询、人工审核形成闭环。
- 页面右侧工具可在没有 API Key 时演示本地业务链路。

## 2. 启动项目

Windows 推荐命令：

```powershell
py -3.11 -m pip install -e ".[dev]"
copy .env.example .env
py -3.11 -m intelligent_customer_service.db init --seed
py -3.11 -m uvicorn intelligent_customer_service.api:app --reload
```

打开：

```text
http://127.0.0.1:8000/
```

真实 LLM 演示需要在 `.env` 中填写：

```env
DASHSCOPE_API_KEY=your_dashscope_api_key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
```

或使用其他 OpenAI-compatible 服务：

```env
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

## 3. 页面讲解顺序

### Runtime 和指标区

打开首页后先看左侧和顶部：

- `Runtime = Online` 表示 FastAPI 服务正常。
- `LLM ready` 表示已填写 API Key。
- `Tickets`、`Approvals`、`Refunds` 会随着操作实时变化。
- `Agent Tool Chain` 展示项目核心链路：意图识别、工具选择、参数校验、业务执行、人工审核。

### 订单查询

点击 `订单查询`。

讲解点：

- 前端调用 `POST /tools/query_order`。
- 入参包含 `order_id` 和 `customer_id`。
- Pydantic 先校验参数格式。
- Repository 层按订单号和客户 ID 查询，避免越权读取其他客户订单。

### 物流追踪

点击 `物流追踪`。

讲解点：

- 物流表通过订单号关联订单表。
- 查询时仍校验客户 ID，防止只知道订单号就能查物流。

### 售后报修

点击 `售后报修`。

讲解点：

- 系统创建一条售后工单。
- 工单列表和 `Tickets` 指标会刷新。
- 联系方式、问题描述等字段由 Pydantic 做长度和空值校验。

### 大额退款和人工审核

点击 `大额退款`。

讲解点：

- 退款金额 `899` 超过阈值 `500`。
- 系统不会直接写入退款表。
- 后端创建 `pending_approvals` 记录，返回 `requires_approval = true`。

点击 `Approve`。

讲解点：

- 审批通过后才创建退款记录。
- 待审批列表清空，退款记录列表新增一条 `processing`。
- 审批和退款创建放在同一个写事务中，避免重复审批造成重复退款。

### 真实 Tool Calling

如果已填写 API Key，在聊天框输入：

```text
帮我查询一下订单 ORD-1001
```

讲解点：

- 后端把工具 JSON Schema 暴露给模型。
- 模型返回 tool call，例如 `query_order`。
- 后端解析模型参数，再用 Pydantic 校验。
- 工具执行结果会再次发送给模型，生成最终客服回复。

## 4. API 文档展示

打开：

```text
http://127.0.0.1:8000/docs
```

建议展示这些接口：

- `POST /chat`
- `POST /tools/{tool_name}`
- `GET /approvals`
- `POST /approvals/{approval_id}/approve`
- `GET /refunds`

## 5. 验收命令

```powershell
py -3.11 -m pytest -q
py -3.11 -m intelligent_customer_service.cli tool query_order --order-id ORD-1001 --customer-id CUST-001
py -3.11 -m intelligent_customer_service.cli tool request_refund --order-id ORD-1001 --customer-id CUST-001 --amount 899 --reason "quality issue"
```

测试通过后可以说明：

```text
项目覆盖了接口、工具调用、参数校验、数据库读写、前端页面和人工审核流程。
```

## 6. 可回答的面试追问

### 为什么需要 Pydantic？

模型输出不稳定，可能漏字段、传错类型或构造非法金额。Pydantic 可以在业务执行前做强校验，把模型误调用控制在工具边界外。

### 为什么高风险操作需要人工审核？

Agent 可以提升自动化效率，但退款、删除、改价等操作有业务风险。Human-in-the-loop 能在自动化和安全之间做平衡。

### 为什么使用 SQLite？

这是演示项目，SQLite 足够表达订单、物流、工单、审批、退款等业务表关系，部署成本低，适合本地面试演示。

### 后续如何生产化？

可以替换真实订单/CRM 系统，增加 Redis 会话记忆、权限体系、审计日志、后台管理页和 LangGraph 状态机编排。
