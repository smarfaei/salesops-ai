from app.ai.providers.base import AIProvider
from app.ai.providers.local import LocalAIProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.core.config import Settings


def create_ai_provider(settings: Settings) -> AIProvider:
    if settings.ai_provider == "local":
        return LocalAIProvider()
    api_key = settings.openai_api_key.get_secret_value() if settings.openai_api_key else None
    return OpenAIProvider(
        api_key=api_key,
        model=settings.openai_model,
        timeout_seconds=settings.openai_timeout_seconds,
    )
