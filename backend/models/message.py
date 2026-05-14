from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Role(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    role: Role
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_api_dict(self) -> dict[str, str]:
        """Serialize to the format expected by LLM provider APIs."""
        return {"role": self.role, "content": self.content}
