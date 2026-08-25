"""Binance spot public REST client (no account, no API key).

Public market data endpoints only: /api/v3/ping, /api/v3/exchangeInfo,
/api/v3/klines. External-call discipline per 17-AI-Development-Protocol
§35-§37: mandatory timeout, bounded retries with exponential backoff,
request pacing, Retry-After honored on 429, hard stop on 418 (IP ban).

Clock and sleep are injectable so every timing behavior is unit-testable
(docs/17 §34); the httpx transport is injectable for offline tests (§77).
"""

from __future__ import annotations

import itertools
import json
import time
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime

import httpx

from quantlab.core.logging import get_logger
from quantlab.core.timeutils import require_utc
from quantlab.data.binance.models import RawKline, SymbolInfo
from quantlab.data.errors import (
    ConnectorError,
    IPBannedError,
    MalformedPayloadError,
    RetryExhaustedError,
)
from quantlab.domain.models import Timeframe

logger = get_logger(__name__)

BINANCE_SPOT_BASE_URL = "https://api.binance.com"
MAX_KLINES_PER_REQUEST = 1000
USED_WEIGHT_HEADER = "X-MBX-USED-WEIGHT-1M"


class BinanceRestClient:
    def __init__(
        self,
        base_url: str = BINANCE_SPOT_BASE_URL,
        *,
        timeout_s: float = 10.0,
        max_attempts: int = 4,
        backoff_base_s: float = 0.5,
        min_request_interval_s: float = 0.2,
        weight_soft_limit: int = 5400,
        weight_cooldown_s: float = 10.0,
        sleep: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        self._client = httpx.Client(base_url=base_url, timeout=timeout_s, transport=transport)
        self._max_attempts = max_attempts
        self._backoff_base_s = backoff_base_s
        self._min_request_interval_s = min_request_interval_s
        self._weight_soft_limit = weight_soft_limit
        self._weight_cooldown_s = weight_cooldown_s
        self._sleep = sleep
        self._monotonic = monotonic
        self._last_request_at: float | None = None

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> BinanceRestClient:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    # -- public API ---------------------------------------------------------

    def fetch_klines(
        self,
        venue_symbol: str,
        timeframe: Timeframe,
        start: datetime,
        end: datetime,
        limit: int = MAX_KLINES_PER_REQUEST,
    ) -> list[RawKline]:
        """Up to `limit` klines with open_time in [start, end), ascending.

        Binance's endTime is inclusive, so it is sent as end - 1ms to keep
        the [start, end) contract used everywhere else in QuantLab.
        """
        start = require_utc(start, "start")
        end = require_utc(end, "end")
        if end <= start:
            raise ValueError("end must be strictly after start")
        if not 1 <= limit <= MAX_KLINES_PER_REQUEST:
            raise ValueError(f"limit must be in [1, {MAX_KLINES_PER_REQUEST}]")
        start_ms = int(start.timestamp() * 1000)
        end_ms = int(end.timestamp() * 1000) - 1
        if end_ms < start_ms:
            return []

        response = self._request(
            "/api/v3/klines",
            {
                "symbol": venue_symbol,
                "interval": timeframe.value,
                "startTime": start_ms,
                "endTime": end_ms,
                "limit": limit,
            },
        )
        payload = response.json()
        if not isinstance(payload, list):
            raise MalformedPayloadError(f"klines response must be an array, got {payload!r}")
        klines = [RawKline.from_api(row) for row in payload]
        for previous, current in itertools.pairwise(klines):
            if current.open_time_ms <= previous.open_time_ms:
                raise MalformedPayloadError("klines are not strictly ascending by open time")
        return klines

    def exchange_info(self, venue_symbols: Sequence[str]) -> list[SymbolInfo]:
        """Instrument metadata for the given venue symbols (e.g. BTCUSDT)."""
        if not venue_symbols:
            raise ValueError("venue_symbols must not be empty")
        params = {"symbols": json.dumps(list(venue_symbols), separators=(",", ":"))}
        response = self._request("/api/v3/exchangeInfo", params)
        payload = response.json()
        symbols = payload.get("symbols") if isinstance(payload, dict) else None
        if not isinstance(symbols, list):
            raise MalformedPayloadError("exchangeInfo response misses the 'symbols' array")
        return [SymbolInfo.from_api(entry) for entry in symbols]

    def health_check(self) -> bool:
        try:
            self._request("/api/v3/ping")
        except ConnectorError:
            return False
        return True

    # -- transport ----------------------------------------------------------

    def _request(self, path: str, params: Mapping[str, str | int] | None = None) -> httpx.Response:
        last_failure = "no attempt made"
        for attempt in range(self._max_attempts):
            self._pace()
            try:
                response = self._client.get(path, params=params)
            except httpx.TransportError as exc:
                last_failure = f"{type(exc).__name__}: {exc}"
                logger.warning("binance_request_failed", path=path, attempt=attempt, error=str(exc))
                self._sleep(self._backoff_base_s * 2**attempt)
                continue

            self._respect_used_weight(response)
            if response.status_code == 200:
                return response
            if response.status_code == 418:
                raise IPBannedError(f"IP banned by venue (HTTP 418) on {path}")
            if response.status_code == 429:
                retry_after = _retry_after_seconds(response)
                last_failure = f"HTTP 429 (Retry-After: {retry_after}s)"
                logger.warning("binance_rate_limited", path=path, retry_after_s=retry_after)
                self._sleep(retry_after)
                continue
            if 500 <= response.status_code < 600:
                last_failure = f"HTTP {response.status_code}"
                logger.warning("binance_server_error", path=path, status=response.status_code)
                self._sleep(self._backoff_base_s * 2**attempt)
                continue
            raise ConnectorError(
                f"unexpected HTTP {response.status_code} on {path}: {response.text[:200]}"
            )
        raise RetryExhaustedError(
            f"{path} failed after {self._max_attempts} attempts (last: {last_failure})"
        )

    def _pace(self) -> None:
        if self._last_request_at is not None:
            wait = self._min_request_interval_s - (self._monotonic() - self._last_request_at)
            if wait > 0:
                self._sleep(wait)
        self._last_request_at = self._monotonic()

    def _respect_used_weight(self, response: httpx.Response) -> None:
        raw = response.headers.get(USED_WEIGHT_HEADER, "")
        if raw.isdigit() and int(raw) >= self._weight_soft_limit:
            logger.warning("binance_weight_soft_limit", used_weight=int(raw))
            self._sleep(self._weight_cooldown_s)


def _retry_after_seconds(response: httpx.Response) -> float:
    raw = response.headers.get("Retry-After", "")
    try:
        return max(float(raw), 1.0)
    except ValueError:
        return 1.0
