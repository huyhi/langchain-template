from __future__ import annotations

from langchain_core.callbacks import adispatch_custom_event
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from loguru import logger

from agent.base import create_model
from langchain.agents import create_agent
from prompt.prompt import SEARCH_SONGS_SYS_PROMPT
from tools.search_songs import SongSearchResponse, search_songs_from_vector_db


# ---------------------------------------------------------------------------
# Wrapper tool — gives the agent access to the vector-DB search
# ---------------------------------------------------------------------------


@tool("vector_search_songs")
async def vector_search_songs_tool(
    query: str,
    top_k: int = 10,
    config: RunnableConfig = None,
) -> str:
    """Search the vector database for songs matching a semantic query.

    Args:
        query: Semantic search query describing the desired songs.
        top_k: Maximum number of results to return (default 10).
    """
    logger.info(f"[search_songs] vector search: query={query!r}, top_k={top_k}")

    response: SongSearchResponse = await search_songs_from_vector_db(
        query=query,
        top_k=top_k,
    )

    if response.results:
        await adispatch_custom_event(
            "search_songs.results_available",
            {
                "success": True,
                "results": [r.model_dump() for r in response.results],
            },
            config=config,
        )

    if not response.results:
        return "No matching songs found for the given query."

    lines = [f"Found {response.total} matching song(s):\n"]
    for i, song in enumerate(response.results, 1):
        line = f"  {i}. {song.title} — {song.artist}"
        if song.genre:
            line += f"  [{song.genre}]"
        if song.album:
            line += f"  (Album: {song.album})"
        line += f"  (score: {song.score:.4f})"
        lines.append(line)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Sub-agent construction
# ---------------------------------------------------------------------------

search_songs_agent = create_agent(
    model=create_model(),
    tools=[vector_search_songs_tool],
    system_prompt=SEARCH_SONGS_SYS_PROMPT,
    name="search-songs-agent",
)


# ---------------------------------------------------------------------------
# Facade tool — exposes the search-songs agent to the main agent
# ---------------------------------------------------------------------------


@tool(
    "search_songs",
    return_direct=True,
    description=(
        "Search for songs based on the user's natural-language description. "
        "Can find songs by mood, genre, theme, lyrics content, artist style, or any free-form description. "
        "Provide the user's raw search request as the query."
    ),
)
async def search_songs_agent_facade(query: str, config: RunnableConfig) -> str:
    """Invoke the search-songs sub-agent and return the results."""

    logger.info(f"[search_songs] facade invoked: {query!r}")

    sub_config = RunnableConfig(callbacks=config.get("callbacks"))

    result = await search_songs_agent.ainvoke(
        {"messages": [{"role": "user", "content": query}]},
        config=sub_config,
    )

    logger.info("[search_songs] facade complete.")

    messages = result.get("messages", [])
    if messages:
        last = messages[-1]
        return last.content if hasattr(last, "content") else str(last)
    return str(result)
