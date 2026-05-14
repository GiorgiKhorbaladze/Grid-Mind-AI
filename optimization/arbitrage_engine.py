"""
BESS price arbitrage optimizer using Pyomo LP.

LP formulation
--------------
maximize  Σ_t  price[t] * (discharge[t] - charge[t])

subject to:
  soc[t+1] = soc[t] + η_c·charge[t] - discharge[t]/η_d    ∀ t
  soc[0]   = soc_initial
  soc_min  ≤ soc[t] ≤ soc_max                              ∀ t
  0        ≤ charge[t]    ≤ P_max·Δt                       ∀ t
  0        ≤ discharge[t] ≤ P_max·Δt                       ∀ t

Variables: charge[t], discharge[t] in MWh; soc[t] in MWh.
The LP never simultaneously charges and discharges at optimum
because that would reduce rather than increase objective value.
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, Optional

from pyomo.environ import (
    ConcreteModel,
    RangeSet,
    Var,
    Objective,
    Constraint,
    NonNegativeReals,
    maximize,
    value,
    SolverFactory,
)
from pyomo.opt import TerminationCondition


_SOLVER_PREFERENCE = ["glpk", "highs", "cbc"]
_ZERO_THRESHOLD = 1e-8  # values below this treated as 0


def _find_solver() -> str:
    for name in _SOLVER_PREFERENCE:
        if SolverFactory(name).available():
            return name
    raise RuntimeError(
        f"No LP solver found. Install one of: {_SOLVER_PREFERENCE}. "
        "Recommended: `conda install -c conda-forge glpk` or `pip install highspy`."
    )


class ArbitrageEngine:
    """
    LP-based BESS arbitrage optimizer.

    Finds the charge/discharge schedule that maximises revenue from
    price arbitrage subject to battery physical constraints.

    Parameters
    ----------
    capacity_mwh : float
        Usable energy capacity (MWh).
    power_mw : float
        Maximum charge / discharge power (MW).
    eta_roundtrip : float
        Round-trip efficiency (0–1). Split symmetrically:
        η_c = η_d = √η_roundtrip.
    soc_min_frac : float
        Minimum state-of-charge as fraction of capacity.
    soc_max_frac : float
        Maximum state-of-charge as fraction of capacity.
    soc_initial_frac : float
        Initial state-of-charge as fraction of capacity.
    dt_hours : float
        Duration of each time step in hours.
    solver : str, optional
        Pyomo solver name. Auto-detected if omitted.
    """

    def __init__(
        self,
        capacity_mwh: float,
        power_mw: float,
        eta_roundtrip: float = 0.92,
        soc_min_frac: float = 0.05,
        soc_max_frac: float = 0.95,
        soc_initial_frac: float = 0.50,
        dt_hours: float = 1.0,
        solver: Optional[str] = None,
    ) -> None:
        self.capacity_mwh = capacity_mwh
        self.power_mw = power_mw
        self.eta_roundtrip = eta_roundtrip
        self.eta_c = np.sqrt(eta_roundtrip)   # charging efficiency
        self.eta_d = np.sqrt(eta_roundtrip)   # discharging efficiency
        self.soc_min = capacity_mwh * soc_min_frac
        self.soc_max = capacity_mwh * soc_max_frac
        self.soc_initial = capacity_mwh * soc_initial_frac
        self.dt_hours = dt_hours
        self.solver_name = solver or _find_solver()

    # ------------------------------------------------------------------
    # Model construction
    # ------------------------------------------------------------------

    def _build_model(self, prices: np.ndarray) -> ConcreteModel:
        T = len(prices)
        energy_limit = self.power_mw * self.dt_hours  # max MWh per step
        eta_c, eta_d = self.eta_c, self.eta_d

        m = ConcreteModel()
        m.T = RangeSet(0, T - 1)
        m.T1 = RangeSet(0, T)   # SOC indexed 0 … T

        m.charge = Var(
            m.T, domain=NonNegativeReals, bounds=(0.0, energy_limit)
        )
        m.discharge = Var(
            m.T, domain=NonNegativeReals, bounds=(0.0, energy_limit)
        )
        m.soc = Var(
            m.T1,
            domain=NonNegativeReals,
            bounds=(self.soc_min, self.soc_max),
        )

        # Objective
        m.objective = Objective(
            expr=sum(prices[t] * (m.discharge[t] - m.charge[t]) for t in m.T),
            sense=maximize,
        )

        # Initial SOC
        m.soc_init = Constraint(expr=m.soc[0] == self.soc_initial)

        # SOC dynamics
        def _dynamics(model, t):
            return (
                model.soc[t + 1]
                == model.soc[t]
                + eta_c * model.charge[t]
                - model.discharge[t] / eta_d
            )

        m.soc_dynamics = Constraint(m.T, rule=_dynamics)

        return m

    # ------------------------------------------------------------------
    # Solve
    # ------------------------------------------------------------------

    def optimize(self, prices: np.ndarray) -> Dict[str, Any]:
        """
        Solve the arbitrage LP for the given price series.

        Parameters
        ----------
        prices : np.ndarray
            Electricity prices in $/MWh, length T.

        Returns
        -------
        dict with keys:
            charge_mwh, discharge_mwh, soc_mwh  – np.ndarray
            gross_revenue_usd                    – float
            prices_per_mwh                       – np.ndarray
            capacity_mwh, power_mw, eta_roundtrip – float
            solver, solver_status, termination_condition – str
            n_periods, dt_hours                  – numeric
        """
        prices = np.asarray(prices, dtype=float)
        T = len(prices)

        model = self._build_model(prices)
        opt = SolverFactory(self.solver_name)
        result = opt.solve(model, tee=False)

        tc = result.solver.termination_condition
        if tc not in (TerminationCondition.optimal, TerminationCondition.feasible):
            raise RuntimeError(
                f"Solver '{self.solver_name}' failed. "
                f"Status: {result.solver.status}, "
                f"Termination: {tc}"
            )

        charge_mwh = np.array(
            [max(0.0, value(model.charge[t])) for t in range(T)]
        )
        discharge_mwh = np.array(
            [max(0.0, value(model.discharge[t])) for t in range(T)]
        )
        soc_mwh = np.array(
            [value(model.soc[t]) for t in range(T + 1)]
        )

        # Zero out numerical noise
        charge_mwh[charge_mwh < _ZERO_THRESHOLD] = 0.0
        discharge_mwh[discharge_mwh < _ZERO_THRESHOLD] = 0.0

        gross_revenue = float(np.dot(prices, discharge_mwh - charge_mwh))

        return {
            "charge_mwh": charge_mwh,
            "discharge_mwh": discharge_mwh,
            "soc_mwh": soc_mwh,
            "gross_revenue_usd": round(gross_revenue, 4),
            "prices_per_mwh": prices,
            "capacity_mwh": self.capacity_mwh,
            "power_mw": self.power_mw,
            "eta_roundtrip": self.eta_roundtrip,
            "solver": self.solver_name,
            "solver_status": str(result.solver.status),
            "termination_condition": str(tc),
            "n_periods": T,
            "dt_hours": self.dt_hours,
        }

    # ------------------------------------------------------------------
    # Convenience: return as DataFrame
    # ------------------------------------------------------------------

    def optimize_series(self, prices: pd.Series) -> pd.DataFrame:
        """
        Optimize and return the schedule as a labelled DataFrame.

        Index matches the input Series index (timestamps).
        Columns: price_per_mwh, charge_mwh, discharge_mwh, net_mwh,
                 soc_mwh, soc_pct, period_revenue_usd.
        """
        raw = self.optimize(prices.values)
        T = len(prices)
        net = raw["discharge_mwh"] - raw["charge_mwh"]

        return pd.DataFrame(
            {
                "price_per_mwh": raw["prices_per_mwh"],
                "charge_mwh": raw["charge_mwh"],
                "discharge_mwh": raw["discharge_mwh"],
                "net_mwh": net,
                "soc_mwh": raw["soc_mwh"][:T],
                "soc_pct": raw["soc_mwh"][:T] / self.capacity_mwh * 100.0,
                "period_revenue_usd": raw["prices_per_mwh"] * net,
            },
            index=prices.index[:T],
        )
