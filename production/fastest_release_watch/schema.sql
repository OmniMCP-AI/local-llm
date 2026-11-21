BEGIN;

CREATE SCHEMA IF NOT EXISTS fastest_release_watch;
REVOKE ALL ON SCHEMA fastest_release_watch FROM PUBLIC;

CREATE TABLE IF NOT EXISTS fastest_release_watch.source_status (
    runtime_id text NOT NULL,
    mode text NOT NULL CHECK (mode IN ('live', 'fixture')),
    last_attempt timestamptz,
    last_error text,
    last_success timestamptz
);

-- Move the original singleton row to its source key without changing its timestamps or table grants.
ALTER TABLE fastest_release_watch.source_status
    ADD COLUMN IF NOT EXISTS runtime_id text NOT NULL DEFAULT 'llama.cpp';
ALTER TABLE fastest_release_watch.source_status
    DROP COLUMN IF EXISTS id,
    ALTER COLUMN runtime_id DROP DEFAULT;
CREATE UNIQUE INDEX IF NOT EXISTS source_status_runtime_id_idx
    ON fastest_release_watch.source_status (runtime_id);

CREATE TABLE IF NOT EXISTS fastest_release_watch.release_revision (
    revision_id text PRIMARY KEY,
    release_id bigint NOT NULL CHECK (release_id > 0),
    observed_at timestamptz NOT NULL,
    ingest_order bigint GENERATED ALWAYS AS IDENTITY UNIQUE,
    document jsonb NOT NULL CHECK (jsonb_typeof(document) = 'object')
);

CREATE OR REPLACE FUNCTION fastest_release_watch.record_refresh(
    runtime text, source_mode text, captured_at timestamptz, revisions jsonb, refresh_error text
)
RETURNS boolean LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
    -- Keep fixture and live histories in separate databases, even on concurrent first writes.
    LOCK TABLE fastest_release_watch.source_status IN SHARE ROW EXCLUSIVE MODE;
    IF EXISTS (SELECT 1 FROM fastest_release_watch.source_status WHERE mode <> source_mode) THEN
        RETURN false;
    END IF;

    INSERT INTO fastest_release_watch.source_status (runtime_id, mode)
    VALUES (runtime, source_mode) ON CONFLICT DO NOTHING;

    IF refresh_error IS NULL THEN
        INSERT INTO fastest_release_watch.release_revision (revision_id, release_id, observed_at, document)
        SELECT revision->>'revision_id', (revision->>'release_id')::bigint, captured_at, revision
        FROM jsonb_array_elements(revisions) AS revision
        ON CONFLICT (revision_id) DO NOTHING;
        UPDATE fastest_release_watch.source_status
        SET last_success = greatest(last_success, captured_at) WHERE runtime_id = runtime;
    END IF;

    UPDATE fastest_release_watch.source_status
    SET last_attempt = captured_at, last_error = refresh_error
    WHERE runtime_id = runtime AND (last_attempt IS NULL OR last_attempt <= captured_at);
    RETURN true;
END;
$$;

CREATE OR REPLACE FUNCTION fastest_release_watch.record_refresh(
    source_mode text, captured_at timestamptz, revisions jsonb, refresh_error text
)
RETURNS boolean LANGUAGE sql SET search_path = pg_catalog AS $$
    SELECT fastest_release_watch.record_refresh('llama.cpp', source_mode, captured_at, revisions, refresh_error);
$$;

COMMIT;
