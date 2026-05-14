# Usage Guide

## Modes of Operation

GridMind AI has three execution modes:

| Mode | Description | Risk |
|---|---|---|
| `backtest` | Simulate strategy on historical data | None |
| `paper` | Live market data, no real orders | None |
| `live` | Real orders placed via exchange | Real money |

Always validate with `backtest` → `paper` → `live`.

---

## Backtesting

### Basic Backtest

```bash
gridmind backtest \
  --symbol BTC/USDT \
  --from 2024-01-01 \
  --to 2025-01-01 \
  --capital 10000
```

### Backtest with Custom Grid Parameters

```bash
gridmind backtest \
  --symbol ETH/USDT \
  --from 2024-06-01 \
  --to 2025-01-01 \
  --capital 5000 \
  --levels 30 \
  --spacing 0.3 \
  --mode fixed
```

### Export HTML Report

```bash
gridmind backtest --symbol BTC/USDT --from 2024-01-01 --export html
# → reports/BTC_USDT_20240101_20250101.html
```

### Python API

```python
from gridmind import BacktestEngine
from gridmind.strategies import AdaptiveGridStrategy
from gridmind.data import HistoricalFeed

strategy = AdaptiveGridStrategy(
    symbol="BTC/USDT",
    initial_capital=10_000,
    grid_levels=20,
    spacing_pct=0.5,
    ai_mode=True,
)

engine = BacktestEngine(
    strategy=strategy,
    feed=HistoricalFeed.from_csv("data/btc_1m.csv"),
    commission=0.001,
    slippage=0.0005,
)

results = engine.run()

# Print summary
results.summary()

# Access metrics directly
print(f"Total Return: {results.total_return_pct:.1f}%")
print(f"Max Drawdown: {results.max_drawdown_pct:.1f}%")
print(f"Sharpe Ratio: {results.sharpe_ratio:.2f}")

# Export
results.export("html", path="reports/")
results.export("csv", path="reports/")
```

---

## Paper Trading

Paper trading uses live exchange data but never places real orders. Ideal for validating live behavior.

```bash
gridmind run --mode paper --symbol BTC/USDT --capital 10000
```

The bot logs all virtual orders and computes real-time P&L exactly as it would in live mode.

---

## Live Trading

> **Warning:** Live mode places real orders and exposes real capital. Ensure you have tested thoroughly in `paper` mode first and configured risk limits in `config.yaml`.

```bash
gridmind run --mode live --symbol BTC/USDT
```

### Emergency Stop

```bash
gridmind stop --symbol BTC/USDT --cancel-orders
```

This cancels all open grid orders and closes any open positions at market.

---

## Running Multiple Symbols

GridMind AI supports concurrent multi-symbol operation:

```bash
gridmind run --mode paper \
  --symbol BTC/USDT \
  --symbol ETH/USDT \
  --symbol SOL/USDT
```

Or via configuration:

```yaml
bots:
  - symbol: BTC/USDT
    capital: 5000
    grid:
      levels: 20
      mode: adaptive

  - symbol: ETH/USDT
    capital: 3000
    grid:
      levels: 25
      mode: adaptive

  - symbol: SOL/USDT
    capital: 2000
    grid:
      levels: 15
      mode: fixed
      spacing_pct: 0.8
```

---

## Training the AI Agent

The RL agent can be retrained on custom historical data to adapt to specific market conditions.

```bash
# Train on 2 years of BTC/USDT 1-minute data
gridmind train \
  --symbol BTC/USDT \
  --from 2023-01-01 \
  --to 2025-01-01 \
  --epochs 300 \
  --device cuda \
  --save-path models/btc_agent_v1.pt
```

```python
from gridmind.ai import PPOAgent, TrainingEnvironment
from gridmind.data import HistoricalFeed

env = TrainingEnvironment(
    feed=HistoricalFeed.from_exchange("BTC/USDT", "1m", days=730),
    initial_capital=10_000,
    commission=0.001,
)

agent = PPOAgent(
    state_dim=env.observation_space.shape[0],
    action_dim=env.action_space.n,
    lr=3e-4,
    gamma=0.99,
)

agent.train(env, epochs=300, device="cuda")
agent.save("models/btc_agent_v1.pt")
```

---

## Hyperparameter Optimization

Use the `optimize` command to search for the best static grid parameters using Optuna:

```bash
gridmind optimize \
  --symbol ETH/USDT \
  --from 2024-01-01 \
  --to 2025-01-01 \
  --trials 500 \
  --metric sharpe_ratio
```

```
Optimization complete — 500 trials
─────────────────────────────────────
Best Parameters:
  levels:       22
  spacing_pct:  0.42
  range_pct:    12.5

Best Metrics:
  Sharpe Ratio: 3.87
  Total Return: +161.4%
  Max Drawdown: -8.1%
```

---

## Dashboard

Launch the live monitoring dashboard:

```bash
gridmind dashboard
# → http://localhost:8501
```

The dashboard displays:
- Active grid visualization with filled/open levels
- Real-time P&L curve
- Open orders and positions
- Sentiment indicator (bullish / neutral / bearish)
- Risk metrics: drawdown, exposure, Kelly fraction
- Trade log with entry/exit details

---

## Downloading Historical Data

```bash
# Download 1-minute OHLCV data from Binance
gridmind data download \
  --exchange binance \
  --symbol BTC/USDT \
  --timeframe 1m \
  --from 2023-01-01 \
  --to 2025-01-01 \
  --output data/btc_usdt_1m.csv
```

---

## Logging

Logs are written to `logs/gridmind.log` by default.

```bash
# Stream live logs
tail -f logs/gridmind.log

# Set log level
gridmind run --symbol BTC/USDT --log-level DEBUG
```

Log levels: `DEBUG` | `INFO` | `WARNING` | `ERROR`

---

*See [docs/architecture.md](architecture.md) for a deep-dive into how GridMind AI makes decisions.*
