import json
from collections.abc import AsyncIterator

import httpx

from backend.models.message import Message

from .base import LLMResponse, LLMUsage


class OllamaProvider:
    """Local LLM provider via Ollama's REST API."""

    def __init__(self, base_url: str, model: str) -> None:
        self._model = model
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=5.0),
        )

    async def complete(
        self,
        messages: list[Message],
        *,
        system_prompt: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> LLMResponse:
        payload: dict = {
            "model": self._model,
            "messages": [m.to_api_dict() for m in messages],
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        if system_prompt:
            payload["system"] = system_prompt

        response = await self._client.post("/api/chat", json=payload)
        response.raise_for_status()
        data = response.json()

        return LLMResponse(
            content=data["message"]["content"],
            model=self._model,
            usage=LLMUsage(
                input_tokens=data.get("prompt_eval_count", 0),
                output_tokens=data.get("eval_count", 0),
            ),
        )

    async def stream(
        self,
        messages: list[Message],
        *,
        system_prompt: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        payload: dict = {
            "model": self._model,
            "messages": [m.to_api_dict() for m in messages],
            "stream": True,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        if system_prompt:
            payload["system"] = system_prompt

        async with self._client.stream("POST", "/api/chat", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line:
                    chunk = json.loads(line)
                    if not chunk.get("done"):
                        yield chunk["message"]["content"]

    async def aclose(self) -> None:
        await self._client.aclose()
