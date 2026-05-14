"""ENTSO-E Transparency Platform loader (optional).

Requires a free API key obtained by registering at:
  https://transparency.entsoe.eu/

Set the key via the environment variable::

    export ENTSOE_API_KEY="your-key-here"

If the key is absent this loader raises :class:`ENTSOEKeyMissingError` on
construction so dependent code can decide whether to skip or abort.

Source:  https://transparency.entsoe.eu/
API:     https://web-api.tp.entsoe.eu/api
License: Public (free registration)

ENTSO-E returns XML.  This implementation parses the Actual Generation
Per Type document (document type A75, process type A16) directly without
external XML-parsing dependencies beyond the standard library.
"""
from __future__ import annotations

import logging
import os
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from typing import Optional

import pandas as pd

from data_sources.cache.file_cache import FileCache
from data_sources.config import (
    CACHE_TTL,
    ENTSOE_API_KEY_ENV,
    ENTSOE_API_URL,
    FUEL_TYPE_COL,
    REGION_COL,
    SOURCE_COL,
    TIMESTAMP_COL,
    UNIT_COL,
    VALUE_COL,
)
from data_sources.loaders.base import BaseLoader
from data_sources.schemas.models import validate_dataframe, _empty_normalized_frame
from data_sources.utils.timezone import normalize_series_to_utc

logger = logging.getLogger(__name__)


class ENTSOEKeyMissingError(RuntimeError):
    """Raised when ENTSOE_API_KEY is not set in the environment."""


# ---------------------------------------------------------------------------
# ENTSO-E psr_type codes → GridMind fuel_type
# ---------------------------------------------------------------------------
_PSR_TYPE_MAP: dict[str, str] = {
    "B01": "biomass",
    "B02": "lignite",
    "B03": "coal",        # fossil coal-derived gas
    "B04": "gas",
    "B05": "coal",        # hard coal
    "B06": "oil",
    "B07": "oil",         # oil shale
    "B08": "other",       # peat
    "B09": "hydro",       # pumped storage
    "B10": "hydro",       # run-of-river / pondage
    "B11": "hydro",       # reservoir
    "B12": "hydro",       # marine
    "B13": "nuclear",
    "B14": "other",       # other renewable
    "B15": "solar",
    "B16": "wind_offshore",
    "B17": "wind_onshore",
    "B18": "other",       # waste
    "B19": "other",       # other
    "B20": "other",       # AC link
}

# ENTSO-E XML namespaces used in A75 documents
_NS = {
    "gl": "urn:iec62325.351:tc57wg16:451-6:generationloaddocument:3:0",
    "base": "urn:iec62325.351:tc57wg16:451-1:coredatadocument:2:0",
}


