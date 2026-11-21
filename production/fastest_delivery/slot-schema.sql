BEGIN;
CREATE SCHEMA IF NOT EXISTS fastest_editorial_slots;

CREATE TABLE IF NOT EXISTS fastest_editorial_slots.slot (
    scheduled_at timestamptz PRIMARY KEY,
    record jsonb NOT NULL,
    CHECK ((jsonb_typeof(record) = 'object'
            AND (record->>'scheduled_at')::timestamptz = scheduled_at
            AND record->>'run_id' ~ '^[0-9a-f]{64}$') IS TRUE)
);

REVOKE ALL ON SCHEMA fastest_editorial_slots FROM PUBLIC;
REVOKE ALL ON TABLE fastest_editorial_slots.slot FROM PUBLIC;
COMMIT;
