BEGIN;

CREATE SCHEMA IF NOT EXISTS fastest_decision_pilot;
REVOKE ALL ON SCHEMA fastest_decision_pilot FROM PUBLIC;

CREATE TABLE IF NOT EXISTS fastest_decision_pilot.decision_case (
    case_id text PRIMARY KEY CHECK (case_id ~ '^case-[0-9]{3}$'),
    consent text CHECK (consent IN ('granted', 'pending', 'declined', 'withdrawn')),
    missing text[] NOT NULL,
    details jsonb,
    CHECK ((details IS NOT NULL) = (cardinality(missing) = 0)),
    CHECK (details IS NULL OR consent IS NOT DISTINCT FROM 'granted')
);

CREATE TABLE IF NOT EXISTS fastest_decision_pilot.buyer_observation (
    participant_id text PRIMARY KEY CHECK (participant_id ~ '^participant-[0-9]{3}$'),
    case_id text REFERENCES fastest_decision_pilot.decision_case (case_id),
    consent text CHECK (consent IN ('granted', 'pending', 'declined', 'withdrawn')),
    missing text[] NOT NULL,
    details jsonb,
    CHECK ((details IS NOT NULL) = (cardinality(missing) = 0)),
    CHECK ((details IS NULL) = (case_id IS NULL)),
    CHECK (details IS NULL OR consent IS NOT DISTINCT FROM 'granted')
);

REVOKE ALL ON ALL TABLES IN SCHEMA fastest_decision_pilot FROM PUBLIC;

COMMIT;
