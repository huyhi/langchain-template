from langchain.agents import create_agent
from langchain.tools import tool
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
def weather_agent_facade(query: str):
    result = weather_agent.stream({"messages": [{"role": "user", "content": query}]})
    for chunk in result:
        print(f"[Weather Agent] Chunk: {chunk}")
        yield chunk
