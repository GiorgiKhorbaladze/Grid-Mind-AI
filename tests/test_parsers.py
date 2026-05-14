"""Tests for data_sources.parsers."""
from __future__ import annotations

import pytest

from data_sources.parsers.csv_parser import melt_wide_to_long, parse_csv_bytes
from data_sources.parsers.json_parser import parse_json_records


class TestParseCsvBytes:
    def test_basic_csv(self):
        csv = b"a,b,c\n1,2,3\n4,5,6\n"
        df = parse_csv_bytes(csv)
        assert list(df.columns) == ["a", "b", "c"]
        assert len(df) == 2

    def test_parse_dates(self):
        csv = b"ts,value\n2023-01-01,100\n2023-01-02,200\n"
        df = parse_csv_bytes(csv, parse_dates=["ts"])
        import pandas as pd
        assert pd.api.types.is_datetime64_any_dtype(df["ts"])

    def test_encoding_fallback(self):
        # Latin-1 encoded content decoded with utf-8 + replace
        csv = "a,b\n1,caf\xe9\n".encode("latin-1")
        df = parse_csv_bytes(csv, encoding="utf-8")
        assert len(df) == 1

    def test_extra_read_kwargs_forwarded(self):
        csv = b"a;b;c\n1;2;3\n"
        df = parse_csv_bytes(csv, sep=";")
        assert list(df.columns) == ["a", "b", "c"]


class TestMeltWideLong:
    def test_basic_melt(self):
        import pandas as pd
        df = pd.DataFrame(
            {
                "timestamp": ["2023-01-01"],
                "region": ["DE"],
                "solar": [100.0],
                "wind": [200.0],
            }
        )
        melted = melt_wide_to_long(df, id_vars=["timestamp", "region"])
        assert len(melted) == 2
        assert set(melted["fuel_type"]) == {"solar", "wind"}
        assert set(melted["value_mw"]) == {100.0, 200.0}


class TestParseJsonRecords:
    def test_list_of_dicts(self):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        df = parse_json_records(data)
        assert len(df) == 2
        assert list(df.columns) == ["a", "b"]

    def test_dict_with_record_path(self):
        data = {"results": [{"x": 1}, {"x": 2}], "total": 2}
        df = parse_json_records(data, record_path="results")
        assert len(df) == 2

    def test_missing_record_path_raises(self):
        data = {"other_key": []}
        with pytest.raises(ValueError, match="Key 'results' not found"):
            parse_json_records(data, record_path="results")

    def test_bare_dict_becomes_single_row(self):
        data = {"a": 1, "b": 2}
        df = parse_json_records(data)
        assert len(df) == 1

    def test_invalid_type_raises(self):
        with pytest.raises(ValueError, match="Cannot convert"):
            parse_json_records("not_a_list_or_dict")
