BEGIN;

CREATE SCHEMA IF NOT EXISTS fastest_intake;
REVOKE ALL ON SCHEMA fastest_intake FROM PUBLIC;

CREATE TABLE IF NOT EXISTS fastest_intake.image_team_scenario (
    pin text PRIMARY KEY CHECK (pin ~ '^[0-9a-f]{64}$'),
    scenario json NOT NULL CHECK (
        (scenario->'schema_version')::text IS NOT DISTINCT FROM '1'
        AND scenario->>'kind' IS NOT DISTINCT FROM 'consented'
        AND (scenario #> '{workload,public_aggregate_allowed}')::text IS NOT DISTINCT FROM 'true'
        AND scenario #>> '{workload,source,kind}' IS NOT DISTINCT FROM 'reviewed'
    )
);

CREATE TABLE IF NOT EXISTS fastest_intake.image_team_withdrawal (
    pin text PRIMARY KEY REFERENCES fastest_intake.image_team_scenario(pin),
    withdrawn_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP
);

REVOKE ALL ON TABLE fastest_intake.image_team_scenario, fastest_intake.image_team_withdrawal FROM PUBLIC;

COMMIT;
