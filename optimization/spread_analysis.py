"""
Price spread analysis for BESS arbitrage opportunity assessment.

Spread is the primary indicator of arbitrage revenue potential:
  theoretical_max_revenue ≈ spread ($/MWh) × capacity (MWh) × η_roundtrip
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Dict, List


DURATION_HOURS = [1, 2, 4, 8]


@dataclass
class SpreadMetrics:
    """Aggregate spread statistics for a price series."""
    mean_daily_spread: float
    median_daily_spread: float
    p25_daily_spread: float
    p75_daily_spread: float
    max_daily_spread: float
    mean_price: float
    std_price: float
    min_price: float
    max_price: float
    n_days: int
    spread_per_duration: Dict[str, float]  # keyed "1h", "2h", "4h", "8h"

    def to_dict(self) -> dict:
        return {
            "mean_daily_spread": self.mean_daily_spread,
            "median_daily_spread": self.median_daily_spread,
            "p25_daily_spread": self.p25_daily_spread,
            "p75_daily_spread": self.p75_daily_spread,
            "max_daily_spread": self.max_daily_spread,
            "mean_price": self.mean_price,
            "std_price": self.std_price,
            "min_price": self.min_price,
            "max_price": self.max_price,
            "n_days": self.n_days,
            "spread_per_duration": self.spread_per_duration,
        }


class SpreadAnalyzer:
    """
    Computes price-spread metrics to quantify BESS arbitrage opportunity.

    Parameters
    ----------
    dt_hours : float
        Duration of each price time step (hours).
    """

    def __init__(self, dt_hours: float = 1.0) -> None:
        self.dt_hours = dt_hours

    # ------------------------------------------------------------------
    # Core spread computations
    # ------------------------------------------------------------------

    def daily_spreads(self, prices: np.ndarray) -> np.ndarray:
        """
        Max-minus-min price spread for each calendar day.
        Partial trailing days are discarded.
        """
        steps_per_day = int(round(24.0 / self.dt_hours))
        n_complete = len(prices) // steps_per_day
        if n_complete == 0:
            return np.array([prices.max() - prices.min()])
        daily = prices[: n_complete * steps_per_day].reshape(n_complete, steps_per_day)
        return daily.max(axis=1) - daily.min(axis=1)

    def rolling_spread(self, prices: np.ndarray, window_h: float) -> np.ndarray:
        """
        Rolling max-minus-min spread over a window of `window_h` hours.

        Returns array of length  max(0, len(prices) - window_steps + 1).
        """
        window_steps = max(1, int(round(window_h / self.dt_hours)))
        if len(prices) < window_steps:
            return np.array([prices.max() - prices.min()])
        n = len(prices) - window_steps + 1
        spreads = np.empty(n)
        for i in range(n):
            window = prices[i : i + window_steps]
            spreads[i] = window.max() - window.min()
        return spreads

    # ------------------------------------------------------------------
    # Full analysis
    # ------------------------------------------------------------------

    def analyze(self, prices: pd.Series) -> SpreadMetrics:
        """
        Compute comprehensive spread metrics from a price Series.

        Parameters
        ----------
        prices : pd.Series
            Electricity prices ($/MWh) with a datetime index.
        """
        arr = np.asarray(prices.values, dtype=float)
        daily = self.daily_spreads(arr)

        spread_by_dur: Dict[str, float] = {}
        for d in DURATION_HOURS:
            rs = self.rolling_spread(arr, float(d))
            spread_by_dur[f"{d}h"] = round(float(np.mean(rs)), 4)

        return SpreadMetrics(
            mean_daily_spread=round(float(np.mean(daily)), 4),
            median_daily_spread=round(float(np.median(daily)), 4),
            p25_daily_spread=round(float(np.percentile(daily, 25)), 4),
            p75_daily_spread=round(float(np.percentile(daily, 75)), 4),
            max_daily_spread=round(float(np.max(daily)), 4),
            mean_price=round(float(np.mean(arr)), 4),
            std_price=round(float(np.std(arr)), 4),
            min_price=round(float(np.min(arr)), 4),
            max_price=round(float(np.max(arr)), 4),
            n_days=len(daily),
            spread_per_duration=spread_by_dur,
        )

    # ------------------------------------------------------------------
    # Duration comparison
    # ------------------------------------------------------------------

    def duration_comparison_table(self, prices: np.ndarray) -> pd.DataFrame:
        """
        Compare spread metrics for 1h / 2h / 4h / 8h battery durations.

        Columns: mean_spread, median_spread, p75_spread, max_spread (all $/MWh).
        """
        rows = []
        for dur in DURATION_HOURS:
            rs = self.rolling_spread(prices, float(dur))
            rows.append(
                {
                    "duration_h": dur,
                    "mean_spread_per_mwh": round(float(np.mean(rs)), 4),
                    "median_spread_per_mwh": round(float(np.median(rs)), 4),
                    "p75_spread_per_mwh": round(float(np.percentile(rs, 75)), 4),
                    "max_spread_per_mwh": round(float(np.max(rs)), 4),
                }
            )
        return pd.DataFrame(rows).set_index("duration_h")

    # ------------------------------------------------------------------
    # Optimal window finder
    # ------------------------------------------------------------------

    def optimal_charge_windows(
        self,
        prices: np.ndarray,
        n_windows: int = 3,
        window_h: float = 4.0,
    ) -> List[Dict]:
        """
        Find the N best charge windows (lowest mean price) and N best
        discharge windows (highest mean price) of duration `window_h`.

        Returns list of dicts with keys:
            type, start_idx, end_idx, mean_price, min_price, max_price.
        """
        steps = max(1, int(round(window_h / self.dt_hours)))
        T = len(prices)
        windows = [
            {
                "start_idx": i,
                "end_idx": i + steps,
                "mean_price": float(np.mean(prices[i : i + steps])),
                "min_price": float(np.min(prices[i : i + steps])),
                "max_price": float(np.max(prices[i : i + steps])),
            }
            for i in range(max(1, T - steps + 1))
        ]

        charge_wins = sorted(windows, key=lambda w: w["mean_price"])[:n_windows]
        discharge_wins = sorted(windows, key=lambda w: -w["mean_price"])[:n_windows]

        for w in charge_wins:
            w["type"] = "charge"
        for w in discharge_wins:
            w["type"] = "discharge"

        return charge_wins + discharge_wins
