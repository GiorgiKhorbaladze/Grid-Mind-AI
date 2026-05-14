"""
Battery capacity degradation model.

Models linear capacity fade as a function of equivalent full cycles (EFC)
and depth-of-discharge (DoD) stress.  Parameters are calibrated for
commercial Li-ion BESS (NMC / LFP chemistry range).

Key relationship
----------------
capacity_fade_per_EFC = nominal_capacity × (1 - EOL_SoH) / cycle_life

DoD stress factor scales the fade rate for partial-depth cycling:
  stress(DoD) = DoD ^ dod_exponent
where dod_exponent > 1 means deep cycling degrades faster per MWh throughput.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class DegradationParams:
    """
    Degradation model parameters.

    Attributes
    ----------
    cycle_life : int
        Full cycles (100 % DoD) to reach EOL SoH.  Typical Li-ion: 3 000–6 000.
    eol_soh : float
        End-of-life state-of-health fraction (e.g. 0.80 = 80 % capacity remaining).
    replacement_cost_per_mwh : float
        All-in installed replacement cost (USD / MWh of nameplate capacity).
    dod_exponent : float
        Stress exponent for depth-of-discharge.  1.0 = linear; >1 = super-linear
        penalty for deep cycles (empirically ~1.2 for NMC, ~1.0 for LFP).
    """
    cycle_life: int = 4_000
    eol_soh: float = 0.80
    replacement_cost_per_mwh: float = 250_000.0
    dod_exponent: float = 1.2


class DegradationModel:
    """
    Linearised cycle-degradation model for Li-ion BESS.

    Capacity fade is proportional to EFC throughput, optionally weighted
    by DoD stress.  No calendar aging term (conservatively useful for
    high-utilisation assets where cycle aging dominates).

    Parameters
    ----------
    capacity_mwh : float
        Nameplate energy capacity (MWh).
    params : DegradationParams, optional
        Model parameters.  Defaults to typical Li-ion values.
    """

    def __init__(
        self,
        capacity_mwh: float,
        params: DegradationParams = None,
    ) -> None:
        self.capacity_mwh = capacity_mwh
        self.params = params or DegradationParams()
        self._precompute()

    def _precompute(self) -> None:
        p = self.params
        # MWh of capacity lost per EFC at 100 % DoD
        total_fade_mwh = self.capacity_mwh * (1.0 - p.eol_soh)
        self.capacity_fade_per_efc_mwh: float = total_fade_mwh / p.cycle_life

        # USD cost per EFC at 100 % DoD
        total_replacement_usd = p.replacement_cost_per_mwh * self.capacity_mwh
        self.degradation_cost_per_efc_usd: float = (
            total_replacement_usd * (1.0 - p.eol_soh) / p.cycle_life
        )

    # ------------------------------------------------------------------
    # State-of-health
    # ------------------------------------------------------------------

    def capacity_after_cycles(self, efc: float) -> float:
        """Remaining capacity (MWh) after `efc` equivalent full cycles."""
        remaining = self.capacity_mwh - self.capacity_fade_per_efc_mwh * efc
        return max(self.capacity_mwh * self.params.eol_soh, remaining)

    def soh(self, efc: float) -> float:
        """State-of-health (0–1) after `efc` equivalent full cycles."""
        return self.capacity_after_cycles(efc) / self.capacity_mwh

    def cycles_to_eol(self, current_efc: float = 0.0) -> float:
        """Remaining EFC budget before end-of-life from current position."""
        return max(0.0, float(self.params.cycle_life) - current_efc)

    # ------------------------------------------------------------------
    # DoD stress
    # ------------------------------------------------------------------

    def dod_stress_factor(self, avg_dod: float) -> float:
        """
        Multiplier that scales degradation cost for partial-depth cycling.

        At avg_dod = 1.0 (full depth) the factor equals 1.0.
        At avg_dod < 1.0 the factor is < 1.0 (shallower → less damage per cycle).
        """
        dod = max(0.01, min(1.0, float(avg_dod)))  # clamp to (0, 1]
        return dod ** self.params.dod_exponent

    # ------------------------------------------------------------------
    # Cost calculation
    # ------------------------------------------------------------------

    def degradation_cost(
        self,
        efc: float,
        avg_dod: float = 1.0,
    ) -> float:
        """
        Total degradation cost (USD) for `efc` equivalent full cycles
        at the given average depth-of-discharge.
        """
        stress = self.dod_stress_factor(avg_dod)
        return self.degradation_cost_per_efc_usd * efc * stress

    # ------------------------------------------------------------------
    # Full metrics dict
    # ------------------------------------------------------------------

    def compute_metrics(
        self,
        efc: float,
        avg_dod: float = 1.0,
    ) -> Dict[str, float]:
        """Return a complete degradation metrics dictionary."""
        return {
            "equivalent_full_cycles": round(efc, 6),
            "avg_dod": round(avg_dod, 6),
            "dod_stress_factor": round(self.dod_stress_factor(avg_dod), 6),
            "soh_pct": round(self.soh(efc) * 100.0, 4),
            "capacity_remaining_mwh": round(self.capacity_after_cycles(efc), 6),
            "degradation_cost_usd": round(self.degradation_cost(efc, avg_dod), 4),
            "capacity_fade_per_efc_mwh": round(self.capacity_fade_per_efc_mwh, 8),
            "degradation_cost_per_efc_usd": round(self.degradation_cost_per_efc_usd, 4),
            "cycles_to_eol": round(self.cycles_to_eol(efc), 2),
            "cycle_life": self.params.cycle_life,
            "eol_soh_pct": round(self.params.eol_soh * 100.0, 1),
        }
