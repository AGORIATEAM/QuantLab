-- Dataset registry (docs/23 §150, ADR-0001 décision 2, Roadmap T6).
-- A dataset is a published, immutable, hash-verified logical selection of
-- candles. It is born 'published' (atomic freeze, no draft state in Phase 1);
-- correcting one means publishing a new version — hence the append-only
-- trigger reusing forbid_mutation() from 0001.

BEGIN;

CREATE TABLE datasets (
    dataset_id UUID PRIMARY KEY,
    dataset_name TEXT NOT NULL,
    version TEXT NOT NULL,
    storage_uri TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    source TEXT NOT NULL,
    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,
    status TEXT NOT NULL CHECK (status = 'published'),
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(dataset_name, version)
);

CREATE TRIGGER datasets_append_only
    BEFORE UPDATE OR DELETE ON datasets
    FOR EACH ROW EXECUTE FUNCTION forbid_mutation();

COMMIT;
