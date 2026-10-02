from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import get_settings


def configured_llm() -> ChatGoogleGenerativeAI:
    settings = get_settings()
    return ChatGoogleGenerativeAI(
        model=settings.llm_model_name,
        google_api_key=settings.llm_api_key,
        temperature=settings.llm_temperature,
        max_output_tokens=settings.llm_max_tokens,
        timeout=settings.llm_request_timeout,
        max_retries=settings.llm_max_retries,
    )
