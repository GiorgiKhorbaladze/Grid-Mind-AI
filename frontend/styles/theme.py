import streamlit as st


def inject_css():
    css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

    /* ── Variables ─────────────────────────────────────────── */
    :root {
        --bg-primary:      #020209;
        --bg-secondary:    #08081a;
        --bg-card:         #0c0c24;
        --accent-cyan:     #00f5ff;
        --accent-green:    #00ff88;
        --accent-purple:   #9d4edd;
        --accent-orange:   #ff6b35;
        --accent-red:      #ff3366;
        --accent-yellow:   #ffd700;
        --text-primary:    #e8e8ff;
        --text-secondary:  #8899bb;
        --text-dim:        #445566;
        --border-primary:  #1a1a4a;
        --glow-cyan:       0 0 10px #00f5ff80, 0 0 25px #00f5ff30;
        --glow-green:      0 0 10px #00ff8880, 0 0 25px #00ff8830;
        --glow-purple:     0 0 10px #9d4edd80, 0 0 25px #9d4edd30;
    }

    /* ── Global ────────────────────────────────────────────── */
    .stApp {
        background-color: var(--bg-primary) !important;
        background-image:
            radial-gradient(ellipse at 15% 40%, rgba(0,245,255,0.04) 0%, transparent 55%),
            radial-gradient(ellipse at 85% 20%, rgba(157,78,221,0.04) 0%, transparent 55%),
            radial-gradient(ellipse at 50% 80%, rgba(0,255,136,0.02) 0%, transparent 55%);
        font-family: 'Inter', sans-serif;
    }

    /* Scanline overlay */
    .stApp::after {
        content: '';
        position: fixed;
        inset: 0;
        background: repeating-linear-gradient(
            0deg,
            transparent,
            transparent 2px,
            rgba(0,0,0,0.025) 2px,
            rgba(0,0,0,0.025) 4px
        );
        pointer-events: none;
        z-index: 9999;
    }

    #MainMenu, footer, .stDeployButton { visibility: hidden; display: none; }

    header[data-testid="stHeader"] {
        background: transparent !important;
        border-bottom: 1px solid var(--border-primary);
    }

    /* ── Sidebar ───────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--bg-secondary) 0%, #040418 100%) !important;
        border-right: 1px solid var(--border-primary) !important;
    }

    [data-testid="stSidebarContent"] {
        padding-top: 1.5rem;
    }

    /* ── Scrollbar ─────────────────────────────────────────── */
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: var(--bg-primary); }
    ::-webkit-scrollbar-thumb { background: #1a1a4a; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--accent-cyan); }

    /* ── Sliders ───────────────────────────────────────────── */
    [data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {
        background: var(--accent-cyan) !important;
        box-shadow: var(--glow-cyan) !important;
    }

    /* ── Select boxes ──────────────────────────────────────── */
    [data-baseweb="select"] > div:first-child {
        background-color: var(--bg-card) !important;
        border-color: var(--border-primary) !important;
        color: var(--text-primary) !important;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
    }
    [data-baseweb="select"] > div:first-child:hover {
        border-color: var(--accent-cyan) !important;
    }
    [data-baseweb="popover"] { background: var(--bg-card) !important; }
    [role="option"] { color: var(--text-primary) !important; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; }
    [role="option"]:hover { background: rgba(0,245,255,0.08) !important; }

    /* ── Buttons ───────────────────────────────────────────── */
    .stButton > button {
        background: linear-gradient(135deg, rgba(0,245,255,0.08), rgba(157,78,221,0.08)) !important;
        border: 1px solid var(--accent-cyan) !important;
        color: var(--accent-cyan) !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.7rem !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
        border-radius: 3px !important;
        transition: all 0.25s ease !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, rgba(0,245,255,0.18), rgba(157,78,221,0.18)) !important;
        box-shadow: var(--glow-cyan) !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, rgba(0,255,136,0.12), rgba(0,245,255,0.08)) !important;
        border-color: var(--accent-green) !important;
        color: var(--accent-green) !important;
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: var(--glow-green) !important;
    }

    /* ── Tabs ──────────────────────────────────────────────── */
    [data-baseweb="tab-list"] {
        background: var(--bg-secondary) !important;
        border-bottom: 1px solid var(--border-primary) !important;
        gap: 0 !important;
    }
    [data-baseweb="tab"] {
        background: transparent !important;
        color: var(--text-dim) !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.68rem !important;
        letter-spacing: 2.5px !important;
        text-transform: uppercase !important;
        padding: 0.85rem 1.75rem !important;
        border: none !important;
        transition: all 0.2s ease !important;
    }
    [data-baseweb="tab"]:hover { color: var(--accent-cyan) !important; background: rgba(0,245,255,0.04) !important; }
    [aria-selected="true"][data-baseweb="tab"] {
        color: var(--accent-cyan) !important;
        background: rgba(0,245,255,0.06) !important;
        border-bottom: 2px solid var(--accent-cyan) !important;
    }

    /* ── Metrics ───────────────────────────────────────────── */
    [data-testid="metric-container"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-primary) !important;
        border-radius: 6px !important;
        padding: 1rem !important;
    }
    [data-testid="metric-container"]:hover {
        border-color: rgba(0,245,255,0.3) !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.6), 0 0 20px rgba(0,245,255,0.07) !important;
    }
    [data-testid="stMetricLabel"] {
        color: var(--text-dim) !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.58rem !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
    }
    [data-testid="stMetricValue"] {
        color: var(--accent-cyan) !important;
        font-family: 'JetBrains Mono', monospace !important;
    }
    [data-testid="stMetricDelta"] { font-family: 'JetBrains Mono', monospace !important; font-size: 0.72rem !important; }

    /* ── Text inputs ───────────────────────────────────────── */
    .stTextInput input, .stTextArea textarea, .stNumberInput input {
        background: var(--bg-card) !important;
        border-color: var(--border-primary) !important;
        color: var(--text-primary) !important;
        font-family: 'JetBrains Mono', monospace !important;
        border-radius: 3px !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--accent-cyan) !important;
        box-shadow: 0 0 0 1px var(--accent-cyan) !important;
    }

    /* ── Download button ───────────────────────────────────── */
    .stDownloadButton > button {
        background: linear-gradient(135deg, rgba(255,107,53,0.08), rgba(255,107,53,0.04)) !important;
        border: 1px solid var(--accent-orange) !important;
        color: var(--accent-orange) !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.68rem !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
        border-radius: 3px !important;
        width: 100%;
    }
    .stDownloadButton > button:hover {
        background: rgba(255,107,53,0.15) !important;
        box-shadow: 0 0 12px rgba(255,107,53,0.4) !important;
    }

    /* ── Alerts ────────────────────────────────────────────── */
    [data-testid="stAlert"] { border-radius: 4px !important; }
    div[data-baseweb="notification"][kind="info"] { background: rgba(0,245,255,0.06) !important; border-color: var(--accent-cyan) !important; }
    div[data-baseweb="notification"][kind="positive"] { background: rgba(0,255,136,0.06) !important; border-color: var(--accent-green) !important; }
    div[data-baseweb="notification"][kind="warning"] { background: rgba(255,107,53,0.06) !important; border-color: var(--accent-orange) !important; }

    /* ── Chat native components ────────────────────────────── */
    [data-testid="stChatInput"] > div {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-primary) !important;
        border-radius: 4px !important;
    }
    [data-testid="stChatInput"] textarea {
        color: var(--text-primary) !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.85rem !important;
        background: transparent !important;
    }
    [data-testid="stChatInput"] > div:focus-within {
        border-color: var(--accent-cyan) !important;
        box-shadow: 0 0 0 1px var(--accent-cyan) !important;
    }

    [data-testid="stChatMessage"] {
        background: transparent !important;
        border: none !important;
        padding: 0.5rem 0 !important;
    }

    /* ── Custom components ─────────────────────────────────── */

    /* Header */
    .gm-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.75rem 0 1.25rem;
        border-bottom: 1px solid var(--border-primary);
        margin-bottom: 1.5rem;
        position: relative;
    }
    .gm-header::after {
        content: '';
        position: absolute;
        bottom: -1px;
        left: 0;
        width: 120px;
        height: 1px;
        background: var(--accent-cyan);
        box-shadow: var(--glow-cyan);
    }

    .gm-logo {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.3rem;
        font-weight: 700;
        color: var(--accent-cyan);
        text-shadow: var(--glow-cyan);
        letter-spacing: 5px;
        text-transform: uppercase;
        line-height: 1;
    }
    .gm-logo em {
        color: var(--accent-green);
        font-style: normal;
        text-shadow: var(--glow-green);
    }
    .gm-tagline {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.55rem;
        color: var(--text-dim);
        letter-spacing: 4px;
        text-transform: uppercase;
        margin-top: 0.3rem;
    }

    .gm-header-right {
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.3rem 0.8rem;
        background: rgba(0,255,136,0.08);
        border: 1px solid rgba(0,255,136,0.3);
        border-radius: 2px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.6rem;
        letter-spacing: 2px;
        color: var(--accent-green);
        text-transform: uppercase;
    }
    .status-dot {
        width: 6px; height: 6px;
        border-radius: 50%;
        background: var(--accent-green);
        box-shadow: 0 0 8px var(--accent-green);
        animation: statusPulse 2s ease-in-out infinite;
        flex-shrink: 0;
    }

    .market-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.3rem 0.8rem;
        background: rgba(0,245,255,0.08);
        border: 1px solid rgba(0,245,255,0.25);
        border-radius: 2px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.6rem;
        letter-spacing: 2px;
        color: var(--accent-cyan);
        text-transform: uppercase;
    }
    .market-icon { opacity: 0.7; }

    .timestamp-pill {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.58rem;
        color: var(--text-dim);
        letter-spacing: 1px;
    }

    /* Section label */
    .section-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.58rem;
        color: var(--text-dim);
        letter-spacing: 4px;
        text-transform: uppercase;
        border-left: 2px solid var(--accent-cyan);
        padding-left: 0.6rem;
        margin: 1.25rem 0 0.9rem;
    }

    /* Sidebar labels */
    .sidebar-section-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.58rem;
        color: var(--accent-cyan);
        letter-spacing: 3px;
        text-transform: uppercase;
        padding-bottom: 0.4rem;
        border-bottom: 1px solid var(--border-primary);
        margin-bottom: 0.75rem;
        margin-top: 1.25rem;
    }

    /* KPI row */
    .kpi-row {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.75rem;
        margin-bottom: 1.5rem;
    }
    .kpi-card {
        background: var(--bg-card);
        border: 1px solid var(--border-primary);
        border-radius: 6px;
        padding: 1rem 1.1rem;
        position: relative;
        overflow: hidden;
        transition: border-color 0.25s, box-shadow 0.25s;
    }
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 1px;
        background: linear-gradient(90deg, var(--accent-cyan), transparent);
        opacity: 0.5;
    }
    .kpi-card:hover {
        border-color: rgba(0,245,255,0.3);
        box-shadow: 0 4px 20px rgba(0,0,0,0.5), 0 0 20px rgba(0,245,255,0.06);
    }
    .kpi-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.54rem;
        color: var(--text-dim);
        letter-spacing: 2.5px;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }
    .kpi-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.35rem;
        font-weight: 700;
        color: var(--accent-cyan);
        text-shadow: 0 0 10px rgba(0,245,255,0.4);
        line-height: 1;
        margin-bottom: 0.3rem;
    }
    .kpi-value.green { color: var(--accent-green); text-shadow: 0 0 10px rgba(0,255,136,0.4); }
    .kpi-value.purple { color: var(--accent-purple); text-shadow: 0 0 10px rgba(157,78,221,0.4); }
    .kpi-value.orange { color: var(--accent-orange); text-shadow: 0 0 10px rgba(255,107,53,0.4); }
    .kpi-delta {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.62rem;
        color: var(--accent-green);
    }
    .kpi-delta.neg { color: var(--accent-red); }

    /* Chat bubbles */
    .chat-msg-user {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        margin-bottom: 1.1rem;
        animation: fadeSlideUp 0.25s ease;
    }
    .chat-msg-ai {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        margin-bottom: 1.1rem;
        animation: fadeSlideUp 0.25s ease;
    }
    .chat-sender {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.55rem;
        color: var(--text-dim);
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 0.25rem;
    }
    .chat-bubble-user {
        max-width: 78%;
        padding: 0.7rem 1rem;
        background: linear-gradient(135deg, rgba(0,245,255,0.12), rgba(0,245,255,0.06));
        border: 1px solid rgba(0,245,255,0.25);
        border-radius: 8px 8px 2px 8px;
        font-family: 'Inter', sans-serif;
        font-size: 0.875rem;
        color: var(--text-primary);
        line-height: 1.6;
    }
    .chat-bubble-ai {
        max-width: 88%;
        padding: 0.85rem 1.1rem;
        background: var(--bg-secondary);
        border: 1px solid var(--border-primary);
        border-left: 2px solid var(--accent-cyan);
        border-radius: 2px 8px 8px 8px;
        font-family: 'Inter', sans-serif;
        font-size: 0.875rem;
        color: var(--text-primary);
        line-height: 1.7;
    }
    .chat-bubble-ai code {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
        background: rgba(0,245,255,0.08);
        color: var(--accent-cyan);
        padding: 0.1rem 0.35rem;
        border-radius: 3px;
    }

    /* Thinking animation */
    .thinking-wrap {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        margin-bottom: 1rem;
        animation: fadeSlideUp 0.25s ease;
    }
    .thinking-bubble {
        display: flex;
        align-items: center;
        gap: 0.8rem;
        padding: 0.7rem 1.1rem;
        background: var(--bg-secondary);
        border: 1px solid var(--border-primary);
        border-left: 2px solid var(--accent-purple);
        border-radius: 2px 8px 8px 8px;
    }
    .thinking-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.65rem;
        color: var(--accent-purple);
        letter-spacing: 2px;
        text-transform: uppercase;
        text-shadow: var(--glow-purple);
    }
    .thinking-dots { display: flex; gap: 5px; align-items: center; }
    .td {
        width: 7px; height: 7px;
        border-radius: 50%;
        background: var(--accent-purple);
        animation: thinkBounce 1.4s ease-in-out infinite;
    }
    .td:nth-child(1) { animation-delay: 0s; }
    .td:nth-child(2) { animation-delay: 0.22s; }
    .td:nth-child(3) { animation-delay: 0.44s; }

    /* Terminal lines */
    .terminal-block {
        background: rgba(0,0,0,0.3);
        border: 1px solid var(--border-primary);
        border-radius: 4px;
        padding: 0.75rem;
        margin: 0.5rem 0;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
    }
    .t-line { color: var(--accent-green); line-height: 1.8; }
    .t-line::before { content: '▸ '; color: var(--text-dim); }
    .t-line.dim { color: var(--text-dim); }
    .t-line.dim::before { content: '  '; }

    /* Chart wrapper */
    .chart-card {
        background: var(--bg-card);
        border: 1px solid var(--border-primary);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        position: relative;
        overflow: hidden;
    }
    .chart-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--accent-cyan), transparent);
        opacity: 0.4;
    }
    .chart-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.62rem;
        color: var(--text-secondary);
        letter-spacing: 3px;
        text-transform: uppercase;
        margin-bottom: 0.75rem;
    }

    /* Run button pulse when ready */
    .run-btn-wrap .stButton > button {
        background: linear-gradient(135deg, rgba(0,255,136,0.15), rgba(0,245,255,0.1)) !important;
        border-color: var(--accent-green) !important;
        color: var(--accent-green) !important;
        width: 100%;
        padding: 0.75rem !important;
        font-size: 0.72rem !important;
        letter-spacing: 3px !important;
        animation: btnGlowPulse 3s ease-in-out infinite;
    }
    .run-btn-wrap .stButton > button:hover {
        box-shadow: 0 0 20px rgba(0,255,136,0.5) !important;
        animation: none;
    }

    /* ── Keyframes ─────────────────────────────────────────── */
    @keyframes statusPulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.4; transform: scale(0.75); }
    }
    @keyframes thinkBounce {
        0%, 80%, 100% { transform: scale(0.55); opacity: 0.35; box-shadow: none; }
        40% { transform: scale(1.1); opacity: 1; box-shadow: 0 0 10px var(--accent-purple); }
    }
    @keyframes fadeSlideUp {
        from { opacity: 0; transform: translateY(8px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes btnGlowPulse {
        0%, 100% { box-shadow: 0 0 6px rgba(0,255,136,0.2); }
        50%       { box-shadow: 0 0 18px rgba(0,255,136,0.45); }
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
