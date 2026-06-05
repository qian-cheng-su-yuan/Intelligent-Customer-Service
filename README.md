# Enterprise Intelligent Customer Service

基于 Tool Calling 的企业智能客服与工单路由引擎。项目面向企业客服常见场景，支持订单查询、物流查询、售后报修、退款申请和高风险操作人工审核，适合作为 AI Agent / 大模型应用开发 / Python 后端开发方向的可交付作品。

项目已包含可视化前端工作台、FastAPI 后端、SQLite 演示数据、CLI 演示命令、pytest 自动化测试和详细文档。填写必要的模型 API Key 后，可以跑通真实 Qwen 百炼 OpenAI 兼容 Tool Calling；没有 API Key 时，也可以通过前端右侧业务工具完整演示本地闭环。

## 功能亮点

- 美观 UI 工作台：首页 `/` 提供会话、业务工具、运行状态和人工审核队列。
- 真实 Tool Calling：使用 OpenAI Python SDK 对接 Qwen 百炼 OpenAI 兼容接口。
- 本地可演示：SQLite 内置订单和物流数据，开箱即可演示查询、工单、退款审核。
- 参数强校验：Pydantic 校验订单号、客户 ID、退款金额、联系方式等参数。
- 风险控制：大额退款进入 Human-in-the-loop 审核，审批后才写入退款记录。
- 工程化交付：标准 `src/` 结构、测试、文档、环境示例和 GitHub 可读说明。

## 技术栈

- Python 3.10+
- FastAPI + Uvicorn
- OpenAI Python SDK
- Pydantic + pydantic-settings
- SQLite
- Typer + Rich
- 原生 HTML/CSS/JavaScript 前端
- pytest + httpx

## 项目结构

```text
.
├── docs/
│   ├── api.md
│   ├── architecture.md
│   ├── delivery-guide.md
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
│       ├── static/
│       │   ├── app.js
│       │   ├── index.html
│       │   └── styles.css
│       └── tools.py
├── tests/
├── .env.example
├── pyproject.toml
└── README.md
```

## 快速运行

### 1. 安装依赖

```bash
python -m pip install -e ".[dev]"
```

建议使用 Python 3.10 到 3.12。不要使用 Python alpha / preview 版本。

### 2. 配置环境变量

复制环境变量模板：

```powershell
copy .env.example .env
```

Linux / macOS：

```bash
cp .env.example .env
```

编辑 `.env`：

```env
DASHSCOPE_API_KEY=your_dashscope_api_key
LLM_API_KEY=
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
DATABASE_PATH=data/customer_service.db
REFUND_REVIEW_THRESHOLD=500
```

