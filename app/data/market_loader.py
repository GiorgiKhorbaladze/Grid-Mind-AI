"""Market data loading and cleaning for BESS/electricity-market workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

CANONICAL_COLUMNS = [
    "timestamp",
    "country",
    "bidding_zone",
    "price_eur_mwh",
    "load_mw",
    "solar_mw",
    "wind_mw",
    "source",
]

NUMERIC_COLUMNS = ["price_eur_mwh", "load_mw", "solar_mw", "wind_mw"]


def demo_market_data(periods: int = 72, country: str = "Germany", bidding_zone: str = "DE-LU") -> pd.DataFrame:
    """Return deterministic hourly demo electricity market data.

    The shape intentionally resembles a day-ahead electricity market profile:
    higher prices during evening demand peaks, lower prices during high solar
    output, and wind variability across the sample horizon.
    """

    timestamps = pd.date_range("2024-01-01", periods=periods, freq="h", tz="UTC")
    hours = np.arange(periods) % 24
    days = np.arange(periods) // 24

    load = 52_000 + 7_500 * np.sin((hours - 7) / 24 * 2 * np.pi) + 2_000 * np.cos(days / 3)
    solar = np.maximum(0, 14_000 * np.sin((hours - 6) / 12 * np.pi))
    wind = 9_000 + 2_500 * np.sin((np.arange(periods) + 4) / 9) + 1_000 * np.cos(hours / 24 * 2 * np.pi)
    residual_load = load - solar - wind
    evening_peak = np.where((hours >= 17) & (hours <= 21), 24, 0)
    price = 58 + 0.0012 * (residual_load - residual_load.mean()) + evening_peak - 0.0009 * solar
    price = np.round(np.clip(price, -20, None), 2)

    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "country": country,
            "bidding_zone": bidding_zone,
            "price_eur_mwh": price,
            "load_mw": np.round(load, 2),
            "solar_mw": np.round(solar, 2),
            "wind_mw": np.round(np.maximum(wind, 0), 2),
            "source": "demo",
        },
        columns=CANONICAL_COLUMNS,
    )


def clean_market_data(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize market data to the canonical schema and safe numeric types."""

    if frame.empty:
        return demo_market_data()

    data = frame.copy()
    for column in CANONICAL_COLUMNS:
        if column not in data.columns:
            data[column] = np.nan

    data = data[CANONICAL_COLUMNS]
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True, errors="coerce")
    for column in NUMERIC_COLUMNS:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    data["country"] = data["country"].fillna("Unknown").astype(str).str.strip().replace("", "Unknown")
    data["bidding_zone"] = data["bidding_zone"].fillna("Unknown").astype(str).str.strip().replace("", "Unknown")
    data["source"] = data["source"].fillna("uploaded").astype(str).str.strip().replace("", "uploaded")

    data = data.dropna(subset=["timestamp", "price_eur_mwh"]).sort_values("timestamp")
    data[NUMERIC_COLUMNS] = data[NUMERIC_COLUMNS].interpolate(limit_direction="both")
    data[NUMERIC_COLUMNS] = data[NUMERIC_COLUMNS].fillna(0.0)
    data[["load_mw", "solar_mw", "wind_mw"]] = data[["load_mw", "solar_mw", "wind_mw"]].clip(lower=0)

    return data.reset_index(drop=True)


def load_market_data(path: str | Path | None = None) -> pd.DataFrame:
    """Load CSV/Parquet market data, or return deterministic demo data.

    No external API token is required. If a path is omitted, missing, unsupported,
    or unreadable, the function returns the demo fallback so the app remains
    runnable end-to-end.
    """

    if path is None:
        return demo_market_data()

    candidate = Path(path)
    if not candidate.exists():
        return demo_market_data()

    try:
        if candidate.suffix.lower() == ".csv":
            return clean_market_data(pd.read_csv(candidate))
        if candidate.suffix.lower() in {".parquet", ".pq"}:
            return clean_market_data(pd.read_parquet(candidate))
    except Exception:
        return demo_market_data()

    return demo_market_data()


def available_zones(frame: pd.DataFrame) -> Iterable[str]:
    """Return sorted bidding zones present in a market data frame."""

    if "bidding_zone" not in frame:
        return []
    return sorted(frame["bidding_zone"].dropna().astype(str).unique())
