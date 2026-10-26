from functools import lru_cache

from src.core.config import get_settings
from src.integrations.llm.gemini import GeminiClient
from src.integrations.llm.types import (
    Completed,
    LLMClient,
    LLMError,
    LLMEvent,
    LLMMessage,
    LLMQuotaExhaustedError,
    LLMUnavailableError,
    Notice,
    TextDelta,
    ToolCall,
    ToolResult,
    ToolSpec,
    TurnComplete,
)


def assert_llm_provider_allowed() -> None:
    """Fake mode is for tests and local demos. Production must call a real provider."""
    settings = get_settings()
    if settings.app_env == "production" and settings.llm_provider == "fake":
        raise RuntimeError("LLM_PROVIDER=fake cannot be used when APP_ENV=production")


@lru_cache
def get_llm_client() -> LLMClient | None:
    """Process-wide client. None when Gemini is selected and no API key is configured."""
    settings = get_settings()
    assert_llm_provider_allowed()
    if settings.llm_provider == "fake":
        from src.integrations.llm.fake import ScriptedLLMClient

        return ScriptedLLMClient.from_path(settings.llm_fake_script_path)
    if not settings.gemini_api_key:
        return None
    return GeminiClient(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        fallback_models=settings.gemini_fallback_model_list,
        first_chunk_timeout_seconds=settings.gemini_first_chunk_timeout_seconds,
        request_timeout_seconds=settings.gemini_request_timeout_seconds,
        max_retries=settings.gemini_max_retries,
        temperature=settings.gemini_temperature,
    )


__all__ = [
    "Completed",
    "LLMClient",
    "LLMError",
    "LLMEvent",
    "LLMMessage",
    "LLMQuotaExhaustedError",
    "LLMUnavailableError",
    "Notice",
    "TextDelta",
    "ToolCall",
    "ToolResult",
    "ToolSpec",
    "TurnComplete",
    "assert_llm_provider_allowed",
    "get_llm_client",
]
