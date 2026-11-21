BEGIN;

CREATE SCHEMA IF NOT EXISTS fastest_prices;

CREATE TABLE IF NOT EXISTS fastest_prices.cohort (
    id text PRIMARY KEY,
    document jsonb NOT NULL,
    CHECK (document #>> '{authorization,status}' IS NOT DISTINCT FROM 'approved'),
    CHECK (document #>> '{authorization,collect}' IS NOT DISTINCT FROM 'allow'),
    CHECK (document #>> '{authorization,retain}' IS NOT DISTINCT FROM 'allow'),
    CHECK (document #>> '{authorization,display}' IS NOT DISTINCT FROM 'allow'),
    CHECK (document #>> '{authorization,export}' IS NOT DISTINCT FROM 'allow')
);

CREATE TABLE IF NOT EXISTS fastest_prices.capture (
    sequence bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cohort_id text NOT NULL REFERENCES fastest_prices.cohort (id),
    id text NOT NULL,
    checked_at timestamptz NOT NULL,
    status text NOT NULL,
    document jsonb NOT NULL,
    UNIQUE (cohort_id, id)
);

ALTER TABLE fastest_prices.capture DROP CONSTRAINT IF EXISTS capture_status_check;
ALTER TABLE fastest_prices.capture ADD CONSTRAINT capture_status_check
    CHECK (status IN ('success', 'failed', 'incomplete'));

CREATE TABLE IF NOT EXISTS fastest_prices.observation (
    capture_sequence bigint NOT NULL REFERENCES fastest_prices.capture (sequence),
    ordinal bigint NOT NULL,
    seller text NOT NULL,
    listing_id text NOT NULL,
    observed_at timestamptz NOT NULL,
    price numeric NOT NULL CHECK (price >= 0 AND price < 1e12),
    document jsonb NOT NULL CHECK (document #>> '{review,status}' IS NOT DISTINCT FROM 'approved'),
    PRIMARY KEY (capture_sequence, ordinal)
);

CREATE TABLE IF NOT EXISTS fastest_prices.release (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    cohort_id text NOT NULL REFERENCES fastest_prices.cohort (id),
    start_day date NOT NULL,
    as_of date NOT NULL,
    capture_cutoff bigint NOT NULL,
    method_version text NOT NULL,
    CHECK (as_of - start_day BETWEEN 0 AND 365),
    UNIQUE (cohort_id, start_day, as_of, capture_cutoff, method_version)
);

CREATE TABLE IF NOT EXISTS fastest_prices.withdrawal (
    cohort_id text PRIMARY KEY REFERENCES fastest_prices.cohort (id),
    reason text NOT NULL,
    withdrawn_at timestamptz NOT NULL DEFAULT clock_timestamp()
);

CREATE OR REPLACE FUNCTION fastest_prices.approve(input jsonb)
RETURNS text LANGUAGE plpgsql AS $$
DECLARE
    cohort_key text := input->>'id';
    expiry text := input #>> '{authorization,expires_at}';
BEGIN
    IF input->'authorization' ? 'expires_at' THEN
        IF expiry IS NULL OR expiry !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]Z$' THEN
            RAISE EXCEPTION 'Authorization expiry requires a UTC timestamp';
        END IF;
        PERFORM expiry::timestamptz;
    END IF;

    IF input->>'source_type' = 'citation' AND (
        input->>'data_class' IS DISTINCT FROM 'reviewed_citations'
        OR input #>> '{authorization,aggregate}' IS DISTINCT FROM 'deny'
        OR input #>> '{scope,kind}' IS DISTINCT FROM 'sku'
    ) THEN
        RAISE EXCEPTION 'Price citation requires an exact SKU and citation-only approval';
    END IF;

    INSERT INTO fastest_prices.cohort (id, document)
    VALUES (cohort_key, input) ON CONFLICT DO NOTHING;

    IF NOT EXISTS (
        SELECT FROM fastest_prices.cohort WHERE id = cohort_key AND document = input
    ) THEN
        RAISE EXCEPTION 'Cohort approval is immutable; use a new cohort ID for a changed policy';
    END IF;
    RETURN cohort_key;
END;
$$;

CREATE OR REPLACE FUNCTION fastest_prices.active_cohort(cohort_key text)
RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE
    policy jsonb;
BEGIN
    SELECT document INTO STRICT policy FROM fastest_prices.cohort WHERE id = cohort_key FOR UPDATE;
    IF EXISTS (SELECT FROM fastest_prices.withdrawal WHERE cohort_id = cohort_key) THEN
        RAISE EXCEPTION 'Cohort approval has been withdrawn';
    END IF;
    RETURN policy;
EXCEPTION WHEN no_data_found THEN
    RAISE EXCEPTION 'Cohort approval is missing';
END;
$$;

CREATE OR REPLACE FUNCTION fastest_prices.record_capture(cohort_key text, input jsonb)
RETURNS bigint LANGUAGE plpgsql AS $$
DECLARE
    policy jsonb := fastest_prices.active_cohort(cohort_key);
    capture_number bigint;
BEGIN
    IF policy->>'source_id' IS DISTINCT FROM input->>'source_id'
        OR policy->>'source_revision' IS DISTINCT FROM input->>'source_revision' THEN
        RAISE EXCEPTION 'Capture source or revision does not match the approval';
    END IF;

    IF (policy->>'source_type' = 'citation') IS DISTINCT FROM (input ? 'references') THEN
        RAISE EXCEPTION 'Capture type does not match the cohort approval';
    END IF;

    IF EXISTS (
        SELECT FROM jsonb_array_elements(input->'observations') AS offers(offer)
        WHERE policy->'seller_aliases'->>(offer->>'seller') IS NULL
            OR policy->'scope' IS DISTINCT FROM offer->'scope'
            OR policy->'market' IS DISTINCT FROM offer->'market'
            OR policy->'destination' IS DISTINCT FROM offer->'destination'
            OR policy->'condition' IS DISTINCT FROM offer->'condition'
            OR policy->'currency' IS DISTINCT FROM offer->'currency'
    ) THEN
        RAISE EXCEPTION 'Observation does not match the approved seller, exact scope, market, destination, condition, or currency';
    END IF;

    SELECT sequence INTO capture_number FROM fastest_prices.capture
    WHERE cohort_id = cohort_key AND id = input->>'id' AND document = input;
    IF FOUND THEN
        RETURN capture_number;
    END IF;

    IF EXISTS (SELECT FROM fastest_prices.capture WHERE cohort_id = cohort_key AND id = input->>'id') THEN
        RAISE EXCEPTION 'Capture ID already exists with different input; append a new capture';
    END IF;

    IF policy->>'source_type' = 'citation' THEN
        IF EXISTS (SELECT FROM fastest_prices.capture WHERE cohort_id = cohort_key) THEN
            RAISE EXCEPTION 'A citation cohort has one reviewed capture';
        END IF;
        IF input ? 'observations' OR input->>'status' IS DISTINCT FROM 'success'
            OR jsonb_array_length(input->'references') NOT BETWEEN 1 AND 3 THEN
            RAISE EXCEPTION 'A citation capture needs one to three price references';
        END IF;
    END IF;

    INSERT INTO fastest_prices.capture (cohort_id, id, checked_at, status, document)
    VALUES (cohort_key, input->>'id', (input->>'checked_at')::timestamptz, input->>'status', input)
    RETURNING sequence INTO capture_number;

    INSERT INTO fastest_prices.observation (capture_sequence, ordinal, seller, listing_id, observed_at, price, document)
    SELECT capture_number, ordinal, policy->'seller_aliases'->>(offer->>'seller'),
        offer->>'listing_id', (offer->>'observed_at')::timestamptz, (offer->>'price')::numeric, offer
    FROM jsonb_array_elements(input->'observations') WITH ORDINALITY AS offers(offer, ordinal);
    RETURN capture_number;
END;
$$;

CREATE OR REPLACE FUNCTION fastest_prices.publish(cohort_key text, window_start date, window_end date, method_key text)
RETURNS uuid LANGUAGE plpgsql AS $$
DECLARE
    policy jsonb := fastest_prices.active_cohort(cohort_key);
    cutoff bigint;
    pinned_method text;
    release_key uuid;
BEGIN
    SELECT coalesce(max(sequence), 0),
        CASE WHEN policy->>'source_type' = 'citation' THEN 'source-reported-price-citation-v1'
             WHEN bool_or(document ? 'source_adapter') THEN 'seller-day-landed-asking-v2'
             ELSE method_key END
    INTO cutoff, pinned_method
    FROM fastest_prices.capture
    WHERE cohort_id = cohort_key AND (checked_at AT TIME ZONE 'UTC')::date <= window_end;

    INSERT INTO fastest_prices.release (cohort_id, start_day, as_of, capture_cutoff, method_version)
    VALUES (cohort_key, window_start, window_end, cutoff, pinned_method)
    ON CONFLICT DO NOTHING;

    SELECT id INTO STRICT release_key FROM fastest_prices.release
    WHERE cohort_id = cohort_key AND start_day = window_start AND as_of = window_end AND capture_cutoff = cutoff
        AND method_version = pinned_method;
    RETURN release_key;
END;
$$;

CREATE OR REPLACE FUNCTION fastest_prices.read_release(release_key uuid)
RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog AS $$
    SELECT jsonb_build_object(
        'release_id', requested.id,
        'cohort_id', requested.cohort_id,
        'method', requested.method_version,
        'status', CASE WHEN rights.available THEN 'published' ELSE 'withdrawn' END
    ) || CASE WHEN rights.available THEN jsonb_build_object(
        'start', requested.start_day,
        'as_of', requested.as_of,
        'cohort', cohort.document - ARRAY['id', 'seller_aliases', 'authorization'],
        'decision_id', cohort.document #>> '{authorization,decision_id}',
        'expires_at', cohort.document #>> '{authorization,expires_at}',
        'can_aggregate', cohort.document #>> '{authorization,aggregate}' = 'allow',
        'captures', coalesce((
            SELECT jsonb_agg(jsonb_build_object('checked_at', captured.document->'checked_at', 'status', captured.status)
                ORDER BY captured.checked_at, captured.sequence)
            FROM fastest_prices.capture AS captured
            WHERE captured.cohort_id = requested.cohort_id AND captured.sequence <= requested.capture_cutoff
                AND (captured.checked_at AT TIME ZONE 'UTC')::date <= requested.as_of
        ), '[]'::jsonb),
        'offers', coalesce((
            SELECT jsonb_agg(dedup.offer ORDER BY dedup.day, dedup.seller, dedup.listing_id, dedup.kind)
            FROM (
                SELECT DISTINCT ON (day, observation.seller, observation.listing_id, kind)
                    (observation.observed_at AT TIME ZONE 'UTC')::date AS day,
                    observation.seller, observation.listing_id, observation.document->>'kind' AS kind,
                    (observation.document - ARRAY['source_event_id', 'source_event_version']) || jsonb_build_object(
                        'seller', observation.seller,
                        'price', observation.price::text,
                        'captured_at', observation.captured_at
                    ) AS offer
                FROM (
                    SELECT offer.*, captured.checked_at, captured.document->'checked_at' AS captured_at,
                        row_number() OVER (PARTITION BY offer.document->>'source_event_id'
                            ORDER BY (offer.document->>'source_event_version')::bigint DESC NULLS LAST)
                            AS event_rank
                    FROM fastest_prices.observation AS offer
                    JOIN fastest_prices.capture AS captured ON captured.sequence = offer.capture_sequence
                    WHERE captured.cohort_id = requested.cohort_id AND captured.sequence <= requested.capture_cutoff
                        AND (captured.checked_at AT TIME ZONE 'UTC')::date <= requested.as_of
                ) AS observation
                WHERE (observation.event_rank = 1 OR NOT observation.document ? 'source_event_id')
                    AND (observation.observed_at AT TIME ZONE 'UTC')::date BETWEEN requested.start_day AND requested.as_of
                ORDER BY day, observation.seller, observation.listing_id, kind,
                    observation.observed_at DESC, observation.checked_at DESC, observation.capture_sequence DESC, observation.ordinal DESC
            ) AS dedup
        ), '[]'::jsonb)
    ) ELSE '{}'::jsonb END
    || CASE WHEN rights.available AND cohort.document->>'source_type' = 'citation' THEN jsonb_build_object(
        'references', coalesce((
            SELECT jsonb_agg(ref.item ORDER BY ref.item->>'observed_on', ref.ordinal)
            FROM fastest_prices.capture AS captured
            CROSS JOIN LATERAL jsonb_array_elements(captured.document->'references')
                WITH ORDINALITY AS ref(item, ordinal)
            WHERE captured.cohort_id = requested.cohort_id AND captured.sequence <= requested.capture_cutoff
                AND (ref.item->>'observed_on')::date BETWEEN requested.start_day AND requested.as_of
        ), '[]'::jsonb)
    ) ELSE '{}'::jsonb END
    FROM fastest_prices.release AS requested
    JOIN fastest_prices.cohort AS cohort ON cohort.id = requested.cohort_id
    LEFT JOIN fastest_prices.withdrawal AS withdrawn ON withdrawn.cohort_id = requested.cohort_id
    CROSS JOIN LATERAL (
        SELECT withdrawn.cohort_id IS NULL AND coalesce(
            (cohort.document #>> '{authorization,expires_at}')::timestamptz > statement_timestamp(), true
        ) AS available
    ) AS rights
    WHERE requested.id = release_key;
$$;

REVOKE ALL ON SCHEMA fastest_prices FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA fastest_prices FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA fastest_prices FROM PUBLIC;

COMMIT;
