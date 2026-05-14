# Configuration Reference

GridMind AI is configured via a single YAML file, defaulting to `config/config.yaml`.

```bash
# Use a custom config path
gridmind run --config /path/to/my-config.yaml
```

---

## Full Configuration Reference

```yaml
# ─────────────────────────────────────────────
# Exchange Credentials
# ─────────────────────────────────────────────
exchange:
  name: binance                   # binance | bybit | okx | oanda | alpaca
  api_key: YOUR_API_KEY
  api_secret: YOUR_API_SECRET
  passphrase: ""                  # Required for OKX only
  testnet: true                   # true = paper/testnet endpoints

# ─────────────────────────────────────────────
# Market Settings
# ─────────────────────────────────────────────
market:
  symbol: BTC/USDT
  quote_currency: USDT
  initial_capital: 10000          # Capital allocated to this bot (quote currency)
  base_currency_precision: 6      # Decimal places for base currency orders

# ─────────────────────────────────────────────
# Grid Settings
# ─────────────────────────────────────────────
grid:
  mode: adaptive                  # 'adaptive' (AI-driven) | 'fixed'
  levels: 20                      # Number of buy + sell levels each side
  spacing_pct: 0.5                # Initial grid spacing as % of price (adaptive: AI will override)
  range_pct: 10.0                 # Total grid range as % of mid-price
  rebalance_threshold_pct: 15     # Rebalance when AI-recommended spacing drifts >15% from active
  min_spacing_pct: 0.1            # Hard floor on spacing (prevents over-tight grids)
  max_spacing_pct: 5.0            # Hard ceiling on spacing

# ─────────────────────────────────────────────
# AI Engine
# ─────────────────────────────────────────────
ai:
  enabled: true
  agent: ppo                      # ppo | sac
  model_path: models/default.pt   # Path to pretrained weights (null = train from scratch)
  inference_interval_s: 60        # How often (seconds) the agent re-evaluates grid params
  device: cpu                     # cpu | cuda | mps

  sentiment:
    enabled: true
    sources:
      news: true                  # NewsAPI / CryptoPanic headlines
      reddit: true                # Reddit community sentiment
      onchain: false              # On-chain signals (requires Glassnode API key)
    glassnode_api_key: ""
    newsapi_key: ""
    poll_interval_s: 60

# ─────────────────────────────────────────────
# Risk Management
# ─────────────────────────────────────────────
risk:
  max_drawdown_pct: 15            # Halt if drawdown from peak exceeds this
  daily_loss_limit_pct: 5         # Halt for the UTC day if daily loss exceeds this
  max_open_orders: 50             # Maximum simultaneous open orders
  max_position_pct: 80            # Max % of capital deployed at once

  position_sizing:
    mode: kelly                   # kelly | fixed | percent
    kelly_fraction: 0.25          # Fractional Kelly multiplier (0.25 = quarter Kelly)
    fixed_qty: null               # Used when mode = fixed
    percent_per_level: null       # Used when mode = percent

  correlation:
    enabled: false                # Scale down positions when correlated symbols are active
    threshold: 0.75               # Pearson correlation threshold

# ─────────────────────────────────────────────
# Execution
# ─────────────────────────────────────────────
execution:
  order_type: limit               # limit | market
  time_in_force: GTC              # GTC | IOC | FOK
  post_only: true                 # Maker-only orders (avoids taker fees where supported)
  retry_attempts: 3               # Retry failed order placement up to N times
  retry_delay_s: 1.0

# ─────────────────────────────────────────────
# Data Storage
# ─────────────────────────────────────────────
database:
  postgres_url: postgresql://gridmind:password@localhost:5432/gridmind
  redis_url: redis://localhost:6379/0
  influxdb_url: http://localhost:8086
  influxdb_token: YOUR_INFLUX_TOKEN
  influxdb_org: gridmind
  influxdb_bucket: market_data

# ─────────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────────
dashboard:
  enabled: true
  host: 0.0.0.0
  port: 8501
  refresh_interval_s: 2

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
logging:
  level: INFO                     # DEBUG | INFO | WARNING | ERROR
  file: logs/gridmind.log
  rotation: daily                 # daily | size
  max_size_mb: 100
  backup_count: 7
```

---

## Multi-Bot Configuration

To run multiple bots simultaneously, use the `bots` list. Each bot entry inherits global defaults and overrides only what differs.

```yaml
# Global defaults
exchange:
  name: binance
  api_key: YOUR_KEY
  api_secret: YOUR_SECRET
  testnet: true

risk:
  max_drawdown_pct: 15

# Per-bot overrides
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
      spacing_pct: 0.4
      mode: adaptive

  - symbol: SOL/USDT
    capital: 2000
    grid:
      levels: 15
      spacing_pct: 0.8
      mode: fixed           # Override: use fixed grid for SOL
```

---

## Environment Variable Overrides

Any config value can be overridden via environment variable using the prefix `GRIDMIND_` and double underscores for nesting:

```bash
export GRIDMIND_EXCHANGE__API_KEY=abc123
export GRIDMIND_EXCHANGE__TESTNET=false
export GRIDMIND_RISK__MAX_DRAWDOWN_PCT=10
export GRIDMIND_LOGGING__LEVEL=DEBUG
```

This is recommended for production deployments to avoid storing credentials in YAML files.

---

## Configuration Validation

GridMind validates the config on startup and will refuse to start if required fields are missing or values are out of range:

```bash
gridmind check --config config/config.yaml
```

```
Config validation
─────────────────────────────
✓ exchange.name          binance
✓ exchange.api_key       set
✓ exchange.api_secret    set
✓ market.symbol          BTC/USDT
✓ grid.levels            20 (valid: 2–200)
✓ risk.max_drawdown_pct  15 (valid: 1–100)
✓ database connectivity  all services reachable
✓ exchange connectivity  Binance Testnet OK

All checks passed.
```