class ENTSOELoader(BaseLoader):
    """Loader for ENTSO-E actual generation per unit type (document A75).

    Parameters
    ----------
    api_key:
        Override the API key instead of reading from the environment.
    cache_dir:
        Override the default cache root.
    """

    source_name = "entsoe"

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_dir=None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._api_key = api_key or os.environ.get(ENTSOE_API_KEY_ENV, "")
        if not self._api_key:
            raise ENTSOEKeyMissingError(
                f"ENTSO-E API key not found.  Set the environment variable "
                f"{ENTSOE_API_KEY_ENV} or pass api_key= to ENTSOELoader."
            )
        cache_kwargs = {"cache_dir": cache_dir} if cache_dir else {}
        self._cache = FileCache("entsoe", ttl_seconds=CACHE_TTL["entsoe"], **cache_kwargs)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def fetch(
        self,
        region: str,
        start: date,
        end: date,
        *,
        use_cache: bool = True,
    ) -> pd.DataFrame:
        """Return hourly actual generation per fuel type for *region*.

        Parameters
        ----------
        region:
            ENTSO-E EIC bidding zone code (e.g. ``"10Y1001A1001A83F"`` for
            Germany, or a short alias like ``"DE"`` resolved via the built-in
            map).
        start / end:
            Inclusive date range (UTC days).
        """
        eic = _resolve_eic(region)
        cache_key = self._cache.cache_key(self.source_name, eic, str(start), str(end))

        if use_cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        logger.info("Fetching ENTSO-E data for EIC=%s %s → %s", eic, start, end)
        df = self._fetch_xml(eic, start, end)
        if use_cache and not df.empty:
            self._cache.set(cache_key, df)
        return df

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _fetch_xml(self, eic: str, start: date, end: date) -> pd.DataFrame:
        params = {
            "securityToken": self._api_key,
            "documentType": "A75",
            "processType": "A16",
            "in_Domain": eic,
            "outBiddingZone_Domain": eic,
            "periodStart": _entsoe_datetime(start),
            "periodEnd": _entsoe_datetime(end, end_of_day=True),
        }
        try:
            resp = self._get(ENTSOE_API_URL, params=params)
        except Exception as exc:
            logger.error("ENTSO-E API request failed: %s", exc)
            return _empty_normalized_frame()

        return self._parse_xml(resp.content, eic)

    def _parse_xml(self, content: bytes, region: str) -> pd.DataFrame:
        """Parse ENTSO-E A75 XML into a normalized DataFrame."""
        try:
            root = ET.fromstring(content)
        except ET.ParseError as exc:
            logger.error("ENTSO-E XML parse error: %s", exc)
            return _empty_normalized_frame()

        # Check for acknowledgement / error document
        if "Acknowledgement_MarketDocument" in root.tag:
            reason = root.find(".//{*}Reason/{*}text")
            msg = reason.text if reason is not None else "unknown"
            logger.error("ENTSO-E API returned error: %s", msg)
            return _empty_normalized_frame()

        records: list[dict] = []

        for ts_elem in root.findall(".//{*}TimeSeries"):
            psr_elem = ts_elem.find(".//{*}MktPSRType/{*}psrType")
            psr_code = psr_elem.text.strip() if psr_elem is not None else "B19"
            fuel_type = _PSR_TYPE_MAP.get(psr_code, "other")
            unit_elem = ts_elem.find(".//{*}quantity_Measure_Unit.name")
            unit = (unit_elem.text.strip() if unit_elem is not None else "MW").upper()

            for period in ts_elem.findall(".//{*}Period"):
                start_elem = period.find("{*}timeInterval/{*}start")
                res_elem = period.find("{*}resolution")
                if start_elem is None or res_elem is None:
                    continue
                period_start = datetime.fromisoformat(
                    start_elem.text.replace("Z", "+00:00")
                )
                resolution = pd.Timedelta(res_elem.text)

                for point in period.findall("{*}Point"):
                    pos_elem = point.find("{*}position")
                    qty_elem = point.find("{*}quantity")
                    if pos_elem is None or qty_elem is None:
                        continue
                    position = int(pos_elem.text)
                    ts = period_start + (position - 1) * resolution
                    records.append(
                        {
                            TIMESTAMP_COL: ts,
                            REGION_COL: region,
                            FUEL_TYPE_COL: fuel_type,
                            VALUE_COL: float(qty_elem.text),
                            UNIT_COL: unit,
                            SOURCE_COL: self.source_name,
                        }
                    )

        if not records:
            return _empty_normalized_frame()

        df = pd.DataFrame(records)
        df[TIMESTAMP_COL] = normalize_series_to_utc(df[TIMESTAMP_COL])
        return validate_dataframe(df, source=self.source_name)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entsoe_datetime(d: date, end_of_day: bool = False) -> str:
    """Format a date as ENTSO-E periodStart/End string (UTC, YYYYMMDDHHММ)."""
    hour = 23 if end_of_day else 0
    return f"{d.year:04d}{d.month:02d}{d.day:02d}{hour:02d}00"


def _resolve_eic(region: str) -> str:
    """Map common ISO-2 codes to ENTSO-E EIC bidding-zone codes."""
    _EIC_MAP: dict[str, str] = {
        "DE": "10Y1001A1001A83F",
        "FR": "10YFR-RTE------C",
        "GB": "10YGB----------A",
        "ES": "10YES-REE------0",
        "IT": "10YIT-GRTN-----B",
        "PL": "10YPL-AREA-----S",
        "NL": "10YNL----------L",
        "BE": "10YBE----------2",
        "AT": "10YAT-APG------L",
        "CH": "10YCH-SWISSGRIDZ",
        "DK": "10Y1001A1001A65H",  # DK1+DK2 combined
        "SE": "10YSE-1--------K",
        "NO": "10YNO-0--------C",
        "FI": "10YFI-1--------U",
        "CZ": "10YCZ-CEPS-----N",
        "HU": "10YHU-MAVIR----U",
        "RO": "10YRO-TEL------P",
    }
    upper = region.upper()
    # If it already looks like a full EIC (16 chars), return as-is
    if len(upper) >= 10:
        return upper
    result = _EIC_MAP.get(upper)
    if result is None:
        raise ValueError(
            f"No EIC code known for region '{region}'. "
            f"Pass the full EIC directly (e.g. '10Y1001A1001A83F')."
        )
    return result
