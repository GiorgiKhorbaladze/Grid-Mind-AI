"""JSON parsing helpers for REST API responses."""
from __future__ import annotations

from typing import Any

import pandas as pd


def parse_json_records(
    data: Any,
    record_path: str | None = None,
) -> pd.DataFrame:
    """Parse a JSON structure into a DataFrame.

    Parameters
    ----------
    data:
        Parsed Python object (list of dicts, or a dict containing a list).
    record_path:
        If *data* is a dict, the key whose value is the list of records.
        If ``None``, *data* itself must be a list.

    Raises
    ------
    ValueError
        If the structure cannot be interpreted as a table.
    """
    if isinstance(data, list):
        return pd.DataFrame(data)

    if isinstance(data, dict):
        if record_path is not None:
            if record_path not in data:
                raise ValueError(
                    f"Key '{record_path}' not found in JSON. "
                    f"Available keys: {list(data.keys())}"
                )
            return pd.DataFrame(data[record_path])
        # Treat a plain dict as a single row
        return pd.DataFrame([data])

    raise ValueError(
        f"Cannot convert JSON of type {type(data).__name__!r} to DataFrame. "
        "Expected list or dict."
    )
