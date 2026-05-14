"""Abstract base class for all GridMind-AI data source loaders."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import date
from typing import Any

import requests

from data_sources.config import DEFAULT_BACKOFF_BASE, DEFAULT_RETRIES, DEFAULT_TIMEOUT
from data_sources.utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)

# Transient HTTP/network errors worth retrying
_RETRY_EXCEPTIONS: tuple[type[Exception], ...] = (
    requests.exceptions.ConnectionError,
    requests.exceptions.Timeout,
    requests.exceptions.ChunkedEncodingError,
)


class BaseLoader(ABC):
    """Template for fetching, normalizing, and caching energy datasets.

    Subclasses must implement :meth:`fetch`.  HTTP helpers ``_get`` and
    ``_get_json`` provide retry logic out of the box.
    """

    #: Human-readable source identifier used in cache keys and log messages.
    source_name: str = "unknown"

    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT,
        retries: int = DEFAULT_RETRIES,
    ) -> None:
        self.timeout = timeout
        self.retries = retries
        self._session = requests.Session()
        self._session.headers.update(
            {"User-Agent": "GridMind-AI/0.1 (+https://github.com/giorgikhorbaladze/grid-mind-ai)"}
        )

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def fetch(
        self,
        region: str,
        start: date,
        end: date,
        *,
        use_cache: bool = True,
    ) -> "pd.DataFrame":  # noqa: F821
        """Fetch and return a normalized DataFrame for the given parameters.

        Parameters
        ----------
        region:
            ISO-2 or ISO-3 country / bidding-zone code (e.g. ``"DE"``, ``"DEU"``).
        start:
            Inclusive start date.
        end:
            Inclusive end date.
        use_cache:
            When ``True`` (default) serve from the on-disk cache when
            available and not stale.
        """

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    def _get(self, url: str, **kwargs: Any) -> requests.Response:
        """GET *url* with automatic retry on transient network errors."""

        @retry_with_backoff(
            max_retries=self.retries,
            backoff_base=DEFAULT_BACKOFF_BASE,
            exceptions=_RETRY_EXCEPTIONS,
        )
        def _fetch() -> requests.Response:
            resp = self._session.get(url, timeout=self.timeout, **kwargs)
            # Raise on 4xx/5xx; HTTPError is not in _RETRY_EXCEPTIONS so it
            # propagates immediately (no point retrying 404, auth errors, etc.)
            resp.raise_for_status()
            return resp

        return _fetch()

    def _get_json(self, url: str, **kwargs: Any) -> Any:
        """GET *url* and return the parsed JSON body."""
        return self._get(url, **kwargs).json()

    def _get_bytes(self, url: str, **kwargs: Any) -> bytes:
        """GET *url* and return the raw response bytes."""
        return self._get(url, **kwargs).content

    def _get_streaming(self, url: str, dest_path: "Path", **kwargs: Any) -> None:  # noqa: F821
        """Stream *url* content to *dest_path* to avoid large in-memory buffers."""
        from pathlib import Path

        dest_path = Path(dest_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        @retry_with_backoff(
            max_retries=self.retries,
            backoff_base=DEFAULT_BACKOFF_BASE,
            exceptions=_RETRY_EXCEPTIONS,
        )
        def _stream() -> None:
            with self._session.get(url, stream=True, timeout=self.timeout, **kwargs) as resp:
                resp.raise_for_status()
                with open(dest_path, "wb") as fh:
                    for chunk in resp.iter_content(chunk_size=1 << 20):  # 1 MiB
                        fh.write(chunk)

        _stream()
        logger.debug("Streamed %s → %s", url, dest_path)

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(source={self.source_name!r})"
