BEGIN;

CREATE SCHEMA IF NOT EXISTS fastest_discoveries;

-- Match the CLI permalink rules for callers using the editor functions directly.
CREATE OR REPLACE FUNCTION fastest_discoveries.valid_permalink(value text)
RETURNS boolean LANGUAGE sql IMMUTABLE STRICT
SET search_path = pg_catalog, pg_temp
AS $$
    SELECT length(value) <= 2048
       AND value COLLATE "C" ~ '^[!-~]+$'
       AND strpos(value, chr(92)) = 0
       AND value COLLATE "C" ~ (
           '^https://(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?[.])+[a-z][a-z0-9-]*/'
           '[^?#]*[^/?#][^?#]*([?][^#]*)?(#[A-Za-z0-9_-]+)?$'
       )
       AND (
           strpos(split_part(value, '#', 1), '?') = 0
           OR split_part(value, '#', 1) COLLATE "C" ~
               '^https://(www[.])?youtube[.]com/watch[?]v=[A-Za-z0-9_-]{11}$'
       );
$$;

CREATE TABLE IF NOT EXISTS fastest_discoveries.discovery (
    source_url text COLLATE "C" PRIMARY KEY CHECK (fastest_discoveries.valid_permalink(source_url)),
    original_url text COLLATE "C" NOT NULL CHECK (fastest_discoveries.valid_permalink(original_url)),
    source_format text NOT NULL CHECK (source_format IN ('forum', 'social', 'video')),
    published_at timestamptz,
    authority text NOT NULL CHECK (authority IN ('rights_holder', 'authorized_representative')),
    consent_reference text NOT NULL,
    scope text NOT NULL CHECK (scope IN ('discovery_only', 'public_source_link')),
    submitted_at timestamptz NOT NULL DEFAULT date_trunc('second', clock_timestamp())
);

CREATE TABLE IF NOT EXISTS fastest_discoveries.youtube_metadata (
    source_url text COLLATE "C" PRIMARY KEY
        CHECK (source_url ~ '^https://www[.]youtube[.]com/watch[?]v=[A-Za-z0-9_-]{11}$'),
    policy text NOT NULL DEFAULT 'youtube_metadata_discovery_only_v1'
        CHECK (policy = 'youtube_metadata_discovery_only_v1'),
    source_reference text NOT NULL CHECK (
        split_part(source_reference, '#', 1) COLLATE "C" ~
            '^opendesign/mockups/llm-observatory/battle-title-sample[.]json@sha256:[a-f0-9]{64}$'
        AND source_reference = split_part(source_reference, '#', 1) || '#video=' || split_part(source_url, '?v=', 2)
    ),
    submitted_at timestamptz NOT NULL DEFAULT date_trunc('second', clock_timestamp())
);

CREATE TABLE IF NOT EXISTS fastest_discoveries.review (
    source_url text COLLATE "C" PRIMARY KEY REFERENCES fastest_discoveries.discovery (source_url),
    choice text NOT NULL CHECK (choice IN ('approve', 'withhold')),
    reviewer text NOT NULL,
    reason text NOT NULL,
    reviewed_at timestamptz NOT NULL DEFAULT date_trunc('second', clock_timestamp())
);

CREATE TABLE IF NOT EXISTS fastest_discoveries.withdrawal (
    source_url text COLLATE "C" PRIMARY KEY CHECK (fastest_discoveries.valid_permalink(source_url)),
    reason text NOT NULL CHECK (reason IN ('source_deleted', 'permission_revoked')),
    recorded_at timestamptz NOT NULL DEFAULT date_trunc('second', clock_timestamp())
);

