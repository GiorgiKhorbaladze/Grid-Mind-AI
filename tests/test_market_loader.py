import pandas as pd

from app.data.market_loader import CANONICAL_COLUMNS, clean_market_data, load_market_data


def test_demo_fallback_uses_canonical_schema():
    data = load_market_data(None)
    assert list(data.columns) == CANONICAL_COLUMNS
    assert len(data) > 0
    assert set(data["source"]) == {"demo"}


def test_clean_market_data_normalizes_schema_and_interpolates():
    raw = pd.DataFrame(
        {
            "timestamp": ["2024-01-01 00:00", "bad", "2024-01-01 02:00"],
            "price_eur_mwh": [50, 60, "70"],
            "load_mw": [1000, None, 1200],
            "solar_mw": [-5, None, 15],
        }
    )
    cleaned = clean_market_data(raw)
    assert list(cleaned.columns) == CANONICAL_COLUMNS
    assert len(cleaned) == 2
    assert cleaned["timestamp"].dt.tz is not None
    assert cleaned["wind_mw"].isna().sum() == 0
    assert cleaned["solar_mw"].min() >= 0
    assert cleaned.loc[0, "country"] == "Unknown"
