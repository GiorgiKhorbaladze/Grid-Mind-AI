import streamlit as st
from datetime import datetime


def render_header(market: str):
    now = datetime.now().strftime("%Y-%m-%d  %H:%M UTC")
    st.markdown(
        f"""
        <div class="gm-header">
            <div>
                <div class="gm-logo">GRID<em>MIND</em> AI</div>
                <div class="gm-tagline">Battery Energy Storage · Optimization Platform · v2.0</div>
            </div>
            <div class="gm-header-right">
                <span class="timestamp-pill">{now}</span>
                <span class="market-pill">
                    <span class="market-icon">◈</span> {market}
                </span>
                <span class="status-pill">
                    <span class="status-dot"></span>SYSTEMS ONLINE
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
