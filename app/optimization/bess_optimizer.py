"""BESS optimizer with mathematical-programming and heuristic fallbacks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class BessConfig:
    """Battery energy storage system parameters."""

    power_mw: float = 10.0
    energy_mwh: float = 20.0
    round_trip_efficiency: float = 0.88
    initial_soc_mwh: float | None = None

    def __post_init__(self) -> None:
        if self.power_mw <= 0:
            raise ValueError("power_mw must be positive")
        if self.energy_mwh <= 0:
            raise ValueError("energy_mwh must be positive")
        if not 0 < self.round_trip_efficiency <= 1:
            raise ValueError("round_trip_efficiency must be in (0, 1]")


@dataclass(frozen=True)
class OptimizationSummary:
    """Aggregate output for a BESS dispatch run."""

    objective_eur: float
    charged_mwh: float
    discharged_mwh: float
    cycles_equivalent: float
    method: Literal["pyomo", "heuristic"]


def optimize_bess(market_data: pd.DataFrame, config: BessConfig | None = None) -> tuple[pd.DataFrame, OptimizationSummary]:
    """Optimize BESS dispatch against electricity prices.

    Pyomo + GLPK is used when both are installed and usable. Otherwise a
    deterministic percentile-based arbitrage heuristic is used.
    """

    cfg = config or BessConfig()
    prices = pd.to_numeric(market_data["price_eur_mwh"], errors="coerce").fillna(0).to_numpy(dtype=float)
    if len(prices) == 0:
        empty = market_data.copy()
        for column in ["charge_mw", "discharge_mw", "soc_mwh", "revenue_eur"]:
            empty[column] = []
        return empty, OptimizationSummary(0.0, 0.0, 0.0, 0.0, "heuristic")

    pyomo_result = _try_pyomo(prices, cfg)
    if pyomo_result is None:
        dispatch, summary = _heuristic_dispatch(prices, cfg)
    else:
        dispatch, summary = pyomo_result

    result = market_data.reset_index(drop=True).copy()
    result["charge_mw"] = dispatch["charge_mw"]
    result["discharge_mw"] = dispatch["discharge_mw"]
    result["soc_mwh"] = dispatch["soc_mwh"]
    result["revenue_eur"] = dispatch["revenue_eur"]
    return result, summary


def _initial_soc(config: BessConfig) -> float:
    return config.energy_mwh / 2 if config.initial_soc_mwh is None else min(max(config.initial_soc_mwh, 0), config.energy_mwh)


def _try_pyomo(prices: np.ndarray, config: BessConfig) -> tuple[pd.DataFrame, OptimizationSummary] | None:
    try:
        import pyomo.environ as pyo
    except ImportError:
        return None

    solver = pyo.SolverFactory("glpk")
    if solver is None or not solver.available(exception_flag=False):
        return None

    n = len(prices)
    charge_eff = np.sqrt(config.round_trip_efficiency)
    discharge_eff = np.sqrt(config.round_trip_efficiency)
    initial_soc = _initial_soc(config)

    model = pyo.ConcreteModel()
    model.t = pyo.RangeSet(0, n - 1)
    model.charge = pyo.Var(model.t, bounds=(0, config.power_mw))
    model.discharge = pyo.Var(model.t, bounds=(0, config.power_mw))
    model.soc = pyo.Var(model.t, bounds=(0, config.energy_mwh))

    def soc_rule(m, t):
        previous_soc = initial_soc if t == 0 else m.soc[t - 1]
        return m.soc[t] == previous_soc + charge_eff * m.charge[t] - m.discharge[t] / discharge_eff

    model.soc_balance = pyo.Constraint(model.t, rule=soc_rule)
    model.objective = pyo.Objective(
        expr=sum(prices[t] * (model.discharge[t] - model.charge[t]) for t in range(n)),
        sense=pyo.maximize,
    )

    try:
        result = solver.solve(model, tee=False)
    except Exception:
        return None
    if result.solver.termination_condition != pyo.TerminationCondition.optimal:
        return None

    charge = np.array([pyo.value(model.charge[t]) for t in range(n)])
    discharge = np.array([pyo.value(model.discharge[t]) for t in range(n)])
    soc = np.array([pyo.value(model.soc[t]) for t in range(n)])
    revenue = prices * (discharge - charge)
    dispatch = pd.DataFrame({"charge_mw": charge, "discharge_mw": discharge, "soc_mwh": soc, "revenue_eur": revenue})
    return dispatch, _summary(dispatch, "pyomo", config)


def _heuristic_dispatch(prices: np.ndarray, config: BessConfig) -> tuple[pd.DataFrame, OptimizationSummary]:
    low = np.nanpercentile(prices, 35)
    high = np.nanpercentile(prices, 65)
    charge_eff = np.sqrt(config.round_trip_efficiency)
    discharge_eff = np.sqrt(config.round_trip_efficiency)
    soc = _initial_soc(config)
    rows = []

    for price in prices:
        charge = 0.0
        discharge = 0.0
        if price <= low and soc < config.energy_mwh:
            charge = min(config.power_mw, (config.energy_mwh - soc) / charge_eff)
            soc += charge * charge_eff
        elif price >= high and soc > 0:
            discharge = min(config.power_mw, soc * discharge_eff)
            soc -= discharge / discharge_eff
        revenue = price * (discharge - charge)
        rows.append({"charge_mw": charge, "discharge_mw": discharge, "soc_mwh": soc, "revenue_eur": revenue})

    dispatch = pd.DataFrame(rows)
    return dispatch, _summary(dispatch, "heuristic", config)


def _summary(dispatch: pd.DataFrame, method: Literal["pyomo", "heuristic"], config: BessConfig) -> OptimizationSummary:
    charged = float(dispatch["charge_mw"].sum())
    discharged = float(dispatch["discharge_mw"].sum())
    revenue = float(dispatch["revenue_eur"].sum())
    cycles = discharged / config.energy_mwh if config.energy_mwh else 0.0
    return OptimizationSummary(
        objective_eur=round(revenue, 2),
        charged_mwh=round(charged, 3),
        discharged_mwh=round(discharged, 3),
        cycles_equivalent=round(cycles, 3),
        method=method,
    )
