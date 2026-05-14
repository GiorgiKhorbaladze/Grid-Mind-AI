"""
BESSOptimizer – main entry point for the GridMind-AI BESS optimization engine.

Orchestrates arbitrage LP, cycle simulation, degradation modelling,
and revenue metrics into a single coherent interface.

Quick start
-----------
    from bess_optimizer import BESSOptimizer, BESSConfig
    from data.sample_prices import generate_day_ahead_prices

    prices = generate_day_ahead_prices(days=7)
    optimizer = BESSOptimizer(BESSConfig(power_mw=1.0))

    # Optimal schedule for a 4-hour battery
    result = optimizer.optimize(prices, capacity_mwh=4.0)
    print(result["schedule"])

    # Compare 1h / 2h / 4h / 8h durations
    comparison = optimizer.compare_durations(prices)
    print(comparison["comparison_table"])

    # Spread analysis without running the LP
    spread = optimizer.spread_analysis(prices)
"""

import json
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from optimization.arbitrage_engine import ArbitrageEngine
from optimization.charging_logic import ChargingLogic, ChargingParams
from optimization.cycle_simulation import CycleSimulator
from optimization.degradation import DegradationModel, DegradationParams
from optimization.revenue_metrics import RevenueMetrics
from optimization.spread_analysis import SpreadAnalyzer

DURATION_HOURS: List[int] = [1, 2, 4, 8]


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass
class BESSConfig:
    """
    Battery configuration and optimiser settings.

    Attributes
    ----------
    power_mw : float
        Rated charge / discharge power (MW).
    eta_roundtrip : float
        Round-trip efficiency (0–1).  Split symmetrically: η_c = η_d = √η_rt.
    soc_min_frac : float
        Minimum state-of-charge as a fraction of capacity (protects chemistry).
    soc_max_frac : float
        Maximum state-of-charge as a fraction of capacity.
    soc_initial_frac : float
        Starting state-of-charge as a fraction of capacity.
    dt_hours : float
        Duration of each price / dispatch time step (hours).
    cycle_life : int
        Full equivalent cycles to end-of-life (for degradation cost).
    eol_soh : float
        End-of-life state-of-health fraction (e.g. 0.80).
    replacement_cost_per_mwh : float
        All-in installed replacement cost (USD / MWh nameplate).
    solver : str, optional
        Pyomo LP solver name.  Auto-detected if None (prefers glpk → highs → cbc).
    """

    power_mw: float = 1.0
    eta_roundtrip: float = 0.92
    soc_min_frac: float = 0.05
    soc_max_frac: float = 0.95
    soc_initial_frac: float = 0.50
    dt_hours: float = 1.0
    cycle_life: int = 4_000
    eol_soh: float = 0.80
    replacement_cost_per_mwh: float = 250_000.0
    solver: Optional[str] = None


# ---------------------------------------------------------------------------
# Main optimiser class
# ---------------------------------------------------------------------------


