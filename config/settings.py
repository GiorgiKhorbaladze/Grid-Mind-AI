from enum import StrEnum

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(StrEnum):
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM provider selection
    llm_provider: LLMProvider = LLMProvider.ANTHROPIC

    # Anthropic
    anthropic_api_key: SecretStr = Field(default=SecretStr(""))
    anthropic_model: str = "claude-sonnet-4-6"

    # Ollama (local LLM)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"

    # Shared LLM inference params
    llm_max_tokens: int = Field(default=4096, gt=0)
    llm_temperature: float = Field(default=0.7, ge=0.0, le=2.0)

    # Session management
    session_max_history: int = Field(default=50, gt=0)
    session_ttl_seconds: int = Field(default=3600, gt=0)

    # Observability
    log_level: str = "INFO"
    log_format: str = "console"  # "console" | "json"

    # Application
    app_name: str = "GridMind-AI"
    debug: bool = False


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Force re-initialisation from environment — useful in tests."""
    global _settings
    _settings = None
