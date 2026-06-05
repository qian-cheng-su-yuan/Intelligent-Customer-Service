import json
from typing import Any

from openai import OpenAI

from .config import Settings
from .tools import build_tool_definitions


SYSTEM_PROMPT = """
You are an enterprise customer service agent. Use tools whenever the user asks
about orders, logistics, repair tickets, or refunds. Ask for missing required
information instead of inventing it. Never execute high-risk operations directly
when the tool result says human approval is required.
""".strip()


class MissingApiKeyError(RuntimeError):
    pass


class OpenAICompatibleToolCallingClient:
    def __init__(self, settings: Settings):
        if not settings.api_key:
            raise MissingApiKeyError(
                "Missing DASHSCOPE_API_KEY or LLM_API_KEY. Copy .env.example to .env and configure a key."
            )
        self.settings = settings
        self.client = OpenAI(api_key=settings.api_key, base_url=settings.llm_base_url)

    def complete_with_tools(self, messages: list[dict[str, Any]]) -> Any:
        return self.client.chat.completions.create(
            model=self.settings.llm_model,
            messages=messages,
            tools=build_tool_definitions(),
            tool_choice="auto",
            temperature=0.2,
        )


def parse_tool_arguments(raw_arguments: str | dict[str, Any] | None) -> dict[str, Any]:
    if raw_arguments is None:
        return {}
    if isinstance(raw_arguments, dict):
        return raw_arguments
    try:
        parsed = json.loads(raw_arguments)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}
