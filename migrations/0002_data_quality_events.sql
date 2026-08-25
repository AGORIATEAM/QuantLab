-- QuantLab migration 0002 — data quality events (23-Database-Schema §19)
-- Records gaps, duplicates, mismatches, out-of-order/stale/invalid data.
-- resolved_at is mutable by design (the only allowed update); everything else
-- is written once at insert time.

BEGIN;

CREATE TABLE data_quality_events (
    event_id UUID PRIMARY KEY,
    dataset_type TEXT NOT NULL,
    instrument_id UUID REFERENCES instruments(instrument_id),
    severity TEXT NOT NULL,
    code TEXT NOT NULL,
    event_time TIMESTAMPTZ NOT NULL,
    details JSONB,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_data_quality_events_instrument_time
    ON data_quality_events(instrument_id, event_time DESC);

-- Fast "open anomalies" queries (scan/backfill and health reporting).
CREATE INDEX idx_data_quality_events_unresolved
    ON data_quality_events(code, event_time DESC)
    WHERE resolved_at IS NULL;

COMMIT;
