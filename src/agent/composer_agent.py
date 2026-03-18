"""
Composer Agent — Plan-and-Execute Architecture
=============================================

Design overview
---------------
1. PLAN   – The LLM analyses the user's request and generates a flexible
             CompositionPlan: an ordered list of steps, each with a `detail`
             description and a `tool_name` to invoke.

2. EXECUTE – A single executor node iterates over the plan steps one by one.
             For each step it dispatches to the matching tool function
             (lyrics / melody / arrangement / full_song), passing along all
             accumulated state so later stages can build on earlier ones.

3. LOOP   – After each execution, a conditional edge checks whether there are
             remaining steps.  If yes → loop back to the executor; if no → END.

Graph topology
--------------
  [START] → planner → executor ⟲ (loop until all steps done) → [END]

State
-----
  ComposerState carries every artifact produced so far, the plan, the current
  step index, and the original user request.
"""

from __future__ import annotations

from typing import Literal, Optional, TypedDict

from langchain_core.callbacks import adispatch_custom_event
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.graph import END, StateGraph
from loguru import logger
from pydantic import BaseModel, Field

from agent.base import create_model
from prompt.prompt import (
    COMPOSER_ARRANGEMENT_PROMPT,
    COMPOSER_FULL_SONG_PROMPT,
    COMPOSER_LYRICS_PROMPT,
    COMPOSER_MELODY_PROMPT,
    COMPOSER_PLANNER_PROMPT,
)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


class PlanStep(BaseModel):
    """A single step in the composition plan."""

    detail: str = Field(
        description="Rich description of what this step should accomplish, "
        "including any relevant musical parameters "
        "(genre, mood, key, tempo, instruments, structure, theme, etc.)"
    )
    tool_name: Literal["lyrics", "melody", "arrangement", "full_song"] = Field(
        description="The tool to invoke: lyrics, melody, arrangement, or full_song"
    )


class CompositionPlan(BaseModel):
    """Flexible composition plan: an ordered list of steps to execute."""

    steps: list[PlanStep] = Field(description="Ordered list of composition steps")


# ---------------------------------------------------------------------------
# Graph state
# ---------------------------------------------------------------------------


class ComposerState(TypedDict):
    """Shared state that flows through every node in the graph."""

    user_request: str

    plan: Optional[list[dict]]       # list of serialised PlanStep dicts
    current_step_index: int          # tracks which step to execute next

    lyrics: str
    arrangement: str
    melody: str
    full_song: str


# ---------------------------------------------------------------------------
# Tool executors — one per tool_name
# ---------------------------------------------------------------------------


async def _execute_lyrics(model, state: ComposerState, detail: str) -> str:
    system_prompt = COMPOSER_LYRICS_PROMPT.format(detail=detail)
    result = await model.ainvoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"User request: {state['user_request']}"),
    ])
    return result.content


async def _execute_arrangement(model, state: ComposerState, detail: str) -> str:
    system_prompt = COMPOSER_ARRANGEMENT_PROMPT.format(detail=detail)
    parts = []
    if state.get("lyrics"):
        parts.append(f"Lyrics:\n{state['lyrics']}")
    parts.append(f"User request: {state['user_request']}")
    result = await model.ainvoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content="\n\n".join(parts)),
    ])
    return result.content


async def _execute_melody(model, state: ComposerState, detail: str) -> str:
    system_prompt = COMPOSER_MELODY_PROMPT.format(detail=detail)
    parts = []
    if state.get("lyrics"):
        parts.append(f"Lyrics:\n{state['lyrics']}")
    if state.get("arrangement"):
        parts.append(f"Arrangement:\n{state['arrangement']}")
    parts.append(f"User request: {state['user_request']}")
    result = await model.ainvoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content="\n\n".join(parts)),
    ])
    return result.content


async def _execute_full_song(model, state: ComposerState, detail: str) -> str:
    system_prompt = COMPOSER_FULL_SONG_PROMPT.format(detail=detail)
    parts = []
    if state.get("lyrics"):
        parts.append(f"Lyrics:\n{state['lyrics']}")
    if state.get("arrangement"):
        parts.append(f"Arrangement:\n{state['arrangement']}")
    if state.get("melody"):
        parts.append(f"Melody:\n{state['melody']}")
    parts.append(f"User request: {state['user_request']}")
    result = await model.ainvoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content="\n\n".join(parts)),
    ])
    return result.content


