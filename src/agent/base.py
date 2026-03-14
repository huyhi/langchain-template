import json
import os
from itertools import count
from typing import Any
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import BaseMessage
from langchain_core.outputs import LLMResult
from langchain_openai import ChatOpenAI
from loguru import logger

_SEP = "=" * 72
_call_counter = count(1)


def _msg_to_dict(msg: BaseMessage) -> dict[str, Any]:
    role_map = {"human": "user", "ai": "assistant"}
    d: dict[str, Any] = {
        "role": role_map.get(msg.type, msg.type),
        "content": msg.content,
    }
    if getattr(msg, "tool_calls", None):
        d["tool_calls"] = [
            {
                "id": tc.get("id", ""),
                "type": "function",
                "function": {
                    "name": tc.get("name", ""),
                    "arguments": json.dumps(tc.get("args", {}), ensure_ascii=False),
                },
            }
            for tc in msg.tool_calls
        ]
    if getattr(msg, "tool_call_id", None):
        d["role"] = "tool"
        d["tool_call_id"] = msg.tool_call_id
    return d


def _pretty(obj: Any) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False)


class LLMCallLogger(BaseCallbackHandler):
    """Logs every LLM call as OpenAI-style request / response JSON."""

    def __init__(self) -> None:
        self._run_seq: dict[UUID, int] = {}

    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[BaseMessage]],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        seq = next(_call_counter)
        self._run_seq[run_id] = seq

        body: dict[str, Any] = {
            "messages": [_msg_to_dict(m) for batch in messages for m in batch],
        }

        inv = kwargs.get("invocation_params") or {}
        for key in ("model", "model_name", "temperature", "max_tokens", "tools", "tool_choice"):
            if key in inv:
                body[key] = inv[key]

        logger.debug(f"\n{_SEP}\n>>> LLM Request #{seq}\n{_SEP}\n{_pretty(body)}")

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        seq = self._run_seq.pop(run_id, "?")

        for gen_list in response.generations:
            for gen in gen_list:
                msg = gen.message
                resp = _msg_to_dict(msg)

                meta = getattr(msg, "response_metadata", None) or {}
                usage = meta.get("token_usage") or meta.get("usage") or {}
                if usage:
                    resp["usage"] = usage
                finish = meta.get("finish_reason")
                if finish:
                    resp["finish_reason"] = finish

                logger.debug(
                    f"\n{_SEP}\n<<< LLM Response #{seq}\n{_SEP}\n{_pretty(resp)}"
                )


_llm_logger = LLMCallLogger()


def create_model() -> ChatOpenAI:
    base_url = os.environ["LLM_BASE_URL"]
    api_key = os.environ["LLM_API_KEY"]
    model_name = os.getenv("LLM_MODEL", "default")

    return ChatOpenAI(
        base_url=base_url,
        api_key=api_key,
        model=model_name,
        callbacks=[_llm_logger],
    )
