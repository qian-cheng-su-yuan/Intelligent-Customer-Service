from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .agent import CustomerServiceAgent
from .config import Settings, get_settings
from .database import initialize_database
from .llm_client import MissingApiKeyError, OpenAICompatibleToolCallingClient
from .repositories import CustomerServiceRepository
from .schemas import ApproveRequest, ChatRequest, ChatResponse
from .tools import CustomerServiceTools


def build_default_components(settings: Settings | None = None) -> tuple[CustomerServiceAgent, CustomerServiceTools]:
    resolved_settings = settings or get_settings()
    initialize_database(resolved_settings.database_path, seed=True)
    repository = CustomerServiceRepository(resolved_settings.database_path)
    tools = CustomerServiceTools(repository, refund_review_threshold=resolved_settings.refund_review_threshold)
    llm_client = OpenAICompatibleToolCallingClient(resolved_settings)
    return CustomerServiceAgent(llm_client, tools), tools


def create_app(agent: CustomerServiceAgent | None = None, tools: CustomerServiceTools | None = None) -> FastAPI:
    app = FastAPI(
        title="Enterprise Intelligent Customer Service",
        description="Tool Calling based customer service and ticket routing engine.",
        version="0.1.0",
    )
    static_dir = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", include_in_schema=False)
    def frontend() -> FileResponse:
        return FileResponse(static_dir / "index.html")

    if agent is None or tools is None:
        try:
            default_agent, default_tools = build_default_components()
            agent = agent or default_agent
            tools = tools or default_tools
        except MissingApiKeyError:
            agent = None
            settings = get_settings()
            initialize_database(settings.database_path, seed=True)
            tools = tools or CustomerServiceTools(
                CustomerServiceRepository(settings.database_path),
                refund_review_threshold=settings.refund_review_threshold,
            )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/config/status")
    def config_status() -> dict[str, Any]:
        settings = get_settings()
        return {
            "provider": "OpenAI-compatible",
            "llm_ready": bool(settings.api_key),
            "model": settings.llm_model,
            "base_url": settings.llm_base_url,
            "database_path": str(settings.database_path),
            "refund_review_threshold": settings.refund_review_threshold,
            "next_step": "Configure DASHSCOPE_API_KEY or LLM_API_KEY in .env to enable /chat."
            if not settings.api_key
            else "LLM chat is ready.",
        }

    @app.post("/chat", response_model=ChatResponse)
    def chat(request: ChatRequest) -> dict:
        if agent is None:
            raise HTTPException(
                status_code=503,
                detail="Missing DASHSCOPE_API_KEY or LLM_API_KEY. Configure .env before using /chat.",
            )
        return agent.chat(request.message, request.customer_id, request.conversation_id)

    @app.post("/tools/{tool_name}")
    def execute_tool(tool_name: str, arguments: dict[str, Any]) -> dict:
        result = tools.execute(tool_name, arguments)
        if not result.get("ok"):
            raise HTTPException(status_code=400, detail=result)
        return result

    @app.get("/tickets")
    def list_tickets() -> list[dict]:
        return tools.repository.list_tickets()

    @app.get("/approvals")
    def list_pending_approvals() -> list[dict]:
        return tools.repository.list_pending_approvals()

    @app.post("/approvals/{approval_id}/approve")
    def approve_refund(approval_id: int, request: ApproveRequest) -> dict:
        try:
            return tools.repository.approve_pending_refund(approval_id, request.reviewer)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return app


app = create_app()
