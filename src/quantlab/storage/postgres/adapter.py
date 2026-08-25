"""PostgreSQL adapters implementing the repository interfaces.

Phase 0 scope: enough to seed reference data, persist candles immutably and
write audit events. Extended in Phase 1 (Data Platform).
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Sequence
from datetime import datetime

import psycopg

from quantlab.audit.events import AuditEvent
from quantlab.domain.models import Candle, Timeframe


class PostgresCandleRepository:
    def __init__(self, conninfo: str) -> None:
        self._conninfo = conninfo

    def insert_many(self, candles: Sequence[Candle]) -> int:
        if not candles:
            return 0
        query = """
            INSERT INTO candles (
                candle_id, instrument_id, timeframe, open_time, close_time,
                open, high, low, close, volume, trade_count, source, data_version
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (instrument_id, timeframe, open_time, source) DO NOTHING
        """
        inserted = 0
        with psycopg.connect(self._conninfo) as conn, conn.cursor() as cur:
            for c in candles:
                cur.execute(
                    query,
                    (
                        c.candle_id,
                        c.instrument_id,
                        c.timeframe.value,
                        c.open_time,
                        c.close_time,
                        c.open,
                        c.high,
                        c.low,
                        c.close,
                        c.volume,
                        c.trade_count,
                        c.source,
                        c.data_version,
                    ),
                )
                inserted += cur.rowcount
            conn.commit()
        return inserted

    def read_range(
        self,
        instrument_id: uuid.UUID,
        timeframe: Timeframe,
        start: datetime,
        end: datetime,
    ) -> list[Candle]:
        query = """
            SELECT candle_id, instrument_id, timeframe, open_time, close_time,
                   open, high, low, close, volume, trade_count, source, data_version
            FROM candles
            WHERE instrument_id = %s AND timeframe = %s
              AND open_time >= %s AND open_time < %s
            ORDER BY open_time ASC
        """
        with psycopg.connect(self._conninfo) as conn, conn.cursor() as cur:
            cur.execute(query, (instrument_id, timeframe.value, start, end))
            rows = cur.fetchall()
        return [
            Candle(
                candle_id=r[0],
                instrument_id=r[1],
                timeframe=Timeframe(r[2]),
                open_time=r[3],
                close_time=r[4],
                open=r[5],
                high=r[6],
                low=r[7],
                close=r[8],
                volume=r[9],
                trade_count=r[10],
                source=r[11],
                data_version=r[12],
            )
            for r in rows
        ]


class PostgresAuditEventWriter:
    def __init__(self, conninfo: str) -> None:
        self._conninfo = conninfo

    def write(self, event: AuditEvent) -> None:
        query = """
            INSERT INTO audit_events (
                audit_event_id, actor_type, actor_id, action, resource_type,
                resource_id, environment, request_id, correlation_id, result, metadata
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        with psycopg.connect(self._conninfo) as conn, conn.cursor() as cur:
            cur.execute(
                query,
                (
                    event.audit_event_id,
                    event.actor_type.value,
                    event.actor_id,
                    event.action,
                    event.resource_type,
                    event.resource_id,
                    event.environment,
                    event.request_id,
                    event.correlation_id,
                    event.result.value,
                    json.dumps(event.metadata) if event.metadata is not None else None,
                ),
            )
            conn.commit()
