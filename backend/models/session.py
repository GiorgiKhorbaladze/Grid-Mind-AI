from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from .message import Message


class Session(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    messages: list[Message] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def add_message(self, message: Message) -> None:
        self.messages.append(message)
        self.updated_at = datetime.now(timezone.utc)

    def get_history(self, max_messages: int | None = None) -> list[Message]:
        if max_messages is None:
            return list(self.messages)
        return list(self.messages[-max_messages:])

    @property
    def message_count(self) -> int:
        return len(self.messages)
