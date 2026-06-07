# Delivery Guide

这份文档用于项目交付验收。详细运行步骤见 [operation-guide.md](operation-guide.md)。

## 交付内容

- FastAPI 后端服务
- 原生 HTML/CSS/JavaScript 运营工作台
- SQLite 业务数据库
- OpenAI-compatible Tool Calling 封装
- Pydantic 参数校验
- Human-in-the-loop 退款审核
- CLI 运维命令
- pytest 自动化测试

## 必要配置

真实 LLM 能力需要以下任意一组配置。

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

本地业务接口不依赖 API Key。

## 启动

```powershell
py -3.11 -m pip install -e ".[dev]"
copy .env.example .env
py -3.11 -m intelligent_customer_service.db init --seed
py -3.11 -m uvicorn intelligent_customer_service.api:app --reload
```

访问：

```text
http://127.0.0.1:8000/
```

## 验收标准

- `py -3.11 -m pytest -q` 全部通过。
- 首页 Runtime 显示 `Online`。
- 订单、物流、售后工单、退款审核和退款记录可完整运行。
- 大额退款审批通过才创建退款记录。
- 大额退款拒绝不创建退款记录。
- 配置 API Key 后，`/chat` 可触发真实 Tool Calling。
