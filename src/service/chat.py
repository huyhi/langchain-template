import json
from dataclasses import dataclass, field
from typing import AsyncGenerator, Callable
from uuid import UUID

from loguru import logger
from pydantic import BaseModel
from sqlmodel import Session

from agent.base import create_model
from agent.main_agent import agent
from db import repository
from db.database import engine
from db.models import Thread
from model.chat import MessageRole
from model.chunk import (
    FinishChunk,
    FinishStepChunk,
    StartChunk,
    StartStepChunk,
    TextDeltaChunk,
    TextEndChunk,
    TextStartChunk,
    ToolInputAvailableChunk,
    ToolInputDeltaChunk,
    ToolInputStartChunk,
    ToolOutputAvailableChunk,
)


# ── SSE helper ────────────────────────────────────────────────────────────────


def _sse(chunk: BaseModel) -> str:
    return f"data: {chunk.model_dump_json(by_alias=True)}\n\n"


# ── Shared streaming state ────────────────────────────────────────────────────


@dataclass
class _StreamState:
    collected_texts: list[str] = field(default_factory=list)
    active_text_runs: set[str] = field(default_factory=set)
    active_tool_calls: dict[str, str] = field(
        default_factory=dict
    )  # tool_call_id -> tool_name
    finish_reason: str = "stop"


# ── Per-event handlers ────────────────────────────────────────────────────────


async def _on_chat_model_start(
    event: dict, state: _StreamState
) -> AsyncGenerator[str, None]:
    yield _sse(StartStepChunk())


async def _on_chat_model_stream(
    event: dict, state: _StreamState
) -> AsyncGenerator[str, None]:
    run_id = event["run_id"]
    chunk_data = event["data"]["chunk"]

    content = chunk_data.content
    if isinstance(content, str) and content:
        if run_id not in state.active_text_runs:
            state.active_text_runs.add(run_id)
            yield _sse(TextStartChunk(id=run_id))
        state.collected_texts.append(content)
        yield _sse(TextDeltaChunk(id=run_id, delta=content))

    for tc in getattr(chunk_data, "tool_call_chunks", []):
        tc_id: str = tc.get("id") or str(tc.get("index", run_id))
        tc_name: str = tc.get("name") or ""
        tc_args: str = tc.get("args") or ""

        if tc_id not in state.active_tool_calls:
            state.active_tool_calls[tc_id] = tc_name
            if tc_name:
                yield _sse(ToolInputStartChunk(tool_call_id=tc_id, tool_name=tc_name))

        if tc_args:
            yield _sse(
                ToolInputDeltaChunk(tool_call_id=tc_id, input_text_delta=tc_args)
            )


async def _on_chat_model_end(
    event: dict, state: _StreamState
) -> AsyncGenerator[str, None]:
    run_id = event["run_id"]

    if run_id in state.active_text_runs:
        yield _sse(TextEndChunk(id=run_id))
        state.active_text_runs.discard(run_id)

    output = event["data"].get("output")
    if output:
        for tc in getattr(output, "tool_calls", []):
            tc_id = tc.get("id", run_id)
            if tc_id in state.active_tool_calls:
                yield _sse(
                    ToolInputAvailableChunk(
                        tool_call_id=tc_id,
                        tool_name=tc.get("name", ""),
                        input=tc.get("args", {}),
                    )
                )
                del state.active_tool_calls[tc_id]

        if hasattr(output, "response_metadata"):
            state.finish_reason = output.response_metadata.get("finish_reason", "stop")

    yield _sse(FinishStepChunk())


async def _on_tool_start(event: dict, state: _StreamState) -> AsyncGenerator[str, None]:
    run_id = event["run_id"]
    metadata = event.get("metadata", {})
    tc_id = metadata.get("tool_call_id", run_id)
    tool_name = event["name"]
    input_data = event["data"].get("input", {})

    if tc_id not in state.active_tool_calls:
        input_str = (
            json.dumps(input_data) if isinstance(input_data, dict) else str(input_data)
        )
        yield _sse(StartStepChunk())
        yield _sse(ToolInputStartChunk(tool_call_id=tc_id, tool_name=tool_name))
        yield _sse(ToolInputDeltaChunk(tool_call_id=tc_id, input_text_delta=input_str))
        yield _sse(
            ToolInputAvailableChunk(
                tool_call_id=tc_id, tool_name=tool_name, input=input_data
            )
        )


async def _on_tool_end(event: dict, state: _StreamState) -> AsyncGenerator[str, None]:
    run_id = event["run_id"]
    metadata = event.get("metadata", {})
    tc_id = metadata.get("tool_call_id", run_id)
    output = event["data"].get("output")
    output_content = output.content if hasattr(output, "content") else str(output)
    yield _sse(ToolOutputAvailableChunk(tool_call_id=tc_id, output=output_content))
    yield _sse(FinishStepChunk())


_EVENT_HANDLERS: dict[str, Callable] = {
    "on_chat_model_start": _on_chat_model_start,
    "on_chat_model_stream": _on_chat_model_stream,
    "on_chat_model_end": _on_chat_model_end,
    "on_tool_start": _on_tool_start,
    "on_tool_end": _on_tool_end,
}


# ── Public streaming entry point ──────────────────────────────────────────────


async def stream_agent(
    message: str, thread_id: UUID, message_id: str
) -> AsyncGenerator[str, None]:
    state = _StreamState()

    yield _sse(StartChunk(message_id=message_id, thread_id=str(thread_id)))

    async for event in agent.astream_events(
        {"messages": [{"role": "user", "content": message}]},
        version="v2",
    ):
        handler = _EVENT_HANDLERS.get(event["event"])
        if handler:
            async for chunk in handler(event, state):
                yield chunk

    full_response = "".join(state.collected_texts)
    if full_response:
        with Session(engine) as session:
            repository.message_create(
                session, thread_id, MessageRole.ASSISTANT, full_response
            )

    yield _sse(FinishChunk(finish_reason=state.finish_reason))
    yield "data: [DONE]\n\n"


# ── Thread helpers ────────────────────────────────────────────────────────────


def get_or_create_thread(session: Session, thread_id: UUID) -> Thread:
    if thread_id:
        thread = repository.thread_get(session, thread_id)
        if not thread:
            thread = repository.thread_create(session)
    else:
        thread = repository.thread_create(session)
    return thread


async def generate_and_set_title(message: str, thread_id: UUID) -> None:
    llm = create_model()
    prompt = (
        "Summarize the following user message into a concise thread title "
        "(max 8 words, no punctuation at the end):\n\n"
        f"{message}"
    )
    response = await llm.ainvoke([{"role": "user", "content": prompt}])

    logger.info(
        f"generate_title {{'title': {response.content.strip()}, 'thread_id': {thread_id}}}"
    )

    title = response.content.strip()
    if title:
        with Session(engine) as session:
            repository.thread_update_title(session, thread_id, title)
