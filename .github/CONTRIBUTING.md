# Contributing to GridMind AI

Thank you for your interest in contributing. GridMind AI is an open-source project and contributions of all kinds are welcome — bug fixes, new exchange adapters, documentation improvements, and AI model enhancements.

---

## Ways to Contribute

- **Bug reports** — Found unexpected behavior? Open an issue with the bug report template.
- **Feature requests** — Have an idea? Open a feature request issue first before building.
- **Exchange adapters** — Implement a new `ExchangeAdapter` for an unsupported broker.
- **AI improvements** — Experiment with new RL algorithms, reward functions, or sentiment sources.
- **Documentation** — Improve clarity, add examples, fix typos.
- **Tests** — Increase test coverage, add edge case tests.

---

## Development Setup

```bash
git clone https://github.com/GiorgiKhorbaladze/Grid-Mind-AI.git
cd Grid-Mind-AI

python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

pip install -e ".[dev]"
pre-commit install
```

### Running Tests

```bash
pytest                          # All tests
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests (requires Docker services)
pytest --cov=gridmind           # With coverage report
```

### Code Style

This project uses:
- **Ruff** for linting and formatting
- **mypy** for type checking
- **pre-commit** hooks to enforce both on every commit

```bash
ruff check .                    # Lint
ruff format .                   # Format
mypy gridmind/                  # Type check
```

pre-commit runs these automatically when you `git commit`. Fix any errors before pushing.

---

## Contribution Workflow

1. **Open an issue first** for anything beyond a trivial fix. This avoids duplicated effort and ensures alignment before you invest time building.
2. **Fork the repository** and create a branch from `main`:
   ```bash
   git checkout -b feature/my-feature-name
   ```
3. **Write tests** for new functionality. PRs without tests for new features will be asked to add them.
4. **Keep commits focused** — one logical change per commit, clear commit messages.
5. **Open a pull request** against `main`. Fill in the PR template completely.
6. **Respond to review feedback** promptly. PRs with no activity for 14 days may be closed.

---

## Adding an Exchange Adapter

Exchange adapters live in `gridmind/exchanges/`. To add a new one:

1. Create `gridmind/exchanges/your_exchange.py`
2. Implement the `ExchangeAdapter` protocol defined in `gridmind/exchanges/base.py`
3. Register the adapter in `gridmind/exchanges/__init__.py`
4. Add unit tests in `tests/unit/exchanges/test_your_exchange.py`
5. Add integration tests using the exchange's sandbox/testnet environment
6. Document the exchange in `docs/markets.md`

The adapter interface:

```python
class ExchangeAdapter(Protocol):
    async def place_limit_order(self, symbol: str, side: str, price: float, qty: float) -> Order: ...
    async def cancel_order(self, order_id: str) -> None: ...
    async def cancel_all_orders(self, symbol: str) -> None: ...
    async def get_open_orders(self, symbol: str) -> list[Order]: ...
    async def get_balance(self) -> dict[str, float]: ...
    async def subscribe_executions(self, callback: Callable[[Order], None]) -> None: ...
```

---

## Commit Message Format

Use the following prefixes:

| Prefix | Use for |
|---|---|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation only |
| `test:` | Tests only |
| `refactor:` | Code change that is not a fix or feature |
| `chore:` | Build, CI, tooling |

Examples:
```
feat: add Bybit perpetuals adapter
fix: prevent grid rebalance during partial fills
docs: add OKX setup guide to markets.md
test: add coverage for Kelly sizer edge cases
```

---

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). By participating, you agree to uphold a respectful, inclusive environment.

---

## Questions?

Open a [Discussion](https://github.com/GiorgiKhorbaladze/Grid-Mind-AI/discussions) or join the [Discord](https://discord.gg/gridmind).
