"""Parquet-backed file cache with TTL support.

Layout under *cache_dir/namespace/*:
  <sha256_prefix>.parquet   — serialized DataFrame
  <sha256_prefix>.meta.json — {"created_at": float, "rows": int, "key": str}
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Optional

import pandas as pd

from data_sources.config import CACHE_DIR

logger = logging.getLogger(__name__)


class FileCache:
    """Persistent file cache that stores DataFrames as Parquet files.

    Parameters
    ----------
    namespace:
        Sub-directory name isolating one data source from others.
    ttl_seconds:
        Maximum age (seconds) before a cached entry is considered stale.
    cache_dir:
        Root cache directory; defaults to ``~/.cache/gridmind``.
    """

    def __init__(
        self,
        namespace: str,
        ttl_seconds: int = 3_600,
        cache_dir: Path = CACHE_DIR,
    ) -> None:
        self.namespace = namespace
        self.ttl = ttl_seconds
        self.cache_dir = Path(cache_dir) / namespace
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, key: str) -> Optional[pd.DataFrame]:
        """Return the cached DataFrame for *key*, or ``None`` if missing/stale."""
        meta_path, data_path = self._paths(key)
        if not meta_path.exists() or not data_path.exists():
            return None
        try:
            meta = self._read_meta(meta_path)
            age = time.time() - meta["created_at"]
            if age > self.ttl:
                logger.debug("Cache stale (%.0fs > %ss) for %s", age, self.ttl, self._short(key))
                return None
            df = pd.read_parquet(data_path)
            logger.debug("Cache hit (%d rows, %.0fs old) for %s", len(df), age, self._short(key))
            return df
        except Exception as exc:
            logger.warning("Cache read error for %s: %s", self._short(key), exc)
            return None

    def set(self, key: str, df: pd.DataFrame) -> None:
        """Write *df* to the cache under *key*."""
        if df is None or df.empty:
            return
        meta_path, data_path = self._paths(key)
        try:
            df.to_parquet(data_path, index=False, engine="pyarrow")
            self._write_meta(meta_path, rows=len(df), key=key)
            logger.debug("Cached %d rows for %s", len(df), self._short(key))
        except Exception as exc:
            logger.warning("Cache write error for %s: %s", self._short(key), exc)

    def invalidate(self, key: str) -> None:
        """Remove a single cached entry."""
        for path in self._paths(key):
            path.unlink(missing_ok=True)

    def clear(self) -> None:
        """Delete all entries in this namespace."""
        removed = 0
        for f in self.cache_dir.glob("*"):
            f.unlink(missing_ok=True)
            removed += 1
        logger.info("Cleared %d cache files in namespace '%s'", removed, self.namespace)

    def cache_key(self, *parts: str) -> str:
        """Build a stable cache key from arbitrary string parts."""
        raw = "|".join(str(p) for p in parts)
        return hashlib.sha256(raw.encode()).hexdigest()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _paths(self, key: str) -> tuple[Path, Path]:
        h = hashlib.sha256(key.encode()).hexdigest()[:24]
        return (
            self.cache_dir / f"{h}.meta.json",
            self.cache_dir / f"{h}.parquet",
        )

    @staticmethod
    def _read_meta(path: Path) -> dict:
        with open(path) as f:
            return json.load(f)

    @staticmethod
    def _write_meta(path: Path, rows: int, key: str) -> None:
        with open(path, "w") as f:
            json.dump({"created_at": time.time(), "rows": rows, "key_preview": key[:60]}, f)

    @staticmethod
    def _short(key: str) -> str:
        return key[:50] + "…" if len(key) > 50 else key
