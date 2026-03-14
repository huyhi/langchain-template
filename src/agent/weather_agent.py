from langchain.agents import create_agent
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from prompt.prompt import WEATHER_SYS_PROMPT
from tools.weather import get_current_weather, get_weather_forecast
from agent.base import create_model

weather_agent = create_agent(
    model=create_model(),
    tools=[get_current_weather, get_weather_forecast],
    system_prompt=WEATHER_SYS_PROMPT,
    name="weather-agent",
)


@tool("weather", description="Get the weather for a given city")
async def weather_agent_facade(query: str, config: RunnableConfig) -> str:
    """Invoke the weather sub-agent and return its final answer."""
    result = await weather_agent.ainvoke(
        {"messages": [{"role": "user", "content": query}]},
        config=config,
    )
    messages = result.get("messages", [])
    if messages:
        last = messages[-1]
        return last.content if hasattr(last, "content") else str(last)
    return str(result)
