# Installation Guide

## Requirements

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.11+ | 3.12 recommended |
| Docker | 24.0+ | For infrastructure services |
| Docker Compose | 2.20+ | Bundled with Docker Desktop |
| RAM | 8 GB minimum | 16 GB recommended for AI training |
| GPU | Optional | CUDA 11.8+ for accelerated training |

---

## Installation Methods

### Method 1: pip (Recommended for users)

```bash
pip install gridmind-ai
```

### Method 2: From Source (Recommended for contributors)

```bash
git clone https://github.com/GiorgiKhorbaladze/Grid-Mind-AI.git
cd Grid-Mind-AI

python -m venv .venv
source .venv/bin/activate       # macOS / Linux
# .venv\Scripts\activate        # Windows

pip install -e ".[dev]"
```

### Method 3: Docker

```bash
docker pull ghcr.io/giorgikhorbaladze/gridmind-ai:latest

docker run -it \
  -v $(pwd)/config:/app/config \
  -p 8501:8501 \
  ghcr.io/giorgikhorbaladze/gridmind-ai:latest \
  gridmind run --mode paper --symbol BTC/USDT
```

---

## Infrastructure Setup

GridMind AI uses three backing services managed via Docker Compose:

| Service | Port | Purpose |
|---|---|---|
| PostgreSQL | 5432 | Trade history, configuration, audit log |
| Redis | 6379 | Real-time price cache, order state |
| InfluxDB | 8086 | Time-series metrics and analytics |

```bash
# Start all services
docker compose up -d

# Verify services are healthy
docker compose ps

# Stop services
docker compose down
```

---

## Configuration

Copy the example configuration and fill in your credentials:

```bash
cp config/config.example.yaml config/config.yaml
```

### Minimal Configuration

```yaml
exchange:
  name: binance          # binance | bybit | okx | oanda | alpaca
  api_key: YOUR_KEY
  api_secret: YOUR_SECRET
  testnet: true

market:
  symbol: BTC/USDT
  initial_capital: 1000

grid:
  mode: adaptive
  levels: 20
```

### Full Configuration Reference

See [docs/configuration.md](configuration.md) for all available options.

---

## Exchange API Setup

### Binance

1. Log in to [Binance](https://binance.com) → Account → API Management
2. Create a new API key with **Spot Trading** permissions
3. Whitelist your IP address
4. Copy key and secret to `config/config.yaml`

> **Testnet:** Use [Binance Testnet](https://testnet.binance.vision/) for safe paper trading.

### Bybit

1. Log in to [Bybit](https://bybit.com) → Account → API
2. Create key with **Read + Trade** permissions
3. Set `testnet: true` to use Bybit Testnet

### OANDA (Forex)

1. Create a [practice account](https://fxtrade.oanda.com/your_account/fxtrade/register/gate?utm_source=oandaapi) at OANDA
2. Generate an API token from Account Settings
3. Your account ID is displayed on the dashboard

---

## Verify Installation

```bash
gridmind --version
# GridMind AI v0.1.0

gridmind check
# ✓ Python 3.12.2
# ✓ Config loaded: config/config.yaml
# ✓ PostgreSQL connection
# ✓ Redis connection
# ✓ Exchange connectivity (Binance Testnet)
# ✓ All systems operational
```

---

## GPU Acceleration (Optional)

To train the RL agent with CUDA acceleration:

```bash
# Install PyTorch with CUDA 12.1
pip install torch --index-url https://download.pytorch.org/whl/cu121

# Verify GPU availability
python -c "import torch; print(torch.cuda.is_available())"
# True

# Train with GPU
gridmind train --symbol BTC/USDT --device cuda
```

---

## Troubleshooting

### `ModuleNotFoundError` after install

Ensure your virtual environment is activated:

```bash
source .venv/bin/activate
pip install -e ".[dev]"
```

### Docker services fail to start

Check for port conflicts:

```bash
lsof -i :5432   # PostgreSQL
lsof -i :6379   # Redis
```

### Exchange connection refused

- Verify API keys are correct and not expired
- Check IP whitelist settings on your exchange
- Confirm `testnet: true/false` matches your key type

---

*For additional help, open an issue or join the [Discord](https://discord.gg/gridmind).*
