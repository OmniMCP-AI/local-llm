BEGIN;

CREATE SCHEMA IF NOT EXISTS fastest_battles;
REVOKE ALL ON SCHEMA fastest_battles FROM PUBLIC;

-- Store the anonymous idempotency key and a digest of the exact selection.
CREATE TABLE IF NOT EXISTS fastest_battles.recorded_request (
    request_id uuid PRIMARY KEY,
    selection_digest bytea NOT NULL CHECK (octet_length(selection_digest) = 32)
);

CREATE TABLE IF NOT EXISTS fastest_battles.daily_comparison (
    snapshot_id text REFERENCES fastest_catalog.snapshot(id),
    kind text CHECK (kind IN ('cards', 'machines')),
    recorded_on date,
    left_id text COLLATE "C",
    right_id text COLLATE "C",
    count bigint NOT NULL DEFAULT 1 CHECK (count > 0),
    CHECK (left_id < right_id),
    PRIMARY KEY (snapshot_id, kind, recorded_on, left_id, right_id)
);

CREATE OR REPLACE FUNCTION fastest_battles.is_catalog_snapshot(pinned_snapshot text)
RETURNS boolean
LANGUAGE sql STABLE SET search_path = pg_catalog AS $$
    SELECT EXISTS (
        SELECT FROM fastest_catalog.snapshot
        WHERE id = pinned_snapshot AND id ~ '^[0-9a-f]{64}$'
            AND document #>> '{pages,projectionDigest}' ~ '^[0-9a-f]{64}$'
    );
$$;

CREATE OR REPLACE FUNCTION fastest_battles.record_comparison(
    pinned_snapshot text, comparison_kind text, first_id text, second_id text, submitted_request uuid
)
RETURNS text
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $$
DECLARE
    pair_left text := LEAST(first_id COLLATE "C", second_id COLLATE "C");
    pair_right text := GREATEST(first_id COLLATE "C", second_id COLLATE "C");
    selection bytea;
BEGIN
    IF NOT fastest_battles.is_catalog_snapshot(pinned_snapshot) THEN
        RETURN 'snapshot_unavailable';
    END IF;

    IF submitted_request IS NULL OR first_id IS NULL OR second_id IS NULL OR pair_left = pair_right
        OR comparison_kind IS NULL OR comparison_kind NOT IN ('cards', 'machines') THEN
        RETURN 'invalid_pair';
    END IF;

    IF comparison_kind = 'cards' THEN
        IF (SELECT count(*) FROM fastest_catalog.gpu
            WHERE snapshot_id = pinned_snapshot AND id IN (pair_left, pair_right)) <> 2 THEN
            RETURN 'invalid_pair';
        END IF;
    ELSE
        IF (SELECT count(*) FROM fastest_catalog.machine
            WHERE snapshot_id = pinned_snapshot AND id IN (pair_left, pair_right)
              AND document->>'kind' <> 'Component reference') <> 2 THEN
            RETURN 'invalid_pair';
        END IF;
    END IF;

    selection := sha256(convert_to(jsonb_build_array(pinned_snapshot, comparison_kind, pair_left, pair_right)::text, 'UTF8'));
    INSERT INTO fastest_battles.recorded_request (request_id, selection_digest)
    VALUES (submitted_request, selection)
    ON CONFLICT (request_id) DO NOTHING;

    IF NOT FOUND THEN
        -- A competing insert completes before the duplicate check. Under READ COMMITTED
        -- this next statement can see the committed selection without rewriting its row.
        IF EXISTS (SELECT FROM fastest_battles.recorded_request
            WHERE request_id = submitted_request AND selection_digest = selection) THEN
            RETURN 'retry';
        END IF;
        RETURN 'conflict';
    END IF;

    INSERT INTO fastest_battles.daily_comparison AS daily (snapshot_id, kind, recorded_on, left_id, right_id)
    VALUES (pinned_snapshot, comparison_kind, (statement_timestamp() AT TIME ZONE 'UTC')::date, pair_left, pair_right)
    ON CONFLICT (snapshot_id, kind, recorded_on, left_id, right_id) DO UPDATE SET count = daily.count + 1;
    RETURN 'created';
END;
$$;

CREATE OR REPLACE FUNCTION fastest_battles.rank_comparisons(pinned_snapshot text, comparison_kind text)
RETURNS jsonb
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog AS $$
    SELECT CASE WHEN fastest_battles.is_catalog_snapshot(pinned_snapshot)
        AND comparison_kind IN ('cards', 'machines') THEN
        COALESCE((
            SELECT jsonb_agg(jsonb_build_object('left', left_id, 'right', right_id, 'count', count)
                ORDER BY count DESC, left_id, right_id)
            FROM (
                SELECT left_id, right_id, sum(count) AS count
                FROM fastest_battles.daily_comparison
                WHERE snapshot_id = pinned_snapshot AND kind = comparison_kind
                  AND recorded_on BETWEEN (statement_timestamp() AT TIME ZONE 'UTC')::date - 29
                                  AND (statement_timestamp() AT TIME ZONE 'UTC')::date
                GROUP BY left_id, right_id
                ORDER BY count DESC, left_id, right_id
                LIMIT 10
            ) AS ranked
        ), '[]'::jsonb)
    END;
$$;

REVOKE ALL ON ALL TABLES IN SCHEMA fastest_battles FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA fastest_battles FROM PUBLIC;

COMMIT;
