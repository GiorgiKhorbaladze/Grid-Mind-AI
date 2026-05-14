from datetime import datetime, timezone

import pytest
from backend.models.grid import GridNode, GridSnapshot, GridStatus


def test_load_factor_zero_capacity():
    node = GridNode(node_id="n1", name="Node 1", capacity_kw=0.0, load_kw=100.0)
    assert node.load_factor == 0.0


def test_load_factor_normal():
    node = GridNode(node_id="n1", name="Node 1", capacity_kw=200.0, load_kw=100.0)
    assert node.load_factor == 0.5


def test_is_overloaded():
    node = GridNode(node_id="n1", name="Node 1", capacity_kw=100.0, load_kw=150.0)
    assert node.is_overloaded is True


def test_not_overloaded():
    node = GridNode(node_id="n1", name="Node 1", capacity_kw=100.0, load_kw=80.0)
    assert node.is_overloaded is False


def test_snapshot_critical_nodes():
    now = datetime.now(timezone.utc)
    nodes = [
        GridNode(node_id="n1", name="A", status=GridStatus.NORMAL),
        GridNode(node_id="n2", name="B", status=GridStatus.CRITICAL),
        GridNode(node_id="n3", name="C", status=GridStatus.CRITICAL),
    ]
    snap = GridSnapshot(timestamp=now, nodes=nodes)
    assert snap.critical_nodes == ["n2", "n3"]


def test_snapshot_system_load_factor():
    now = datetime.now(timezone.utc)
    snap = GridSnapshot(
        timestamp=now,
        total_load_kw=750.0,
        total_capacity_kw=1000.0,
    )
    assert snap.system_load_factor == 0.75
