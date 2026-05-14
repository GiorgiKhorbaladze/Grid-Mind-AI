import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

from frontend.utils.mock_data import (
    generate_price_profile,
    generate_dispatch_schedule,
    get_kpi_summary,
)

# ── Shared Plotly layout defaults ────────────────────────────────────────────

_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(8,8,26,0.6)",
    font=dict(family="JetBrains Mono, monospace", color="#8899bb", size=11),
    margin=dict(l=48, r=16, t=36, b=36),
    hoverlabel=dict(
        bgcolor="#0c0c24",
        bordercolor="#00f5ff",
        font=dict(family="JetBrains Mono, monospace", color="#e8e8ff", size=11),
    ),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        bordercolor="#1a1a4a",
        borderwidth=1,
        font=dict(color="#8899bb", size=10),
    ),
)

_XAXIS = dict(
    gridcolor="#1a1a4a",
    linecolor="#1a1a4a",
    tickfont=dict(color="#8899bb", size=10),
    zeroline=False,
    showspikes=True,
    spikecolor="#00f5ff",
    spikemode="across",
    spikethickness=1,
    spikedash="dot",
)

_YAXIS = dict(
    gridcolor="#1a1a4a",
    linecolor="#1a1a4a",
    tickfont=dict(color="#8899bb", size=10),
    zeroline=False,
)

_CONFIG = dict(
    displayModeBar=True,
    modeBarButtonsToRemove=["pan2d", "lasso2d", "select2d", "autoScale2d"],
    displaylogo=False,
    toImageButtonOptions=dict(format="png", scale=2),
)

HOURS = list(range(24))
HOUR_LABELS = [f"{h:02d}:00" for h in HOURS]


def _apply_layout(fig, **overrides):
    layout = {**_LAYOUT, **overrides}
    fig.update_layout(**layout)
    fig.update_xaxes(**_XAXIS)
    fig.update_yaxes(**_YAXIS)
    return fig


# ── KPI Row ──────────────────────────────────────────────────────────────────

