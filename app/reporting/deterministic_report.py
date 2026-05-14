"""AI-style deterministic report text without requiring an LLM API."""

from __future__ import annotations

from app.optimization.bess_optimizer import OptimizationSummary


def build_report(market_kpis: dict, optimization: OptimizationSummary) -> str:
    """Generate a stable narrative report for the UI and tests."""

    spread = market_kpis["p10_p90_spread_eur_mwh"]
    opportunity = "strong" if spread >= 45 else "moderate" if spread >= 20 else "limited"
    return (
        "### GridMind-AI BESS Market Report\n\n"
        f"The selected electricity market window contains {market_kpis['rows']} hourly records "
        f"from {market_kpis['start']} to {market_kpis['end']}. Average price is "
        f"{market_kpis['avg_price_eur_mwh']} €/MWh with a P10-P90 spread of {spread} €/MWh, "
        f"indicating a {opportunity} arbitrage opportunity for a battery energy storage system.\n\n"
        f"The BESS optimizer used the **{optimization.method}** method and produced estimated gross arbitrage "
        f"value of **{optimization.objective_eur} €**. It charged {optimization.charged_mwh} MWh, "
        f"discharged {optimization.discharged_mwh} MWh, and used approximately "
        f"{optimization.cycles_equivalent} equivalent cycles.\n\n"
        "This report is generated deterministically from market and optimizer outputs; it does not require "
        "OpenAI, Anthropic, ENTSO-E, crypto, forex, or live-trading integrations."
    )
