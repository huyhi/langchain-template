import os
from langchain_openai import ChatOpenAI

def create_model() -> ChatOpenAI:
    """Return a ChatOpenAI instance pointed at the company's self-hosted LLM."""
    base_url = os.environ["LLM_BASE_URL"]
    api_key = os.environ["LLM_API_KEY"]
    model_name = os.getenv("LLM_MODEL", "default")

    return ChatOpenAI(
        base_url=base_url,
        api_key=api_key,
        model=model_name,
    )
