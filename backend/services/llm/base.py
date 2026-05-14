from collections.abc import AsyncIterator
from typing import Protocol, TypedDict, runtime_checkable

from backend.models.message import Message


class LLMUsage(TypedDict):
    input_tokens: int
    output_tokens: int


class LLMResponse(TypedDict):
    content: str
    model: str
    usage: LLMUsage


@runtime_checkable
class LLMProviderProtocol(Protocol):
    """Structural interface every LLM backend must satisfy."""

    async def complete(
        self,
        messages: list[Message],
        *,
        system_prompt: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> LLMResponse: ...

    def stream(
        self,
        messages: list[Message],
        *,
        system_prompt: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]: ...
