-- QuantLab migration 0001 — core foundation
-- Tables: assets, venues, instruments, candles, strategies, strategy_versions, audit_events
-- Conventions (23-Database-Schema): UUID PKs, TIMESTAMPTZ UTC, NUMERIC for financial values,
-- append-only audit, candle integrity CHECK constraints.

BEGIN;

CREATE TABLE assets (
    asset_id UUID PRIMARY KEY,
    symbol TEXT NOT NULL,
    asset_class TEXT NOT NULL,
    base_asset TEXT,
    quote_asset TEXT,
    price_precision INTEGER,
    quantity_precision INTEGER,
    tick_size NUMERIC,
    lot_size NUMERIC,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(symbol)
);

CREATE TABLE venues (
    venue_id UUID PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    venue_type TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE instruments (
    instrument_id UUID PRIMARY KEY,
    venue_id UUID NOT NULL REFERENCES venues(venue_id),
    asset_id UUID REFERENCES assets(asset_id),
    venue_symbol TEXT NOT NULL,
    instrument_type TEXT NOT NULL,
    tick_size NUMERIC NOT NULL,
    lot_size NUMERIC NOT NULL,
    min_quantity NUMERIC,
    min_notional NUMERIC,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(venue_id, venue_symbol)
);

CREATE TABLE candles (
    candle_id UUID PRIMARY KEY,
    instrument_id UUID NOT NULL REFERENCES instruments(instrument_id),
    timeframe TEXT NOT NULL,
    open_time TIMESTAMPTZ NOT NULL,
    close_time TIMESTAMPTZ NOT NULL,
    open NUMERIC NOT NULL,
    high NUMERIC NOT NULL,
    low NUMERIC NOT NULL,
    close NUMERIC NOT NULL,
    volume NUMERIC NOT NULL,
    trade_count BIGINT,
    source TEXT NOT NULL,
    data_version TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(instrument_id, timeframe, open_time, source),
    -- Candle integrity (23-Database-Schema §17)
    CONSTRAINT candle_high_ge_open  CHECK (high >= open),
    CONSTRAINT candle_high_ge_close CHECK (high >= close),
    CONSTRAINT candle_high_ge_low   CHECK (high >= low),
    CONSTRAINT candle_low_le_open   CHECK (low <= open),
    CONSTRAINT candle_low_le_close  CHECK (low <= close),
    CONSTRAINT candle_volume_ge_0   CHECK (volume >= 0),
    CONSTRAINT candle_time_order    CHECK (close_time > open_time)
);

CREATE INDEX idx_candles_lookup
    ON candles(instrument_id, timeframe, open_time DESC);

CREATE TABLE strategies (
    strategy_id UUID PRIMARY KEY,
    strategy_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL,
    current_version TEXT,
    owner TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE strategy_versions (
    strategy_version_id UUID PRIMARY KEY,
    strategy_id UUID NOT NULL REFERENCES strategies(strategy_id),
    version TEXT NOT NULL,
    code_commit TEXT NOT NULL,
    config_version TEXT NOT NULL,
    artifact_hash TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(strategy_id, version)
);

CREATE TABLE audit_events (
    audit_event_id UUID PRIMARY KEY,
    actor_type TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT,
    environment TEXT,
    request_id TEXT,
    correlation_id TEXT,
    result TEXT NOT NULL,
    metadata JSONB,
    event_time TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_events_resource
    ON audit_events(resource_type, resource_id);

CREATE INDEX idx_audit_events_time
    ON audit_events(event_time DESC);

-- Append-only enforcement (23-Database-Schema §10, §75)
CREATE OR REPLACE FUNCTION forbid_mutation() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'Table % is append-only (audit immutability)', TG_TABLE_NAME;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_events_append_only
    BEFORE UPDATE OR DELETE ON audit_events
    FOR EACH ROW EXECUTE FUNCTION forbid_mutation();

COMMIT;
