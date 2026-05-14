"""Tests for data_sources.loaders.ember."""
from __future__ import annotations

from datetime import date
from unittest.mock import patch

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
from data_sources.loaders.ember import EmberLoader
from data_sources.schemas.models import REQUIRED_COLUMNS


@pytest.fixture()
def loader(tmp_cache):
    return EmberLoader(resolution="monthly", cache_dir=tmp_cache)


class TestEmberLoader:
    def test_fetch_returns_normalized_df(self, loader, ember_response):
        with patch.object(loader, "_get_json", return_value=ember_response):
            df = loader.fetch("DEU", date(2023, 1, 1), date(2023, 2, 28), use_cache=False)

        assert not df.empty
        assert list(df.columns) == REQUIRED_COLUMNS
        assert df[SOURCE_COL].unique().tolist() == ["ember"]

    def test_fuel_types_normalized(self, loader, ember_response):
        with patch.object(loader, "_get_json", return_value=ember_response):
            df = loader.fetch("DEU", date(2023, 1, 1), date(2023, 2, 28), use_cache=False)

        assert "solar" in df[FUEL_TYPE_COL].values
        assert "wind" in df[FUEL_TYPE_COL].values

    def test_unit_is_twh(self, loader, ember_response):
        with patch.object(loader, "_get_json", return_value=ember_response):
            df = loader.fetch("DEU", date(2023, 1, 1), date(2023, 2, 28), use_cache=False)
        assert (df[UNIT_COL] == "TWh").all()

    def test_timestamps_utc(self, loader, ember_response):
        with patch.object(loader, "_get_json", return_value=ember_response):
            df = loader.fetch("DEU", date(2023, 1, 1), date(2023, 2, 28), use_cache=False)
        assert str(df[TIMESTAMP_COL].dt.tz) == "UTC"

    def test_iso2_region_auto_converted(self, loader, ember_response):
        """ISO-2 codes like 'DE' must be silently converted to ISO-3 'DEU'."""
        with patch.object(loader, "_get_json", return_value=ember_response) as mock_get:
            loader.fetch("DE", date(2023, 1, 1), date(2023, 2, 28), use_cache=False)
        call_params = mock_get.call_args[1].get("params", {})
        assert call_params.get("country") == "DEU"

    def test_api_dict_with_data_key(self, loader):
        response = {
            "data": [
                {"date": "2023-01", "country_code": "DEU", "series": "Solar", "generation_twh": 4.5},
            ]
        }
        with patch.object(loader, "_get_json", return_value=response):
            df = loader.fetch("DEU", date(2023, 1, 1), date(2023, 1, 31), use_cache=False)
        assert not df.empty

    def test_empty_api_response_returns_empty(self, loader):
        with patch.object(loader, "_get_json", return_value=[]):
            df = loader.fetch("DEU", date(2023, 1, 1), date(2023, 1, 31), use_cache=False)
        assert df.empty
        assert list(df.columns) == REQUIRED_COLUMNS

    def test_api_failure_returns_empty(self, loader):
        with patch.object(loader, "_get_json", side_effect=RuntimeError("timeout")):
            df = loader.fetch("DEU", date(2023, 1, 1), date(2023, 1, 31), use_cache=False)
        assert df.empty

    def test_cache_prevents_second_api_call(self, loader, ember_response):
        with patch.object(loader, "_get_json", return_value=ember_response) as mock_get:
            loader.fetch("DEU", date(2023, 1, 1), date(2023, 2, 28))
            loader.fetch("DEU", date(2023, 1, 1), date(2023, 2, 28))
        assert mock_get.call_count == 1

    def test_invalid_resolution_raises(self, tmp_cache):
        with pytest.raises(ValueError, match="resolution"):
            EmberLoader(resolution="weekly", cache_dir=tmp_cache)

    def test_yearly_resolution_date_params(self, tmp_cache, ember_response):
        loader = EmberLoader(resolution="yearly", cache_dir=tmp_cache)
        with patch.object(loader, "_get_json", return_value=ember_response) as mock_get:
            loader.fetch("DEU", date(2020, 1, 1), date(2022, 12, 31), use_cache=False)
        params = mock_get.call_args[1].get("params", {})
        assert params["start_date"] == "2020"
        assert params["end_date"] == "2022"
