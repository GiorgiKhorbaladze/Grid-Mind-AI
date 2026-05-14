"""Tests for data_sources.loaders.open_meteo."""
from __future__ import annotations

import json
from datetime import date
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from data_sources.config import (
    FUEL_TYPE_COL,
    REGION_COL,
    SOURCE_COL,
    TIMESTAMP_COL,
    UNIT_COL,
    VALUE_COL,
)
from data_sources.loaders.open_meteo import OpenMeteoLoader
from data_sources.schemas.models import REQUIRED_COLUMNS


@pytest.fixture()
def loader(tmp_cache):
    return OpenMeteoLoader(
        variables=["temperature_2m", "wind_speed_10m"],
        cache_dir=tmp_cache,
    )


class TestOpenMeteoLoader:
    def test_fetch_returns_normalized_df(self, loader, open_meteo_response, tmp_cache):
        # Trim response to only requested variables
        open_meteo_response["hourly"] = {
            "time": open_meteo_response["hourly"]["time"],
            "temperature_2m": open_meteo_response["hourly"]["temperature_2m"],
            "wind_speed_10m": open_meteo_response["hourly"]["wind_speed_10m"],
        }
        with patch.object(loader, "_get_json", return_value=open_meteo_response):
            df = loader.fetch("DE", date(2023, 1, 1), date(2023, 1, 1), use_cache=False)

        assert not df.empty
        assert list(df.columns) == REQUIRED_COLUMNS
        assert set(df[SOURCE_COL].unique()) == {"open_meteo"}
        assert df[REGION_COL].unique().tolist() == ["DE"]
        # Two variables × 3 time steps = 6 rows
        assert len(df) == 6

    def test_temperature_fuel_type_and_unit(self, loader, open_meteo_response, tmp_cache):
        open_meteo_response["hourly"] = {
            "time": open_meteo_response["hourly"]["time"],
            "temperature_2m": [1.0, 2.0, 3.0],
            "wind_speed_10m": [4.0, 5.0, 6.0],
        }
        with patch.object(loader, "_get_json", return_value=open_meteo_response):
            df = loader.fetch("DE", date(2023, 1, 1), date(2023, 1, 1), use_cache=False)

        temp_rows = df[df[FUEL_TYPE_COL] == "temperature"]
        assert not temp_rows.empty
        assert (temp_rows[UNIT_COL] == "degC").all()

        wind_rows = df[df[FUEL_TYPE_COL] == "wind_speed"]
        assert not wind_rows.empty
        assert (wind_rows[UNIT_COL] == "m/s").all()

    def test_timestamps_are_utc(self, loader, open_meteo_response):
        open_meteo_response["hourly"] = {
            "time": ["2023-01-01T00:00", "2023-01-01T01:00"],
            "temperature_2m": [1.0, 2.0],
            "wind_speed_10m": [3.0, 4.0],
        }
        with patch.object(loader, "_get_json", return_value=open_meteo_response):
            df = loader.fetch("DE", date(2023, 1, 1), date(2023, 1, 1), use_cache=False)

        assert str(df[TIMESTAMP_COL].dt.tz) == "UTC"

    def test_cache_used_on_second_call(self, loader, open_meteo_response):
        open_meteo_response["hourly"] = {
            "time": ["2023-01-01T00:00"],
            "temperature_2m": [5.0],
            "wind_speed_10m": [3.0],
        }
        with patch.object(loader, "_get_json", return_value=open_meteo_response) as mock_get:
            loader.fetch("DE", date(2023, 1, 1), date(2023, 1, 1))
            loader.fetch("DE", date(2023, 1, 1), date(2023, 1, 1))
        # API should only be called once; second call served from cache
        assert mock_get.call_count == 1

    def test_cache_bypassed_when_disabled(self, loader, open_meteo_response):
        open_meteo_response["hourly"] = {
            "time": ["2023-01-01T00:00"],
            "temperature_2m": [5.0],
            "wind_speed_10m": [3.0],
        }
        with patch.object(loader, "_get_json", return_value=open_meteo_response) as mock_get:
            loader.fetch("DE", date(2023, 1, 1), date(2023, 1, 1), use_cache=False)
            loader.fetch("DE", date(2023, 1, 1), date(2023, 1, 1), use_cache=False)
        assert mock_get.call_count == 2

    def test_unknown_region_raises(self, tmp_cache):
        loader = OpenMeteoLoader(cache_dir=tmp_cache)
        with pytest.raises(ValueError, match="No coordinates known"):
            loader.fetch("XX", date(2023, 1, 1), date(2023, 1, 1))

    def test_custom_coordinates_accepted(self, tmp_cache, open_meteo_response):
        loader = OpenMeteoLoader(
            variables=["temperature_2m", "wind_speed_10m"],
            coordinates={"CUSTOM": (48.0, 11.0)},
            cache_dir=tmp_cache,
        )
        open_meteo_response["hourly"] = {
            "time": ["2023-01-01T00:00"],
            "temperature_2m": [10.0],
            "wind_speed_10m": [5.0],
        }
        with patch.object(loader, "_get_json", return_value=open_meteo_response):
            df = loader.fetch("CUSTOM", date(2023, 1, 1), date(2023, 1, 1), use_cache=False)
        assert not df.empty

    def test_api_failure_returns_empty(self, loader):
        with patch.object(loader, "_get_json", side_effect=RuntimeError("network error")):
            df = loader.fetch("DE", date(2023, 1, 1), date(2023, 1, 1), use_cache=False)
        assert df.empty
        assert list(df.columns) == REQUIRED_COLUMNS
