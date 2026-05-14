"""Ember Climate electricity generation loader.

Fetches monthly or yearly electricity generation data from the Ember
public API.  No API key is required.

Source: https://ember-climate.org/data/
API:    https://api.ember-climate.org/v1/
License: CC BY 4.0
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Optional

import pandas as pd

from data_sources.cache.file_cache import FileCache
from data_sources.config import (
    CACHE_TTL,
    EMBER_GENERATION_MONTHLY,
    EMBER_GENERATION_YEARLY,
    FUEL_TYPE_COL,
    REGION_COL,
    SOURCE_COL,
    TIMESTAMP_COL,
    UNIT_COL,
    VALUE_COL,
)
from data_sources.loaders.base import BaseLoader
from data_sources.parsers.json_parser import parse_json_records
from data_sources.schemas.models import validate_dataframe, _empty_normalized_frame
from data_sources.utils.timezone import normalize_series_to_utc

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Fuel-type normalisation: Ember series name → GridMind fuel_type
# ---------------------------------------------------------------------------
_EMBER_FUEL_MAP: dict[str, str] = {
    "Solar": "solar",
    "Wind": "wind",
    "Wind Onshore": "wind_onshore",
    "Wind Offshore": "wind_offshore",
    "Hydro": "hydro",
    "Nuclear": "nuclear",
    "Gas": "gas",
    "Coal": "coal",
    "Other Fossil": "other",
    "Other Renewables": "other_renewable",
    "Bioenergy": "biomass",
    "Demand": "demand",
    "Total Generation": "total",
    "Net Imports": "other",
}


class EmberLoader(BaseLoader):
    """Loader for Ember Climate monthly/yearly electricity generation data.

    The Ember API returns generation volumes in TWh.  Values are kept as-is
    with ``unit="TWh"``; consumers can convert to MW-equivalent if needed.

    Parameters
    ----------
    resolution:
        ``"monthly"`` (default) or ``"yearly"``.
    cache_dir:
        Override the default cache root.
    """

    source_name = "ember"

    def __init__(
        self,
        resolution: str = "monthly",
        cache_dir=None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        if resolution not in ("monthly", "yearly"):
            raise ValueError("resolution must be 'monthly' or 'yearly'")
        self.resolution = resolution
        self._endpoint = (
            EMBER_GENERATION_MONTHLY if resolution == "monthly" else EMBER_GENERATION_YEARLY
        )
        cache_kwargs = {"cache_dir": cache_dir} if cache_dir else {}
        self._cache = FileCache("ember", ttl_seconds=CACHE_TTL["ember"], **cache_kwargs)

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
        """Return Ember generation data for *region* in [*start*, *end*].

        Parameters
        ----------
        region:
            ISO-3 country code (e.g. ``"DEU"``, ``"FRA"``, ``"GBR"``).
            ISO-2 codes are auto-converted using the built-in mapping.
        start / end:
            Inclusive date range.
        """
        region = self._normalize_region(region)
        cache_key = self._cache.cache_key(
            self.source_name, self.resolution, region, str(start), str(end)
        )

        if use_cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        logger.info(
            "Fetching Ember %s data for region=%s %s → %s",
            self.resolution, region, start, end,
        )
        df = self._fetch_from_api(region, start, end)
        if use_cache and not df.empty:
            self._cache.set(cache_key, df)
        return df

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _fetch_from_api(self, region: str, start: date, end: date) -> pd.DataFrame:
        start_str, end_str = self._date_params(start, end)
        params: dict = {
            "country": region,
            "start_date": start_str,
            "end_date": end_str,
            "is_aggregate_series": "false",
        }

        try:
            data = self._get_json(self._endpoint, params=params)
        except Exception as exc:
            logger.error("Ember API request failed: %s", exc)
            return _empty_normalized_frame()

        # API may return {"data": [...]} or a bare list
        if isinstance(data, dict) and "data" in data:
            records_raw = data["data"]
        elif isinstance(data, list):
            records_raw = data
        else:
            logger.warning("Unexpected Ember API response shape: %s", type(data))
            return _empty_normalized_frame()

        if not records_raw:
            logger.info("Ember API returned 0 records for %s", region)
            return _empty_normalized_frame()

        raw_df = parse_json_records(records_raw)
        return self._normalize(raw_df, region)

    def _normalize(self, raw: pd.DataFrame, region: str) -> pd.DataFrame:
        """Map Ember API columns to the normalized schema."""
        # Expected Ember API columns: date, country_code, series, generation_twh
        date_col = self._find_col(raw, ("date", "month", "year", "period"))
        series_col = self._find_col(raw, ("series", "fuel", "fuel_type", "variable"))
        value_col = self._find_col(raw, ("generation_twh", "value", "generation", "demand_twh"))

        if date_col is None or series_col is None or value_col is None:
            logger.warning(
                "Ember response columns not recognized: %s",
                list(raw.columns),
            )
            return _empty_normalized_frame()

        out = pd.DataFrame()
        out[TIMESTAMP_COL] = normalize_series_to_utc(
            pd.to_datetime(raw[date_col], errors="coerce")
        )
        out[REGION_COL] = region
        out[FUEL_TYPE_COL] = raw[series_col].map(
            lambda s: _EMBER_FUEL_MAP.get(str(s), str(s).lower().replace(" ", "_"))
        )
        out[VALUE_COL] = pd.to_numeric(raw[value_col], errors="coerce")
        out[UNIT_COL] = "TWh"
        out[SOURCE_COL] = self.source_name

        return validate_dataframe(out, source=self.source_name)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _date_params(self, start: date, end: date) -> tuple[str, str]:
        """Return (start_str, end_str) formatted for the Ember API."""
        if self.resolution == "monthly":
            return start.strftime("%Y-%m"), end.strftime("%Y-%m")
        return str(start.year), str(end.year)

    @staticmethod
    def _normalize_region(region: str) -> str:
        """Convert ISO-2 to ISO-3 if needed; pass ISO-3 through unchanged."""
        _ISO2_TO_ISO3 = {
            "DE": "DEU", "FR": "FRA", "GB": "GBR", "ES": "ESP",
            "IT": "ITA", "PL": "POL", "NL": "NLD", "BE": "BEL",
            "AT": "AUT", "CH": "CHE", "DK": "DNK", "SE": "SWE",
            "NO": "NOR", "FI": "FIN", "CZ": "CZE", "HU": "HUN",
            "RO": "ROU", "US": "USA", "AU": "AUS", "JP": "JPN",
            "CN": "CHN", "IN": "IND", "BR": "BRA", "ZA": "ZAF",
        }
        upper = region.upper()
        return _ISO2_TO_ISO3.get(upper, upper)

    @staticmethod
    def _find_col(df: pd.DataFrame, candidates: tuple[str, ...]) -> Optional[str]:
        """Return the first column in *candidates* that exists in *df*, or None."""
        for c in candidates:
            if c in df.columns:
                return c
        return None
