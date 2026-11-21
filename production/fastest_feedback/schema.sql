BEGIN;

CREATE SCHEMA IF NOT EXISTS fastest_feedback;
REVOKE ALL ON SCHEMA fastest_feedback FROM PUBLIC;

CREATE TABLE IF NOT EXISTS fastest_feedback.feedback_submission (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id uuid UNIQUE NOT NULL,
    category text NOT NULL CHECK (category IN ('correction', 'missing', 'confusing', 'other')),
    message text NOT NULL,
    context_json jsonb,
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status text NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'reviewed'))
);

CREATE TABLE IF NOT EXISTS fastest_feedback.feedback_resolution (
    receipt_id uuid PRIMARY KEY REFERENCES fastest_feedback.feedback_submission (id),
    public_path text NOT NULL CHECK (public_path ~ '^/wiki/evidence-updates#[a-f0-9]{64}$')
);

CREATE OR REPLACE FUNCTION fastest_feedback.submit_feedback(
    submitted_request uuid, submitted_category text, submitted_message text, submitted_context jsonb
)
RETURNS TABLE (id uuid, status text, outcome text)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $$
DECLARE
    stored fastest_feedback.feedback_submission%ROWTYPE;
BEGIN
    INSERT INTO fastest_feedback.feedback_submission AS submission (request_id, category, message, context_json)
    VALUES (submitted_request, submitted_category, submitted_message, submitted_context)
    ON CONFLICT (request_id) DO NOTHING
    RETURNING submission.* INTO stored;
    IF FOUND THEN
        RETURN QUERY SELECT stored.id, stored.status, 'created'::text;
        RETURN;
    END IF;

    -- Under READ COMMITTED the insert waits for any competing write, then the
    -- next statement can see its committed receipt without rewriting the row.
    SELECT * INTO STRICT stored FROM fastest_feedback.feedback_submission AS submission
    WHERE submission.request_id = submitted_request;

    IF stored.category <> submitted_category OR stored.message <> submitted_message
        OR stored.context_json IS DISTINCT FROM submitted_context THEN
        RETURN QUERY SELECT NULL::uuid, NULL::text, 'conflict'::text;
        RETURN;
    END IF;
    RETURN QUERY SELECT stored.id, stored.status, 'retry'::text;
END;
$$;

CREATE OR REPLACE FUNCTION fastest_feedback.read_feedback_receipt(receipt uuid)
RETURNS TABLE (id uuid, status text, public_path text)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog AS $$
    SELECT submission.id, submission.status, resolution.public_path
    FROM fastest_feedback.feedback_submission AS submission
    LEFT JOIN fastest_feedback.feedback_resolution AS resolution ON resolution.receipt_id = submission.id
    WHERE submission.id = receipt;
$$;

CREATE OR REPLACE FUNCTION fastest_feedback.link_feedback_resolution(
    receipt uuid, accepted_context jsonb, approved_path text
)
RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $$
BEGIN
    UPDATE fastest_feedback.feedback_submission
    SET status = 'reviewed'
    WHERE id = receipt AND category = 'correction' AND context_json = accepted_context;
    IF NOT FOUND THEN
        RETURN false;
    END IF;

    INSERT INTO fastest_feedback.feedback_resolution (receipt_id, public_path)
    VALUES (receipt, approved_path)
    ON CONFLICT (receipt_id) DO UPDATE SET public_path = excluded.public_path;
    RETURN true;
END;
$$;

REVOKE ALL ON ALL TABLES IN SCHEMA fastest_feedback FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA fastest_feedback FROM PUBLIC;

COMMIT;
