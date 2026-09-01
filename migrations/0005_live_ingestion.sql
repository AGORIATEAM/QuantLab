-- Live WebSocket ingestion (T8, ADR-0001 addendum A).
-- raw_ws_messages: append-only journal of closed-kline WS messages, exactly
-- as pushed by the venue (no deduplication — A.2). candles_canonical: one
-- candle per (instrument, timeframe, open_time), REST precedence — the read
-- path for live consumers while research keeps reading pure REST (A.4).

BEGIN;

CREATE TABLE raw_ws_messages (
    message_id UUID PRIMARY KEY,
    received_at TIMESTAMPTZ NOT NULL,
    stream TEXT NOT NULL,
    payload JSONB NOT NULL
);

CREATE INDEX raw_ws_messages_stream_received
    ON raw_ws_messages(stream, received_at DESC);

CREATE TRIGGER raw_ws_messages_append_only
    BEFORE UPDATE OR DELETE ON raw_ws_messages
    FOR EACH ROW EXECUTE FUNCTION forbid_mutation();

CREATE VIEW candles_canonical AS
SELECT DISTINCT ON (instrument_id, timeframe, open_time)
    candle_id, instrument_id, timeframe, open_time, close_time,
    open, high, low, close, volume, trade_count, source, data_version
FROM candles
WHERE source IN ('binance', 'binance_ws')
ORDER BY instrument_id, timeframe, open_time,
         CASE source WHEN 'binance' THEN 0 ELSE 1 END;

COMMIT;
