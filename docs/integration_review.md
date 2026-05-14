# Integration review

This repository snapshot did not include the original PR #7 document or branches for PR #1, #3, #4, and #5. The MVP integration therefore implements the requested source-of-truth behavior directly:

- focus only on BESS and electricity markets;
- no crypto, forex, or live-trading framing;
- no mandatory OpenAI, Anthropic, or ENTSO-E credentials;
- runnable through `pip install -r requirements.txt` and `streamlit run app/ui/streamlit_app.py`;
- canonical market schema: `timestamp, country, bidding_zone, price_eur_mwh, load_mw, solar_mw, wind_mw, source`;
- loader fallback, optimizer fallback, analytics, Plotly charts, deterministic report, Streamlit UI, README, and tests.
