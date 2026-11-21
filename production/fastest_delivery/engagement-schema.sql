BEGIN;
CREATE SCHEMA IF NOT EXISTS fastest_pilot_engagement;

CREATE TABLE IF NOT EXISTS fastest_pilot_engagement.binding (
    attribution_key uuid PRIMARY KEY,
    mode text NOT NULL CHECK (mode IN ('live', 'rehearsal')),
    start_date date NOT NULL,
    release_id uuid NOT NULL,
    manifest_sha256 text NOT NULL CHECK (manifest_sha256 ~ '^[0-9a-f]{64}$'),
    evidence_destination text NOT NULL,
    receipt_id text NOT NULL UNIQUE CHECK (receipt_id ~ '^[0-9a-f]{64}$'),
    post_url text NOT NULL UNIQUE,
    published_at timestamptz NOT NULL,
    CHECK ((published_at AT TIME ZONE 'Asia/Shanghai')::date BETWEEN start_date AND start_date + 6)
);

CREATE TABLE IF NOT EXISTS fastest_pilot_engagement.journey (
    attribution_key uuid NOT NULL REFERENCES fastest_pilot_engagement.binding,
    visit_id uuid PRIMARY KEY,
    visited_at timestamptz NOT NULL,
    comparison_id uuid UNIQUE,
    compared_at timestamptz,
    CHECK ((comparison_id IS NULL) = (compared_at IS NULL)),
    CHECK (compared_at IS NULL OR compared_at >= visited_at)
);

CREATE OR REPLACE VIEW fastest_pilot_engagement.available AS
SELECT attribution_key, mode, release_id, manifest_sha256, evidence_destination
FROM fastest_pilot_engagement.binding
WHERE published_at <= statement_timestamp()
  AND (statement_timestamp() AT TIME ZONE 'Asia/Shanghai')::date < start_date + 7;

CREATE OR REPLACE FUNCTION fastest_pilot_engagement.arrive(key uuid, source_mode text, visit uuid)
RETURNS boolean LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog AS $$
    INSERT INTO fastest_pilot_engagement.journey (attribution_key, visit_id, visited_at)
    SELECT attribution_key, visit, statement_timestamp()
    FROM fastest_pilot_engagement.available WHERE attribution_key = key AND mode = source_mode
    ON CONFLICT (visit_id) DO UPDATE SET visit_id = EXCLUDED.visit_id
    WHERE journey.attribution_key = EXCLUDED.attribution_key
    RETURNING true;
$$;

CREATE OR REPLACE FUNCTION fastest_pilot_engagement.complete(key uuid, source_mode text, visit uuid, comparison uuid)
RETURNS boolean LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog AS $$
    UPDATE fastest_pilot_engagement.journey AS j
    SET comparison_id = coalesce(j.comparison_id, comparison),
        compared_at = coalesce(j.compared_at, statement_timestamp())
    FROM fastest_pilot_engagement.available AS a
    WHERE a.attribution_key = key AND a.mode = source_mode
        AND j.attribution_key = key AND j.visit_id = visit
    RETURNING true;
$$;

REVOKE ALL ON SCHEMA fastest_pilot_engagement FROM PUBLIC;
REVOKE ALL ON FUNCTION fastest_pilot_engagement.arrive(uuid, text, uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION fastest_pilot_engagement.complete(uuid, text, uuid, uuid) FROM PUBLIC;
COMMIT;
