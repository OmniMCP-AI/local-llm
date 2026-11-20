BEGIN;

CREATE SCHEMA IF NOT EXISTS fastest_contributor;

CREATE TABLE IF NOT EXISTS fastest_contributor.submission (
    submission_id uuid PRIMARY KEY,
    receipt uuid NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    evidence_id uuid NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    contributor_id text
);

CREATE TABLE IF NOT EXISTS fastest_contributor.entry (
    submission_id uuid NOT NULL REFERENCES fastest_contributor.submission (submission_id),
    version integer NOT NULL CHECK (version > 0),
    document text NOT NULL,
    issues jsonb NOT NULL,
    received_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    review jsonb,
    release_id uuid REFERENCES fastest_release.data_release (id),
    PRIMARY KEY (submission_id, version)
);

CREATE UNIQUE INDEX IF NOT EXISTS contributor_decision_id
    ON fastest_contributor.entry ((review->>'decision_id')) WHERE review IS NOT NULL;

CREATE OR REPLACE FUNCTION fastest_contributor.submit_record(
    identifier uuid, submitted_version integer, owner_id text, raw text, intake_issues jsonb
)
RETURNS uuid LANGUAGE plpgsql AS $$
DECLARE
    filing fastest_contributor.submission%ROWTYPE;
    prior text;
BEGIN
    INSERT INTO fastest_contributor.submission (submission_id, contributor_id)
    VALUES (identifier, owner_id) ON CONFLICT DO NOTHING;

    SELECT * INTO STRICT filing FROM fastest_contributor.submission
    WHERE submission_id = identifier FOR UPDATE;

    SELECT document INTO prior FROM fastest_contributor.entry
    WHERE submission_id = identifier AND version = submitted_version;
    IF FOUND THEN
        IF prior <> raw THEN
            RAISE EXCEPTION 'Submission version already exists with different input';
        END IF;
        RETURN filing.receipt;
    END IF;

    IF owner_id IS NOT NULL THEN
        IF filing.contributor_id IS NULL THEN
            UPDATE fastest_contributor.submission SET contributor_id = owner_id WHERE submission_id = identifier;
        ELSIF filing.contributor_id <> owner_id THEN
            RAISE EXCEPTION 'Amendments require the original contributor ID';
        END IF;
    END IF;

    INSERT INTO fastest_contributor.entry (submission_id, version, document, issues)
    VALUES (identifier, submitted_version, raw, intake_issues);
    RETURN filing.receipt;
END;
$$;

CREATE OR REPLACE FUNCTION fastest_contributor.review_entry(
    receipt_code uuid, submitted_version integer, reviewed jsonb, observation jsonb
)
RETURNS void LANGUAGE plpgsql AS $$
DECLARE
    filing fastest_contributor.submission%ROWTYPE;
    entry fastest_contributor.entry%ROWTYPE;
    published uuid;
BEGIN
    SELECT * INTO STRICT filing FROM fastest_contributor.submission
    WHERE receipt = receipt_code FOR UPDATE;

    SELECT * INTO STRICT entry FROM fastest_contributor.entry
    WHERE submission_id = filing.submission_id AND version = submitted_version;

    IF entry.review IS NOT NULL THEN
        IF entry.review <> reviewed THEN
            RAISE EXCEPTION 'Submission version already has an editorial decision';
        END IF;
        RETURN;
    END IF;

    IF reviewed->>'outcome' = 'publish' THEN
        IF entry.issues <> '[]'::jsonb OR observation IS NULL THEN
            RAISE EXCEPTION 'Only reviewed, eligible submission versions can be published';
        END IF;
        IF EXISTS (
            SELECT FROM fastest_contributor.entry
            WHERE submission_id = filing.submission_id AND version > submitted_version
        ) THEN
            RAISE EXCEPTION 'Only the latest submitted version can be newly published';
        END IF;
        IF (observation #>> '{rights,expires_at}')::timestamptz <= clock_timestamp() THEN
            RAISE EXCEPTION 'Publication authorization expired';
        END IF;
        published := fastest_release.publish_observation(observation);
    END IF;

    UPDATE fastest_contributor.entry
    SET review = reviewed, release_id = published
    WHERE submission_id = filing.submission_id AND version = submitted_version;
END;
$$;

CREATE OR REPLACE FUNCTION fastest_contributor.receipt_status(receipt_code uuid)
RETURNS jsonb LANGUAGE sql STABLE AS $$
    SELECT jsonb_build_object(
        'receipt', submission.receipt,
        'revisions', jsonb_agg(
            jsonb_build_object(
                'version', entry.version,
                'status', CASE
                    WHEN entry.release_id IS NOT NULL THEN fastest_release.read_release(entry.release_id)->>'status'
                    WHEN entry.review IS NOT NULL THEN 'rejected'
                    WHEN entry.issues <> '[]'::jsonb THEN 'quarantined'
                    ELSE 'pending_review'
                END,
                'issues', entry.issues
            ) || CASE WHEN entry.release_id IS NULL THEN '{}'::jsonb ELSE jsonb_build_object(
                'release_id', entry.release_id,
                'url', '/releases/' || entry.release_id || '/benchmark.html'
            ) END ORDER BY entry.version
        )
    )
    FROM fastest_contributor.submission AS submission
    JOIN fastest_contributor.entry AS entry USING (submission_id)
    WHERE submission.receipt = receipt_code
    GROUP BY submission.receipt;
$$;

REVOKE ALL ON SCHEMA fastest_contributor FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA fastest_contributor FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA fastest_contributor FROM PUBLIC;

COMMIT;
