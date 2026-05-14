"""
Rule-based charging / discharging heuristics for BESS.

Used as a deterministic baseline or for real-time dispatch
when running a full LP is impractical.

Three dispatch strategies
--------------------------
threshold  – charge below a fixed low price, discharge above a fixed high price
percentile – derive thresholds from the price distribution
valley_peak – charge during fixed off-peak hours, discharge during peak hours
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass
class ChargingParams:
    """Physical parameters shared across all strategies."""
    capacity_mwh: float
    power_mw: float
    eta_roundtrip: float = 0.92
    soc_min_frac: float = 0.05
    soc_max_frac: float = 0.95
    soc_initial_frac: float = 0.50
    dt_hours: float = 1.0

    @property
    def eta_c(self) -> float:
        return float(np.sqrt(self.eta_roundtrip))

    @property
    def eta_d(self) -> float:
        return float(np.sqrt(self.eta_roundtrip))

    @property
    def soc_min(self) -> float:
        return self.capacity_mwh * self.soc_min_frac

    @property
    def soc_max(self) -> float:
        return self.capacity_mwh * self.soc_max_frac

    @property
    def soc_initial(self) -> float:
        return self.capacity_mwh * self.soc_initial_frac

    @property
    def energy_per_step(self) -> float:
        return self.power_mw * self.dt_hours


# Return type alias: (charge_mwh, discharge_mwh, soc_mwh)
Schedule = Tuple[np.ndarray, np.ndarray, np.ndarray]


class ChargingLogic:
    """
    Deterministic rule-based charging heuristics.

    All strategies simulate forward in time with physically consistent
    SOC tracking.  No look-ahead beyond thresholds derived from the
    full price series (acceptable for backtesting; flag as look-ahead
    for real-time use with rolling windows instead).
    """

    def __init__(self, params: ChargingParams) -> None:
        self.p = params

    # ------------------------------------------------------------------
    # Internal SOC step
    # ------------------------------------------------------------------

    def _step_soc(
        self,
        soc: float,
        charge: float,
        discharge: float,
    ) -> float:
        """Apply one time-step of SOC dynamics and clip to bounds."""
        new_soc = soc + charge * self.p.eta_c - discharge / self.p.eta_d
        return float(np.clip(new_soc, self.p.soc_min, self.p.soc_max))

    # ------------------------------------------------------------------
    # Strategy 1: fixed-threshold
    # ------------------------------------------------------------------

    def threshold_dispatch(
        self,
        prices: np.ndarray,
        low_threshold: float,
        high_threshold: float,
    ) -> Schedule:
        """
        Charge when price < low_threshold; discharge when price > high_threshold.

        Returns
        -------
        charge_mwh, discharge_mwh, soc_mwh : np.ndarray
            charge and discharge arrays length T; soc array length T+1.
        """
        T = len(prices)
        p = self.p
        charge = np.zeros(T)
        discharge = np.zeros(T)
        soc = np.zeros(T + 1)
        soc[0] = p.soc_initial

        for t in range(T):
            # Maximum energy that can be absorbed / delivered this step
            max_chargeable = (p.soc_max - soc[t]) / p.eta_c
            max_dischargeable = (soc[t] - p.soc_min) * p.eta_d

            if prices[t] < low_threshold and max_chargeable > 0:
                charge[t] = min(p.energy_per_step, max_chargeable)
            elif prices[t] > high_threshold and max_dischargeable > 0:
                discharge[t] = min(p.energy_per_step, max_dischargeable)

            soc[t + 1] = self._step_soc(soc[t], charge[t], discharge[t])

        return charge, discharge, soc

    # ------------------------------------------------------------------
    # Strategy 2: percentile thresholds
    # ------------------------------------------------------------------

    def percentile_dispatch(
        self,
        prices: np.ndarray,
        low_pct: float = 25.0,
        high_pct: float = 75.0,
    ) -> Schedule:
        """
        Derive thresholds from the Nth percentile of the price series,
        then apply threshold dispatch.
        """
        low_thresh = float(np.percentile(prices, low_pct))
        high_thresh = float(np.percentile(prices, high_pct))
        return self.threshold_dispatch(prices, low_thresh, high_thresh)

    # ------------------------------------------------------------------
    # Strategy 3: time-of-use valley / peak
    # ------------------------------------------------------------------

    def valley_peak_dispatch(
        self,
        prices: np.ndarray,
        valley_hours: Tuple[int, int] = (0, 6),
        peak_hours: Tuple[int, int] = (16, 21),
    ) -> Schedule:
        """
        Charge during valley hours, discharge during peak hours.

        Hours are clock hours (0–23).  Works with any dt_hours by
        computing the clock hour of each step from the step index.
        """
        T = len(prices)
        p = self.p
        charge = np.zeros(T)
        discharge = np.zeros(T)
        soc = np.zeros(T + 1)
        soc[0] = p.soc_initial

        for t in range(T):
            hour = int((t * p.dt_hours) % 24)
            max_chargeable = (p.soc_max - soc[t]) / p.eta_c
            max_dischargeable = (soc[t] - p.soc_min) * p.eta_d

            in_valley = valley_hours[0] <= hour < valley_hours[1]
            in_peak = peak_hours[0] <= hour < peak_hours[1]

            if in_valley and max_chargeable > 0:
                charge[t] = min(p.energy_per_step, max_chargeable)
            elif in_peak and max_dischargeable > 0:
                discharge[t] = min(p.energy_per_step, max_dischargeable)

            soc[t + 1] = self._step_soc(soc[t], charge[t], discharge[t])

        return charge, discharge, soc

    # ------------------------------------------------------------------
    # Revenue helper
    # ------------------------------------------------------------------

    def compute_revenue(
        self,
        prices: np.ndarray,
        charge_mwh: np.ndarray,
        discharge_mwh: np.ndarray,
    ) -> float:
        """Gross revenue (USD) for a given dispatch schedule."""
        return float(np.dot(prices, discharge_mwh - charge_mwh))

    # ------------------------------------------------------------------
    # Schedule → DataFrame
    # ------------------------------------------------------------------

    def to_dataframe(
        self,
        prices: np.ndarray,
        charge_mwh: np.ndarray,
        discharge_mwh: np.ndarray,
        soc_mwh: np.ndarray,
        index: pd.Index = None,
    ) -> pd.DataFrame:
        T = len(prices)
        net = discharge_mwh - charge_mwh
        df = pd.DataFrame(
            {
                "price_per_mwh": prices,
                "charge_mwh": charge_mwh,
                "discharge_mwh": discharge_mwh,
                "net_mwh": net,
                "soc_mwh": soc_mwh[:T],
                "soc_pct": soc_mwh[:T] / self.p.capacity_mwh * 100.0,
                "period_revenue_usd": prices * net,
            }
        )
        if index is not None:
            df.index = index[:T]
        return df
