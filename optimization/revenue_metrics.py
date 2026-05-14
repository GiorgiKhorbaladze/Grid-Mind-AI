"""
Revenue metrics for BESS optimization results.

Computes gross revenue, degradation cost, net revenue, and annualised
projections.  Supports multi-duration comparison tables.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Dict


@dataclass
class RevenueResult:
    """Revenue metrics for a single simulation window."""
    gross_revenue_usd: float
    degradation_cost_usd: float
    net_revenue_usd: float
    revenue_per_mwh_capacity: float   # net USD per MWh of nameplate capacity
    revenue_per_efc: float            # net USD per equivalent full cycle
    efc: float
    capacity_mwh: float

    def to_dict(self) -> Dict[str, float]:
        return {
            "gross_revenue_usd": self.gross_revenue_usd,
            "degradation_cost_usd": self.degradation_cost_usd,
            "net_revenue_usd": self.net_revenue_usd,
            "revenue_per_mwh_capacity": self.revenue_per_mwh_capacity,
            "revenue_per_efc": self.revenue_per_efc,
            "efc": self.efc,
            "capacity_mwh": self.capacity_mwh,
        }


class RevenueMetrics:
    """
    Calculates revenue, cost, and profitability metrics for BESS dispatch.

    Parameters
    ----------
    capacity_mwh : float
        Nameplate battery capacity (MWh).
    replacement_cost_per_mwh : float
        All-in replacement cost (USD / MWh).
    cycle_life : int
        Full cycles to EOL.
    eol_soh : float
        End-of-life state-of-health (fraction).
    """

    def __init__(
        self,
        capacity_mwh: float,
        replacement_cost_per_mwh: float = 250_000.0,
        cycle_life: int = 4_000,
        eol_soh: float = 0.80,
    ) -> None:
        self.capacity_mwh = capacity_mwh
        self.replacement_cost_per_mwh = replacement_cost_per_mwh
        self.cycle_life = cycle_life
        self.eol_soh = eol_soh
        self._deg_cost_per_efc = self._compute_deg_cost_per_efc()

    def _compute_deg_cost_per_efc(self) -> float:
        total_cost = self.replacement_cost_per_mwh * self.capacity_mwh
        usable_fraction = 1.0 - self.eol_soh   # capacity fraction consumed over lifetime
        return (total_cost * usable_fraction) / self.cycle_life

    # ------------------------------------------------------------------
    # Core computation
    # ------------------------------------------------------------------

    def compute(
        self,
        prices: np.ndarray,
        charge_mwh: np.ndarray,
        discharge_mwh: np.ndarray,
    ) -> RevenueResult:
        """
        Compute revenue metrics from a resolved dispatch schedule.

        Parameters
        ----------
        prices : np.ndarray
            Electricity prices ($/MWh), length T.
        charge_mwh : np.ndarray
            Energy charged from grid each step (MWh), length T.
        discharge_mwh : np.ndarray
            Energy discharged to grid each step (MWh), length T.
        """
        gross = float(np.dot(prices, discharge_mwh - charge_mwh))
        efc = float(np.sum(discharge_mwh)) / self.capacity_mwh if self.capacity_mwh > 0 else 0.0
        deg_cost = self._deg_cost_per_efc * efc
        net = gross - deg_cost
        rev_per_mwh = net / self.capacity_mwh if self.capacity_mwh > 0 else 0.0
        rev_per_efc = net / efc if efc > 1e-9 else 0.0

        return RevenueResult(
            gross_revenue_usd=round(gross, 4),
            degradation_cost_usd=round(deg_cost, 4),
            net_revenue_usd=round(net, 4),
            revenue_per_mwh_capacity=round(rev_per_mwh, 4),
            revenue_per_efc=round(rev_per_efc, 4),
            efc=round(efc, 6),
            capacity_mwh=self.capacity_mwh,
        )

    # ------------------------------------------------------------------
    # Annualisation
    # ------------------------------------------------------------------

    def annualize(
        self,
        result: RevenueResult,
        simulation_days: float,
    ) -> Dict[str, float]:
        """Scale simulation-window metrics to annual figures."""
        if simulation_days <= 0:
            raise ValueError("simulation_days must be positive.")
        scale = 365.0 / simulation_days
        return {
            "annual_gross_revenue_usd": round(result.gross_revenue_usd * scale, 2),
            "annual_degradation_cost_usd": round(result.degradation_cost_usd * scale, 2),
            "annual_net_revenue_usd": round(result.net_revenue_usd * scale, 2),
            "annual_efc": round(result.efc * scale, 4),
            "annual_revenue_per_mwh_usd": round(result.revenue_per_mwh_capacity * scale, 2),
            "simulation_days": simulation_days,
            "capacity_mwh": self.capacity_mwh,
        }

    # ------------------------------------------------------------------
    # Multi-duration comparison
    # ------------------------------------------------------------------

    def duration_comparison(
        self,
        prices: np.ndarray,
        schedules: Dict[str, Dict],
    ) -> pd.DataFrame:
        """
        Build a revenue comparison table across battery durations.

        Parameters
        ----------
        prices : np.ndarray
            Electricity prices ($/MWh), length T.
        schedules : dict
            Keyed by duration label (e.g. "1h"), each value a dict with:
              capacity_mwh, charge_mwh, discharge_mwh.

        Returns
        -------
        pd.DataFrame indexed by duration label with revenue columns.
        """
        rows = []
        for label, sched in schedules.items():
            cap = sched["capacity_mwh"]
            rm = RevenueMetrics(
                cap,
                self.replacement_cost_per_mwh,
                self.cycle_life,
                self.eol_soh,
            )
            rv = rm.compute(prices, sched["charge_mwh"], sched["discharge_mwh"])
            rows.append(
                {
                    "duration": label,
                    "capacity_mwh": cap,
                    "gross_revenue_usd": rv.gross_revenue_usd,
                    "degradation_cost_usd": rv.degradation_cost_usd,
                    "net_revenue_usd": rv.net_revenue_usd,
                    "efc": rv.efc,
                    "net_revenue_per_mwh_usd": rv.revenue_per_mwh_capacity,
                    "revenue_per_efc_usd": rv.revenue_per_efc,
                }
            )
        return pd.DataFrame(rows).set_index("duration")
