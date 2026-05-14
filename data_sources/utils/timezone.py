"""Timezone normalization utilities — all outputs are UTC-aware."""
from __future__ import annotations

from datetime import date, datetime
from typing import Union

import pandas as pd
import pytz

UTC = pytz.utc


def to_utc(dt: datetime, source_tz: str | None = None) -> datetime:
    """Return a UTC-aware datetime from a naive or tz-aware *dt*.

    If *dt* is naive and *source_tz* is given, the datetime is first
    localized to *source_tz* before conversion.  A naive *dt* with no
    *source_tz* is assumed to already be UTC.
    """
    if dt.tzinfo is None:
        tz = pytz.timezone(source_tz) if source_tz else UTC
        dt = tz.localize(dt)
    return dt.astimezone(UTC)


def normalize_series_to_utc(
    series: pd.Series, source_tz: str | None = None
) -> pd.Series:
    """Normalize a pandas timestamp Series to UTC.

    Handles naive, tz-aware, and mixed-offset series robustly.
    If the series is naive and *source_tz* is provided it is localized first.
    """
    if not pd.api.types.is_datetime64_any_dtype(series):
        series = pd.to_datetime(series, utc=False)

    if series.dt.tz is None:
        if source_tz:
            series = series.dt.tz_localize(source_tz, ambiguous="infer", nonexistent="shift_forward")
        else:
            series = series.dt.tz_localize("UTC")
    return series.dt.tz_convert("UTC")


def date_to_datetime_utc(d: Union[date, str]) -> datetime:
    """Convert a *date* or ISO-8601 date string to a UTC-aware datetime at midnight."""
    if isinstance(d, str):
        d = date.fromisoformat(d)
    return UTC.localize(datetime(d.year, d.month, d.day))


def floor_to_hour(dt: datetime) -> datetime:
    """Truncate a UTC-aware datetime to the start of the hour."""
    return dt.replace(minute=0, second=0, microsecond=0)
