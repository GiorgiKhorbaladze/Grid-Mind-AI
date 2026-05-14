from datetime import datetime, timezone

import pytest
from backend.models.grid import GridSnapshot
from backend.services.data.grid_repository import InMemoryGridRepository


def _make_snapshot(load: float = 100.0) -> GridSnapshot:
    return GridSnapshot(
        timestamp=datetime.now(timezone.utc),
        total_load_kw=load,
        total_capacity_kw=1000.0,
    )


@pytest.mark.asyncio
async def test_save_and_get():
    repo = InMemoryGridRepository()
    snap = _make_snapshot()
    saved = await repo.save(snap)
    fetched = await repo.get(saved.snapshot_id)
    assert fetched is not None
    assert fetched.snapshot_id == snap.snapshot_id


@pytest.mark.asyncio
async def test_get_missing_returns_none():
    repo = InMemoryGridRepository()
    result = await repo.get("does-not-exist")
    assert result is None


@pytest.mark.asyncio
async def test_list_returns_ordered_descending():
    repo = InMemoryGridRepository()
    for load in [100.0, 200.0, 300.0]:
        await repo.save(_make_snapshot(load))
    snapshots = await repo.list(limit=10)
    assert len(snapshots) == 3


@pytest.mark.asyncio
async def test_delete():
    repo = InMemoryGridRepository()
    snap = await repo.save(_make_snapshot())
    deleted = await repo.delete(snap.snapshot_id)
    assert deleted is True
    assert await repo.get(snap.snapshot_id) is None


@pytest.mark.asyncio
async def test_delete_missing_returns_false():
    repo = InMemoryGridRepository()
    assert await repo.delete("ghost") is False


@pytest.mark.asyncio
async def test_get_latest():
    repo = InMemoryGridRepository()
    assert await repo.get_latest() is None
    await repo.save(_make_snapshot(50.0))
    latest = await repo.save(_make_snapshot(200.0))
    result = await repo.get_latest()
    assert result is not None


@pytest.mark.asyncio
async def test_count():
    repo = InMemoryGridRepository()
    assert await repo.count() == 0
    await repo.save(_make_snapshot())
    assert await repo.count() == 1
