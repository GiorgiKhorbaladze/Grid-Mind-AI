import streamlit as st
from frontend.utils.mock_data import MARKET_PROFILES


def render_sidebar() -> dict:
    with st.sidebar:
        # Logo mark
        st.markdown(
            """
            <div style="text-align:center; padding: 0.5rem 0 1.5rem; border-bottom: 1px solid #1a1a4a;">
                <div style="font-family:'JetBrains Mono',monospace; font-size:1.1rem; font-weight:700;
                            color:#00f5ff; letter-spacing:4px; text-shadow: 0 0 15px #00f5ff80;">
                    ⚡ GM·AI
                </div>
                <div style="font-family:'JetBrains Mono',monospace; font-size:0.52rem;
                            color:#445566; letter-spacing:3px; margin-top:0.3rem;">
                    BESS OPTIMIZER
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Market Selection ──────────────────────────────────
        st.markdown('<div class="sidebar-section-label">◈ MARKET</div>', unsafe_allow_html=True)
        market = st.selectbox(
            "Energy Market",
            options=list(MARKET_PROFILES.keys()),
            index=0,
            label_visibility="collapsed",
        )

        profile = MARKET_PROFILES[market]
        st.markdown(
            f"""
            <div class="terminal-block" style="margin-top:0.4rem;">
                <div class="t-line">Base: {profile['base_price']} $/MWh</div>
                <div class="t-line">Peak mult: {profile['peak_mult']}×</div>
                <div class="t-line">TZ: {profile['timezone']}</div>
                {"<div class='t-line'>Duck curve: YES</div>" if profile['duck_curve'] else ""}
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── BESS Parameters ───────────────────────────────────
        st.markdown('<div class="sidebar-section-label">⚙ BESS PARAMETERS</div>', unsafe_allow_html=True)

        capacity_mwh = st.slider(
            "Capacity (MWh)",
            min_value=10,
            max_value=500,
            value=st.session_state.get("bess_capacity", 100),
            step=5,
            help="Total usable energy capacity of the BESS",
        )
        st.session_state.bess_capacity = capacity_mwh

        power_mw = st.slider(
            "Power Rating (MW)",
            min_value=5,
            max_value=250,
            value=st.session_state.get("bess_power", 50),
            step=5,
            help="Maximum charge/discharge power",
        )
        st.session_state.bess_power = power_mw

        efficiency_pct = st.slider(
            "Round-trip Efficiency (%)",
            min_value=75,
            max_value=98,
            value=int(st.session_state.get("bess_efficiency", 0.92) * 100),
            step=1,
            help="AC-AC round-trip efficiency",
        )
        efficiency = efficiency_pct / 100.0
        st.session_state.bess_efficiency = efficiency

        duration_h = st.slider(
            "Duration (hours)",
            min_value=1,
            max_value=8,
            value=st.session_state.get("bess_duration", 4),
            step=1,
            help="Rated discharge duration at full power",
        )
        st.session_state.bess_duration = duration_h

        # ── SOC Limits ────────────────────────────────────────
        st.markdown('<div class="sidebar-section-label">◧ SOC LIMITS</div>', unsafe_allow_html=True)

        soc_col1, soc_col2 = st.columns(2)
        with soc_col1:
            soc_min = st.number_input("Min (%)", min_value=0, max_value=30, value=10, step=1)
        with soc_col2:
            soc_max = st.number_input("Max (%)", min_value=70, max_value=100, value=90, step=1)

        # Computed stats
        c_ratio = round(capacity_mwh / power_mw, 2) if power_mw > 0 else 0
        st.markdown(
            f"""
            <div class="terminal-block" style="margin-top:0.6rem;">
                <div class="t-line">C-ratio: {c_ratio} h</div>
                <div class="t-line">Usable: {capacity_mwh * (soc_max - soc_min) / 100:.0f} MWh</div>
                <div class="t-line">Efficiency: {efficiency_pct}%</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Actions ───────────────────────────────────────────
        st.markdown('<div class="sidebar-section-label">▶ ACTIONS</div>', unsafe_allow_html=True)

        st.markdown('<div class="run-btn-wrap">', unsafe_allow_html=True)
        run_clicked = st.button("⚡  RUN OPTIMIZATION", type="primary", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if run_clicked:
            st.session_state.optimization_ran = True
            st.session_state.run_seed = st.session_state.get("run_seed", 42) + 1

        # Download button (placeholder — backend will provide real data)
        if st.session_state.get("optimization_ran", False):
            report_csv = _build_report_csv(market, capacity_mwh, power_mw, efficiency)
            st.download_button(
                label="⬇  DOWNLOAD REPORT",
                data=report_csv,
                file_name=f"gridmind_{market}_report.csv",
                mime="text/csv",
                use_container_width=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            """
            <div style="font-family:'JetBrains Mono',monospace; font-size:0.52rem;
                        color:#445566; text-align:center; letter-spacing:1px; line-height:1.8;">
                GridMind AI · BESS Optimizer<br>
                © 2026 GiorgiKhorbaladze<br>
                MIT License
            </div>
            """,
            unsafe_allow_html=True,
        )

    return {
        "market": market,
        "capacity_mwh": capacity_mwh,
        "power_mw": power_mw,
        "efficiency": efficiency,
        "duration_h": duration_h,
        "soc_min": soc_min / 100.0,
        "soc_max": soc_max / 100.0,
    }


def _build_report_csv(market: str, capacity: float, power: float, efficiency: float) -> bytes:
    from frontend.utils.mock_data import generate_price_profile, generate_dispatch_schedule
    seed = st.session_state.get("run_seed", 42)
    price_df = generate_price_profile(market, seed=seed)
    df = generate_dispatch_schedule(price_df, capacity, power, efficiency)
    return df.to_csv(index=False).encode("utf-8")
