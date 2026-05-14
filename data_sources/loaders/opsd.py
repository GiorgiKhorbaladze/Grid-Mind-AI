"""Open Power System Data (OPSD) loader.

Downloads the 60-minute time-series package, streams it to the local cache,
then filters by region and date range.

Source: https://open-power-system-data.org/
Dataset: Time Series (60-min singleindex)
License: CC BY 4.0 — free, no API key required.
"""
from __future__ import annotations

import logging
import tempfile
from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd

from data_sources.cache.file_cache import FileCache
from data_sources.config import (
    CACHE_TTL,
    FUEL_TYPE_COL,
    OPSD_CHUNK_SIZE,
    OPSD_DATAPACKAGE_URL,
    OPSD_FALLBACK_CSV_URL,
    OPSD_UTC_COLUMN,
    REGION_COL,
    SOURCE_COL,
    TIMESTAMP_COL,
    UNIT_COL,
    VALUE_COL,
)
from data_sources.loaders.base import BaseLoader
from data_sources.schemas.models import validate_dataframe
from data_sources.utils.timezone import normalize_series_to_utc

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Column mapping: OPSD suffix → normalized fuel_type and unit
# ---------------------------------------------------------------------------
_OPSD_COLUMN_MAP: dict[str, tuple[str, str]] = {
    "load_actual_entsoe_transparency": ("demand", "MW"),
    "load_actual_entsoe_power_statistics": ("demand", "MW"),
    "solar_generation_actual": ("solar", "MW"),
    "wind_generation_actual": ("wind", "MW"),
    "wind_onshore_generation_actual": ("wind_onshore", "MW"),
    "wind_offshore_generation_actual": ("wind_offshore", "MW"),
    "nuclear_generation_actual": ("nuclear", "MW"),
    "coal_generation_actual": ("coal", "MW"),
    "lignite_generation_actual": ("lignite", "MW"),
    "gas_generation_actual": ("gas", "MW"),
    "hydro_generation_actual": ("hydro", "MW"),
    "biomass_generation_actual": ("biomass", "MW"),
    "other_renewable_generation_actual": ("other_renewable", "MW"),
    "other_conventional_generation_actual": ("other", "MW"),
}


