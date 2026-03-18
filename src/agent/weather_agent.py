from langchain.agents import create_agent
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from loguru import logger
from prompt.prompt import WEATHER_SYS_PROMPT
from tools.weather import get_current_weather, get_weather_forecast
from agent.base import create_model

weather_agent = create_agent(
    model=create_model(),
    tools=[get_current_weather, get_weather_forecast],
    system_prompt=WEATHER_SYS_PROMPT,
    name="weather-agent",
)


@tool("weather", description="Get the weather for a given city", return_direct=True)
async def weather_agent_facade(query: str, config: RunnableConfig) -> str:
    """Invoke the weather sub-agent and return its final answer."""

    logger.info(f"weather_agent_facade_invoked: {query}")

    # Strip the parent thread's configurable (thread_id / checkpointer) so that
    # the sub-agent starts with a clean slate and does NOT inherit the full
    # main-agent chat history, which would waste tokens on every LLM call.
    sub_config = RunnableConfig(callbacks=config.get("callbacks"))

    result = await weather_agent.ainvoke(
        {"messages": [{"role": "user", "content": query}]},
        config=sub_config,
    )

    logger.info(f"weather_agent_facade_result: {result}")

    messages = result.get("messages", [])
    if messages:
        last = messages[-1]
        return last.content if hasattr(last, "content") else str(last)
    return str(result)