CREATE OR REPLACE FUNCTION fastest_discoveries.utc_text(value timestamptz)
RETURNS text LANGUAGE sql STABLE STRICT
SET search_path = pg_catalog, pg_temp
AS $$
    SELECT to_char(value AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"');
$$;

CREATE OR REPLACE VIEW fastest_discoveries.entries AS
WITH candidates AS (
    SELECT COALESCE(d.source_url, m.source_url) AS source_url,
           COALESCE(d.original_url, m.source_url) AS original_url,
           COALESCE(d.source_format, 'video') AS source_format,
           d.published_at, d.authority, d.consent_reference,
           COALESCE(d.scope, 'discovery_only') AS scope,
           COALESCE(d.submitted_at, m.submitted_at) AS submitted_at,
           m.policy AS metadata_policy, m.source_reference AS metadata_source_reference
    FROM fastest_discoveries.discovery AS d
    FULL JOIN fastest_discoveries.youtube_metadata AS m USING (source_url)
)
SELECT d.source_url, d.original_url, d.source_format,
       fastest_discoveries.utc_text(d.published_at) AS published_at,
       d.authority, d.consent_reference, d.scope,
       fastest_discoveries.utc_text(d.submitted_at) AS submitted_at,
       r.choice, r.reviewer, r.reason, fastest_discoveries.utc_text(r.reviewed_at) AS reviewed_at,
       COALESCE(self.reason, origin.reason) AS withdrawal_reason,
       fastest_discoveries.utc_text(COALESCE(self.recorded_at, origin.recorded_at)) AS withdrawal_at,
       CASE
           WHEN COALESCE(self.reason, origin.reason) IS NOT NULL THEN COALESCE(self.reason, origin.reason)
           WHEN d.source_url <> d.original_url THEN 'cross_post'
           WHEN d.scope = 'discovery_only' THEN 'discovery_only'
       END AS withholding,
       d.metadata_policy, d.metadata_source_reference
FROM candidates AS d
LEFT JOIN fastest_discoveries.review AS r USING (source_url)
LEFT JOIN fastest_discoveries.withdrawal AS self ON self.source_url = d.source_url
LEFT JOIN fastest_discoveries.withdrawal AS origin ON origin.source_url = d.original_url;

-- Serialize private writes across the original and its cross-posts, including absent rows.
CREATE OR REPLACE FUNCTION fastest_discoveries.lock_history()
RETURNS void LANGUAGE sql VOLATILE
SET search_path = pg_catalog, pg_temp
AS $$
    SELECT pg_advisory_xact_lock(45110, 22);
$$;

CREATE OR REPLACE FUNCTION fastest_discoveries.submit(submission jsonb)
RETURNS json LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
    candidate fastest_discoveries.discovery;
    recorded fastest_discoveries.discovery;
BEGIN
    PERFORM fastest_discoveries.lock_history();
    candidate := jsonb_populate_record(NULL::fastest_discoveries.discovery, submission);
    INSERT INTO fastest_discoveries.discovery
        (source_url, original_url, source_format, published_at, authority, consent_reference, scope)
    VALUES (candidate.source_url, candidate.original_url, candidate.source_format, candidate.published_at,
            candidate.authority, candidate.consent_reference, candidate.scope)
    ON CONFLICT (source_url) DO NOTHING;

    SELECT * INTO recorded FROM fastest_discoveries.discovery WHERE source_url = candidate.source_url;
    candidate.submitted_at := recorded.submitted_at;
    IF recorded IS DISTINCT FROM candidate THEN
        RETURN json_build_object('error', 'A different submission already exists for this source permalink');
    END IF;
    RETURN json_build_object('source_url', recorded.source_url,
                             'submitted_at', fastest_discoveries.utc_text(recorded.submitted_at));
END;
$$;

CREATE OR REPLACE FUNCTION fastest_discoveries.intake_youtube_metadata(snapshot_reference text, video_ids jsonb)
RETURNS json LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
    video_id text;
    permalink text;
    reference text;
    discoveries integer := 0;
BEGIN
    IF video_ids IS NULL OR jsonb_typeof(video_ids) <> 'array' THEN
        RETURN json_build_object('error', 'Expected a YouTube metadata array');
    END IF;
    IF jsonb_array_length(video_ids) NOT BETWEEN 1 AND 100 THEN
        RETURN json_build_object('error', 'Expected a bounded YouTube metadata snapshot');
    END IF;

    PERFORM fastest_discoveries.lock_history();
    FOR video_id IN SELECT DISTINCT jsonb_array_elements_text(video_ids) LOOP
        permalink := 'https://www.youtube.com/watch?v=' || video_id;
        reference := snapshot_reference || '#video=' || video_id;
        INSERT INTO fastest_discoveries.youtube_metadata (source_url, source_reference)
        VALUES (permalink, reference) ON CONFLICT (source_url) DO NOTHING;
        IF EXISTS (
            SELECT FROM fastest_discoveries.youtube_metadata
            WHERE source_url = permalink AND source_reference <> reference
        ) THEN
            RAISE unique_violation;
        END IF;
        discoveries := discoveries + 1;
    END LOOP;

    RETURN json_build_object('discoveries', discoveries);
EXCEPTION WHEN unique_violation THEN
    RETURN json_build_object('error', 'Conflicting YouTube metadata provenance. The snapshot was rolled back.');
END;
$$;

CREATE OR REPLACE FUNCTION fastest_discoveries.review(
    permalink text, decision text, editor text, explanation text
)
RETURNS json LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
    recorded fastest_discoveries.review;
    restriction text;
    has_consent boolean;
BEGIN
    PERFORM fastest_discoveries.lock_history();
    SELECT * INTO recorded FROM fastest_discoveries.review WHERE source_url = permalink;
    IF FOUND THEN
        IF (recorded.choice, recorded.reviewer, recorded.reason) IS DISTINCT FROM (decision, editor, explanation) THEN
            RETURN json_build_object('error', 'The recorded review choice is immutable');
        END IF;
    ELSE
        SELECT withholding, authority IS NOT NULL INTO restriction, has_consent
        FROM fastest_discoveries.entries WHERE source_url = permalink;
        IF NOT FOUND THEN
            RETURN json_build_object('error', 'No submission for this source permalink');
        END IF;
        IF restriction IS NOT NULL AND (decision = 'approve' OR NOT has_consent) THEN
            RETURN json_build_object('error', 'Publication is withheld: ' || restriction);
        END IF;
        INSERT INTO fastest_discoveries.review (source_url, choice, reviewer, reason)
        VALUES (permalink, decision, editor, explanation) RETURNING * INTO recorded;
    END IF;
    RETURN json_build_object('source_url', recorded.source_url, 'choice', recorded.choice,
                             'reviewer', recorded.reviewer, 'reason', recorded.reason,
                             'reviewed_at', fastest_discoveries.utc_text(recorded.reviewed_at));
END;
$$;

CREATE OR REPLACE FUNCTION fastest_discoveries.withdraw(permalink text, disposition text)
RETURNS json LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
    recorded fastest_discoveries.withdrawal;
BEGIN
    PERFORM fastest_discoveries.lock_history();
    INSERT INTO fastest_discoveries.withdrawal (source_url, reason) VALUES (permalink, disposition)
    ON CONFLICT (source_url) DO NOTHING;
    SELECT * INTO recorded FROM fastest_discoveries.withdrawal WHERE source_url = permalink;
    IF recorded.reason <> disposition THEN
        RETURN json_build_object('error', 'A withdrawal is already recorded for this source permalink');
    END IF;
    RETURN json_build_object('source_url', recorded.source_url, 'reason', recorded.reason,
                             'recorded_at', fastest_discoveries.utc_text(recorded.recorded_at));
END;
$$;

CREATE OR REPLACE FUNCTION fastest_discoveries.queue_entries()
RETURNS json LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
    SELECT COALESCE(json_agg(e ORDER BY original_url, source_url), '[]'::json)
    FROM fastest_discoveries.entries AS e;
$$;

CREATE OR REPLACE FUNCTION fastest_discoveries.public_report()
RETURNS json LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
    SELECT json_build_object(
        'schema', 'fastest.ai/discovery-public/v1',
        'entries', COALESCE(json_agg(
            CASE
                WHEN withholding IS NOT NULL THEN json_build_object('status', 'withheld', 'reason', withholding)
                WHEN choice = 'withhold' THEN json_build_object('status', 'withheld', 'reason', 'editor_withheld')
                WHEN choice = 'approve' THEN json_build_object(
                    'status', 'approved', 'reason', 'source_link_approved',
                    'source_url', source_url, 'published_at', published_at
                )
            END ORDER BY original_url, source_url
        ), '[]'::json)
    )
    FROM fastest_discoveries.entries
    WHERE withholding IS NOT NULL OR choice IS NOT NULL;
$$;

-- The schema owner can import an entire legacy snapshot, including withdrawals
-- whose source, or original, has yet to be submitted.
CREATE OR REPLACE FUNCTION fastest_discoveries.import_history(history jsonb)
RETURNS json LANGUAGE plpgsql
SET search_path = pg_catalog, pg_temp
AS $$
BEGIN
    PERFORM fastest_discoveries.lock_history();
    BEGIN
        INSERT INTO fastest_discoveries.discovery
        SELECT * FROM jsonb_populate_recordset(NULL::fastest_discoveries.discovery, history -> 'discovery')
        ON CONFLICT (source_url) DO NOTHING;
        INSERT INTO fastest_discoveries.review
        SELECT * FROM jsonb_populate_recordset(NULL::fastest_discoveries.review, history -> 'review')
        ON CONFLICT (source_url) DO NOTHING;
        INSERT INTO fastest_discoveries.withdrawal
        SELECT * FROM jsonb_populate_recordset(NULL::fastest_discoveries.withdrawal, history -> 'withdrawal')
        ON CONFLICT (source_url) DO NOTHING;

        IF EXISTS (
            SELECT FROM jsonb_populate_recordset(NULL::fastest_discoveries.discovery, history -> 'discovery') AS old
            JOIN fastest_discoveries.discovery AS current USING (source_url)
            WHERE old IS DISTINCT FROM current
            UNION ALL
            SELECT FROM jsonb_populate_recordset(NULL::fastest_discoveries.review, history -> 'review') AS old
            JOIN fastest_discoveries.review AS current USING (source_url)
            WHERE old IS DISTINCT FROM current
            UNION ALL
            SELECT FROM jsonb_populate_recordset(NULL::fastest_discoveries.withdrawal, history -> 'withdrawal') AS old
            JOIN fastest_discoveries.withdrawal AS current USING (source_url)
            WHERE old IS DISTINCT FROM current
        ) THEN
            RAISE unique_violation;
        END IF;
    EXCEPTION WHEN unique_violation THEN
        RETURN json_build_object('error', 'Conflicting legacy history. No history was imported.');
    END;

    RETURN json_build_object(
        'discoveries', jsonb_array_length(history -> 'discovery'),
        'reviews', jsonb_array_length(history -> 'review'),
        'withdrawals', jsonb_array_length(history -> 'withdrawal')
    );
END;
$$;

REVOKE ALL ON SCHEMA fastest_discoveries FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA fastest_discoveries FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA fastest_discoveries FROM PUBLIC;

COMMIT;