class OPSDLoader(BaseLoader):
    """Loader for Open Power System Data hourly time series.

    The full OPSD dataset is a wide CSV (all countries combined).  On first
    use the raw file is streamed to ``<cache_dir>/opsd/raw/`` and filtered
    per-country results are stored separately so subsequent calls are fast.

    Parameters
    ----------
    cache_dir:
        Override the default cache root.
    """

    source_name = "opsd"

    def __init__(self, cache_dir: Optional[Path] = None, **kwargs) -> None:
        super().__init__(**kwargs)
        cache_kwargs = {"cache_dir": cache_dir} if cache_dir else {}
        self._cache = FileCache("opsd", ttl_seconds=CACHE_TTL["opsd"], **cache_kwargs)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def fetch(
        self,
        region: str,
        start: date,
        end: date,
        *,
        use_cache: bool = True,
    ) -> pd.DataFrame:
        """Return hourly generation/demand data for *region* in [*start*, *end*].

        Parameters
        ----------
        region:
            ISO-2 country code (e.g. ``"DE"``, ``"FR"``, ``"GB"``).
        start / end:
            Inclusive date range; time is expanded to full days in UTC.
        use_cache:
            Serve from disk cache when available.
        """
        region = region.upper()
        cache_key = self._cache.cache_key(region, str(start), str(end))

        if use_cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        logger.info("Fetching OPSD data for region=%s %s → %s", region, start, end)
        df = self._download_and_filter(region, start, end)
        if use_cache:
            self._cache.set(cache_key, df)
        return df

    # ------------------------------------------------------------------
    # Internal: download → filter → normalize
    # ------------------------------------------------------------------

    def _download_and_filter(
        self,
        region: str,
        start: date,
        end: date,
    ) -> pd.DataFrame:
        """Download the full OPSD CSV, filter, and return a normalized DataFrame."""
        csv_url = self._resolve_csv_url()
        raw_path = self._raw_cache_path()

        if not raw_path.exists():
            logger.info("Streaming OPSD raw CSV from %s", csv_url)
            self._get_streaming(csv_url, raw_path)
        else:
            logger.debug("Using existing raw OPSD file at %s", raw_path)

        return self._parse_raw(raw_path, region, start, end)

    def _resolve_csv_url(self) -> str:
        """Resolve the latest OPSD CSV URL via the datapackage metadata JSON."""
        try:
            pkg = self._get_json(OPSD_DATAPACKAGE_URL)
            for resource in pkg.get("resources", []):
                name = resource.get("name", "")
                media = resource.get("mediatype", "")
                path = resource.get("path", "")
                if "singleindex" in name and "60min" in name and "csv" in media:
                    if path.startswith("http"):
                        return path
                    # Relative path — prepend base URL
                    base = OPSD_DATAPACKAGE_URL.rsplit("/", 1)[0]
                    return f"{base}/{path}"
        except Exception as exc:
            logger.warning("Could not resolve OPSD metadata URL: %s — using fallback", exc)
        return OPSD_FALLBACK_CSV_URL

    def _raw_cache_path(self) -> Path:
        raw_dir = self._cache.cache_dir / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        return raw_dir / "time_series_60min_singleindex.csv"

    def _parse_raw(
        self, raw_path: Path, region: str, start: date, end: date
    ) -> pd.DataFrame:
        """Read the large raw CSV in chunks, filter to *region* and date range."""
        region_cols = self._discover_region_columns(raw_path, region)
        if not region_cols:
            logger.warning("No OPSD columns found for region '%s'", region)
            from data_sources.schemas.models import _empty_normalized_frame
            return _empty_normalized_frame()

        usecols = [OPSD_UTC_COLUMN] + region_cols
        logger.debug("Reading OPSD columns: %s", usecols)

        chunks: list[pd.DataFrame] = []
        start_dt = pd.Timestamp(start, tz="UTC")
        end_dt = pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)

        for chunk in pd.read_csv(
            raw_path,
            usecols=lambda c: c in usecols,
            parse_dates=[OPSD_UTC_COLUMN],
            chunksize=OPSD_CHUNK_SIZE,
            low_memory=False,
        ):
            chunk[OPSD_UTC_COLUMN] = normalize_series_to_utc(chunk[OPSD_UTC_COLUMN])
            mask = (chunk[OPSD_UTC_COLUMN] >= start_dt) & (chunk[OPSD_UTC_COLUMN] < end_dt)
            sliced = chunk.loc[mask]
            if not sliced.empty:
                chunks.append(sliced)

        if not chunks:
            from data_sources.schemas.models import _empty_normalized_frame
            return _empty_normalized_frame()

        wide = pd.concat(chunks, ignore_index=True)
        return self._normalize(wide, region, region_cols)

    def _discover_region_columns(self, raw_path: Path, region: str) -> list[str]:
        """Read only the header row to find columns matching *region*."""
        header = pd.read_csv(raw_path, nrows=0)
        prefix = f"{region}_"
        return [c for c in header.columns if c.startswith(prefix)]

    def _normalize(
        self, wide: pd.DataFrame, region: str, region_cols: list[str]
    ) -> pd.DataFrame:
        """Melt wide OPSD DataFrame to the normalized long schema."""
        records: list[dict] = []
        prefix = f"{region}_"

        for col in region_cols:
            suffix = col[len(prefix):]
            mapping = _OPSD_COLUMN_MAP.get(suffix)
            if mapping is None:
                # Unknown suffix — include as "other" with best-guess unit
                fuel_type, unit = "other", "MW"
            else:
                fuel_type, unit = mapping

            col_data = wide[[OPSD_UTC_COLUMN, col]].rename(
                columns={col: VALUE_COL, OPSD_UTC_COLUMN: TIMESTAMP_COL}
            )
            col_data[REGION_COL] = region
            col_data[FUEL_TYPE_COL] = fuel_type
            col_data[UNIT_COL] = unit
            col_data[SOURCE_COL] = self.source_name
            records.append(col_data)

        if not records:
            from data_sources.schemas.models import _empty_normalized_frame
            return _empty_normalized_frame()

        combined = pd.concat(records, ignore_index=True)
        return validate_dataframe(combined, source=self.source_name)
