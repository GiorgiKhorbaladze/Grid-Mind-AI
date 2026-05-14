"""Tests for ChatEngine using a fake LLM provider (no network calls)."""
from collections.abc import AsyncIterator
from unittest.mock import patch

import pytest

from app.chat_engine import ChatEngine
from backend.services.llm.base import LLMResponse, LLMUsage
from backend.models.message import Role


class FakeLLMProvider:
    """Deterministic stub that echoes the last user message back."""

    def __init__(self, reply: str = "fake reply") -> None:
        self._reply = reply

    async def complete(
        self,
        messages,
        *,
        system_prompt=None,
        max_tokens=4096,
        temperature=0.7,
    ) -> LLMResponse:
        return LLMResponse(
            content=self._reply,
            model="fake-model",
            usage=LLMUsage(input_tokens=10, output_tokens=5),
        )

    async def stream(
        self,
        messages,
        *,
        system_prompt=None,
        max_tokens=4096,
        temperature=0.7,
    ) -> AsyncIterator[str]:
        for char in self._reply:
            yield char


@pytest.mark.asyncio
async def test_chat_returns_reply():
    engine = ChatEngine(llm_provider=FakeLLMProvider("hello world"))
    session = engine.create_session()
    reply = await engine.chat(session.id, "test input")
    assert reply == "hello world"


@pytest.mark.asyncio
async def test_chat_records_history():
    engine = ChatEngine(llm_provider=FakeLLMProvider("response"))
    session = engine.create_session()
    await engine.chat(session.id, "user msg")
    s = engine.get_session(session.id)
    assert s.messages[0].role == Role.USER
    assert s.messages[1].role == Role.ASSISTANT
    assert s.messages[1].content == "response"


@pytest.mark.asyncio
async def test_stream_chat_yields_chunks():
    engine = ChatEngine(llm_provider=FakeLLMProvider("abc"))
    session = engine.create_session()
    chunks = [c async for c in engine.stream_chat(session.id, "hi")]
    assert "".join(chunks) == "abc"


@pytest.mark.asyncio
async def test_stream_chat_records_full_reply():
    engine = ChatEngine(llm_provider=FakeLLMProvider("xyz"))
    session = engine.create_session()
    async for _ in engine.stream_chat(session.id, "q"):
        pass
    s = engine.get_session(session.id)
    assert s.messages[-1].content == "xyz"


def test_delete_session():
    engine = ChatEngine(llm_provider=FakeLLMProvider())
    session = engine.create_session()
    engine.delete_session(session.id)
    from backend.services.session.manager import SessionNotFoundError
    with pytest.raises(SessionNotFoundError):
        engine.get_session(session.id)