_TOOL_EXECUTORS = {
    "lyrics": _execute_lyrics,
    "arrangement": _execute_arrangement,
    "melody": _execute_melody,
    "full_song": _execute_full_song,
}


# ---------------------------------------------------------------------------
# Node factories
# ---------------------------------------------------------------------------


def _make_planner_node(model):
    """Planner node — analyses the user request and returns a list of plan steps."""

    structured_model = model.with_structured_output(CompositionPlan)

    async def planner_node(state: ComposerState, config: RunnableConfig) -> dict:
        logger.info("[composer] planner: analysing request …")

        plan: CompositionPlan = await structured_model.ainvoke(
            [
                SystemMessage(content=COMPOSER_PLANNER_PROMPT),
                HumanMessage(content=state["user_request"]),
            ]
        )

        steps = [step.model_dump() for step in plan.steps]
        logger.info(
            f"[composer] plan: {len(steps)} steps — "
            f"{[s['tool_name'] for s in steps]}"
        )

        await adispatch_custom_event(
            "composer.plan_available",
            {"plan": steps},
            config=config,
        )

        return {"plan": steps, "current_step_index": 0}

    return planner_node


def _make_executor_node(model):
    """Executor node — picks the current plan step and dispatches to the right tool."""

    async def executor_node(state: ComposerState, config: RunnableConfig) -> dict:
        plan = state["plan"]
        idx = state["current_step_index"]
        step = plan[idx]
        tool_name = step["tool_name"]
        detail = step["detail"]

        logger.info(
            f"[composer] executing step {idx + 1}/{len(plan)}: {tool_name}"
        )
        await adispatch_custom_event(
            "composer.step_start",
            {"step": tool_name, "detail": detail, "index": idx},
            config=config,
        )

        executor_fn = _TOOL_EXECUTORS[tool_name]
        result = await executor_fn(model, state, detail)

        logger.info(
            f"[composer] step {idx + 1}/{len(plan)} complete: {tool_name}"
        )
        await adispatch_custom_event(
            "composer.step_complete",
            {"step": tool_name, "index": idx},
            config=config,
        )

        return {
            tool_name: result,
            "current_step_index": idx + 1,
        }

    return executor_node


# ---------------------------------------------------------------------------
# Conditional edge
# ---------------------------------------------------------------------------


def _should_continue(state: ComposerState) -> str:
    """Return 'executor' if there are remaining steps, otherwise END."""
    if state["current_step_index"] < len(state["plan"]):
        return "executor"
    return END


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------


def _build_composer_graph():
    """Compile the plan-and-execute LangGraph for music composition."""

    model = create_model()

    builder = StateGraph(ComposerState)

    builder.add_node("planner", _make_planner_node(model))
    builder.add_node("executor", _make_executor_node(model))

    builder.set_entry_point("planner")
    builder.add_edge("planner", "executor")
    builder.add_conditional_edges(
        "executor",
        _should_continue,
        {"executor": "executor", END: END},
    )

    return builder.compile()


_composer_graph = _build_composer_graph()


# ---------------------------------------------------------------------------
# Facade tool — exposes the composer agent to the main agent
# ---------------------------------------------------------------------------


@tool("compose_music", return_direct=True, description=(
    "Compose a complete original song for the user. "
    "Handles everything: lyrics, arrangement, melody, and final presentation. "
    "Provide the user's raw music request as the query."
))
async def composer_agent_facade(query: str, config: RunnableConfig) -> str:
    """Invoke the composer sub-agent and return the finished song."""

    logger.info(f"[composer] facade invoked: {query!r}")

    sub_config = RunnableConfig(callbacks=config.get("callbacks"))

    initial_state: ComposerState = {
        "user_request": query,
        "plan": None,
        "current_step_index": 0,
        "lyrics": "",
        "arrangement": "",
        "melody": "",
        "full_song": "",
    }

    result = await _composer_graph.ainvoke(initial_state, config=sub_config)

    logger.info("[composer] facade complete.")
    return result.get("full_song", "Composition failed — no output produced.")
