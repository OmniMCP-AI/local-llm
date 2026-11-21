BEGIN;

CREATE TABLE IF NOT EXISTS fastest_intake.tariff_reference_review (
    pin text PRIMARY KEY CHECK (pin ~ '^[0-9a-f]{64}$'),
    decision_id uuid NOT NULL UNIQUE,
    expires_at timestamptz NOT NULL,
    selection jsonb NOT NULL CHECK (jsonb_typeof(selection) = 'array'),
    components jsonb NOT NULL CHECK (jsonb_typeof(components) = 'array'),
    approved_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (expires_at > approved_at)
);

CREATE TABLE IF NOT EXISTS fastest_intake.tariff_reference_withdrawal (
    pin text PRIMARY KEY REFERENCES fastest_intake.tariff_reference_review(pin),
    withdrawn_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE SCHEMA IF NOT EXISTS fastest_cost_public;
REVOKE ALL ON SCHEMA fastest_cost_public FROM PUBLIC;
REVOKE ALL ON TABLE fastest_intake.tariff_reference_review, fastest_intake.tariff_reference_withdrawal FROM PUBLIC;

CREATE OR REPLACE FUNCTION fastest_cost_public.read_tariff_references(exact_pin text)
RETURNS jsonb
LANGUAGE SQL STABLE SECURITY DEFINER
SET search_path = pg_catalog
AS $$
    SELECT jsonb_build_object(
        'schema_version', 1,
        'revision', review.pin,
        'authorization', jsonb_build_object(
            'status', 'approved',
            'decision_id', review.decision_id,
            'expires_at', to_char(review.expires_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"')
        ),
        'references', active.components
    )
    FROM fastest_intake.tariff_reference_review AS review
    CROSS JOIN LATERAL (
        SELECT jsonb_agg(item.component ORDER BY item.ordinal) AS components
        FROM jsonb_array_elements(review.components) WITH ORDINALITY AS item(component, ordinal)
        WHERE (item.component->>'effective_from' IS NULL
              OR (item.component->>'effective_from')::date <= (CURRENT_TIMESTAMP AT TIME ZONE 'UTC')::date)
          AND (item.component->>'effective_until' IS NULL
              OR (CURRENT_TIMESTAMP AT TIME ZONE 'UTC')::date < (item.component->>'effective_until')::date)
    ) AS active
    WHERE review.pin = exact_pin AND review.expires_at > CURRENT_TIMESTAMP AND active.components IS NOT NULL
      AND NOT EXISTS (
          SELECT FROM fastest_intake.tariff_reference_withdrawal AS withdrawal WHERE withdrawal.pin = review.pin
      );
$$;

REVOKE ALL ON FUNCTION fastest_cost_public.read_tariff_references(text) FROM PUBLIC;

COMMIT;
