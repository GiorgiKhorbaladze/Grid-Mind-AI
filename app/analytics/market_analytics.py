"""Deterministic analytics for electricity market and BESS results."""

from __future__ import annotations

import pandas as pd


def market_summary(market_data: pd.DataFrame) -> dict[str, float | str | int]:
    """Compute a compact set of market KPIs from canonical market data."""

    data = market_data.copy()
    price = pd.to_numeric(data["price_eur_mwh"], errors="coerce")
    renewables = pd.to_numeric(data["solar_mw"], errors="coerce").fillna(0) + pd.to_numeric(data["wind_mw"], errors="coerce").fillna(0)
    load = pd.to_numeric(data["load_mw"], errors="coerce").replace(0, pd.NA)
    spread = price.quantile(0.90) - price.quantile(0.10)

    return {
        "rows": int(len(data)),
        "start": str(data["timestamp"].min()) if len(data) else "n/a",
        "end": str(data["timestamp"].max()) if len(data) else "n/a",
        "avg_price_eur_mwh": round(float(price.mean()), 2),
        "min_price_eur_mwh": round(float(price.min()), 2),
        "max_price_eur_mwh": round(float(price.max()), 2),
        "p10_p90_spread_eur_mwh": round(float(spread), 2),
        "avg_load_mw": round(float(pd.to_numeric(data["load_mw"], errors="coerce").mean()), 2),
        "avg_renewable_share": round(float((renewables / load).mean()), 3),
    }


def dispatch_summary(dispatch_data: pd.DataFrame) -> dict[str, float]:
    """Compute BESS dispatch KPIs from optimized dispatch data."""

    return {
        "total_revenue_eur": round(float(dispatch_data["revenue_eur"].sum()), 2),
        "charged_mwh": round(float(dispatch_data["charge_mw"].sum()), 3),
        "discharged_mwh": round(float(dispatch_data["discharge_mw"].sum()), 3),
        "max_soc_mwh": round(float(dispatch_data["soc_mwh"].max()), 3),
        "min_soc_mwh": round(float(dispatch_data["soc_mwh"].min()), 3),
    }
