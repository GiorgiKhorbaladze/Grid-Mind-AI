from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field


class GridStatus(StrEnum):
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    OFFLINE = "offline"


class GridNode(BaseModel):
    node_id: str
    name: str
    status: GridStatus = GridStatus.NORMAL
    load_kw: float = Field(default=0.0, ge=0.0)
    capacity_kw: float = Field(default=0.0, ge=0.0)
    metadata: dict[str, str] = Field(default_factory=dict)

    @computed_field  # type: ignore[misc]
    @property
    def load_factor(self) -> float:
        if self.capacity_kw == 0:
            return 0.0
        return round(self.load_kw / self.capacity_kw, 4)

    @computed_field  # type: ignore[misc]
    @property
    def is_overloaded(self) -> bool:
        return self.load_factor > 1.0


class GridSnapshot(BaseModel):
    snapshot_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime
    nodes: list[GridNode] = Field(default_factory=list)
    total_load_kw: float = Field(default=0.0, ge=0.0)
    total_capacity_kw: float = Field(default=0.0, ge=0.0)
    metadata: dict[str, str] = Field(default_factory=dict)

    @computed_field  # type: ignore[misc]
    @property
    def system_load_factor(self) -> float:
        if self.total_capacity_kw == 0:
            return 0.0
        return round(self.total_load_kw / self.total_capacity_kw, 4)

    @computed_field  # type: ignore[misc]
    @property
    def critical_nodes(self) -> list[str]:
        return [n.node_id for n in self.nodes if n.status == GridStatus.CRITICAL]
