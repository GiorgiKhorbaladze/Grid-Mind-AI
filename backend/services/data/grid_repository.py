from backend.models.grid import GridSnapshot


class InMemoryGridRepository:
    """In-memory GridSnapshot store.

    Satisfies the DataRepository[GridSnapshot] protocol without inheriting from it,
    keeping the class decoupled from the interface definition. Swap for a
    time-series DB adapter (InfluxDB, TimescaleDB) without changing callers.
    """

    def __init__(self) -> None:
        self._store: dict[str, GridSnapshot] = {}

    async def get(self, snapshot_id: str) -> GridSnapshot | None:
        return self._store.get(snapshot_id)

    async def list(self, limit: int = 100, offset: int = 0) -> list[GridSnapshot]:
        sorted_snapshots = sorted(
            self._store.values(),
            key=lambda s: s.timestamp,
            reverse=True,
        )
        return sorted_snapshots[offset : offset + limit]

    async def save(self, snapshot: GridSnapshot) -> GridSnapshot:
        self._store[snapshot.snapshot_id] = snapshot
        return snapshot

    async def delete(self, snapshot_id: str) -> bool:
        return self._store.pop(snapshot_id, None) is not None

    async def get_latest(self) -> GridSnapshot | None:
        if not self._store:
            return None
        return max(self._store.values(), key=lambda s: s.timestamp)

    async def count(self) -> int:
        return len(self._store)
