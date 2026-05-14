"""Streamlit MVP for GridMind-AI BESS electricity-market analysis."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from app.analytics.market_analytics import dispatch_summary, market_summary
from app.data.market_loader import clean_market_data, load_market_data
from app.optimization.bess_optimizer import BessConfig, optimize_bess
from app.reporting.deterministic_report import build_report
from app.ui.charts import bess_dispatch_chart, market_chart

st.set_page_config(page_title="GridMind-AI MVP", page_icon="🔋", layout="wide")

st.title("GridMind-AI MVP")
st.caption("BESS optimization and analytics for electricity markets. No LLM key or ENTSO-E token required.")

with st.sidebar:
    st.header("Market data")
    uploaded = st.file_uploader("Upload canonical CSV", type=["csv"])
    st.caption("Expected schema: timestamp, country, bidding_zone, price_eur_mwh, load_mw, solar_mw, wind_mw, source")

    st.header("BESS parameters")
    power_mw = st.number_input("Power (MW)", min_value=0.1, value=10.0, step=1.0)
    energy_mwh = st.number_input("Energy (MWh)", min_value=0.1, value=20.0, step=1.0)
    rte = st.slider("Round-trip efficiency", min_value=0.50, max_value=1.0, value=0.88, step=0.01)

if uploaded is None:
    market_data = load_market_data()
    data_label = "Demo fallback data"
else:
    market_data = clean_market_data(pd.read_csv(uploaded))
    data_label = "Uploaded data"

config = BessConfig(power_mw=power_mw, energy_mwh=energy_mwh, round_trip_efficiency=rte)
dispatch_data, optimization = optimize_bess(market_data, config)
market_kpis = market_summary(market_data)
dispatch_kpis = dispatch_summary(dispatch_data)

st.subheader(data_label)
cols = st.columns(4)
cols[0].metric("Average price", f"{market_kpis['avg_price_eur_mwh']} €/MWh")
cols[1].metric("P10-P90 spread", f"{market_kpis['p10_p90_spread_eur_mwh']} €/MWh")
cols[2].metric("BESS value", f"{optimization.objective_eur} €")
cols[3].metric("Optimizer", optimization.method)

st.plotly_chart(market_chart(market_data), use_container_width=True)
st.plotly_chart(bess_dispatch_chart(dispatch_data), use_container_width=True)

with st.expander("Market analytics", expanded=True):
    st.json(market_kpis)

with st.expander("BESS analytics", expanded=True):
    st.json(dispatch_kpis)

st.markdown(build_report(market_kpis, optimization))

with st.expander("Canonical data preview"):
    st.dataframe(dispatch_data.head(100), use_container_width=True)
