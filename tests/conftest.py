"""Shared pytest fixtures for GridMind-AI data_sources tests."""
from __future__ import annotations

import json
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path

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


# ---------------------------------------------------------------------------
# Reusable temporary cache directory
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_cache(tmp_path: Path) -> Path:
    """Provide a clean temporary cache directory for each test."""
    return tmp_path / "cache"


# ---------------------------------------------------------------------------
# Sample normalized DataFrames
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_normalized_df() -> pd.DataFrame:
    """Minimal valid normalized DataFrame (3 rows)."""
    return pd.DataFrame(
        {
            TIMESTAMP_COL: pd.to_datetime(
                ["2023-01-01 00:00", "2023-01-01 01:00", "2023-01-01 02:00"],
                utc=True,
            ),
            REGION_COL: ["DE", "DE", "DE"],
            FUEL_TYPE_COL: ["solar", "solar", "solar"],
            VALUE_COL: [100.0, 200.0, float("nan")],
            UNIT_COL: ["MW", "MW", "MW"],
            SOURCE_COL: ["test", "test", "test"],
        }
    )


@pytest.fixture()
def sample_naive_df() -> pd.DataFrame:
    """DataFrame with naive (tz-unaware) timestamps — needs coercion."""
    return pd.DataFrame(
        {
            TIMESTAMP_COL: pd.to_datetime(["2023-06-15 12:00", "2023-06-15 13:00"]),
            REGION_COL: ["FR", "FR"],
            FUEL_TYPE_COL: ["wind", "wind"],
            VALUE_COL: [350.0, 420.5],
            UNIT_COL: ["MW", "MW"],
            SOURCE_COL: ["test", "test"],
        }
    )


# ---------------------------------------------------------------------------
# Open-Meteo mock API response
# ---------------------------------------------------------------------------

@pytest.fixture()
def open_meteo_response() -> dict:
    """Minimal Open-Meteo archive API response."""
    return {
        "latitude": 51.2,
        "longitude": 10.5,
        "timezone": "UTC",
        "hourly": {
            "time": [
                "2023-01-01T00:00",
                "2023-01-01T01:00",
                "2023-01-01T02:00",
            ],
            "temperature_2m": [2.1, 1.9, 1.7],
            "shortwave_radiation": [0.0, 0.0, 0.0],
            "wind_speed_10m": [5.2, 5.5, 4.8],
            "wind_direction_10m": [270.0, 265.0, 280.0],
            "precipitation": [0.0, 0.1, 0.0],
            "cloudcover": [80, 85, 75],
        },
    }


# ---------------------------------------------------------------------------
# Ember mock API response
# ---------------------------------------------------------------------------

@pytest.fixture()
def ember_response() -> list[dict]:
    """Minimal Ember API monthly generation response."""
    return [
        {"date": "2023-01", "country_code": "DEU", "series": "Solar", "generation_twh": 4.5},
        {"date": "2023-01", "country_code": "DEU", "series": "Wind", "generation_twh": 12.3},
        {"date": "2023-02", "country_code": "DEU", "series": "Solar", "generation_twh": 5.1},
        {"date": "2023-02", "country_code": "DEU", "series": "Wind", "generation_twh": 14.0},
    ]
