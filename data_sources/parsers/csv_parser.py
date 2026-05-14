"""CSV parsing helpers shared across all loaders."""
from __future__ import annotations

import io
from typing import Any

import pandas as pd


def parse_csv_bytes(
    content: bytes,
    encoding: str = "utf-8",
    parse_dates: list[str] | None = None,
    **read_kwargs: Any,
) -> pd.DataFrame:
    """Decode *content* and parse it as CSV into a DataFrame.

    Parameters
    ----------
    content:
        Raw HTTP response bytes.
    encoding:
        Character encoding; falls back to ``replace`` on errors.
    parse_dates:
        Column names to parse as datetimes.
    **read_kwargs:
        Forwarded verbatim to :func:`pandas.read_csv`.
    """
    text = content.decode(encoding, errors="replace")
    kwargs: dict[str, Any] = {"low_memory": False, **read_kwargs}
    if parse_dates:
        kwargs["parse_dates"] = parse_dates
    return pd.read_csv(io.StringIO(text), **kwargs)


def parse_csv_chunks(
    content: bytes,
    chunksize: int = 50_000,
    encoding: str = "utf-8",
    parse_dates: list[str] | None = None,
    **read_kwargs: Any,
) -> pd.DataFrame:
    """Parse a large CSV from bytes using chunked reading to limit peak memory."""
    text = content.decode(encoding, errors="replace")
    kwargs: dict[str, Any] = {
        "low_memory": False,
        "chunksize": chunksize,
        **read_kwargs,
    }
    if parse_dates:
        kwargs["parse_dates"] = parse_dates
    chunks = pd.read_csv(io.StringIO(text), **kwargs)
    return pd.concat(list(chunks), ignore_index=True)


def melt_wide_to_long(
    df: pd.DataFrame,
    id_vars: list[str],
    value_name: str = "value_mw",
    var_name: str = "fuel_type",
) -> pd.DataFrame:
    """Pivot a wide DataFrame (columns = fuel types) into long form.

    All columns not in *id_vars* become rows in the *var_name* column.
    """
    return df.melt(id_vars=id_vars, var_name=var_name, value_name=value_name)
