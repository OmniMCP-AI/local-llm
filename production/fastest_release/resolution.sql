BEGIN;

CREATE TABLE IF NOT EXISTS fastest_release.evidence_resolution (
    request_hash bytea PRIMARY KEY,
    result jsonb NOT NULL
);

CREATE OR REPLACE FUNCTION fastest_release.resolve_benchmark(input jsonb)
RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE
    evidence uuid := (input->>'evidenceId')::uuid;
    prior uuid := (input->>'previousRelease')::uuid;
    action text := input->>'action';
    input_hash bytea := sha256(convert_to(input::text, 'UTF8'));
    previous jsonb;
    latest uuid;
    result jsonb;
    before_snapshots jsonb;
    after_snapshots jsonb;
    outcome uuid;
BEGIN
    PERFORM 1 FROM fastest_release.current_release WHERE singleton FOR UPDATE;
    SELECT entry.result INTO result FROM fastest_release.evidence_resolution AS entry
    WHERE entry.request_hash = input_hash;
    IF FOUND THEN
        RETURN result;
    END IF;

    previous := fastest_release.read_release(prior);
    IF previous->>'status' IS DISTINCT FROM 'published'
        OR (previous #>> '{row,evidence_id}')::uuid IS DISTINCT FROM evidence
        OR previous #>> '{row,source,locator}' IS DISTINCT FROM input->>'sourceLocator' THEN
        RAISE EXCEPTION 'Evidence ID and locator do not match the published benchmark';
    END IF;

    IF action = 'correct' THEN
        SELECT id INTO latest FROM fastest_release.data_release AS release
        WHERE release.evidence_id = evidence ORDER BY revision DESC LIMIT 1;
        IF latest IS DISTINCT FROM prior OR (input #>> '{correction,evidence_id}')::uuid IS DISTINCT FROM evidence THEN
            RAISE EXCEPTION 'Correction must match the latest published benchmark evidence';
        END IF;
        outcome := fastest_release.publish_observation(input->'correction');
        IF EXISTS (SELECT FROM fastest_release.data_release WHERE id = outcome AND revision <= (previous->>'revision')::integer) THEN
            RAISE EXCEPTION 'Correction must publish a new revision';
        END IF;
        before_snapshots := '[]'::jsonb;
        after_snapshots := jsonb_build_array(fastest_release.read_release(outcome));
    ELSIF action = 'withdraw' THEN
        SELECT jsonb_agg(fastest_release.read_release(id) ORDER BY revision) INTO before_snapshots
        FROM fastest_release.data_release WHERE evidence_id = evidence;
        PERFORM fastest_release.withdraw_evidence(evidence, 'Reviewed evidence resolution');
        SELECT jsonb_agg(fastest_release.read_release(id) ORDER BY revision) INTO after_snapshots
        FROM fastest_release.data_release WHERE evidence_id = evidence;
        outcome := prior;
    ELSE
        RAISE EXCEPTION 'Unknown benchmark resolution action';
    END IF;

    result := jsonb_build_object('release', outcome, 'before', before_snapshots, 'after', after_snapshots);
    INSERT INTO fastest_release.evidence_resolution VALUES (input_hash, result);
    RETURN result;
END;
$$;

REVOKE ALL ON FUNCTION fastest_release.resolve_benchmark(jsonb) FROM PUBLIC;
REVOKE ALL ON TABLE fastest_release.evidence_resolution FROM PUBLIC;

COMMIT;
