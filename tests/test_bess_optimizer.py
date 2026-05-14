import pandas as pd

from app.data.market_loader import demo_market_data
from app.optimization.bess_optimizer import BessConfig, optimize_bess


def test_optimizer_returns_dispatch_columns_and_summary():
    data = demo_market_data(periods=24)
    dispatch, summary = optimize_bess(data, BessConfig(power_mw=5, energy_mwh=10, round_trip_efficiency=0.9))
    assert len(dispatch) == len(data)
    assert {"charge_mw", "discharge_mw", "soc_mwh", "revenue_eur"}.issubset(dispatch.columns)
    assert summary.method in {"pyomo", "heuristic"}
    assert dispatch["soc_mwh"].between(0, 10).all()


def test_heuristic_can_capture_simple_price_spread(monkeypatch):
    import app.optimization.bess_optimizer as optimizer

    monkeypatch.setattr(optimizer, "_try_pyomo", lambda prices, config: None)
    data = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=6, freq="h", tz="UTC"),
            "country": ["Germany"] * 6,
            "bidding_zone": ["DE-LU"] * 6,
            "price_eur_mwh": [10, 12, 15, 90, 95, 100],
            "load_mw": [1000] * 6,
            "solar_mw": [0] * 6,
            "wind_mw": [0] * 6,
            "source": ["test"] * 6,
        }
    )
    dispatch, summary = optimize_bess(data, BessConfig(power_mw=2, energy_mwh=4, round_trip_efficiency=1.0, initial_soc_mwh=0))
    assert summary.method == "heuristic"
    assert summary.objective_eur > 0
    assert dispatch["charge_mw"].sum() > 0
    assert dispatch["discharge_mw"].sum() > 0
