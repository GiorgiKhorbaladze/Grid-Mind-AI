"""Open-Meteo weather loader.

Fetches hourly meteorological variables relevant for grid operations
(temperature, solar radiation, wind speed/direction, precipitation,
cloud cover) from the free Open-Meteo API.

No API key required.

Source:  https://open-meteo.com/
Archive: https://archive-api.open-meteo.com/v1/archive
License: CC BY 4.0
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timezone

import pandas as pd

from data_sources.cache.file_cache import FileCache
from data_sources.config import (
    CACHE_TTL,
    FUEL_TYPE_COL,
    OPEN_METEO_ARCHIVE_URL,
    OPEN_METEO_FORECAST_URL,
    OPEN_METEO_HOURLY_VARS,
    REGION_COL,
    REGION_COORDS,
    SOURCE_COL,
    TIMESTAMP_COL,
    UNIT_COL,
    VALUE_COL,
)
from data_sources.loaders.base import BaseLoader
from data_sources.schemas.models import validate_dataframe, _empty_normalized_frame
from data_sources.utils.timezone import normalize_series_to_utc

logger = logging.getLogger(__name__)

# Mapping from Open-Meteo variable name → (GridMind fuel_type, unit)
_VAR_META: dict[str, tuple[str, str]] = {
    "temperature_2m": ("temperature", "degC"),
    "shortwave_radiation": ("radiation", "W/m2"),
    "wind_speed_10m": ("wind_speed", "m/s"),
    "wind_direction_10m": ("wind_direction", "degrees"),
    "precipitation": ("precipitation", "mm"),
    "cloudcover": ("cloud_cover", "%"),
    # newer API uses "cloud_cover" without "age" suffix
    "cloud_cover": ("cloud_cover", "%"),
}


class OpenMeteoLoader(BaseLoader):
    """Loader for Open-Meteo hourly weather data.

    For each region the loader resolves coordinates via the built-in
    :data:`~data_sources.config.REGION_COORDS` mapping.  Custom coordinates
    can be supplied directly via the *coordinates* parameter.

    Parameters
    ----------
    variables:
        List of Open-Meteo hourly variable names to request.
        Defaults to :data:`~data_sources.config.OPEN_METEO_HOURLY_VARS`.
    coordinates:
        Override region→coordinates mapping with ``{region: (lat, lon)}``.
    cache_dir:
        Override the default cache root.
    """

    source_name = "open_meteo"

    def __init__(
        self,
        variables: list[str] | None = None,
        coordinates: dict[str, tuple[float, float]] | None = None,
        cache_dir=None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.variables = variables or OPEN_METEO_HOURLY_VARS
        self._extra_coords: dict[str, tuple[float, float]] = coordinates or {}
        cache_kwargs = {"cache_dir": cache_dir} if cache_dir else {}
        self._cache = FileCache("open_meteo", ttl_seconds=CACHE_TTL["open_meteo"], **cache_kwargs)

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
        """Return hourly weather data for *region* in [*start*, *end*].

        Parameters
        ----------
        region:
            ISO-2 country code, or any key present in ``coordinates`` passed
            at construction time.
        start / end:
            Inclusive date range.

        Raises
        ------
        ValueError
            If no coordinates are known for *region*.
        """
        region = region.upper()
        lat, lon = self._resolve_coords(region)
        cache_key = self._cache.cache_key(
            self.source_name, region, str(start), str(end),
            ",".join(sorted(self.variables)),
        )

        if use_cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        logger.info(
            "Fetching Open-Meteo data for region=%s (%.2f,%.2f) %s → %s",
            region, lat, lon, start, end,
        )
        df = self._request(region, lat, lon, start, end)
        if use_cache and not df.empty:
            self._cache.set(cache_key, df)
        return df

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _request(
        self,
        region: str,
        lat: float,
        lon: float,
        start: date,
        end: date,
    ) -> pd.DataFrame:
        today = datetime.now(tz=timezone.utc).date()
        # Use archive endpoint for historical data (>5 days in the past)
        if end < today - pd.Timedelta(days=5).to_pytimedelta():
            url = OPEN_METEO_ARCHIVE_URL
        else:
            url = OPEN_METEO_FORECAST_URL

        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": ",".join(self.variables),
            "timezone": "UTC",
            "start_date": str(start),
            "end_date": str(end),
            "wind_speed_unit": "ms",
        }

        try:
            data = self._get_json(url, params=params)
        except Exception as exc:
            logger.error("Open-Meteo request failed: %s", exc)
            return _empty_normalized_frame()

        return self._normalize(data, region)

    def _normalize(self, data: dict, region: str) -> pd.DataFrame:
        """Unpack the Open-Meteo hourly JSON into long-format normalized rows."""
        hourly = data.get("hourly", {})
        time_series = hourly.get("time")
        if not time_series:
            logger.warning("Open-Meteo response missing 'hourly.time'")
            return _empty_normalized_frame()

        timestamps = normalize_series_to_utc(pd.Series(pd.to_datetime(time_series)))

        frames: list[pd.DataFrame] = []
        for var in self.variables:
            values = hourly.get(var)
            if values is None:
                logger.debug("Variable '%s' not in Open-Meteo response", var)
                continue
            fuel_type, unit = _VAR_META.get(var, (var, "unknown"))
            frame = pd.DataFrame(
                {
                    TIMESTAMP_COL: timestamps,
                    REGION_COL: region,
                    FUEL_TYPE_COL: fuel_type,
                    VALUE_COL: pd.to_numeric(pd.Series(values), errors="coerce"),
                    UNIT_COL: unit,
                    SOURCE_COL: self.source_name,
                }
            )
            frames.append(frame)

        if not frames:
            return _empty_normalized_frame()

        combined = pd.concat(frames, ignore_index=True)
        return validate_dataframe(combined, source=self.source_name)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolve_coords(self, region: str) -> tuple[float, float]:
        if region in self._extra_coords:
            return self._extra_coords[region]
        if region in REGION_COORDS:
            return REGION_COORDS[region]
        raise ValueError(
            f"No coordinates known for region '{region}'. "
            f"Pass coordinates={{'{region}': (lat, lon)}} to OpenMeteoLoader."
        )
