from agent.weather_agent import weather_agent_facade
from langchain.agents import create_agent
from prompt.prompt import MAIN_SYS_PROMPT
from agent.base import create_model


agent = create_agent(
    model=create_model(),
    tools=[weather_agent_facade],
    system_prompt=MAIN_SYS_PROMPT,
    name="main-agent",
)

def run(query: str):
    for chunk in agent.stream({"messages": [{"role": "user", "content": query}]}):
        print(f"[Main Agent] Chunk: {chunk}")
