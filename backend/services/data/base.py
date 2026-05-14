from typing import Protocol, TypeVar

T = TypeVar("T")


class DataRepository(Protocol[T]):
    """Generic async repository interface — implement this for any persistence backend."""

    async def get(self, entity_id: str) -> T | None: ...

    async def list(self, limit: int = 100, offset: int = 0) -> list[T]: ...

    async def save(self, entity: T) -> T: ...

    async def delete(self, entity_id: str) -> bool: ...
