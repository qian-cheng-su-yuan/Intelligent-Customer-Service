import json
import uuid
from typing import Any

from .llm_client import SYSTEM_PROMPT, MissingApiKeyError, OpenAICompatibleToolCallingClient, parse_tool_arguments
from .tools import CustomerServiceTools


class CustomerServiceAgent:
    def __init__(self, llm_client: OpenAICompatibleToolCallingClient, tools: CustomerServiceTools):
        self.llm_client = llm_client
        self.tools = tools

    def chat(self, message: str, customer_id: str, conversation_id: str | None = None) -> dict[str, Any]:
        conv_id = conversation_id or f"conv-{uuid.uuid4().hex[:12]}"
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"customer_id={customer_id}\nUser message: {message}",
            },
        ]

        try:
            first_response = self.llm_client.complete_with_tools(messages)
        except MissingApiKeyError:
            raise
        except Exception as exc:
            return {
                "conversation_id": conv_id,
                "answer": f"LLM request failed: {exc}",
                "tool_calls": [],
            }

        assistant_message = first_response.choices[0].message
        tool_calls = getattr(assistant_message, "tool_calls", None) or []
        if not tool_calls:
            return {
                "conversation_id": conv_id,
                "answer": assistant_message.content or "I did not need to call a tool for this request.",
                "tool_calls": [],
            }

        messages.append(
            {
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": [tool_call.model_dump() for tool_call in tool_calls],
            }
        )
        executed_calls: list[dict[str, Any]] = []
        for tool_call in tool_calls:
            name = tool_call.function.name
            arguments = parse_tool_arguments(tool_call.function.arguments)
            arguments.setdefault("customer_id", customer_id)
            result = self.tools.execute(name, arguments)
            executed_calls.append({"name": name, "arguments": arguments, "result": result})
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": name,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

        try:
            final_response = self.llm_client.complete_with_tools(messages)
            answer = final_response.choices[0].message.content or "Tool call completed."
        except Exception:
            answer = self._fallback_answer(executed_calls)

        return {"conversation_id": conv_id, "answer": answer, "tool_calls": executed_calls}

    @staticmethod
    def _fallback_answer(executed_calls: list[dict[str, Any]]) -> str:
        if not executed_calls:
            return "No tool was executed."
        latest = executed_calls[-1]["result"]
        if latest.get("requires_approval"):
            approval_id = latest["approval"]["id"]
            return f"Operation is suspended for human approval. Approval ID: {approval_id}."
        if latest.get("ok"):
            return "Tool call completed successfully. See tool_calls for structured details."
        return f"Tool call failed: {latest.get('error', 'unknown error')}"
