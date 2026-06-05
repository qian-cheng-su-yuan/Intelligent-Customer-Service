# Delivery Guide

这份文档面向项目交付、面试演示和本地验收。目标是让评审者在填写必要信息后，能够从零启动项目并跑通核心业务闭环。

## 交付内容

- FastAPI 后端服务
- 原生 HTML/CSS/JavaScript 前端工作台
- SQLite 演示数据库
- OpenAI-compatible Tool Calling 封装
- Pydantic 参数校验
- Human-in-the-loop 大额退款审核
- CLI 演示命令
- pytest 自动化测试

## 必要信息

真实 LLM 演示需要以下任意一组配置：

### Qwen 百炼

```env
DASHSCOPE_API_KEY=your_dashscope_api_key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
```

### DeepSeek 或其他 OpenAI 兼容模型

```env
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

本地业务工具演示不依赖 API Key。

## 从零启动

1. 安装依赖：

```bash
python -m pip install -e ".[dev]"
```

2. 复制配置：

```powershell
copy .env.example .env
```

3. 填写 `.env` 中的 API Key。

4. 初始化数据库：

```bash
python -m intelligent_customer_service.db init --seed
```

5. 启动服务：

```bash
uvicorn intelligent_customer_service.api:app --reload
```

6. 打开前端：

```text
http://127.0.0.1:8000/
```

## 推荐演示脚本

### 1. 展示运行状态

打开首页后，说明左侧显示：

- FastAPI 服务在线状态
- LLM 配置状态
- 当前工单数
- 当前待审核数

### 2. 展示订单查询

点击 `订单查询`，结果面板应显示：

- `order_id = ORD-1001`
- `customer_id = CUST-001`
- 商品名和订单金额

### 3. 展示物流查询

点击 `物流追踪`，结果面板应显示承运商、运单号和最新物流事件。

### 4. 展示售后报修

点击 `售后报修`，系统会创建一条售后工单，左侧 Tickets 数字增加。

### 5. 展示风险审核

点击 `大额退款`：

- 系统不会直接退款
- 结果中返回 `requires_approval = true`
- 人工审核区域出现待审核记录

点击 `Approve`：

- 待审核记录清空
- 系统创建退款记录
- 退款状态为 `processing`

### 6. 展示真实 Tool Calling

如果已填写 API Key，在会话框输入：

```text
帮我查询一下订单 ORD-1001
```

模型应选择 `query_order` 工具，后端完成参数校验和数据库查询，再返回自然语言结果。

## 验收命令

```bash
python -m pytest
python -m intelligent_customer_service.db init --seed
python -m intelligent_customer_service.cli tool query_order --order-id ORD-1001 --customer-id CUST-001
python -m intelligent_customer_service.cli tool request_refund --order-id ORD-1001 --customer-id CUST-001 --amount 899 --reason "quality issue"
```

## 交付验收标准

- `python -m pytest` 全部通过。
- 首页 `/` 可访问且无控制台错误。
- `/docs` 可访问 Swagger 文档。
- 不配置 API Key 时，本地工具链路仍可完整演示。
- 配置 API Key 后，`/chat` 可使用真实 LLM Tool Calling。
- README 和 docs 中包含安装、配置、启动、演示、测试和常见问题。