def render_kpis(kpis: dict, params: dict):
    market = params["market"]
    daily = kpis["daily_revenue"]
    annual = kpis["annual_revenue"]
    spread = kpis["price_spread"]
    cycles = kpis["cycles_today"]
    peak = kpis["peak_price"]

    st.markdown(
        f"""
        <div class="kpi-row">
            <div class="kpi-card">
                <div class="kpi-label">Daily Revenue</div>
                <div class="kpi-value green">${daily:,.0f}</div>
                <div class="kpi-delta">▲ +{daily/max(annual/365*0.85,1)*100-100:.1f}% vs baseline</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Annual Run-rate</div>
                <div class="kpi-value">${annual/1000:,.1f}K</div>
                <div class="kpi-delta">365-day projection</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Price Spread</div>
                <div class="kpi-value purple">${spread:.1f}</div>
                <div class="kpi-delta">/MWh  peak–offpeak</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Cycles Today</div>
                <div class="kpi-value orange">{cycles:.2f}</div>
                <div class="kpi-delta">Peak: ${peak:.0f}/MWh</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Chart 1: Price Forecast ──────────────────────────────────────────────────

def render_price_chart(dispatch_df, market: str):
    prices = dispatch_df["price"].values
    threshold_charge = np.percentile(prices, 30)
    threshold_discharge = np.percentile(prices, 70)

    fig = go.Figure()

    # Fill bands
    fig.add_hrect(
        y0=0, y1=threshold_charge,
        fillcolor="rgba(0,255,136,0.04)", line_width=0,
        annotation_text="CHARGE ZONE", annotation_position="top left",
        annotation=dict(font=dict(color="#00ff8866", size=9, family="JetBrains Mono")),
    )
    fig.add_hrect(
        y0=threshold_discharge, y1=max(prices) * 1.15,
        fillcolor="rgba(255,51,102,0.04)", line_width=0,
        annotation_text="DISCHARGE ZONE", annotation_position="top right",
        annotation=dict(font=dict(color="#ff336666", size=9, family="JetBrains Mono")),
    )

    # Threshold lines
    fig.add_hline(
        y=threshold_charge, line=dict(color="#00ff8840", width=1, dash="dot"),
    )
    fig.add_hline(
        y=threshold_discharge, line=dict(color="#ff336640", width=1, dash="dot"),
    )

    # Price area fill
    fig.add_trace(go.Scatter(
        x=HOUR_LABELS, y=prices,
        fill="tozeroy",
        fillcolor="rgba(0,245,255,0.05)",
        line=dict(color="#00f5ff", width=2),
        name="DA Price",
        hovertemplate="<b>%{x}</b><br>Price: $%{y:.2f}/MWh<extra></extra>",
    ))

    # Charge/discharge markers
    charge_mask = dispatch_df["dispatch_mw"] < 0
    discharge_mask = dispatch_df["dispatch_mw"] > 0

    fig.add_trace(go.Scatter(
        x=[HOUR_LABELS[i] for i in range(24) if charge_mask.iloc[i]],
        y=[prices[i] for i in range(24) if charge_mask.iloc[i]],
        mode="markers",
        marker=dict(color="#00ff88", size=10, symbol="triangle-up",
                    line=dict(color="#00ff8880", width=1)),
        name="Charging",
        hovertemplate="<b>%{x}</b><br>Charging @ $%{y:.2f}/MWh<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=[HOUR_LABELS[i] for i in range(24) if discharge_mask.iloc[i]],
        y=[prices[i] for i in range(24) if discharge_mask.iloc[i]],
        mode="markers",
        marker=dict(color="#ff3366", size=10, symbol="triangle-down",
                    line=dict(color="#ff336680", width=1)),
        name="Discharging",
        hovertemplate="<b>%{x}</b><br>Discharging @ $%{y:.2f}/MWh<extra></extra>",
    ))

    _apply_layout(
        fig,
        title=dict(
            text=f"<span style='color:#445566;font-size:11px;letter-spacing:3px'>ELECTRICITY PRICE FORECAST  ·  {market}</span>",
            x=0, xanchor="left",
        ),
        yaxis_title="$/MWh",
        height=300,
        xaxis_tickangle=0,
    )
    fig.update_xaxes(tickvals=HOUR_LABELS[::2], ticktext=HOUR_LABELS[::2])

    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config=_CONFIG)
    st.markdown("</div>", unsafe_allow_html=True)


# ── Chart 2: BESS Dispatch & SOC ─────────────────────────────────────────────

def render_dispatch_chart(dispatch_df):
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.6, 0.4],
        vertical_spacing=0.08,
        subplot_titles=["", ""],
    )

    dispatch = dispatch_df["dispatch_mw"].values
    soc = dispatch_df["soc"].values

    # Color bars by charge vs discharge
    bar_colors = ["#00ff88" if v < 0 else "#ff3366" if v > 0 else "#1a1a4a" for v in dispatch]
    bar_text = [f"{v:.1f} MW" if v != 0 else "" for v in dispatch]

    fig.add_trace(go.Bar(
        x=HOUR_LABELS,
        y=dispatch,
        marker_color=bar_colors,
        marker_line_width=0,
        name="Dispatch (MW)",
        hovertemplate="<b>%{x}</b><br>Dispatch: %{y:.1f} MW<extra></extra>",
        showlegend=True,
    ), row=1, col=1)

    # Zero line for dispatch
    fig.add_hline(y=0, line=dict(color="#1a1a4a", width=1), row=1, col=1)

    # SOC area
    fig.add_trace(go.Scatter(
        x=HOUR_LABELS,
        y=soc,
        fill="tonexty",
        fillcolor="rgba(157,78,221,0.12)",
        line=dict(color="#9d4edd", width=2),
        name="SOC (%)",
        hovertemplate="<b>%{x}</b><br>SOC: %{y:.1f}%<extra></extra>",
    ), row=2, col=1)

    # SOC bands
    fig.add_hline(y=10, line=dict(color="#ff336640", width=1, dash="dot"), row=2, col=1)
    fig.add_hline(y=90, line=dict(color="#00f5ff40", width=1, dash="dot"), row=2, col=1)

    _apply_layout(
        fig,
        title=dict(
            text="<span style='color:#445566;font-size:11px;letter-spacing:3px'>BESS DISPATCH SCHEDULE  ·  STATE OF CHARGE</span>",
            x=0, xanchor="left",
        ),
        height=380,
    )
    fig.update_yaxes(title_text="MW", row=1, col=1, **_YAXIS)
    fig.update_yaxes(title_text="SOC %", row=2, col=1, range=[0, 105], **_YAXIS)
    fig.update_xaxes(**_XAXIS)
    fig.update_xaxes(tickvals=HOUR_LABELS[::2], ticktext=HOUR_LABELS[::2])

    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config=_CONFIG)
    st.markdown("</div>", unsafe_allow_html=True)


# ── Chart 3: Cumulative Revenue ──────────────────────────────────────────────

def render_revenue_chart(dispatch_df):
    cum_rev = dispatch_df["cumulative_revenue"].values
    hourly_rev = dispatch_df["revenue"].values

    fig = make_subplots(
        specs=[[{"secondary_y": True}]]
    )

    # Hourly bars
    bar_colors = ["#00ff8866" if v > 0 else "#ff336666" if v < 0 else "#1a1a4a" for v in hourly_rev]
    fig.add_trace(go.Bar(
        x=HOUR_LABELS,
        y=hourly_rev,
        marker_color=bar_colors,
        marker_line_width=0,
        name="Hourly Revenue ($)",
        hovertemplate="<b>%{x}</b><br>Revenue: $%{y:.2f}<extra></extra>",
    ), secondary_y=False)

    # Cumulative line
    fig.add_trace(go.Scatter(
        x=HOUR_LABELS,
        y=cum_rev,
        line=dict(color="#ffd700", width=2.5),
        mode="lines",
        name="Cumulative ($)",
        hovertemplate="<b>%{x}</b><br>Cumulative: $%{y:.2f}<extra></extra>",
        fill="tozeroy",
        fillcolor="rgba(255,215,0,0.04)",
    ), secondary_y=True)

    _apply_layout(
        fig,
        title=dict(
            text="<span style='color:#445566;font-size:11px;letter-spacing:3px'>REVENUE ATTRIBUTION  ·  DAILY P&L</span>",
            x=0, xanchor="left",
        ),
        height=300,
        hovermode="x unified",
    )
    fig.update_yaxes(title_text="$/hour", secondary_y=False, **_YAXIS)
    fig.update_yaxes(title_text="Cumulative $", secondary_y=True, **_YAXIS)
    fig.update_xaxes(tickvals=HOUR_LABELS[::2], ticktext=HOUR_LABELS[::2])

    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config=_CONFIG)
    st.markdown("</div>", unsafe_allow_html=True)


# ── Main render function ──────────────────────────────────────────────────────

def render_charts(params: dict):
    market = params["market"]
    seed = st.session_state.get("run_seed", 42)

    price_df = generate_price_profile(market, seed=seed)
    dispatch_df = generate_dispatch_schedule(
        price_df,
        params["capacity_mwh"],
        params["power_mw"],
        params["efficiency"],
        params["soc_min"],
        params["soc_max"],
    )
    kpis = get_kpi_summary(dispatch_df, params["capacity_mwh"])

    if not st.session_state.get("optimization_ran", False):
        st.markdown(
            """
            <div style="text-align:center; padding:3rem; border:1px solid #1a1a4a;
                        border-radius:8px; background:rgba(12,12,36,0.5); margin-bottom:1rem;">
                <div style="font-family:'JetBrains Mono',monospace; font-size:2rem;
                            color:#1a1a4a; margin-bottom:1rem;">⚡</div>
                <div style="font-family:'JetBrains Mono',monospace; font-size:0.75rem;
                            color:#445566; letter-spacing:3px; text-transform:uppercase;">
                    Configure parameters and run optimization<br>to view results
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        # Still show preview charts with dimmed state
        with st.expander("▸  PREVIEW  ( click Run Optimization to activate )", expanded=False):
            render_kpis(kpis, params)
            render_price_chart(dispatch_df, market)
    else:
        st.markdown('<div class="section-label">PERFORMANCE METRICS</div>', unsafe_allow_html=True)
        render_kpis(kpis, params)

        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown('<div class="section-label">PRICE FORECAST</div>', unsafe_allow_html=True)
            render_price_chart(dispatch_df, market)
        with col2:
            st.markdown('<div class="section-label">P&L ATTRIBUTION</div>', unsafe_allow_html=True)
            render_revenue_chart(dispatch_df)

        st.markdown('<div class="section-label">DISPATCH SCHEDULE</div>', unsafe_allow_html=True)
        render_dispatch_chart(dispatch_df)
