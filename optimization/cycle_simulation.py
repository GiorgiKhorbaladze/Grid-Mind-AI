"""
Battery cycle simulation.

Tracks energy throughput and computes equivalent full cycles (EFC),
depth-of-discharge statistics, and annual throughput projections.

EFC = total discharged energy (MWh) / nominal capacity (MWh).
This is the standard industry metric for Li-ion cycle counting.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class CycleStats:
    """Results from a single simulation window."""
    equivalent_full_cycles: float
    total_charged_mwh: float
    total_discharged_mwh: float
    total_throughput_mwh: float     # charged + discharged
    avg_depth_of_discharge: float   # fraction of capacity, 0–1
    max_depth_of_discharge: float
    n_discharge_events: int

    def to_dict(self) -> Dict[str, float]:
        return {
            "equivalent_full_cycles": self.equivalent_full_cycles,
            "total_charged_mwh": self.total_charged_mwh,
            "total_discharged_mwh": self.total_discharged_mwh,
            "total_throughput_mwh": self.total_throughput_mwh,
            "avg_depth_of_discharge": self.avg_depth_of_discharge,
            "max_depth_of_discharge": self.max_depth_of_discharge,
            "n_discharge_events": self.n_discharge_events,
        }


class CycleSimulator:
    """
    Derives cycling statistics from a resolved charge/discharge schedule.

    Parameters
    ----------
    capacity_mwh : float
        Nominal battery capacity (MWh).
    """

    def __init__(self, capacity_mwh: float) -> None:
        self.capacity_mwh = capacity_mwh

    # ------------------------------------------------------------------
    # Primary metric
    # ------------------------------------------------------------------

    def compute_cycle_stats(
        self,
        charge_mwh: np.ndarray,
        discharge_mwh: np.ndarray,
        soc_mwh: np.ndarray,
    ) -> CycleStats:
        """
        Compute cycle statistics from a charge/discharge profile.

        Parameters
        ----------
        charge_mwh : array of length T
        discharge_mwh : array of length T
        soc_mwh : array of length T+1  (soc[0] … soc[T])
        """
        total_discharged = float(np.sum(discharge_mwh))
        total_charged = float(np.sum(charge_mwh))
        efc = total_discharged / self.capacity_mwh if self.capacity_mwh > 0 else 0.0

        dod_values = self._extract_dod_events(soc_mwh)
        avg_dod = float(np.mean(dod_values)) if dod_values else 0.0
        max_dod = float(np.max(dod_values)) if dod_values else 0.0

        return CycleStats(
            equivalent_full_cycles=round(efc, 6),
            total_charged_mwh=round(total_charged, 6),
            total_discharged_mwh=round(total_discharged, 6),
            total_throughput_mwh=round(total_charged + total_discharged, 6),
            avg_depth_of_discharge=round(avg_dod, 6),
            max_depth_of_discharge=round(max_dod, 6),
            n_discharge_events=len(dod_values),
        )

    # ------------------------------------------------------------------
    # DoD event extraction
    # ------------------------------------------------------------------

    def _extract_dod_events(self, soc_mwh: np.ndarray) -> List[float]:
        """
        Identify individual discharge events from the SOC trajectory.

        A discharge event begins when SOC decreases for the first time and
        ends when SOC stops decreasing. Returns fractional DoD per event.
        """
        dod_list: List[float] = []
        in_discharge = False
        soc_peak = 0.0

        for i in range(1, len(soc_mwh)):
            delta = soc_mwh[i] - soc_mwh[i - 1]

            if delta < -1e-9:                       # SOC falling → discharging
                if not in_discharge:
                    soc_peak = soc_mwh[i - 1]
                    in_discharge = True
            else:                                   # SOC flat or rising
                if in_discharge:
                    dod = (soc_peak - soc_mwh[i - 1]) / self.capacity_mwh
                    if dod > 1e-6:
                        dod_list.append(dod)
                    in_discharge = False

        # Close any event that runs to the end of the horizon
        if in_discharge:
            dod = (soc_peak - soc_mwh[-1]) / self.capacity_mwh
            if dod > 1e-6:
                dod_list.append(dod)

        return dod_list

    # ------------------------------------------------------------------
    # Annual projection
    # ------------------------------------------------------------------

    def simulate_annual_throughput(
        self,
        daily_efc: float,
        days: int = 365,
    ) -> Dict[str, float]:
        """
        Project annual energy throughput from a representative daily EFC.

        Parameters
        ----------
        daily_efc : float
            Equivalent full cycles per day.
        days : int
            Number of operating days per year.
        """
        annual_efc = daily_efc * days
        annual_discharged_mwh = annual_efc * self.capacity_mwh
        annual_charged_mwh = annual_discharged_mwh / self.capacity_mwh * self.capacity_mwh

        return {
            "daily_efc": round(daily_efc, 6),
            "annual_efc": round(annual_efc, 4),
            "annual_discharged_mwh": round(annual_discharged_mwh, 4),
            "annual_charged_mwh": round(annual_charged_mwh, 4),
            "capacity_mwh": self.capacity_mwh,
            "operating_days": days,
        }
