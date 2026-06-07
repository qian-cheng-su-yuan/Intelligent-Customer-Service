# 交付运行指南

这份文档面向项目交付、部署检查和本地验收。目标是让接收项目的人在填写必要信息后，可以从零启动系统，并完整跑通订单、物流、售后、退款审核和真实 Tool Calling。

## 1. 环境要求

- Windows 10 / Windows 11
- Python 3.10 到 3.12，推荐 Python 3.11
- 可访问大模型服务的网络环境
- 可选：Qwen 百炼、DeepSeek 或其他 OpenAI 兼容模型 API Key

检查 Python：

```powershell
py -0p
py -3.11 --version
```

## 2. 配置 API Key

复制配置文件：

```powershell
copy .env.example .env
```

Qwen 百炼配置：

```env
DASHSCOPE_API_KEY=your_dashscope_api_key
LLM_API_KEY=
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
DATABASE_PATH=data/customer_service.db
REFUND_REVIEW_THRESHOLD=500
```

DeepSeek 或其他 OpenAI 兼容模型：

```env
DASHSCOPE_API_KEY=
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
DATABASE_PATH=data/customer_service.db
REFUND_REVIEW_THRESHOLD=500
```

说明：

- 未配置 Key 时，业务接口仍可运行。
- 配置 Key 后，`/chat` 才会调用真实模型。
- 不要把真实 `.env` 提交到 Git。

## 3. 安装依赖

```powershell
py -3.11 -m pip install -e ".[dev]"
```

## 4. 初始化数据库

```powershell
py -3.11 -m intelligent_customer_service.db init --reset --seed
```

该命令会删除旧的本地 SQLite 文件，重新创建表，并写入初始订单和物流数据，适合首次交付验收或重新跑通完整流程。已有业务数据需要保留时，请去掉 `--reset`。默认数据库路径：

```text
data/customer_service.db
```

## 5. 启动服务

```powershell
py -3.11 -m uvicorn intelligent_customer_service.api:app --reload
```

访问地址：

```text
http://127.0.0.1:8000/
```

API 文档：

```text
http://127.0.0.1:8000/docs
```

## 6. 业务验收流程

### 6.1 订单和物流

1. 打开首页，确认 Runtime 显示 `Online`。
2. 查看 `订单记录`，确认存在 `ORD-1001`、`ORD-1002`、`ORD-2001`。
3. 点击 `订单查询`，确认结果中包含订单号、客户 ID、商品名和金额。
4. 点击 `物流追踪`，确认结果中包含承运商、运单号和最新物流事件。

### 6.2 售后工单

1. 点击 `售后报修`。
2. `Tickets` 指标增加。
3. `售后工单` 列表出现新的工单记录。

### 6.3 退款审核

1. 点击 `大额退款`。
2. 系统返回 `requires_approval = true`。
3. `人工审核` 列表出现待处理记录。
4. 点击 `Approve`，确认待审核记录清空，`退款记录` 新增 `processing` 记录。
5. 再次点击 `大额退款` 后点击 `Reject`，确认退款记录不新增。

### 6.4 真实 Tool Calling

配置 API Key 后，在聊天框输入：

```text
帮我查询一下订单 ORD-1001
```

预期结果：

- 模型选择 `query_order` 工具。
- 后端校验 `order_id` 和 `customer_id`。
- 系统查询 SQLite 并返回客服回复。
- 工具调用轨迹显示在 `工具结果` 面板。

## 7. 自动化测试

```powershell
py -3.11 -m pytest -q
```

验收标准：

- 所有测试通过。
- 首页无中文乱码。
- `/orders`、`/tickets`、`/approvals`、`/refunds` 可正常返回数据。
- 大额退款审批通过才创建退款记录。
- 大额退款拒绝不创建退款记录。

## 8. 常用排查

### `/chat` 返回 503

检查 `.env` 是否填写了 `DASHSCOPE_API_KEY` 或 `LLM_API_KEY`，修改后重启服务。

### 页面显示 Config unavailable

确认后端服务仍在运行，并访问：

```text
http://127.0.0.1:8000/health
```

### Python 依赖安装失败

优先确认 Python 版本：

```powershell
py -3.11 --version
```

如果系统默认 `python` 指向 3.13 或 3.14，请显式使用 `py -3.11`。

## 9. 交付清单

- 源码仓库
- `.env.example`
- README
- `docs/operation-guide.md`
- `docs/api.md`
- `docs/architecture.md`
- pytest 测试
- 可初始化的 SQLite 数据库脚本
