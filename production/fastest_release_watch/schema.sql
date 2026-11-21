BEGIN;

CREATE SCHEMA IF NOT EXISTS fastest_release_watch;
REVOKE ALL ON SCHEMA fastest_release_watch FROM PUBLIC;

CREATE TABLE IF NOT EXISTS fastest_release_watch.source_status (
    id smallint PRIMARY KEY CHECK (id = 1),
    mode text NOT NULL CHECK (mode IN ('live', 'fixture')),
    last_attempt timestamptz,
    last_error text,
    last_success timestamptz
);

CREATE TABLE IF NOT EXISTS fastest_release_watch.release_revision (
    revision_id text PRIMARY KEY,
    release_id bigint NOT NULL CHECK (release_id > 0),
    observed_at timestamptz NOT NULL,
    ingest_order bigint GENERATED ALWAYS AS IDENTITY UNIQUE,
    document jsonb NOT NULL CHECK (jsonb_typeof(document) = 'object')
);

CREATE OR REPLACE FUNCTION fastest_release_watch.record_refresh(
    source_mode text, captured_at timestamptz, revisions jsonb, refresh_error text
)
RETURNS boolean LANGUAGE plpgsql SET search_path = pg_catalog AS $$
DECLARE
    stored_mode text;
BEGIN
    INSERT INTO fastest_release_watch.source_status (id, mode)
    VALUES (1, source_mode) ON CONFLICT DO NOTHING;

    -- Serialize overlapping refreshes for this feed.
    SELECT mode INTO STRICT stored_mode
    FROM fastest_release_watch.source_status WHERE id = 1 FOR UPDATE;
    IF stored_mode <> source_mode THEN
        RETURN false;
    END IF;

    IF refresh_error IS NULL THEN
        INSERT INTO fastest_release_watch.release_revision (revision_id, release_id, observed_at, document)
        SELECT revision->>'revision_id', (revision->>'release_id')::bigint, captured_at, revision
        FROM jsonb_array_elements(revisions) AS revision
        ON CONFLICT (revision_id) DO NOTHING;
        UPDATE fastest_release_watch.source_status
        SET last_success = greatest(last_success, captured_at) WHERE id = 1;
    END IF;

    UPDATE fastest_release_watch.source_status
    SET last_attempt = captured_at, last_error = refresh_error
    WHERE id = 1 AND (last_attempt IS NULL OR last_attempt <= captured_at);
    RETURN true;
END;
$$;

COMMIT;
