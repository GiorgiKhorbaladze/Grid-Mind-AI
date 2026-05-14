import streamlit as st

st.set_page_config(
    page_title="GridMind AI · BESS Optimizer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

from frontend.styles.theme import inject_css
from frontend.components.header import render_header
from frontend.components.sidebar import render_sidebar
from frontend.components.charts import render_charts
from frontend.components.chat import render_chat


def init_session():
    defaults = {
        "messages": None,
        "bess_capacity": 100,
        "bess_power": 50,
        "bess_efficiency": 0.92,
        "bess_duration": 4,
        "optimization_ran": False,
        "run_seed": 42,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def main():
    init_session()
    inject_css()

    # Sidebar returns all params
    params = render_sidebar()

    # Header (in main area, above tabs)
    render_header(params["market"])

    # Main tabs
    tab_dash, tab_chat = st.tabs([
        "⬡  DASHBOARD",
        "◈  AI ANALYST",
    ])

    with tab_dash:
        render_charts(params)

    with tab_chat:
        render_chat(params)


if __name__ == "__main__":
    main()