默认使用 Qwen 百炼 OpenAI 兼容接口。官方文档参考：
[阿里云百炼 OpenAI 兼容说明](https://help.aliyun.com/zh/model-studio/compatibility-of-openai-with-dashscope)。

如果使用 DeepSeek，可改为：

```env
LLM_API_KEY=your_deepseek_api_key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

DeepSeek Function Calling 参考：
[DeepSeek Function Calling](https://api-docs.deepseek.com/guides/function_calling)。

### 3. 初始化数据库

```bash
python -m intelligent_customer_service.db init --seed
```

### 4. 启动服务

```bash
uvicorn intelligent_customer_service.api:app --reload
```

打开前端工作台：

```text
http://127.0.0.1:8000/
```

打开 API 文档：

```text
http://127.0.0.1:8000/docs
```

## 前端演示步骤

1. 打开 `http://127.0.0.1:8000/`。
2. 确认左侧 Runtime 显示 `Online`。
3. 如已填写 API Key，LLM 状态会显示 `LLM ready: qwen-plus`。
4. 在会话框输入：`帮我查询一下订单 ORD-1001`，点击 `Send`。
5. 点击右侧 `订单查询`，查看结构化订单结果。
6. 点击 `物流追踪`，查看物流状态。
7. 点击 `售后报修`，生成售后工单。
8. 点击 `大额退款`，系统生成待审核记录。
9. 在人工审核区域点击 `Approve`，退款记录进入 `processing` 状态。

没有 API Key 时，第 4 步 `/chat` 会提示配置缺失，但第 5 到第 9 步仍然可以完整跑通本地业务闭环。

## CLI 演示步骤

直接调用本地业务工具，不消耗 LLM token：

```bash
ics tool query_order --order-id ORD-1001 --customer-id CUST-001
ics tool query_logistics --order-id ORD-1001 --customer-id CUST-001
ics tool create_repair_ticket --order-id ORD-1001 --customer-id CUST-001 --issue-type hardware --description "Noise cancelling is unstable" --contact 19838622783
ics tool request_refund --order-id ORD-1001 --customer-id CUST-001 --amount 899 --reason "quality issue"
ics approvals
ics approve 1 --reviewer admin
```

真实 LLM Tool Calling：

```bash
ics chat "帮我查询一下订单 ORD-1001" --customer-id CUST-001
```

## API 示例

健康检查：

```bash
curl http://127.0.0.1:8000/health
```

配置状态：

```bash
curl http://127.0.0.1:8000/config/status
```

智能客服对话：

```bash
curl -X POST http://127.0.0.1:8000/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"帮我查询一下订单 ORD-1001\",\"customer_id\":\"CUST-001\"}"
```

本地工具调用：

```bash
curl -X POST http://127.0.0.1:8000/tools/query_order ^
  -H "Content-Type: application/json" ^
  -d "{\"order_id\":\"ORD-1001\",\"customer_id\":\"CUST-001\"}"
```

审批大额退款：

```bash
curl -X POST http://127.0.0.1:8000/approvals/1/approve ^
  -H "Content-Type: application/json" ^
  -d "{\"reviewer\":\"admin\"}"
```

## Tool Calling 设计

系统向大模型暴露 4 个工具：

| 工具名 | 功能 | 关键参数 |
| --- | --- | --- |
| `query_order` | 查询订单信息 | `order_id`, `customer_id` |
| `query_logistics` | 查询物流状态 | `order_id`, `customer_id` |
| `create_repair_ticket` | 创建售后报修工单 | `order_id`, `issue_type`, `description`, `contact` |
| `request_refund` | 申请退款 | `order_id`, `amount`, `reason` |

工具参数由 Pydantic 模型生成 JSON Schema。模型返回 Tool Call 后，后端会再次使用 Pydantic 做强校验，避免缺字段、金额非法、客户越权等问题直接进入业务执行。

## 数据库设计

- `orders`：订单模拟数据
- `logistics`：物流模拟数据
- `repair_tickets`：售后工单
- `refunds`：退款记录
- `pending_approvals`：高风险操作人工审核队列

内置演示数据：

- `ORD-1001` / `CUST-001`
- `ORD-1002` / `CUST-001`
- `ORD-2001` / `CUST-002`

## 测试与验收

运行测试：

```bash
python -m pytest
```

验收点：

- 首页 `/` 可打开，并显示漂亮的客服工作台。
- `/config/status` 能显示模型配置状态。
- 订单查询、物流追踪、售后报修、大额退款审核能通过前端跑通。
- 配置 API Key 后，`/chat` 能调用真实 LLM 并触发 Tool Calling。
- 所有测试通过。

## 常见问题

### `/chat` 返回 503

说明未配置 `DASHSCOPE_API_KEY` 或 `LLM_API_KEY`。复制 `.env.example` 为 `.env` 后填写真实 key。

### 前端可以打开，但大模型不可用

这是正常的交付演示模式。右侧业务工具不依赖模型，可以先演示本地闭环；配置 key 后再演示真实 Tool Calling。

### 默认 Python 跑测试报 Pydantic DLL 错误

通常是使用了 Python alpha / preview 版本。请切换到 Python 3.10 到 3.12。

## 可扩展方向

- 接入真实订单系统、物流系统和 CRM。
- 增加 Redis 会话记忆和多轮上下文持久化。
- 使用 LangGraph 编排复杂客服流程。
- 将人工审核扩展为管理后台。
- 接入向量库，实现客服知识库 RAG 问答。
