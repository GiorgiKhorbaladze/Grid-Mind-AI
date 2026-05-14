"""Tests for data_sources.utils.timezone."""
from __future__ import annotations

from datetime import date, datetime, timezone

import pandas as pd
import pytest
import pytz

from data_sources.utils.timezone import (
    date_to_datetime_utc,
    floor_to_hour,
    normalize_series_to_utc,
    to_utc,
)


class TestToUtc:
    def test_utc_aware_passthrough(self):
        dt = datetime(2023, 6, 1, 12, 0, tzinfo=timezone.utc)
        result = to_utc(dt)
        assert result.tzinfo == pytz.UTC
        assert result.hour == 12

    def test_naive_assumed_utc(self):
        dt = datetime(2023, 6, 1, 12, 0)
        result = to_utc(dt)
        assert result.tzinfo is not None
        assert result.hour == 12

    def test_naive_with_source_tz(self):
        dt = datetime(2023, 6, 1, 13, 0)  # 13:00 CET (UTC+1 in winter, UTC+2 in summer)
        result = to_utc(dt, source_tz="Europe/Berlin")
        # June: CEST = UTC+2, so 13:00 Berlin → 11:00 UTC
        assert result.hour == 11

    def test_tz_aware_converted(self):
        berlin = pytz.timezone("Europe/Berlin")
        dt = berlin.localize(datetime(2023, 1, 1, 12, 0))  # CET = UTC+1
        result = to_utc(dt)
        assert result.hour == 11


class TestNormalizeSeriestoUtc:
    def test_naive_series_localized(self):
        s = pd.Series(pd.to_datetime(["2023-01-01 10:00", "2023-01-01 11:00"]))
        result = normalize_series_to_utc(s)
        assert str(result.dt.tz) == "UTC"

    def test_naive_series_with_source_tz(self):
        s = pd.Series(pd.to_datetime(["2023-01-01 12:00"]))
        result = normalize_series_to_utc(s, source_tz="Europe/Paris")
        # CET winter: UTC+1, so 12:00 Paris → 11:00 UTC
        assert result.iloc[0].hour == 11

    def test_utc_aware_series_unchanged(self):
        s = pd.Series(pd.to_datetime(["2023-06-01 08:00"], utc=True))
        result = normalize_series_to_utc(s)
        assert str(result.dt.tz) == "UTC"
        assert result.iloc[0].hour == 8

    def test_non_utc_tz_converted(self):
        # Use a pytz timezone object so the test works without the tzdata package.
        eastern = pytz.timezone("US/Eastern")
        dt = eastern.localize(pd.Timestamp("2023-06-01 10:00").to_pydatetime())
        s = pd.Series([pd.Timestamp(dt)])
        result = normalize_series_to_utc(s)
        assert str(result.dt.tz) == "UTC"
        # US/Eastern summer = UTC-4, so 10:00 Eastern → 14:00 UTC
        assert result.iloc[0].hour == 14

    def test_string_series_parsed(self):
        s = pd.Series(["2023-01-01T00:00:00", "2023-01-01T01:00:00"])
        result = normalize_series_to_utc(s)
        assert str(result.dt.tz) == "UTC"
        assert len(result) == 2


class TestDateToDatetimeUtc:
    def test_date_object(self):
        d = date(2023, 3, 15)
        result = date_to_datetime_utc(d)
        assert result.year == 2023
        assert result.month == 3
        assert result.day == 15
        assert result.hour == 0
        assert result.tzinfo == pytz.UTC

    def test_iso_string(self):
        result = date_to_datetime_utc("2024-12-25")
        assert result.year == 2024
        assert result.day == 25

    def test_invalid_string_raises(self):
        with pytest.raises(ValueError):
            date_to_datetime_utc("not-a-date")


class TestFloorToHour:
    def test_truncates_minutes_and_seconds(self):
        dt = datetime(2023, 6, 1, 14, 37, 59, 999999, tzinfo=timezone.utc)
        result = floor_to_hour(dt)
        assert result.hour == 14
        assert result.minute == 0
        assert result.second == 0
        assert result.microsecond == 0
