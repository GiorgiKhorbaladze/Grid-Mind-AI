# Supported Markets

GridMind AI is designed as a market-agnostic grid trading system. The exchange adapter layer normalizes all market-specific behavior so the core AI and grid engine operate identically regardless of asset class.

---

## Cryptocurrency

Crypto markets are the primary target for grid trading due to their continuous 24/7 operation and tendency to oscillate within ranges — ideal conditions for a grid strategy.

### Spot Trading

| Exchange | Status | Symbols | Notes |
|---|---|---|---|
| Binance | Supported | All USDT/BUSD pairs | Testnet available |
| Bybit | Supported | All USDT pairs | Testnet available |
| OKX | Supported | All USDT pairs | Requires passphrase |
| Coinbase Advanced | Planned v0.3 | USD pairs | |
| Kraken | Planned v0.3 | USD/EUR pairs | |

### Perpetual Futures

| Exchange | Status | Leverage | Notes |
|---|---|---|---|
| Binance Futures | Planned v0.2 | 1–125x | Isolated margin recommended |
| Bybit Perpetual | Planned v0.2 | 1–100x | |
| OKX Perpetuals | Planned v0.3 | 1–100x | |

> **Recommendation:** Start with spot trading on a testnet. Perpetuals amplify both gains and losses — only use them if you understand the liquidation mechanics.

### Recommended Crypto Pairs for Grid Trading

Pairs with moderate volatility and strong liquidity are best for grid strategies:

| Pair | Volatility Profile | Grid Mode | Notes |
|---|---|---|---|
| BTC/USDT | Medium | Adaptive | Most liquid, tight spreads |
| ETH/USDT | Medium-High | Adaptive | High volume, good oscillation |
| SOL/USDT | High | Adaptive (wide) | Larger range needed |
| BNB/USDT | Medium | Fixed or Adaptive | Tends to range-trade |
| MATIC/USDT | High | Adaptive | |

---

## Forex

Forex markets offer deep liquidity and well-defined trading sessions, making them suitable for time-aware grid strategies that adjust activity around market open/close.

### Supported Brokers

| Broker | Status | Account Types | Notes |
|---|---|---|---|
| OANDA | Supported | Practice + Live | REST + Streaming API |
| Interactive Brokers | Planned v0.3 | Paper + Live | TWS API required |
| Alpaca | Supported | Paper + Live | Commission-free |

### Recommended Pairs

| Pair | Session | Characteristics |
|---|---|---|
| EUR/USD | London / NY | Highest volume, tightest spread |
| GBP/USD | London | High volatility, good for wider grids |
| USD/JPY | Tokyo / NY | Strong trend tendencies — use with caution |
| AUD/USD | Sydney / NY | Medium volatility, range-friendly |
| EUR/GBP | London | Low volatility, tight grid spacing |

### Forex-Specific Settings

```yaml
market:
  symbol: EUR/USD
  quote_currency: USD

grid:
  mode: adaptive
  levels: 15
  spacing_pct: 0.05         # Forex moves in fractions of a percent

ai:
  sentiment:
    sources:
      news: true            # Macro news is critical for Forex
      reddit: false
      onchain: false
```

---

## US Equities

Equity grids operate only during market hours (09:30–16:00 ET). GridMind automatically suspends order activity outside of trading hours and pre-market/after-market sessions.

### Supported Brokers

| Broker | Status | Notes |
|---|---|---|
| Alpaca | Supported | Commission-free, paper trading available |
| Interactive Brokers | Planned v0.3 | Full suite of order types |
| TD Ameritrade (thinkorswim) | Planned v0.4 | |

### Recommended Instruments

| Symbol | Type | Notes |
|---|---|---|
| SPY | ETF | S&P 500 — low volatility, very liquid |
| QQQ | ETF | Nasdaq 100 — higher volatility |
| AAPL | Stock | High liquidity, moderate range trading |
| TSLA | Stock | High volatility — wide grids recommended |
| GLD | ETF | Gold proxy — good for hedging strategies |

### Equities-Specific Settings

```yaml
market:
  symbol: SPY
  quote_currency: USD
  market_hours:
    open: "09:30"
    close: "16:00"
    timezone: "America/New_York"

grid:
  mode: adaptive
  levels: 10
  spacing_pct: 0.2
```

---

## Commodities

Commodities are accessed through broker APIs (Interactive Brokers) rather than direct exchange APIs. GridMind treats them identically to other instruments once the adapter normalizes the feed.

| Instrument | Broker | Symbol | Notes |
|---|---|---|---|
| Gold (Spot) | OANDA, IB | XAU/USD | Classic safe-haven asset |
| Silver (Spot) | OANDA, IB | XAG/USD | Higher volatility than gold |
| Crude Oil (WTI) | IB | CL | Futures contract |
| Natural Gas | IB | NG | High volatility, wide grids |

---

## Market Selection Guidelines

### Grid trading works best when:

- Price action is **range-bound** rather than strongly trending
- There is **high liquidity** (tight spreads, deep order book)
- The asset has **consistent oscillation** within a predictable range
- Volatility is **moderate and stable** — not spiking or collapsing

### Signs a market is poor for grid trading:

- Strong, sustained directional trend without retracements
- Very low volume / wide bid-ask spread
- Extreme volatility spikes (e.g., around major news events)
- Illiquid off-hours (for equities and forex)

### How GridMind's AI handles market regime changes

The RL agent monitors volatility regime indicators (ATR, Bollinger Band width, realized vs. implied vol ratio). When it detects a trending regime, it automatically:

1. Widens grid spacing to reduce fill frequency
2. Reduces position size per level
3. Narrows the total grid range to follow price without over-committing capital
4. If the trend is too strong, it can recommend pausing the grid entirely pending regime reversal

This protects capital during adverse market conditions without requiring manual intervention.
