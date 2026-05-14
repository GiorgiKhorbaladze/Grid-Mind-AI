import time
import streamlit as st
from frontend.utils.mock_data import get_ai_response

_WELCOME = (
    "Welcome to **GridMind AI** — your BESS optimization analyst.\n\n"
    "I have full visibility into your battery configuration and the selected energy market. "
    "I can help you understand dispatch strategies, revenue projections, risk factors, "
    "degradation economics, and cross-market opportunities.\n\n"
    "Configure your BESS parameters in the sidebar and run the optimizer — then ask me anything. "
    "What would you like to explore?"
)

_THINKING_HTML = """
<div class="thinking-wrap">
    <div class="chat-sender">GRIDMIND AI</div>
    <div class="thinking-bubble">
        <div class="thinking-label">PROCESSING</div>
        <div class="thinking-dots">
            <div class="td"></div>
            <div class="td"></div>
            <div class="td"></div>
        </div>
    </div>
</div>
"""


def _init_chat():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": _WELCOME}
        ]


def _render_message(role: str, content: str):
    if role == "user":
        st.markdown(
            f"""
            <div class="chat-msg-user">
                <div class="chat-sender">YOU</div>
                <div class="chat-bubble-user">{content}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # Process markdown-like bold for the HTML bubble
        rendered = _simple_md(content)
        st.markdown(
            f"""
            <div class="chat-msg-ai">
                <div class="chat-sender">GRIDMIND AI</div>
                <div class="chat-bubble-ai">{rendered}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _simple_md(text: str) -> str:
    """Minimal markdown → HTML conversion for chat bubbles."""
    import re
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong style="color:#00f5ff">\1</strong>', text)
    # Inline code
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    # Newlines to <br>
    text = text.replace("\n\n", "<br><br>").replace("\n", "<br>")
    # Bullet points
    text = re.sub(r'<br>- ', r'<br>· ', text)
    return text


def render_chat(params: dict):
    _init_chat()

    st.markdown('<div class="section-label">AI ANALYST</div>', unsafe_allow_html=True)

    # Render message history
    for msg in st.session_state.messages:
        _render_message(msg["role"], msg["content"])

    # Thinking placeholder
    thinking_placeholder = st.empty()

    # Chat input — always visible at the bottom
    user_input = st.chat_input(
        placeholder="Ask about revenue, strategy, risk, degradation…",
    )

    if user_input and user_input.strip():
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        _render_message("user", user_input)

        # Show thinking animation
        thinking_placeholder.markdown(_THINKING_HTML, unsafe_allow_html=True)

        # Simulate processing delay
        time.sleep(1.2)

        # Generate and store response
        response = get_ai_response(user_input, params["market"], params)
        thinking_placeholder.empty()
        st.session_state.messages.append({"role": "assistant", "content": response})
        _render_message("assistant", response)

    # Quick action pills
    st.markdown(
        """
        <div style="margin-top:1rem; display:flex; flex-wrap:wrap; gap:0.5rem;">
            <div style="font-family:'JetBrains Mono',monospace; font-size:0.6rem;
                        color:#445566; letter-spacing:2px; align-self:center;">
                QUICK QUERIES:
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    qcol1, qcol2, qcol3, qcol4 = st.columns(4)
    quick_queries = [
        ("Revenue Estimate", "What is the estimated daily and annual revenue for this configuration?"),
        ("Dispatch Strategy", "What is the optimal dispatch strategy for this market?"),
        ("Risk Assessment", "What are the main risks and how should I hedge?"),
        ("Battery Degradation", "Explain the degradation economics and replacement timeline."),
    ]

    for col, (label, query) in zip([qcol1, qcol2, qcol3, qcol4], quick_queries):
        with col:
            if st.button(label, key=f"quick_{label}", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": query})
                response = get_ai_response(query, params["market"], params)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()
