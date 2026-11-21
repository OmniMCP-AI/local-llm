BEGIN;

CREATE TABLE IF NOT EXISTS fastest_prices.refresh_source (
    cohort_id text PRIMARY KEY REFERENCES fastest_prices.cohort (id),
    config jsonb NOT NULL,
    cursor text,
    attempt_id uuid,
    next_attempt_at timestamptz
);

CREATE TABLE IF NOT EXISTS fastest_prices.refresh_event (
    cohort_id text NOT NULL REFERENCES fastest_prices.refresh_source (cohort_id),
    event_id text NOT NULL,
    version bigint NOT NULL,
    offer jsonb NOT NULL,
    PRIMARY KEY (cohort_id, event_id, version)
);

CREATE OR REPLACE FUNCTION fastest_prices.refresh_policy(cohort_key text)
RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE
    policy jsonb := fastest_prices.active_cohort(cohort_key);
BEGIN
    IF policy->>'source_type' <> 'seller' THEN
        RAISE EXCEPTION 'The price refresh adapter requires one approved direct seller';
    END IF;
    IF (policy #>> '{authorization,expires_at}')::timestamptz <= clock_timestamp() THEN
        RAISE EXCEPTION 'Cohort approval has expired';
    END IF;
    RETURN policy;
END;
$$;

CREATE OR REPLACE FUNCTION fastest_prices.register_refresh(cohort_key text, settings jsonb)
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
    PERFORM fastest_prices.refresh_policy(cohort_key);
    INSERT INTO fastest_prices.refresh_source (cohort_id, config) VALUES (cohort_key, settings)
    ON CONFLICT DO NOTHING;
    IF NOT EXISTS (
        SELECT FROM fastest_prices.refresh_source WHERE cohort_id = cohort_key AND config = settings
    ) THEN
        RAISE EXCEPTION 'Refresh settings are immutable; register a new approved cohort to change them';
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION fastest_prices.begin_refresh(
    cohort_key text, attempt uuid, checked text, live boolean
)
RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE
    policy jsonb := fastest_prices.refresh_policy(cohort_key);
    source fastest_prices.refresh_source%ROWTYPE;
BEGIN
    IF live AND policy->>'data_class' <> 'authorized_observations' THEN
        RAISE EXCEPTION 'Live refresh requires approval for authorized observations';
    END IF;
    SELECT * INTO source FROM fastest_prices.refresh_source WHERE cohort_id = cohort_key;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Seller refresh settings are missing';
    END IF;
    IF checked::timestamptz < source.next_attempt_at THEN
        RETURN jsonb_build_object('status', 'deferred', 'next_attempt_at', source.next_attempt_at);
    END IF;
    UPDATE fastest_prices.refresh_source SET attempt_id = attempt,
        next_attempt_at = checked::timestamptz + make_interval(secs => (source.config->>'minimum_interval_seconds')::int)
    WHERE cohort_id = cohort_key;
    PERFORM fastest_prices.record_capture(cohort_key, jsonb_build_object(
        'id', 'refresh:' || attempt || ':started',
        'source_id', policy->'source_id', 'source_revision', policy->'source_revision',
        'checked_at', checked, 'status', 'incomplete', 'observations', '[]'::jsonb, 'source_adapter', true
    ));
    RETURN jsonb_build_object('status', 'incomplete', 'cursor', source.cursor, 'config', source.config);
END;
$$;

CREATE OR REPLACE FUNCTION fastest_prices.finish_refresh(
    cohort_key text, attempt uuid, checked text, outcome text, next_cursor text, records jsonb, retry_at text
)
RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE
    policy jsonb := fastest_prices.refresh_policy(cohort_key);
    source fastest_prices.refresh_source%ROWTYPE;
    accepted jsonb := '[]'::jsonb;
BEGIN
    SELECT * INTO source FROM fastest_prices.refresh_source WHERE cohort_id = cohort_key;
    IF source.attempt_id IS DISTINCT FROM attempt THEN
        RAISE EXCEPTION 'Refresh attempt is no longer active';
    END IF;
    IF outcome NOT IN ('success', 'failed', 'incomplete') THEN
        RAISE EXCEPTION 'Invalid seller refresh outcome';
    END IF;
    IF outcome = 'success' THEN
        WITH inserted AS (
            INSERT INTO fastest_prices.refresh_event (cohort_id, event_id, version, offer)
            SELECT cohort_key, item->>'source_event_id', (item->>'source_event_version')::bigint, item
            FROM jsonb_array_elements(records) AS rows(item)
            ON CONFLICT DO NOTHING
            RETURNING event_id, version, offer
        )
        SELECT coalesce(jsonb_agg(offer ORDER BY event_id, version), '[]'::jsonb)
        INTO accepted FROM inserted;

        IF EXISTS (
            SELECT FROM jsonb_array_elements(records) AS rows(item)
            JOIN fastest_prices.refresh_event AS event ON event.cohort_id = cohort_key
                AND event.event_id = item->>'source_event_id'
                AND event.version = (item->>'source_event_version')::bigint
            WHERE event.offer <> item
        ) THEN
            RAISE EXCEPTION 'Seller sent conflicting data for an existing observation version';
        END IF;
    END IF;
    IF outcome <> 'incomplete' THEN
        PERFORM fastest_prices.record_capture(cohort_key, jsonb_build_object(
            'id', 'refresh:' || attempt || ':finished',
            'source_id', policy->'source_id', 'source_revision', policy->'source_revision',
            'checked_at', checked, 'status', outcome, 'observations', accepted, 'source_adapter', true
        ));
    END IF;
    UPDATE fastest_prices.refresh_source SET attempt_id = NULL,
        cursor = CASE WHEN outcome = 'success' THEN next_cursor ELSE cursor END,
        next_attempt_at = greatest(next_attempt_at, retry_at::timestamptz)
    WHERE cohort_id = cohort_key;
    RETURN jsonb_build_object('status', outcome, 'observations_recorded', jsonb_array_length(accepted));
END;
$$;

REVOKE ALL ON ALL TABLES IN SCHEMA fastest_prices FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA fastest_prices FROM PUBLIC;

COMMIT;
