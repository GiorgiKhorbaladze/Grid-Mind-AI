# GridMind-AI

GridMind-AI is a runnable MVP for **battery energy storage system (BESS)** analytics in **electricity markets**. It loads canonical market data, optimizes battery dispatch, visualizes results with Plotly, and produces a deterministic AI-style narrative report.

This MVP intentionally avoids crypto, forex, live-trading framing, mandatory LLM APIs, and mandatory ENTSO-E tokens.

## Quick start

```bash
pip install -r requirements.txt
streamlit run app/ui/streamlit_app.py
```

If no data is uploaded, the app uses deterministic demo electricity-market data so the workflow runs end-to-end immediately.

## Canonical market schema

CSV uploads should use these columns:

```text
timestamp, country, bidding_zone, price_eur_mwh, load_mw, solar_mw, wind_mw, source
```

- `timestamp`: parseable timestamp; UTC is recommended.
- `country`: country name.
- `bidding_zone`: electricity bidding zone such as `DE-LU`.
- `price_eur_mwh`: electricity price in EUR/MWh.
- `load_mw`, `solar_mw`, `wind_mw`: power values in MW.
- `source`: data provenance label.

The loader cleans uploaded data into this schema and falls back to demo data when a file is missing or unreadable.

## What the MVP includes

- Market data loader with a deterministic demo fallback.
- Canonical data cleaning and schema normalization.
- BESS optimizer that uses Pyomo/GLPK when available.
- Deterministic heuristic optimizer fallback when Pyomo or GLPK is unavailable.
- Market analytics for prices, spread, load, and renewable share.
- BESS analytics for revenue, charge, discharge, and state of charge.
- Plotly market and dispatch charts in Streamlit.
- Deterministic AI-style report with no OpenAI or Anthropic dependency.
- Tests covering data cleaning and optimizer behavior.

## Optional solver support

`pyomo` and a GLPK executable are optional. When either is unavailable, GridMind-AI automatically uses the heuristic dispatch optimizer. This keeps the app runnable with only the documented quick-start commands.

## Run tests

```bash
pytest
```

## Project layout

```text
app/
  analytics/        Market and dispatch KPI helpers
  data/             Canonical loader, cleaner, and demo fallback
  optimization/     BESS optimizer and heuristic fallback
  reporting/        Deterministic report generator
  ui/               Streamlit app and Plotly charts
tests/              Data-cleaning and optimizer tests
```
