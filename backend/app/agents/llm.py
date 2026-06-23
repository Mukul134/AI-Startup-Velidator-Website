import os
import logging
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings

logger = logging.getLogger("uvicorn.error")

def get_llm(temperature: float = 0.1):
    """
    Centrally returns the appropriate LangChain ChatModel based on configured keys.
    Provider order is configurable, with a practical fallback to the next available provider.
    """
    gemini_key = (
        getattr(settings, "GEMINI_API_KEY", None)
        or getattr(settings, "GOOGLE_API_KEY", None)
        or os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
    )
    openai_key = getattr(settings, "OPENAI_API_KEY", None) or os.environ.get("OPENAI_API_KEY")
    preferred_provider = (getattr(settings, "LLM_PROVIDER", "gemini") or "gemini").lower()
    gemini_model = getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash") or "gemini-2.5-flash"
    openai_model = getattr(settings, "OPENAI_MODEL", "gpt-4o") or "gpt-4o"

    provider_order = ["gemini", "openai"] if preferred_provider == "gemini" else ["openai", "gemini"]

    for provider in provider_order:
        if provider == "gemini" and gemini_key:
            logger.info(f"Initializing LLM client: Gemini ({gemini_model})")
            return ChatGoogleGenerativeAI(
                model=gemini_model,
                temperature=temperature,
                google_api_key=gemini_key
            )

        if provider == "openai" and openai_key:
            logger.info(f"Initializing LLM client: OpenAI ({openai_model})")
            return ChatOpenAI(
                model=openai_model,
                temperature=temperature,
                openai_api_key=openai_key
            )

    logger.warning("No usable LLM API keys found. Workflow will trigger mock behaviors.")
    return None
