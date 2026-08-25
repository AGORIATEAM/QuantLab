"""BinanceRestClient behavior: parsing, pacing, retries, rate-limit handling.

No live API involved (docs/17 §77): httpx.MockTransport plays the venue,
sleep/monotonic are recorded fakes.
"""

from __future__ import annotations

import itertools
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from fixtures_binance import KLINES_PAYLOAD, SECOND_KLINE_ROW, SYMBOL_ENTRY, VALID_KLINE_ROW

from quantlab.data.binance.client import BinanceRestClient
from quantlab.data.errors import (
    ConnectorError,
    IPBannedError,
    MalformedPayloadError,
    RetryExhaustedError,
)
from quantlab.domain.models import Timeframe

START = datetime.fromtimestamp(1756166400, tz=UTC)  # open time of VALID_KLINE_ROW
END = START + timedelta(minutes=2)


def make_client(
    handler: Callable[[httpx.Request], httpx.Response],
    sleeps: list[float] | None = None,
    **overrides: object,
) -> BinanceRestClient:
    counter = itertools.count()
    defaults: dict[str, object] = {
        "transport": httpx.MockTransport(handler),
        "sleep": sleeps.append if sleeps is not None else (lambda _s: None),
        # advances 1s per call: the default 0.2s pacing never sleeps in tests
        "monotonic": lambda: float(next(counter)),
    }
    defaults.update(overrides)
    return BinanceRestClient(**defaults)  # type: ignore[arg-type]


def test_fetch_klines_parses_payload() -> None:
    client = make_client(lambda _r: httpx.Response(200, json=KLINES_PAYLOAD))
    klines = client.fetch_klines("BTCUSDT", Timeframe.M1, START, END)
    assert [k.open_time_ms for k in klines] == [1756166400000, 1756166460000]
    assert str(klines[0].close) == "111585.19000000"


def test_fetch_klines_sends_exclusive_end_time() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=KLINES_PAYLOAD)

    make_client(handler).fetch_klines("BTCUSDT", Timeframe.M1, START, END, limit=500)
    params = seen[0].url.params
    assert params["symbol"] == "BTCUSDT"
    assert params["interval"] == "1m"
    assert params["startTime"] == "1756166400000"
    assert params["endTime"] == "1756166519999"  # end - 1ms: [start, end) contract
    assert params["limit"] == "500"


def test_fetch_klines_rejects_naive_datetimes() -> None:
    client = make_client(lambda _r: httpx.Response(200, json=[]))
    with pytest.raises(ValueError, match="timezone-aware"):
        client.fetch_klines("BTCUSDT", Timeframe.M1, datetime(2026, 1, 1), END)


def test_fetch_klines_rejects_inverted_range() -> None:
    client = make_client(lambda _r: httpx.Response(200, json=[]))
    with pytest.raises(ValueError, match="strictly after"):
        client.fetch_klines("BTCUSDT", Timeframe.M1, END, START)


def test_sub_millisecond_range_returns_empty_without_calling_the_venue() -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json=KLINES_PAYLOAD)

    result = make_client(handler).fetch_klines(
        "BTCUSDT", Timeframe.M1, START, START + timedelta(microseconds=500)
    )
    assert result == []
    assert calls == []


def test_non_ascending_klines_are_rejected() -> None:
    client = make_client(lambda _r: httpx.Response(200, json=[SECOND_KLINE_ROW, VALID_KLINE_ROW]))
    with pytest.raises(MalformedPayloadError, match="ascending"):
        client.fetch_klines("BTCUSDT", Timeframe.M1, START, END)


def test_429_honors_retry_after_then_succeeds() -> None:
    responses = [
        httpx.Response(429, headers={"Retry-After": "3"}),
        httpx.Response(200, json=KLINES_PAYLOAD),
    ]
    sleeps: list[float] = []
    client = make_client(lambda _r: responses.pop(0), sleeps=sleeps)
    klines = client.fetch_klines("BTCUSDT", Timeframe.M1, START, END)
    assert len(klines) == 2
    assert 3.0 in sleeps


def test_418_raises_ip_banned_without_retry() -> None:
    calls: list[int] = []

    def handler(_request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(418)

    with pytest.raises(IPBannedError):
        make_client(handler).fetch_klines("BTCUSDT", Timeframe.M1, START, END)
    assert len(calls) == 1


def test_timeouts_are_retried_with_backoff_then_exhausted() -> None:
    calls: list[int] = []

    def handler(_request: httpx.Request) -> httpx.Response:
        calls.append(1)
        raise httpx.ConnectTimeout("connect timed out")

    sleeps: list[float] = []
    client = make_client(handler, sleeps=sleeps, max_attempts=3, backoff_base_s=0.5)
    with pytest.raises(RetryExhaustedError, match="after 3 attempts"):
        client.fetch_klines("BTCUSDT", Timeframe.M1, START, END)
    assert len(calls) == 3
    assert sleeps == [0.5, 1.0, 2.0]  # exponential, bounded


def test_5xx_is_retried_then_succeeds() -> None:
    responses = [httpx.Response(503), httpx.Response(200, json=KLINES_PAYLOAD)]
    client = make_client(lambda _r: responses.pop(0))
    assert len(client.fetch_klines("BTCUSDT", Timeframe.M1, START, END)) == 2


def test_unexpected_4xx_raises_immediately() -> None:
    calls: list[int] = []

    def handler(_request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(400, text='{"code":-1121,"msg":"Invalid symbol."}')

    with pytest.raises(ConnectorError, match="HTTP 400"):
        make_client(handler).fetch_klines("NOPEUSDT", Timeframe.M1, START, END)
    assert len(calls) == 1


def test_pacing_sleeps_between_back_to_back_requests() -> None:
    sleeps: list[float] = []
    client = make_client(
        lambda _r: httpx.Response(200, json=[]),
        sleeps=sleeps,
        monotonic=lambda: 100.0,  # frozen clock: zero elapsed between requests
        min_request_interval_s=0.2,
    )
    client.health_check()
    client.health_check()
    assert sleeps == [pytest.approx(0.2)]


def test_used_weight_soft_limit_triggers_cooldown() -> None:
    sleeps: list[float] = []
    client = make_client(
        lambda _r: httpx.Response(200, json=[], headers={"X-MBX-USED-WEIGHT-1M": "5900"}),
        sleeps=sleeps,
        weight_soft_limit=5400,
        weight_cooldown_s=7.0,
    )
    client.fetch_klines("BTCUSDT", Timeframe.M1, START, END)
    assert 7.0 in sleeps


def test_exchange_info_parses_symbols_and_sends_compact_json() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"symbols": [SYMBOL_ENTRY]})

    infos = make_client(handler).exchange_info(["BTCUSDT", "ETHUSDT"])
    assert seen[0].url.params["symbols"] == '["BTCUSDT","ETHUSDT"]'
    assert infos[0].symbol == "BTCUSDT"
    assert str(infos[0].tick_size) == "0.01000000"


def test_health_check_true_on_ping_and_false_on_failure() -> None:
    assert make_client(lambda _r: httpx.Response(200, json={})).health_check() is True

    def failing(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("down")

    assert make_client(failing, max_attempts=1).health_check() is False
