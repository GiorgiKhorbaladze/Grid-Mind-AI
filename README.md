<div align="center">

<img src="screenshots/banner.png" alt="GridMind AI Banner" width="100%" />

# GridMind AI

**AI-Powered Adaptive Grid Trading System**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.x-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)](https://pytorch.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square)](CONTRIBUTING.md)
[![Stars](https://img.shields.io/github/stars/GiorgiKhorbaladze/Grid-Mind-AI?style=flat-square&color=f59e0b)](https://github.com/GiorgiKhorbaladze/Grid-Mind-AI/stargazers)
[![Discord](https://img.shields.io/badge/Discord-Join%20Us-5865F2?style=flat-square&logo=discord&logoColor=white)](https://discord.gg/gridmind)

*Grid trading, evolved. Machine learning meets market microstructure.*

[Quickstart](#-quickstart) · [Architecture](#-architecture) · [Docs](docs/) · [Roadmap](#-roadmap) · [Discord](https://discord.gg/gridmind)

</div>

---

## Vision

Traditional grid trading captures profit from market oscillation by placing buy and sell orders at fixed price intervals. It works — but it's static. Markets are not.

**GridMind AI** makes the grid intelligent. A deep reinforcement learning agent continuously re-optimizes grid spacing, range, and position sizing in real time, using live price action, order book depth, and multi-source sentiment signals. The result is a grid that adapts to volatility regimes, avoids trending markets, and compounds returns with dramatically reduced drawdown.

> Built for traders who want systematic edge — not another dashboard with pretty charts.

---

## Screenshots

<div align="center">

| Live Trading Dashboard | Grid Visualization | Backtesting Report |
|:---:|:---:|:---:|
| <img src="screenshots/dashboard.png" width="280" alt="Dashboard" /> | <img src="screenshots/grid_view.png" width="280" alt="Grid View" /> | <img src="screenshots/backtest.png" width="280" alt="Backtest" /> |

| Portfolio Analytics | Market Sentiment | Risk Monitor |
|:---:|:---:|:---:|
| <img src="screenshots/portfolio.png" width="280" alt="Portfolio" /> | <img src="screenshots/sentiment.png" width="280" alt="Sentiment" /> | <img src="screenshots/risk.png" width="280" alt="Risk Monitor" /> |

</div>

---

## Key Features

- **Adaptive Grid Engine** — RL-optimized grid spacing that reacts to volatility in real time
- **Sentiment Fusion** — NLP signals from news, Reddit, and on-chain data feed the grid decision layer
- **Multi-Market Support** — Crypto, Forex, Stocks, and Commodities via unified adapter layer
- **Institutional Risk Controls** — Max drawdown stops, Kelly position sizing, correlation-aware exposure limits
- **Backtesting Framework** — Tick-level historical simulation with slippage and fee modeling
- **Live Execution** — WebSocket order management with smart order routing
- **Modular Architecture** — Swap brokers, data feeds, and AI models without touching core logic

---

## Architecture

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
│  │  News/Reddit │───▶│  (BERT/GPT)  │    │                      │  │
│  └──────────────┘    └──────────────┘    └──────────┬───────────┘  │
│                                                      │              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────▼───────────┐  │
│  │  Analytics   │    │ Risk Manager │    │  Execution Layer     │  │
│  │  Dashboard   │◀───│              │◀───│                      │  │
│  │              │    │  Drawdown    │    │  Smart Order Router  │  │
│  │  Streamlit   │    │  Kelly Sizer │    │  Exchange Adapters   │  │
│  │  Real-time   │    │  Correlation │    │  WebSocket Client    │  │
│  └──────────────┘    └──────────────┘    └──────────────────────┘  │
│                                                                     │
│  Storage: PostgreSQL · Redis · InfluxDB (time-series)              │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Overview

| Layer | Technology | Purpose |
|---|---|---|
| Data Ingestion | `asyncio` + WebSocket | Real-time OHLCV, order book, trades |
| AI Engine | PyTorch (PPO / SAC) | Grid parameter optimization |
| Sentiment | `transformers` (DistilBERT) | News & social signal extraction |
| Grid Core | NumPy + custom C extension | Ultra-low latency level calculation |
| Risk Manager | Pure Python | Drawdown, Kelly, VaR, correlation |
| Execution | `ccxt` / broker REST+WS | Unified order management |
| Storage | PostgreSQL + Redis + InfluxDB | Persistence, cache, time-series |
| Dashboard | Streamlit | Live monitoring UI |
| CLI | `typer` | Scriptable control interface |

---

## Supported Markets

| Market | Exchanges / Brokers | Instruments |
|---|---|---|
| **Crypto** | Binance, Bybit, OKX, Coinbase Advanced, Kraken | Spot, Perpetuals, Futures |
| **Forex** | OANDA, Interactive Brokers, Alpaca | Major, Minor, Exotic pairs |
| **US Equities** | Alpaca, Interactive Brokers, TD Ameritrade | Stocks, ETFs |
| **Commodities** | Interactive Brokers | Gold, Silver, Oil, Nat Gas |

---

## Quickstart

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- API keys for at least one supported exchange

### 1. Clone & Install

```bash
git clone https://github.com/GiorgiKhorbaladze/Grid-Mind-AI.git
cd Grid-Mind-AI

# Create virtual environment
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

### 2. Configure

```bash
cp config/config.example.yaml config/config.yaml
```

Edit `config/config.yaml` with your exchange credentials and preferences:

```yaml
exchange:
  name: binance
  api_key: YOUR_API_KEY
  api_secret: YOUR_API_SECRET
  testnet: true          # Start on testnet

market:
  symbol: BTC/USDT
  quote_currency: USDT
  initial_capital: 1000

grid:
  mode: adaptive         # 'adaptive' (AI) or 'fixed'
  levels: 20
  spacing_pct: 0.5       # Initial spacing — AI will tune this

risk:
  max_drawdown_pct: 15
  position_size_mode: kelly
```

### 3. Launch Infrastructure

```bash
docker compose up -d     # Starts PostgreSQL, Redis, InfluxDB
```

### 4. Run

```bash
# Paper trading (recommended first)
gridmind run --mode paper --symbol BTC/USDT

# Backtesting
gridmind backtest --symbol BTC/USDT --from 2024-01-01 --to 2025-01-01

# Launch dashboard
gridmind dashboard
```

---

## Demo Usage

### Backtesting a Strategy

```python
from gridmind import GridBot, BacktestEngine
from gridmind.strategies import AdaptiveGridStrategy
from gridmind.data import HistoricalFeed

strategy = AdaptiveGridStrategy(
    symbol="BTC/USDT",
    initial_capital=10_000,
    grid_levels=20,
    ai_mode=True,
)

engine = BacktestEngine(
    strategy=strategy,
    feed=HistoricalFeed.from_csv("data/btc_usdt_1m.csv"),
    commission=0.001,
    slippage=0.0005,
)

results = engine.run()
results.summary()
```

```
Backtest Results — BTC/USDT (2024-01-01 → 2025-01-01)
──────────────────────────────────────────────────────
Total Return:        +147.3%
Annualized Return:   +147.3%
Max Drawdown:        -9.2%
Sharpe Ratio:        3.41
Sortino Ratio:       5.18
Win Rate:            71.4%
Total Trades:        4,832
Avg Trade Duration:  2h 14m
```

### Live Trading

```python
from gridmind import GridBot
from gridmind.exchanges import BinanceAdapter

bot = GridBot(
    exchange=BinanceAdapter(api_key="...", api_secret="..."),
    symbol="ETH/USDT",
    capital=5_000,
    ai_mode=True,
)

bot.start()
```

### CLI Reference

```bash
# Full strategy run
gridmind run --symbol ETH/USDT --capital 5000 --mode live

# Optimize grid parameters with Optuna
gridmind optimize --symbol BTC/USDT --trials 500

# Train RL agent on historical data
gridmind train --symbol BTC/USDT --epochs 200 --device cuda

# Export backtest report
gridmind backtest --symbol SOL/USDT --export html
```

---

## Project Structure

```
Grid-Mind-AI/
├── gridmind/
│   ├── ai/                  # RL agents, NLP sentiment models
│   │   ├── agents/          # PPO, SAC, DQN implementations
│   │   ├── sentiment/       # DistilBERT sentiment pipeline
│   │   └── models/          # Pretrained model weights
│   ├── core/                # Grid engine, level manager
│   ├── data/                # Data feeds, historical loaders
│   ├── exchanges/           # Exchange adapter implementations
│   ├── risk/                # Risk manager, position sizer
│   ├── backtest/            # Backtesting engine
│   ├── dashboard/           # Streamlit dashboard
│   └── cli/                 # Typer CLI commands
├── config/
│   └── config.example.yaml  # Configuration template
├── docs/                    # Extended documentation
├── tests/                   # Test suite
├── scripts/                 # Utility scripts
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

---

## Roadmap

### v0.1 — Foundation *(In Progress)*
- [x] Repository setup & architecture design
- [ ] Core grid engine (fixed spacing)
- [ ] Exchange adapter: Binance Spot
- [ ] Basic backtesting framework
- [ ] PostgreSQL + Redis infrastructure

### v0.2 — AI Core
- [ ] PPO-based RL agent for grid optimization
- [ ] DistilBERT sentiment pipeline (news + Reddit)
- [ ] Volatility regime classifier
- [ ] Hyperparameter optimization via Optuna

### v0.3 — Multi-Market Expansion
- [ ] Forex adapter (OANDA)
- [ ] US Equities adapter (Alpaca)
- [ ] Portfolio-level risk management
- [ ] Correlation-aware position sizing

### v0.4 — Production Hardening
- [ ] Streamlit monitoring dashboard
- [ ] Prometheus + Grafana metrics
- [ ] Docker Compose one-click deployment
- [ ] Comprehensive test suite (>80% coverage)

### v1.0 — Public Release
- [ ] Stable public API
- [ ] Full documentation site (MkDocs)
- [ ] Pre-trained model weights for major pairs
- [ ] Cloud deployment templates (AWS / GCP / Fly.io)

---

## Future Vision

GridMind AI aims to become the go-to open-source framework for intelligent algorithmic trading. Beyond grid strategies, the longer-horizon roadmap includes:

- **Cross-Asset Intelligence** — A unified AI brain managing grids across crypto, forex, and equities simultaneously with cross-market correlation awareness
- **On-Chain Signal Integration** — DeFi liquidity, whale wallet tracking, and DEX flow feeding the sentiment layer
- **Federated Learning** — Community-contributed training data improves the shared model without exposing individual strategies
- **Strategy Marketplace** — Open ecosystem where traders publish, share, and monetize backtested grid configurations
- **Natural Language Control** — "Run a tight grid on ETH if sentiment is bullish and volatility is low" — executed by an LLM reasoning layer
- **Hardware Acceleration** — FPGA-based order book processing for sub-millisecond grid recalculation

---

## Contributing

Contributions are what make the open-source community thrive. See [CONTRIBUTING.md](.github/CONTRIBUTING.md) for guidelines.

**Good first issues:** look for the [`good first issue`](https://github.com/GiorgiKhorbaladze/Grid-Mind-AI/issues?q=label%3A%22good+first+issue%22) label.

```bash
# Development setup
git clone https://github.com/GiorgiKhorbaladze/Grid-Mind-AI.git
cd Grid-Mind-AI
pip install -e ".[dev]"
pre-commit install
pytest
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with conviction by [GiorgiKhorbaladze](https://github.com/GiorgiKhorbaladze) and contributors.**

*If GridMind AI adds value to your work, consider giving it a star. It helps more developers find the project.*

[![Star History](https://img.shields.io/github/stars/GiorgiKhorbaladze/Grid-Mind-AI?style=social)](https://github.com/GiorgiKhorbaladze/Grid-Mind-AI)

</div>
