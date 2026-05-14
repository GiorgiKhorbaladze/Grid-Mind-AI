# Architecture

## Overview

GridMind AI is built around a layered, event-driven architecture. Each layer has a single responsibility and communicates through well-defined interfaces, making it straightforward to swap components — a different exchange, a different AI model, or a different data source — without touching unrelated code.

```
┌─────────────────────────────────────────────────────────────────────┐
│                          GridMind AI                                │
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │  Data Layer  │    │  AI Engine   │    │   Grid Strategy      │  │
│  │              │    │              │    │   Engine             │  │
│  │  WebSocket   │───▶│  RL Agent    │───▶│                      │  │
│  │  REST APIs   │    │  (PPO/SAC)   │    │  Adaptive Spacing    │  │
│  │  Order Book  │    │              │    │  Range Optimizer     │  │
│  │  On-Chain    │    │  NLP Fusion  │    │  Level Manager       │  │
│  │  News/Reddit │───▶│  (DistilBERT)│    │                      │  │
│  └──────────────┘    └──────────────┘    └──────────┬───────────┘  │
│                                                      │              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────▼───────────┐  │
│  │  Analytics   │    │ Risk Manager │    │  Execution Layer     │  │
│  │  Dashboard   │◀───│              │◀───│                      │  │
│  │  (Streamlit) │    │  Drawdown    │    │  Smart Order Router  │  │
│  │              │    │  Kelly Sizer │    │  Exchange Adapters   │  │
│  │              │    │  Correlation │    │  WebSocket Client    │  │
│  └──────────────┘    └──────────────┘    └──────────────────────┘  │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Storage: PostgreSQL · Redis · InfluxDB                     │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Layer

The data layer is responsible for ingesting, normalizing, and distributing market data to the rest of the system.

### Price Feed

Real-time OHLCV data arrives via WebSocket from the connected exchange. The feed normalizer converts exchange-specific formats into a unified `Candle` object used throughout the codebase. Data is simultaneously:

- Published to an in-memory event bus for immediate consumption by the AI Engine
- Written to InfluxDB for historical querying and analytics
- Cached in Redis for dashboard reads

### Order Book Feed

Level-2 order book snapshots and incremental updates stream in parallel with the price feed. The order book provides:

- **Bid/ask spread** — used by the risk manager for slippage estimation
- **Depth imbalance** — a feature signal for the RL agent indicating short-term directional pressure
- **Liquidity zones** — used by the grid engine to anchor level placement near natural support/resistance

### Sentiment Feed

An async background worker polls external sources every 60 seconds:

| Source | Method | Signal |
|---|---|---|
| CryptoPanic / NewsAPI | REST polling | Article headline sentiment |
| Reddit (r/bitcoin, etc.) | PRAW streaming | Community sentiment score |
| On-chain (Glassnode) | REST polling | Whale inflow/outflow, exchange reserves |

Each source produces a normalized sentiment score in `[-1, 1]`. These are fused into a single `SentimentVector` via a weighted ensemble and fed to the AI Engine.

---

## AI Engine

The AI Engine continuously computes optimal grid parameters given current market state.

### RL Agent

The core decision-maker is a **Proximal Policy Optimization (PPO)** agent (with SAC as an optional alternative for continuous action spaces).

**State space** — the observation vector fed to the agent at each step:

| Feature | Description |
|---|---|
| Price returns (20-period) | Normalized recent price movement |
| Volatility (ATR, Bollinger Width) | Current volatility regime |
| Order book imbalance | Directional pressure from depth |
| Realized vs implied vol ratio | Vol regime indicator |
| Sentiment vector (3-dim) | News, social, on-chain scores |
| Active grid metrics | Current fill rate, open PnL |
| Position exposure | Current net market exposure |

**Action space** — the agent outputs adjustments to:

- Grid spacing percentage
- Grid range (upper/lower bound offset from mid-price)
- Number of active levels
- Position size per level (as a fraction of Kelly-optimal)

**Reward function:**

```
reward = risk_adjusted_pnl - λ₁ · drawdown_penalty - λ₂ · exposure_penalty
```

Where `risk_adjusted_pnl` is the Sortino ratio of realized trades in the current episode window, and penalties discourage excessive drawdown and net directional exposure.

### NLP Sentiment Pipeline

Headlines and social posts pass through a fine-tuned **DistilBERT** classifier (trained on crypto-financial text). The model outputs a 3-class probability distribution: `[bearish, neutral, bullish]`, collapsed to a scalar score.

The sentiment pipeline runs in a separate process to avoid blocking the trading loop.

---

## Grid Strategy Engine

The grid engine translates AI-computed parameters into concrete price levels and manages their lifecycle.

### Level Placement

Given the AI-recommended spacing `δ` and mid-price `P`:

```
buy_levels  = [P - δ, P - 2δ, ..., P - n·δ]
sell_levels = [P + δ, P + 2δ, ..., P + n·δ]
```

In adaptive mode, `δ` is recomputed on every closed candle. Levels shift gradually to avoid excessive order cancellation/replacement, which would generate unnecessary fees.

### Grid Rebalancing

The engine tracks two triggers for rebalancing:

1. **Price escape** — price moves outside the current grid range, requiring full reset
2. **Parameter drift** — AI-recommended spacing deviates from active spacing by more than a configurable threshold (default 15%)

Rebalancing is performed in a single atomic batch: cancel all existing orders → compute new levels → place new orders.

---

## Risk Manager

The risk manager acts as a gatekeeper between the grid engine and the execution layer. Every proposed order batch passes through risk checks before being sent to the exchange.

### Checks Performed

| Check | Action on Breach |
|---|---|
| Max drawdown from peak | Cancel all orders, halt trading |
| Maximum net exposure | Reduce position size proportionally |
| Single-order size limit | Reject oversized order |
| Daily loss limit | Halt trading until next UTC day |
| Correlation with other symbols | Scale down correlated positions |

### Position Sizing

Default mode uses **fractional Kelly**:

```
f* = (edge / odds) × kelly_fraction
```

Where `edge` is estimated from the strategy's historical win rate and average win/loss ratio, `odds` is the reward-to-risk ratio of the current grid setup, and `kelly_fraction` (default 0.25) caps the recommendation at 25% of full Kelly to account for estimation error.

---

## Execution Layer

The execution layer translates grid-level orders into exchange API calls.

### Exchange Adapters

All exchange communication is abstracted behind a unified `ExchangeAdapter` interface:

```python
class ExchangeAdapter(Protocol):
    async def place_limit_order(self, symbol, side, price, qty) -> Order: ...
    async def cancel_order(self, order_id) -> None: ...
    async def get_open_orders(self, symbol) -> list[Order]: ...
    async def get_balance(self) -> dict[str, float]: ...
