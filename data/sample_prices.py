"""
Deterministic synthetic electricity price generator.

Generates realistic day-ahead price profiles with:
  - Base price level
  - Dual daily peaks (morning ramp + evening peak)
  - Midday solar dip (negative or near-zero prices)
  - Overnight valley
  - Controlled noise (seed-reproducible)

All outputs are fully deterministic given the same seed.
"""

import numpy as np
import pandas as pd
from typing import Optional


# ---------------------------------------------------------------------------
# Hourly shape template (relative offsets from base price)
# ---------------------------------------------------------------------------
# 24-element array representing typical price shape over one day.
# Units: $/MWh offset from base.

_HOURLY_SHAPE = np.array([
    -12.0,  # 00:00  overnight valley
    -14.0,  # 01:00
    -15.0,  # 02:00  trough
    -14.0,  # 03:00
    -12.0,  # 04:00
    - 8.0,  # 05:00  pre-dawn ramp begins
      5.0,  # 06:00
     18.0,  # 07:00  morning peak starts
     25.0,  # 08:00
     22.0,  # 09:00
     12.0,  # 10:00  solar pushes prices down
      2.0,  # 11:00
     -8.0,  # 12:00  midday solar trough
     -6.0,  # 13:00
      0.0,  # 14:00
      8.0,  # 15:00  evening ramp
     20.0,  # 16:00
     32.0,  # 17:00  evening peak
     38.0,  # 18:00  highest price of the day
     35.0,  # 19:00
     28.0,  # 20:00
     18.0,  # 21:00
      5.0,  # 22:00
     -5.0,  # 23:00  back to overnight
], dtype=float)


def generate_day_ahead_prices(
    days: int = 7,
    base_price: float = 35.0,
    noise_std: float = 5.0,
    trend_per_day: float = 0.0,
    seed: int = 42,
    freq: str = "h",
    start: str = "2026-01-01",
) -> pd.Series:
    """
    Generate a deterministic day-ahead price Series.

    Parameters
    ----------
    days : int
        Number of calendar days to generate.
    base_price : float
        Mean base price level ($/MWh).
    noise_std : float
        Standard deviation of Gaussian noise added each hour.
    trend_per_day : float
        Linear price trend ($/MWh per day); 0 = flat.
    seed : int
        Random seed for reproducibility.
    freq : str
        Pandas frequency string (default "h" = hourly).
    start : str
        ISO date string for the first timestamp.

    Returns
    -------
    pd.Series
        Electricity prices ($/MWh) with a DatetimeIndex.
    """
    rng = np.random.default_rng(seed)
    T = days * 24

    shape = np.tile(_HOURLY_SHAPE, days)
    trend = np.linspace(0.0, trend_per_day * days, T)
    noise = rng.normal(0.0, noise_std, T)

    prices = base_price + shape + trend + noise
    # Prices can be negative (realistic for high-solar periods); no floor applied.

    index = pd.date_range(start=start, periods=T, freq=freq)
    return pd.Series(prices, index=index, name="price_per_mwh")


def generate_price_scenario(
    scenario: str = "high_spread",
    days: int = 7,
    seed: int = 42,
) -> pd.Series:
    """
    Generate a named price scenario for sensitivity analysis.

    Scenarios
    ---------
    high_spread  – large daily spread (~$60/MWh), favours all durations
    low_spread   – small daily spread (~$15/MWh), challenges longer durations
    negative     – frequent negative prices (solar oversupply)
    volatile     – high noise, unpredictable spread pattern
    flat         – near-constant prices, minimal arbitrage opportunity

    Parameters
    ----------
    scenario : str
    days : int
    seed : int

    Returns
    -------
    pd.Series  ($/MWh, hourly DatetimeIndex)
    """
    scenarios = {
        "high_spread":  dict(base_price=50.0,  noise_std=4.0,  trend_per_day=0.0),
        "low_spread":   dict(base_price=30.0,  noise_std=2.0,  trend_per_day=0.0),
        "negative":     dict(base_price=5.0,   noise_std=8.0,  trend_per_day=0.0),
        "volatile":     dict(base_price=40.0,  noise_std=18.0, trend_per_day=0.0),
        "flat":         dict(base_price=35.0,  noise_std=0.5,  trend_per_day=0.0),
    }
    if scenario not in scenarios:
        raise ValueError(
            f"Unknown scenario '{scenario}'. Choose from: {list(scenarios)}."
        )
    kwargs = scenarios[scenario]
    return generate_day_ahead_prices(days=days, seed=seed, **kwargs)


# ---------------------------------------------------------------------------
# Convenience: quick summary of a price series
# ---------------------------------------------------------------------------

def price_summary(prices: pd.Series) -> dict:
    """Return descriptive statistics for a price series."""
    arr = prices.values.astype(float)
    return {
        "n_periods": len(arr),
        "mean_price": round(float(np.mean(arr)), 4),
        "std_price": round(float(np.std(arr)), 4),
        "min_price": round(float(np.min(arr)), 4),
        "max_price": round(float(np.max(arr)), 4),
        "daily_spread_mean": round(
            float(
                np.mean(
                    [
                        arr[i * 24 : (i + 1) * 24].max() - arr[i * 24 : (i + 1) * 24].min()
                        for i in range(len(arr) // 24)
                    ]
                )
            ),
            4,
        ),
        "n_negative_hours": int(np.sum(arr < 0)),
    }
