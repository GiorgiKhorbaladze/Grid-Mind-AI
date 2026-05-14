from collections.abc import AsyncIterator
from uuid import UUID

from config.settings import get_settings
from backend.models.message import Role
from backend.models.session import Session
from backend.services.llm.base import LLMProviderProtocol, LLMResponse
from backend.services.llm.factory import create_llm_provider
from backend.services.session.manager import SessionManager
from backend.utils.logging import get_logger

logger = get_logger(__name__)

_DEFAULT_SYSTEM_PROMPT = (
    "You are GridMind, an AI assistant specialized in smart grid management and energy "
    "systems analysis. You provide clear, accurate, and actionable insights about grid "
    "operations, load distribution, fault detection, and system monitoring. Always be "
    "precise with numerical data and treat safety-critical information with care."
)


class ChatEngine:
    """Orchestrates conversation flow between the user, session state, and the LLM.

    The engine is deliberately UI-agnostic: callers receive plain strings or async
    generators of strings, and pass back plain strings. All persistence and inference
    concerns are delegated to injected services.
    """

    def __init__(
        self,
        llm_provider: LLMProviderProtocol | None = None,
        session_manager: SessionManager | None = None,
        system_prompt: str = _DEFAULT_SYSTEM_PROMPT,
    ) -> None:
        settings = get_settings()
        self._llm = llm_provider or create_llm_provider(settings)
        self._sessions = session_manager or SessionManager(
            max_history=settings.session_max_history
        )
        self._system_prompt = system_prompt
        self._settings = settings

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    def create_session(self, metadata: dict[str, str] | None = None) -> Session:
        session = self._sessions.create_session(metadata)
        logger.debug("Session created: %s", session.id)
        return session

    def get_session(self, session_id: UUID) -> Session:
        return self._sessions.get_session(session_id)

    def delete_session(self, session_id: UUID) -> None:
        self._sessions.delete_session(session_id)
        logger.debug("Session deleted: %s", session_id)

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    async def chat(self, session_id: UUID, user_message: str) -> str:
        """Send a message and return the assistant's full reply."""
        self._sessions.add_message(session_id, Role.USER, user_message)
        history = self._sessions.get_session(session_id).get_history(
            max_messages=self._settings.session_max_history
        )

        response: LLMResponse = await self._llm.complete(
            history,
            system_prompt=self._system_prompt,
            max_tokens=self._settings.llm_max_tokens,
            temperature=self._settings.llm_temperature,
        )

        assistant_reply = response["content"]
        self._sessions.add_message(session_id, Role.ASSISTANT, assistant_reply)

        logger.info(
            "chat_complete session=%s in=%d out=%d",
            session_id,
            response["usage"]["input_tokens"],
            response["usage"]["output_tokens"],
        )
        return assistant_reply

    async def stream_chat(
        self, session_id: UUID, user_message: str
    ) -> AsyncIterator[str]:
        """Send a message and stream the assistant's reply token-by-token."""
        self._sessions.add_message(session_id, Role.USER, user_message)
        history = self._sessions.get_session(session_id).get_history(
            max_messages=self._settings.session_max_history
        )

        chunks: list[str] = []
        async for chunk in self._llm.stream(
            history,
            system_prompt=self._system_prompt,
            max_tokens=self._settings.llm_max_tokens,
            temperature=self._settings.llm_temperature,
        ):
            chunks.append(chunk)
            yield chunk

        self._sessions.add_message(
            session_id, Role.ASSISTANT, "".join(chunks)
        )
