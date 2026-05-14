"""Normalized data models and schema validation for GridMind-AI."""
from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Sequence

import pandas as pd

from data_sources.config import (
    FUEL_TYPE_COL,
    REGION_COL,
    SOURCE_COL,
    TIMESTAMP_COL,
    UNIT_COL,
    VALUE_COL,
)


# ---------------------------------------------------------------------------
# Enumerations (open-ended — use .value strings for unknown types)
# ---------------------------------------------------------------------------

class FuelType(str, Enum):
    SOLAR = "solar"
    WIND_ONSHORE = "wind_onshore"
    WIND_OFFSHORE = "wind_offshore"
    WIND = "wind"
    NUCLEAR = "nuclear"
    COAL = "coal"
    LIGNITE = "lignite"
    GAS = "gas"
    HYDRO = "hydro"
    BIOMASS = "biomass"
    OIL = "oil"
    OTHER_RENEWABLE = "other_renewable"
    OTHER = "other"
    TOTAL = "total"
    DEMAND = "demand"
    # Weather-derived variables
    TEMPERATURE = "temperature"
    RADIATION = "radiation"
    WIND_SPEED = "wind_speed"
    WIND_DIRECTION = "wind_direction"
    PRECIPITATION = "precipitation"
    CLOUD_COVER = "cloud_cover"


class Unit(str, Enum):
    MW = "MW"
    MWH = "MWh"
    GW = "GW"
    GWH = "GWh"
    TWH = "TWh"
    CELSIUS = "degC"
    WM2 = "W/m2"
    MS = "m/s"
    DEGREES = "degrees"
    MM = "mm"
    PCT = "%"


# ---------------------------------------------------------------------------
# Normalized schema contract
# ---------------------------------------------------------------------------

NORMALIZED_SCHEMA: dict[str, str] = {
    TIMESTAMP_COL: "datetime64[ns, UTC]",
    REGION_COL: "object",
    FUEL_TYPE_COL: "object",
    VALUE_COL: "float64",
    UNIT_COL: "object",
    SOURCE_COL: "object",
}

REQUIRED_COLUMNS: list[str] = list(NORMALIZED_SCHEMA.keys())


# ---------------------------------------------------------------------------
# Record dataclass
# ---------------------------------------------------------------------------

@dataclass
class DataRecord:
    """Single normalized energy or weather data point."""

    timestamp: datetime
    region: str
    fuel_type: str
    value_mw: float
    unit: str
    source: str
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            TIMESTAMP_COL: self.timestamp,
            REGION_COL: self.region,
            FUEL_TYPE_COL: self.fuel_type,
            VALUE_COL: self.value_mw,
            UNIT_COL: self.unit,
            SOURCE_COL: self.source,
        }


def records_to_dataframe(records: Sequence[DataRecord]) -> pd.DataFrame:
    """Convert a list of DataRecords to a validated normalized DataFrame."""
    df = pd.DataFrame([r.to_dict() for r in records])
    return validate_dataframe(df, source="records_to_dataframe")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_dataframe(df: pd.DataFrame, source: str = "unknown") -> pd.DataFrame:
    """Validate and coerce a DataFrame to the normalized schema.

    Raises ValueError for missing required columns. Warns (does not raise)
    for missing numeric values so callers can decide how to handle gaps.
    """
    if df.empty:
        return _empty_normalized_frame()

    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(
            f"[{source}] Missing required columns: {missing_cols}. "
            f"Available: {list(df.columns)}"
        )

    df = df.copy()

    # --- Timestamp → UTC-aware datetime ---
    if not pd.api.types.is_datetime64_any_dtype(df[TIMESTAMP_COL]):
        df[TIMESTAMP_COL] = pd.to_datetime(df[TIMESTAMP_COL], utc=True)
    elif getattr(df[TIMESTAMP_COL].dt, "tz", None) is None:
        df[TIMESTAMP_COL] = df[TIMESTAMP_COL].dt.tz_localize("UTC")
    else:
        df[TIMESTAMP_COL] = df[TIMESTAMP_COL].dt.tz_convert("UTC")

    # --- Numeric value column ---
    df[VALUE_COL] = pd.to_numeric(df[VALUE_COL], errors="coerce")
    null_count = int(df[VALUE_COL].isna().sum())
    if null_count > 0:
        pct = null_count / len(df) * 100
        warnings.warn(
            f"[{source}] {null_count} missing values ({pct:.1f}%) in '{VALUE_COL}'",
            stacklevel=2,
        )

    # --- String columns ---
    for col in (REGION_COL, FUEL_TYPE_COL, UNIT_COL, SOURCE_COL):
        df[col] = df[col].astype(str).str.strip()

    # Return only canonical columns in canonical order
    return df[REQUIRED_COLUMNS].reset_index(drop=True)


def _empty_normalized_frame() -> pd.DataFrame:
    """Return an empty DataFrame with the correct normalized schema."""
    return pd.DataFrame(columns=REQUIRED_COLUMNS).astype(
        {VALUE_COL: "float64"}
    )
