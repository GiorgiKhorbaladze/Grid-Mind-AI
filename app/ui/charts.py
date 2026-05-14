"""Plotly chart builders for GridMind-AI."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def market_chart(market_data: pd.DataFrame) -> go.Figure:
    """Create a price/load/renewables market chart."""

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=market_data["timestamp"], y=market_data["price_eur_mwh"], name="Price (€/MWh)"), secondary_y=False)
    fig.add_trace(go.Scatter(x=market_data["timestamp"], y=market_data["load_mw"], name="Load (MW)", opacity=0.55), secondary_y=True)
    fig.add_trace(go.Scatter(x=market_data["timestamp"], y=market_data["solar_mw"], name="Solar (MW)", opacity=0.55), secondary_y=True)
    fig.add_trace(go.Scatter(x=market_data["timestamp"], y=market_data["wind_mw"], name="Wind (MW)", opacity=0.55), secondary_y=True)
    fig.update_layout(title="Electricity market profile", hovermode="x unified", legend_orientation="h")
    fig.update_yaxes(title_text="€/MWh", secondary_y=False)
    fig.update_yaxes(title_text="MW", secondary_y=True)
    return fig


def bess_dispatch_chart(dispatch_data: pd.DataFrame) -> go.Figure:
    """Create a BESS charge/discharge/state-of-charge chart."""

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=dispatch_data["timestamp"], y=dispatch_data["charge_mw"], name="Charge (MW)"), secondary_y=False)
    fig.add_trace(go.Bar(x=dispatch_data["timestamp"], y=-dispatch_data["discharge_mw"], name="Discharge (MW)"), secondary_y=False)
    fig.add_trace(go.Scatter(x=dispatch_data["timestamp"], y=dispatch_data["soc_mwh"], name="SOC (MWh)", line={"color": "black"}), secondary_y=True)
    fig.update_layout(title="BESS dispatch", barmode="relative", hovermode="x unified", legend_orientation="h")
    fig.update_yaxes(title_text="MW", secondary_y=False)
    fig.update_yaxes(title_text="MWh", secondary_y=True)
    return fig