```

Concrete implementations exist for Binance, Bybit, OKX, OANDA, and Alpaca. Adding a new exchange requires only implementing this interface.

### Smart Order Router

Before placing an order, the router checks:

- Current spread vs. commission to ensure the trade is economically viable
- Whether an equivalent order is already open (deduplication)
- Whether the order would immediately cross the book (converts to market order if configured)

### WebSocket Order Management

Order state is tracked via WebSocket execution reports rather than polling. This gives sub-100ms fill confirmation and eliminates the polling overhead that accumulates with large numbers of open orders.

---

## Storage

| Store | Role |
|---|---|
| **PostgreSQL** | Trade history, configuration, audit log, backtest results |
| **Redis** | Real-time price cache, current order state, session data |
| **InfluxDB** | Time-series OHLCV, metrics, P&L curve for dashboard |

---

## Event Bus

Internal components communicate via an async publish/subscribe event bus (backed by `asyncio.Queue`). Key events:

| Event | Publisher | Subscribers |
|---|---|---|
| `CandleClose` | Data Layer | AI Engine, Grid Engine |
| `OrderFilled` | Execution Layer | Risk Manager, Analytics, Grid Engine |
| `SentimentUpdate` | Sentiment Feed | AI Engine |
| `GridRebalance` | Grid Engine | Execution Layer |
| `RiskBreachHalt` | Risk Manager | Grid Engine, Execution Layer, Dashboard |

This decoupled design means any component can be tested in isolation by emitting mock events.

---

## Module Map

```
gridmind/
├── ai/
│   ├── agents/
│   │   ├── ppo.py          # PPO implementation (PyTorch)
│   │   ├── sac.py          # SAC implementation (PyTorch)
│   │   └── base.py         # Abstract Agent interface
│   ├── sentiment/
│   │   ├── pipeline.py     # DistilBERT inference pipeline
│   │   ├── sources.py      # News, Reddit, on-chain adapters
│   │   └── fusion.py       # Weighted ensemble combiner
│   └── models/             # Saved model weights
├── core/
│   ├── grid.py             # Level calculation, rebalancing logic
│   ├── events.py           # Event bus implementation
│   └── types.py            # Shared data types (Candle, Order, etc.)
├── data/
│   ├── feeds.py            # WebSocket price + book feeds
│   ├── historical.py       # Historical data loader
│   └── normalizer.py       # Exchange format → internal format
├── exchanges/
│   ├── base.py             # ExchangeAdapter protocol
│   ├── binance.py
│   ├── bybit.py
│   ├── okx.py
│   ├── oanda.py
│   └── alpaca.py
├── risk/
│   ├── manager.py          # Pre-trade risk checks
│   └── sizer.py            # Kelly position sizing
├── backtest/
│   ├── engine.py           # Simulation loop
│   ├── report.py           # Metrics calculation + export
│   └── slippage.py         # Slippage & commission models
├── dashboard/
│   └── app.py              # Streamlit dashboard
└── cli/
    └── main.py             # Typer CLI entry point
```
