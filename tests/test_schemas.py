"""Tests for data_sources.schemas.models."""
from __future__ import annotations

import warnings
from datetime import datetime, timezone

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
from data_sources.schemas.models import (
    REQUIRED_COLUMNS,
    DataRecord,
    records_to_dataframe,
    validate_dataframe,
    _empty_normalized_frame,
)


class TestValidateDataframe:
    def test_valid_df_passes(self, sample_normalized_df):
        result = validate_dataframe(sample_normalized_df, source="test")
        assert list(result.columns) == REQUIRED_COLUMNS
        assert result[TIMESTAMP_COL].dt.tz is not None
        assert str(result[TIMESTAMP_COL].dt.tz) == "UTC"

    def test_naive_timestamps_localized_to_utc(self, sample_naive_df):
        result = validate_dataframe(sample_naive_df)
        assert str(result[TIMESTAMP_COL].dt.tz) == "UTC"

    def test_tz_aware_non_utc_converted(self):
        df = pd.DataFrame(
            {
                TIMESTAMP_COL: pd.to_datetime(["2023-01-01 10:00"]).tz_localize("Europe/Berlin"),
                REGION_COL: ["DE"],
                FUEL_TYPE_COL: ["solar"],
                VALUE_COL: [50.0],
                UNIT_COL: ["MW"],
                SOURCE_COL: ["test"],
            }
        )
        result = validate_dataframe(df)
        assert str(result[TIMESTAMP_COL].dt.tz) == "UTC"
        # 10:00 Berlin (CET = UTC+1) → 09:00 UTC
        assert result[TIMESTAMP_COL].iloc[0].hour == 9

    def test_missing_column_raises(self):
        df = pd.DataFrame(
            {
                TIMESTAMP_COL: pd.to_datetime(["2023-01-01"], utc=True),
                REGION_COL: ["DE"],
                FUEL_TYPE_COL: ["solar"],
                VALUE_COL: [100.0],
                # UNIT_COL missing
                SOURCE_COL: ["test"],
            }
        )
        with pytest.raises(ValueError, match="Missing required columns"):
            validate_dataframe(df)

    def test_non_numeric_values_coerced_to_nan(self):
        df = pd.DataFrame(
            {
                TIMESTAMP_COL: pd.to_datetime(["2023-01-01"], utc=True),
                REGION_COL: ["DE"],
                FUEL_TYPE_COL: ["solar"],
                VALUE_COL: ["not_a_number"],
                UNIT_COL: ["MW"],
                SOURCE_COL: ["test"],
            }
        )
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = validate_dataframe(df)
        assert pd.isna(result[VALUE_COL].iloc[0])
        assert any("missing values" in str(warning.message) for warning in w)

    def test_missing_values_emit_warning(self, sample_normalized_df):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validate_dataframe(sample_normalized_df, source="test")
        assert any("missing values" in str(warning.message) for warning in w)

    def test_empty_df_returns_empty_frame(self):
        result = validate_dataframe(pd.DataFrame())
        assert result.empty
        assert list(result.columns) == REQUIRED_COLUMNS

    def test_only_canonical_columns_returned(self):
        df = pd.DataFrame(
            {
                TIMESTAMP_COL: pd.to_datetime(["2023-01-01"], utc=True),
                REGION_COL: ["DE"],
                FUEL_TYPE_COL: ["solar"],
                VALUE_COL: [99.0],
                UNIT_COL: ["MW"],
                SOURCE_COL: ["test"],
                "extra_col": ["should_be_dropped"],
            }
        )
        result = validate_dataframe(df)
        assert "extra_col" not in result.columns
        assert list(result.columns) == REQUIRED_COLUMNS


class TestDataRecord:
    def test_to_dict_keys_match_schema(self):
        dt = datetime(2023, 1, 1, tzinfo=timezone.utc)
        rec = DataRecord(
            timestamp=dt,
            region="DE",
            fuel_type="solar",
            value_mw=100.0,
            unit="MW",
            source="test",
        )
        d = rec.to_dict()
        for col in REQUIRED_COLUMNS:
            assert col in d

    def test_records_to_dataframe(self):
        dt = datetime(2023, 1, 1, tzinfo=timezone.utc)
        records = [
            DataRecord(dt, "DE", "solar", 100.0, "MW", "test"),
            DataRecord(dt, "DE", "wind", 200.0, "MW", "test"),
        ]
        df = records_to_dataframe(records)
        assert len(df) == 2
        assert list(df.columns) == REQUIRED_COLUMNS


class TestEmptyFrame:
    def test_empty_frame_has_correct_columns(self):
        df = _empty_normalized_frame()
        assert df.empty
        assert list(df.columns) == REQUIRED_COLUMNS
        assert df[VALUE_COL].dtype == "float64"
