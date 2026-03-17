from __future__ import annotations

from typing import Any, Literal, Union

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class _BaseChunk(BaseModel):
    """Base class for all SSE stream chunk types.

    Serializes with camelCase field names via `model_dump_json(by_alias=True)`.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class StartChunk(_BaseChunk):
    """Emitted once at the beginning of a stream."""

    type: Literal["start"] = "start"
    message_id: str
    thread_id: str


class StartStepChunk(_BaseChunk):
    """Marks the start of a processing step (LLM call or tool execution)."""

    type: Literal["start-step"] = "start-step"


class TextStartChunk(_BaseChunk):
    """Emitted when an LLM begins producing text tokens."""

    type: Literal["text-start"] = "text-start"
    id: str


class TextDeltaChunk(_BaseChunk):
    """A single incremental text token from the LLM."""

    type: Literal["text-delta"] = "text-delta"
    id: str
    delta: str


class TextEndChunk(_BaseChunk):
    """Emitted when an LLM stops producing text tokens."""

    type: Literal["text-end"] = "text-end"
    id: str


class ToolInputStartChunk(_BaseChunk):
    """Emitted when the LLM begins streaming arguments for a tool call."""

    type: Literal["tool-input-start"] = "tool-input-start"
    tool_call_id: str
    tool_name: str


class ToolInputDeltaChunk(_BaseChunk):
    """Incremental JSON fragment of a tool call's argument string."""

    type: Literal["tool-input-delta"] = "tool-input-delta"
    tool_call_id: str
    input_text_delta: str


class ToolInputAvailableChunk(_BaseChunk):
    """Emitted once the full, parsed tool input is available."""

    type: Literal["tool-input-available"] = "tool-input-available"
    tool_call_id: str
    tool_name: str
    input: Any


class ToolOutputAvailableChunk(_BaseChunk):
    """Emitted when a tool finishes executing and its output is ready."""

    type: Literal["tool-output-available"] = "tool-output-available"
    tool_call_id: str
    output: Any


class FinishStepChunk(_BaseChunk):
    """Marks the end of a processing step."""

    type: Literal["finish-step"] = "finish-step"


class FinishChunk(_BaseChunk):
    """Emitted at the end of the stream with the terminal finish reason."""

    type: Literal["finish"] = "finish"
    finish_reason: str


# ── Composer plan chunks ───────────────────────────────────────────────────────


class PlanAvailableChunk(_BaseChunk):
    """Emitted once the planner node finishes generating the composition plan."""

    type: Literal["plan-available"] = "plan-available"
    plan: Any


class PlanStepStartChunk(_BaseChunk):
    """Emitted when a plan execution step (lyrics / arrangement / melody / full_song) begins."""

    type: Literal["plan-step-start"] = "plan-step-start"
    step: str


class PlanStepCompleteChunk(_BaseChunk):
    """Emitted when a plan execution step finishes."""

    type: Literal["plan-step-complete"] = "plan-step-complete"
    step: str


StreamChunk = Union[
    StartChunk,
    StartStepChunk,
    TextStartChunk,
    TextDeltaChunk,
    TextEndChunk,
    ToolInputStartChunk,
    ToolInputDeltaChunk,
    ToolInputAvailableChunk,
    ToolOutputAvailableChunk,
    FinishStepChunk,
    FinishChunk,
    PlanAvailableChunk,
    PlanStepStartChunk,
    PlanStepCompleteChunk,
]
