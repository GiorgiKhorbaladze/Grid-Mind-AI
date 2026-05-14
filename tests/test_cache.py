"""Tests for data_sources.cache.file_cache."""
from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import pytest

from data_sources.cache.file_cache import FileCache
from data_sources.config import TIMESTAMP_COL, VALUE_COL, REGION_COL, FUEL_TYPE_COL, UNIT_COL, SOURCE_COL


def _make_df(n: int = 5) -> pd.DataFrame:
    return pd.DataFrame(
        {
            TIMESTAMP_COL: pd.to_datetime(
                [f"2023-01-01 {h:02d}:00" for h in range(n)], utc=True
            ),
            REGION_COL: ["DE"] * n,
            FUEL_TYPE_COL: ["solar"] * n,
            VALUE_COL: [float(i * 10) for i in range(n)],
            UNIT_COL: ["MW"] * n,
            SOURCE_COL: ["test"] * n,
        }
    )


class TestFileCache:
    def test_miss_on_empty_cache(self, tmp_cache):
        cache = FileCache("test", ttl_seconds=3600, cache_dir=tmp_cache)
        assert cache.get("nonexistent_key") is None

    def test_set_then_get_returns_same_data(self, tmp_cache):
        cache = FileCache("test", ttl_seconds=3600, cache_dir=tmp_cache)
        df = _make_df(3)
        key = cache.cache_key("region", "2023-01-01", "2023-01-31")
        cache.set(key, df)
        result = cache.get(key)
        assert result is not None
        assert len(result) == 3
        assert list(result.columns) == list(df.columns)

    def test_stale_entry_returns_none(self, tmp_cache):
        cache = FileCache("test", ttl_seconds=1, cache_dir=tmp_cache)
        df = _make_df(2)
        key = "stale_key"
        cache.set(key, df)
        time.sleep(1.1)
        assert cache.get(key) is None

    def test_fresh_entry_within_ttl(self, tmp_cache):
        cache = FileCache("test", ttl_seconds=60, cache_dir=tmp_cache)
        df = _make_df(2)
        key = "fresh_key"
        cache.set(key, df)
        result = cache.get(key)
        assert result is not None

    def test_invalidate_removes_entry(self, tmp_cache):
        cache = FileCache("test", ttl_seconds=3600, cache_dir=tmp_cache)
        df = _make_df()
        key = "to_invalidate"
        cache.set(key, df)
        cache.invalidate(key)
        assert cache.get(key) is None

    def test_clear_removes_all_entries(self, tmp_cache):
        cache = FileCache("test", ttl_seconds=3600, cache_dir=tmp_cache)
        df = _make_df()
        for i in range(3):
            cache.set(f"key_{i}", df)
        cache.clear()
        for i in range(3):
            assert cache.get(f"key_{i}") is None

    def test_different_namespaces_isolated(self, tmp_cache):
        cache_a = FileCache("ns_a", ttl_seconds=3600, cache_dir=tmp_cache)
        cache_b = FileCache("ns_b", ttl_seconds=3600, cache_dir=tmp_cache)
        df = _make_df()
        key = cache_a.cache_key("same", "key")
        cache_a.set(key, df)
        # Same logical key, different namespace — must not collide
        assert cache_b.get(key) is None

    def test_cache_key_is_deterministic(self, tmp_cache):
        cache = FileCache("test", cache_dir=tmp_cache)
        k1 = cache.cache_key("DE", "2023-01-01", "2023-01-31")
        k2 = cache.cache_key("DE", "2023-01-01", "2023-01-31")
        assert k1 == k2

    def test_cache_key_differs_for_different_inputs(self, tmp_cache):
        cache = FileCache("test", cache_dir=tmp_cache)
        k1 = cache.cache_key("DE", "2023-01-01", "2023-01-31")
        k2 = cache.cache_key("FR", "2023-01-01", "2023-01-31")
        assert k1 != k2

    def test_set_empty_df_is_no_op(self, tmp_cache):
        cache = FileCache("test", ttl_seconds=3600, cache_dir=tmp_cache)
        cache.set("empty_key", pd.DataFrame())
        assert cache.get("empty_key") is None

    def test_cache_dir_created_automatically(self, tmp_path):
        deep_path = tmp_path / "a" / "b" / "c"
        assert not deep_path.exists()
        cache = FileCache("ns", cache_dir=deep_path)
        assert (deep_path / "ns").exists()
