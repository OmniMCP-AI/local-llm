BEGIN;

CREATE SCHEMA IF NOT EXISTS fastest_release;

CREATE TABLE IF NOT EXISTS fastest_release.metric_definition (
    metric_key text NOT NULL,
    version integer NOT NULL CHECK (version > 0),
    unit text NOT NULL,
    statistic text NOT NULL,
    boundary text NOT NULL,
    PRIMARY KEY (metric_key, version),
    UNIQUE (metric_key, version, unit, statistic, boundary)
);

INSERT INTO fastest_release.metric_definition
    (metric_key, version, unit, statistic, boundary)
VALUES (
    'decode-throughput', 1, 'tok/s', 'median',
    'Generated tokens after the first token per second of decode.'
)
ON CONFLICT DO NOTHING;

INSERT INTO fastest_release.metric_definition
    (metric_key, version, unit, statistic, boundary)
VALUES
    ('llama-bench-decode', 1, 'tok/s', 'median',
      'llama-bench synchronized time for 128 single-token steps starting at empty KV.'),
    ('llama-bench-prefill', 1, 'tok/s', 'median',
      'llama-bench synchronized prompt processing time for 1,024 prompt tokens with empty initial KV.'),
    ('comfyui-seconds-per-accepted-image', 1, 's/image', 'ratio',
      'Sum of repeat elapsed times including failed and rejected attempts divided by accepted repeats.'),
    ('comfyui-median-completion', 1, 's', 'median',
      'Use a monotonic client clock on the same host. Start just before POST /prompt. End when the complete PNG is read from /view or when a terminal error or the deadline is observed. Record offsets for the first execution events for sampler, decode and save, followed by successful execution completion. Time includes local transport and PNG retrieval. Exclude setup before POST, inter-attempt recovery and offline review.')
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS fastest_release.observation_revision (
    evidence_id uuid NOT NULL,
    revision integer NOT NULL CHECK (revision > 0),
    document jsonb NOT NULL,
    input_digest bytea NOT NULL,
    metric_key text GENERATED ALWAYS AS (document #>> '{metric,id}') STORED NOT NULL,
    metric_version integer GENERATED ALWAYS AS ((document #>> '{metric,version}')::integer) STORED NOT NULL,
    metric_value numeric GENERATED ALWAYS AS ((document #>> '{metric,value}')::numeric) STORED NOT NULL,
    metric_unit text GENERATED ALWAYS AS (document #>> '{metric,unit}') STORED NOT NULL,
    metric_statistic text GENERATED ALWAYS AS (document #>> '{metric,statistic}') STORED NOT NULL,
    metric_boundary text GENERATED ALWAYS AS (document #>> '{metric,boundary}') STORED NOT NULL,
    CHECK (metric_value >= 0 AND metric_value < 1e20),
    CHECK (document #>> '{rights,core}' IS NOT DISTINCT FROM 'allow'),
    CHECK (document #>> '{rights,destination}' IS NOT DISTINCT FROM 'public-release'),
    PRIMARY KEY (evidence_id, revision),
    UNIQUE (evidence_id, input_digest),
    FOREIGN KEY (metric_key, metric_version, metric_unit, metric_statistic, metric_boundary)
        REFERENCES fastest_release.metric_definition (metric_key, version, unit, statistic, boundary)
);

CREATE TABLE IF NOT EXISTS fastest_release.data_release (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    evidence_id uuid NOT NULL,
    revision integer NOT NULL,
    previous_release_id uuid REFERENCES fastest_release.data_release(id),
    schema_version integer NOT NULL DEFAULT 1,
    UNIQUE (evidence_id, revision),
    FOREIGN KEY (evidence_id, revision)
        REFERENCES fastest_release.observation_revision (evidence_id, revision)
);

CREATE TABLE IF NOT EXISTS fastest_release.current_release (
    singleton boolean PRIMARY KEY DEFAULT true CHECK (singleton),
    release_id uuid REFERENCES fastest_release.data_release(id)
);

INSERT INTO fastest_release.current_release (singleton)
VALUES (true)
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS fastest_release.evidence_withdrawal (
    evidence_id uuid PRIMARY KEY,
    reason text NOT NULL,
    withdrawn_at timestamptz NOT NULL DEFAULT clock_timestamp()
);

CREATE OR REPLACE FUNCTION fastest_release.publish_observation(input jsonb)
RETURNS uuid LANGUAGE plpgsql AS $$
DECLARE
    evidence uuid := (input->>'evidence_id')::uuid;
    digest bytea := sha256(convert_to(input::text, 'UTF8'));
    published_id uuid;
    prior_id uuid;
    next_revision integer;
    expiry text := input #>> '{rights,expires_at}';
BEGIN
    IF input->'rights' ? 'expires_at' THEN
        IF expiry IS NULL OR expiry !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]Z$' THEN
            RAISE EXCEPTION 'Rights expiry requires a UTC timestamp';
        END IF;
        PERFORM expiry::timestamptz;
    END IF;

    SELECT current.release_id INTO prior_id
    FROM fastest_release.current_release AS current
    WHERE singleton
    FOR UPDATE;

    IF EXISTS (SELECT FROM fastest_release.evidence_withdrawal WHERE evidence_id = evidence) THEN
        RAISE EXCEPTION 'Evidence has been withdrawn';
    END IF;

    SELECT released.id INTO published_id
    FROM fastest_release.observation_revision AS observation
    JOIN fastest_release.data_release AS released USING (evidence_id, revision)
    WHERE observation.evidence_id = evidence AND observation.input_digest = digest;

    IF FOUND THEN
        RETURN published_id;
    END IF;

    SELECT coalesce(max(revision), 0) + 1 INTO next_revision
    FROM fastest_release.observation_revision
    WHERE evidence_id = evidence;

    INSERT INTO fastest_release.observation_revision (evidence_id, revision, document, input_digest)
    VALUES (evidence, next_revision, input, digest);

    INSERT INTO fastest_release.data_release (evidence_id, revision, previous_release_id)
    VALUES (evidence, next_revision, prior_id)
    RETURNING id INTO published_id;

    UPDATE fastest_release.current_release AS current
    SET release_id = published_id
    WHERE singleton;

    RETURN published_id;
END;
$$;

CREATE OR REPLACE FUNCTION fastest_release.read_release(requested uuid)
RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog AS $$
    SELECT jsonb_build_object(
        'release_id', released.id,
        'previous_release_id', released.previous_release_id,
        'schema_version', released.schema_version,
        'revision', released.revision,
        'status', CASE WHEN rights.available THEN 'published' ELSE 'withdrawn' END
    ) || CASE WHEN rights.available THEN jsonb_build_object(
        'row', jsonb_build_object(
            'evidence_id', observation.evidence_id,
            'kind', observation.document->'kind',
            'hardware', observation.document->'hardware',
            'artifact', observation.document->'artifact',
            'workload', observation.document->'workload',
            'metric', observation.document->'metric' || jsonb_build_object(
                'value', observation.metric_value::text,
                'unit', observation.metric_unit
            ),
            'source', observation.document->'source',
            'rights', observation.document->'rights',
            'fields', coalesce((
                SELECT jsonb_object_agg(field.key, field.value - 'rights')
                FROM jsonb_each(observation.document->'fields') AS field
                WHERE field.value->>'rights' = 'allow'
            ), '{}'::jsonb)
        )
    ) ELSE '{}'::jsonb END
    FROM fastest_release.data_release AS released
    JOIN fastest_release.observation_revision AS observation USING (evidence_id, revision)
    LEFT JOIN fastest_release.evidence_withdrawal AS withdrawn USING (evidence_id)
    CROSS JOIN LATERAL (
        SELECT withdrawn.evidence_id IS NULL AND coalesce(
            (observation.document #>> '{rights,expires_at}')::timestamptz > statement_timestamp(), true
        ) AS available
    ) AS rights
    WHERE released.id = coalesce(requested, (SELECT release_id FROM fastest_release.current_release));
$$;

CREATE OR REPLACE FUNCTION fastest_release.read_evidence(requested uuid)
RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog AS $$
    SELECT fastest_release.read_release(released.id)
    FROM fastest_release.data_release AS released
    WHERE released.evidence_id = requested
    ORDER BY released.revision DESC
    LIMIT 1;
$$;

CREATE OR REPLACE FUNCTION fastest_release.withdraw_evidence(evidence uuid, withdrawal_reason text)
RETURNS boolean LANGUAGE plpgsql AS $$
BEGIN
    PERFORM 1 FROM fastest_release.current_release WHERE singleton FOR UPDATE;

    IF NOT EXISTS (SELECT FROM fastest_release.observation_revision WHERE evidence_id = evidence) THEN
        RETURN false;
    END IF;

    INSERT INTO fastest_release.evidence_withdrawal (evidence_id, reason)
    VALUES (evidence, withdrawal_reason)
    ON CONFLICT DO NOTHING;

    RETURN true;
END;
$$;

REVOKE ALL ON FUNCTION fastest_release.publish_observation(jsonb) FROM PUBLIC;
REVOKE ALL ON FUNCTION fastest_release.read_release(uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION fastest_release.read_evidence(uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION fastest_release.withdraw_evidence(uuid, text) FROM PUBLIC;

COMMIT;
