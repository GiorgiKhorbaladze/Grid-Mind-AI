"""Central configuration constants for data source retrieval."""
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------
CACHE_DIR = Path(os.environ.get("GRIDMIND_CACHE_DIR", Path.home() / ".cache" / "gridmind"))

# ---------------------------------------------------------------------------
# HTTP defaults
# ---------------------------------------------------------------------------
DEFAULT_TIMEOUT = 60        # seconds per request
DEFAULT_RETRIES = 3
DEFAULT_BACKOFF_BASE = 2.0  # exponential backoff base (seconds)

# ---------------------------------------------------------------------------
# Open Power System Data (OPSD)
# ---------------------------------------------------------------------------
OPSD_DATAPACKAGE_URL = (
    "https://data.open-power-system-data.org/time_series/datapackage.json"
)
OPSD_FALLBACK_CSV_URL = (
    "https://data.open-power-system-data.org/time_series/latest/"
    "time_series_60min_singleindex.csv"
)
# Timestamp column name used in OPSD CSV files
OPSD_UTC_COLUMN = "utc_timestamp"
# Chunk size for streaming large OPSD CSV files
OPSD_CHUNK_SIZE = 50_000

# ---------------------------------------------------------------------------
# Ember Climate
# ---------------------------------------------------------------------------
EMBER_API_BASE = "https://api.ember-climate.org/v1"
EMBER_GENERATION_MONTHLY = f"{EMBER_API_BASE}/electricity-generation/monthly"
EMBER_GENERATION_YEARLY = f"{EMBER_API_BASE}/electricity-generation/yearly"

# ---------------------------------------------------------------------------
# Open-Meteo
# ---------------------------------------------------------------------------
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

# Default hourly variables requested for grid-relevant weather
OPEN_METEO_HOURLY_VARS = [
    "temperature_2m",
    "shortwave_radiation",
    "wind_speed_10m",
    "wind_direction_10m",
    "precipitation",
    "cloudcover",
]

# Mapping from ISO-2 region code to (latitude, longitude) for weather queries
REGION_COORDS: dict[str, tuple[float, float]] = {
    "DE": (51.2, 10.5),
    "FR": (46.2, 2.2),
    "GB": (52.4, -1.5),
    "ES": (40.2, -3.7),
    "IT": (42.5, 12.6),
    "PL": (52.1, 19.4),
    "NL": (52.3, 5.3),
    "BE": (50.5, 4.5),
    "AT": (47.5, 13.5),
    "CH": (46.8, 8.2),
    "DK": (56.1, 10.0),
    "SE": (59.7, 14.9),
    "NO": (61.9, 10.2),
    "FI": (64.0, 26.0),
    "CZ": (49.8, 15.5),
    "HU": (47.1, 19.5),
    "RO": (45.9, 24.9),
    "US": (39.0, -95.0),
    "AU": (-25.3, 133.8),
    "JP": (36.2, 138.3),
}

# ---------------------------------------------------------------------------
# ENTSO-E (optional — requires free API key)
# ---------------------------------------------------------------------------
ENTSOE_API_URL = "https://web-api.tp.entsoe.eu/api"
ENTSOE_API_KEY_ENV = "ENTSOE_API_KEY"

# ---------------------------------------------------------------------------
# Cache TTL per source (seconds)
# ---------------------------------------------------------------------------
CACHE_TTL: dict[str, int] = {
    "opsd": 86_400 * 7,   # 7 days — OPSD releases infrequently
    "ember": 86_400,      # 1 day
    "open_meteo": 3_600,  # 1 hour — forecasts change often
    "entsoe": 3_600,      # 1 hour
}

# ---------------------------------------------------------------------------
# Normalized column names (shared schema contract)
# ---------------------------------------------------------------------------
TIMESTAMP_COL = "timestamp"
REGION_COL = "region"
FUEL_TYPE_COL = "fuel_type"
VALUE_COL = "value_mw"
UNIT_COL = "unit"
SOURCE_COL = "source"