class BESSOptimizer:
    """
    Battery Energy Storage System optimiser.

    Integrates LP-based price arbitrage with cycle simulation,
    degradation modelling, and revenue metrics.

    Parameters
    ----------
    config : BESSConfig, optional
        Battery and solver settings.  Uses library defaults if omitted.
    """

    def __init__(self, config: BESSConfig = None) -> None:
        self.config = config or BESSConfig()

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------

    def _engine(self, capacity_mwh: float) -> ArbitrageEngine:
        c = self.config
        return ArbitrageEngine(
            capacity_mwh=capacity_mwh,
            power_mw=c.power_mw,
            eta_roundtrip=c.eta_roundtrip,
            soc_min_frac=c.soc_min_frac,
            soc_max_frac=c.soc_max_frac,
            soc_initial_frac=c.soc_initial_frac,
            dt_hours=c.dt_hours,
            solver=c.solver,
        )

    def _deg_model(self, capacity_mwh: float) -> DegradationModel:
        c = self.config
        return DegradationModel(
            capacity_mwh,
            DegradationParams(
                cycle_life=c.cycle_life,
                eol_soh=c.eol_soh,
                replacement_cost_per_mwh=c.replacement_cost_per_mwh,
            ),
        )

    def _rev_metrics(self, capacity_mwh: float) -> RevenueMetrics:
        c = self.config
        return RevenueMetrics(
            capacity_mwh,
            c.replacement_cost_per_mwh,
            c.cycle_life,
            c.eol_soh,
        )

    # ------------------------------------------------------------------
    # Single-run optimisation
    # ------------------------------------------------------------------

    def optimize(
        self,
        prices: pd.Series,
        capacity_mwh: float,
    ) -> Dict[str, Any]:
        """
        Run the LP arbitrage optimisation for a given battery capacity.

        Parameters
        ----------
        prices : pd.Series
            Hourly electricity prices ($/MWh) with a datetime index.
        capacity_mwh : float
            Energy capacity to optimise for (MWh).

        Returns
        -------
        dict with keys:
            schedule            – pd.DataFrame  (per-period operation table)
            gross_revenue_usd   – float
            degradation_cost_usd– float
            net_revenue_usd     – float
            efc                 – float  (equivalent full cycles)
            cycle_stats         – dict
            degradation         – dict
            annual_projection   – dict
            capacity_mwh        – float
            power_mw            – float
            eta_roundtrip       – float
        """
        engine = self._engine(capacity_mwh)
        raw = engine.optimize(prices.values)

        # Build operation table
        T = len(prices)
        net_mwh = raw["discharge_mwh"] - raw["charge_mwh"]
        schedule = pd.DataFrame(
            {
                "price_per_mwh": raw["prices_per_mwh"],
                "charge_mwh": raw["charge_mwh"],
                "discharge_mwh": raw["discharge_mwh"],
                "net_mwh": net_mwh,
                "soc_mwh": raw["soc_mwh"][:T],
                "soc_pct": raw["soc_mwh"][:T] / capacity_mwh * 100.0,
                "period_revenue_usd": raw["prices_per_mwh"] * net_mwh,
            },
            index=prices.index[:T],
        )

        # Cycle statistics
        cycle_sim = CycleSimulator(capacity_mwh)
        cycle_stats = cycle_sim.compute_cycle_stats(
            raw["charge_mwh"], raw["discharge_mwh"], raw["soc_mwh"]
        )

        # Degradation metrics
        deg_model = self._deg_model(capacity_mwh)
        deg_metrics = deg_model.compute_metrics(
            cycle_stats.equivalent_full_cycles,
            cycle_stats.avg_depth_of_discharge,
        )

        # Revenue metrics
        rev = self._rev_metrics(capacity_mwh)
        rev_result = rev.compute(
            raw["prices_per_mwh"],
            raw["charge_mwh"],
            raw["discharge_mwh"],
        )

        sim_days = len(prices) * self.config.dt_hours / 24.0
        annual = rev.annualize(rev_result, max(sim_days, 1e-9))

        return {
            "schedule": schedule,
            "gross_revenue_usd": rev_result.gross_revenue_usd,
            "degradation_cost_usd": rev_result.degradation_cost_usd,
            "net_revenue_usd": rev_result.net_revenue_usd,
            "efc": rev_result.efc,
            "cycle_stats": cycle_stats.to_dict(),
            "degradation": deg_metrics,
            "annual_projection": annual,
            "capacity_mwh": capacity_mwh,
            "power_mw": self.config.power_mw,
            "eta_roundtrip": self.config.eta_roundtrip,
            "solver": raw["solver"],
            "solver_status": raw["solver_status"],
        }

    # ------------------------------------------------------------------
    # Duration comparison: 1h / 2h / 4h / 8h
    # ------------------------------------------------------------------

    def compare_durations(
        self,
        prices: pd.Series,
        durations_h: List[int] = None,
    ) -> Dict[str, Any]:
        """
        Compare 1h / 2h / 4h / 8h battery durations for the same power rating.

        Each duration maps to a different energy capacity:
            capacity_mwh = power_mw × duration_h

        Parameters
        ----------
        prices : pd.Series
            Electricity prices ($/MWh) with a datetime index.
        durations_h : list of int, optional
            Durations to compare.  Defaults to [1, 2, 4, 8].

        Returns
        -------
        dict with keys:
            comparison_table            – pd.DataFrame  (one row per duration)
            per_duration                – dict of full optimize() results
            best_by_net_revenue         – str  (label of best duration)
            best_by_net_revenue_per_mwh – str
        """
        durations = durations_h or DURATION_HOURS
        per_duration: Dict[str, Dict] = {}
        schedules_for_table: Dict[str, Dict] = {}

        for dur in durations:
            capacity_mwh = self.config.power_mw * dur
            label = f"{dur}h"
            res = self.optimize(prices, capacity_mwh)
            per_duration[label] = res
            schedules_for_table[label] = {
                "capacity_mwh": capacity_mwh,
                "charge_mwh": res["schedule"]["charge_mwh"].values,
                "discharge_mwh": res["schedule"]["discharge_mwh"].values,
            }

        # Build comparison table using the shared revenue_metrics helper
        ref_rev = self._rev_metrics(self.config.power_mw)   # capacity overridden per duration
        table = ref_rev.duration_comparison(prices.values, schedules_for_table)

        # Augment table with cycle and degradation data
        table["efc"] = [per_duration[l]["efc"] for l in table.index]
        table["soh_pct"] = [
            per_duration[l]["degradation"]["soh_pct"] for l in table.index
        ]

        best_net = table["net_revenue_usd"].idxmax()
        best_per_mwh = table["net_revenue_per_mwh_usd"].idxmax()

        return {
            "comparison_table": table,
            "per_duration": per_duration,
            "best_by_net_revenue": best_net,
            "best_by_net_revenue_per_mwh": best_per_mwh,
        }

    # ------------------------------------------------------------------
    # Spread analysis (no LP needed)
    # ------------------------------------------------------------------

    def spread_analysis(self, prices: pd.Series) -> Dict[str, Any]:
        """
        Analyse the price series for arbitrage opportunity without running the LP.

        Returns spread statistics, per-duration opportunity estimates, and
        optimal charge/discharge windows.
        """
        analyzer = SpreadAnalyzer(self.config.dt_hours)
        metrics = analyzer.analyze(prices)
        dur_table = analyzer.duration_comparison_table(prices.values)
        windows = analyzer.optimal_charge_windows(prices.values, n_windows=3, window_h=4.0)

        # Theoretical max revenue per duration (upper bound, no efficiency loss yet)
        eta = self.config.eta_roundtrip
        power_mw = self.config.power_mw
        theoretical: Dict[str, float] = {}
        for dur in DURATION_HOURS:
            cap = power_mw * dur
            mean_spread = metrics.spread_per_duration.get(f"{dur}h", 0.0)
            theoretical[f"{dur}h"] = round(mean_spread * cap * eta, 4)

        return {
            "spread_metrics": metrics.to_dict(),
            "duration_spread_table": dur_table,
            "optimal_windows": windows,
            "theoretical_max_revenue_per_cycle_usd": theoretical,
        }

    # ------------------------------------------------------------------
    # Rule-based heuristic dispatch (no LP)
    # ------------------------------------------------------------------

    def heuristic_dispatch(
        self,
        prices: pd.Series,
        capacity_mwh: float,
        strategy: str = "percentile",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Run a rule-based dispatch strategy as a benchmark.

        Parameters
        ----------
        prices : pd.Series
        capacity_mwh : float
        strategy : str
            One of "threshold", "percentile", "valley_peak".
        **kwargs
            Passed to the chosen strategy method.

        Returns
        -------
        dict with schedule DataFrame and revenue metrics.
        """
        params = ChargingParams(
            capacity_mwh=capacity_mwh,
            power_mw=self.config.power_mw,
            eta_roundtrip=self.config.eta_roundtrip,
            soc_min_frac=self.config.soc_min_frac,
            soc_max_frac=self.config.soc_max_frac,
            soc_initial_frac=self.config.soc_initial_frac,
            dt_hours=self.config.dt_hours,
        )
        logic = ChargingLogic(params)
        arr = prices.values.astype(float)

        if strategy == "threshold":
            charge, discharge, soc = logic.threshold_dispatch(arr, **kwargs)
        elif strategy == "percentile":
            charge, discharge, soc = logic.percentile_dispatch(arr, **kwargs)
        elif strategy == "valley_peak":
            charge, discharge, soc = logic.valley_peak_dispatch(arr, **kwargs)
        else:
            raise ValueError(f"Unknown strategy '{strategy}'. Choose: threshold, percentile, valley_peak.")

        schedule = logic.to_dataframe(arr, charge, discharge, soc, index=prices.index)
        rev = self._rev_metrics(capacity_mwh)
        rev_result = rev.compute(arr, charge, discharge)

        return {
            "strategy": strategy,
            "schedule": schedule,
            "gross_revenue_usd": rev_result.gross_revenue_usd,
            "degradation_cost_usd": rev_result.degradation_cost_usd,
            "net_revenue_usd": rev_result.net_revenue_usd,
            "efc": rev_result.efc,
            "capacity_mwh": capacity_mwh,
        }

    # ------------------------------------------------------------------
    # JSON serialisation
    # ------------------------------------------------------------------

    def to_json(self, result: Dict[str, Any], indent: int = 2) -> str:
        """
        Serialise an optimize() or compare_durations() result to JSON.

        DataFrames are converted to record-oriented lists.
        NumPy scalars are cast to native Python types.
        """

        def _convert(obj: Any) -> Any:
            if isinstance(obj, pd.DataFrame):
                return obj.reset_index().to_dict(orient="records")
            if isinstance(obj, pd.Series):
                return obj.tolist()
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            if isinstance(obj, (np.integer,)):
                return int(obj)
            if isinstance(obj, (np.floating,)):
                return float(obj)
            if isinstance(obj, dict):
                return {k: _convert(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_convert(v) for v in obj]
            return obj

        return json.dumps(_convert(result), indent=indent, default=str)
