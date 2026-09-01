"""Binance combined-stream WebSocket client and kline message parsing (T8).

Sync client (`websockets.sync`) — the codebase is synchronous and the live
loop is a single sequential consumer. Reconnection policy lives in the
ingestion loop (data/live.py), not here: this module only connects, yields
raw text frames, and parses kline events.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass

from websockets.sync.client import connect

from quantlab.core.logging import get_logger
from quantlab.data.binance.models import RawKline
from quantlab.data.errors import MalformedPayloadError
from quantlab.domain.models import Timeframe

logger = get_logger(__name__)

WS_BASE_URL = "wss://stream.binance.com:9443/stream"


def stream_name(venue_symbol: str, timeframe: Timeframe) -> str:
    return f"{venue_symbol.lower()}@kline_{timeframe.value}"


def combined_stream_url(streams: list[str], base_url: str = WS_BASE_URL) -> str:
    if not streams:
        raise ValueError("at least one stream is required")
    return f"{base_url}?streams={'/'.join(streams)}"


@dataclass(frozen=True)
class WsKlineEvent:
    """One parsed kline event from the combined stream."""

    stream: str
    venue_symbol: str
    timeframe: Timeframe
    event_time_ms: int
    closed: bool
    kline: RawKline
    payload: dict[str, object]  # the full message, archived verbatim when closed


def parse_ws_message(text: str) -> WsKlineEvent | None:
    """Parse one combined-stream frame. Returns None for non-kline frames
    (subscription acks, other event types); raises MalformedPayloadError for
    kline frames that do not parse — never silently drops a broken kline."""
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise MalformedPayloadError(f"ws frame must be an object, got {type(payload).__name__}")
    data = payload.get("data")
    if not isinstance(data, dict) or data.get("e") != "kline":
        return None
    stream = payload.get("stream")
    kline_obj = data.get("k")
    if not isinstance(stream, str) or not isinstance(kline_obj, dict):
        raise MalformedPayloadError("kline frame misses 'stream' or 'k'")
    symbol = kline_obj.get("s")
    interval = kline_obj.get("i")
    event_time = data.get("E")
    closed = kline_obj.get("x")
    if not isinstance(symbol, str) or not isinstance(interval, str):
        raise MalformedPayloadError("kline frame misses symbol or interval")
    if not isinstance(event_time, int) or isinstance(event_time, bool):
        raise MalformedPayloadError("kline frame misses event time 'E'")
    if not isinstance(closed, bool):
        raise MalformedPayloadError("kline frame misses closed flag 'x'")
    try:
        timeframe = Timeframe(interval)
    except ValueError as exc:
        raise MalformedPayloadError(f"unknown kline interval {interval!r}") from exc
    return WsKlineEvent(
        stream=stream,
        venue_symbol=symbol,
        timeframe=timeframe,
        event_time_ms=event_time,
        closed=closed,
        kline=RawKline.from_ws(kline_obj),
        payload=payload,
    )


class BinanceWsClient:
    """Minimal connection wrapper: connect once, iterate text frames.
    websockets handles ping/pong keepalive internally; any disconnect
    surfaces as an exception from the iterator, handled by the caller."""

    def __init__(self, url: str, open_timeout: float = 10.0) -> None:
        self._url = url
        self._open_timeout = open_timeout

    def frames(self) -> Iterator[str]:
        with connect(self._url, open_timeout=self._open_timeout) as connection:
            logger.info("ws_connected", url=self._url)
            for frame in connection:
                yield frame if isinstance(frame, str) else frame.decode()
