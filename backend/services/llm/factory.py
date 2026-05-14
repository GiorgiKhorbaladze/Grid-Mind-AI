from config.settings import LLMProvider, Settings

from .anthropic_provider import AnthropicProvider
from .base import LLMProviderProtocol
from .ollama_provider import OllamaProvider


def create_llm_provider(settings: Settings) -> LLMProviderProtocol:
    """Instantiate the configured LLM provider from application settings."""
    match settings.llm_provider:
        case LLMProvider.ANTHROPIC:
            return AnthropicProvider(
                api_key=settings.anthropic_api_key.get_secret_value(),
                model=settings.anthropic_model,
            )
        case LLMProvider.OLLAMA:
            return OllamaProvider(
                base_url=settings.ollama_base_url,
                model=settings.ollama_model,
            )
        case _:
            raise ValueError(f"Unsupported LLM provider: {settings.llm_provider!r}")
