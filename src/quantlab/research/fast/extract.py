"""Phase 1 of ADR-0003: one fail-closed replay pass materialized as plain
tuples for the float hot loop.

The Decimal -> float conversion happens HERE and only here (ADR-0003
décision 2): each replay event becomes
(is_5m, is_warmup, open_epoch_s, open, high, low, close) with prices as
float64. The merged availability order of the replay is preserved.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from quantlab.core.clock import SimulatedClock
from quantlab.data.datasets import SeriesResolver
from quantlab.data.replay import replay_candles
from quantlab.domain.models import Timeframe
from quantlab.storage.postgres.adapter import (
    PostgresAuditEventWriter,
    PostgresCandleSnapshotFactory,
    PostgresDataQualityEventRepository,
    PostgresDatasetRepository,
    PostgresInstrumentRepository,
    PostgresVenueRepository,
)

Row = tuple[bool, bool, int, float, float, float, float]


def extract_rows(
    url: str,
    dataset_name: str,
    version: str,
    symbol: str,
    start: datetime,
    end: datetime,
    lookback_days: int = 30,
) -> list[Row]:
    datasets = PostgresDatasetRepository(url)
    resolve = SeriesResolver(PostgresVenueRepository(url), PostgresInstrumentRepository(url))
    rows: list[Row] = []
    for event in replay_candles(
        PostgresCandleSnapshotFactory(url),
        datasets,
        resolve,
        PostgresDataQualityEventRepository(url),
        PostgresAuditEventWriter(url),
        dataset_name,
        version,
        SimulatedClock(start),
        symbols=[symbol],
        timeframes=[Timeframe.M5, Timeframe.H1],
        start=start,
        end=end,
        lookback=timedelta(days=lookback_days),
    ):
        c = event.candle
        rows.append(
            (
                event.series.timeframe is Timeframe.M5,
                event.is_warmup,
                int(c.open_time.timestamp()),
                float(c.open),
                float(c.high),
                float(c.low),
                float(c.close),
            )
        )
    return rows


MultiRow = tuple[int, bool, int, float, float, float, float]


def extract_rows_multi(
    url: str,
    dataset_name: str,
    version: str,
    symbol: str,
    start: datetime,
    end: datetime,
    timeframes: list[Timeframe],
    lookback_days: int = 30,
) -> list[MultiRow]:
    """Like extract_rows for an arbitrary timeframe list: the first tuple
    element is the INDEX of the event's timeframe in `timeframes`."""
    datasets = PostgresDatasetRepository(url)
    resolve = SeriesResolver(PostgresVenueRepository(url), PostgresInstrumentRepository(url))
    index = {tf: i for i, tf in enumerate(timeframes)}
    rows: list[MultiRow] = []
    for event in replay_candles(
        PostgresCandleSnapshotFactory(url),
        datasets,
        resolve,
        PostgresDataQualityEventRepository(url),
        PostgresAuditEventWriter(url),
        dataset_name,
        version,
        SimulatedClock(start),
        symbols=[symbol],
        timeframes=timeframes,
        start=start,
        end=end,
        lookback=timedelta(days=lookback_days),
    ):
        c = event.candle
        rows.append(
            (
                index[event.series.timeframe],
                event.is_warmup,
                int(c.open_time.timestamp()),
                float(c.open),
                float(c.high),
                float(c.low),
                float(c.close),
            )
        )
    return rows
