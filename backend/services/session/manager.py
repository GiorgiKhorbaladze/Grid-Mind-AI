from uuid import UUID

from backend.models.message import Message, Role
from backend.models.session import Session


class SessionNotFoundError(KeyError):
    pass


class SessionManager:
    """In-process session store. Thread-safe for single-process deployments.

    Replace the internal dict with a Redis or DB adapter to scale horizontally
    without changing the caller interface.
    """

    def __init__(self, max_history: int = 50) -> None:
        self._sessions: dict[UUID, Session] = {}
        self._max_history = max_history

    def create_session(self, metadata: dict[str, str] | None = None) -> Session:
        session = Session(metadata=metadata or {})
        self._sessions[session.id] = session
        return session

    def get_session(self, session_id: UUID) -> Session:
        try:
            return self._sessions[session_id]
        except KeyError:
            raise SessionNotFoundError(f"Session {session_id} not found") from None

    def add_message(self, session_id: UUID, role: Role, content: str) -> Message:
        session = self.get_session(session_id)
        message = Message(role=role, content=content)
        session.add_message(message)
        self._enforce_history_limit(session)
        return message

    def delete_session(self, session_id: UUID) -> None:
        self._sessions.pop(session_id, None)

    def list_sessions(self) -> list[UUID]:
        return list(self._sessions)

    def session_exists(self, session_id: UUID) -> bool:
        return session_id in self._sessions

    def _enforce_history_limit(self, session: Session) -> None:
        if len(session.messages) > self._max_history:
            session.messages = session.messages[-self._max_history :]
