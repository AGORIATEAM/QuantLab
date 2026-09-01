-- Candles are historical facts: INSERT-only (duplicates already skipped via
-- ON CONFLICT DO NOTHING). Enforce at the database level like audit_events
-- and datasets — a rewrite must be a new source/data_version, never an
-- UPDATE (T7 amendement 3).

BEGIN;

CREATE TRIGGER candles_append_only
    BEFORE UPDATE OR DELETE ON candles
    FOR EACH ROW EXECUTE FUNCTION forbid_mutation();

COMMIT;
