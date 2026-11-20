BEGIN;

CREATE SCHEMA IF NOT EXISTS fastest_research;
REVOKE ALL ON SCHEMA fastest_research FROM PUBLIC;

CREATE TABLE IF NOT EXISTS fastest_research.seed (
    id text PRIMARY KEY CHECK (id ~ '^[0-9a-f]{64}$'),
    manifest jsonb NOT NULL
);

CREATE TABLE IF NOT EXISTS fastest_research.seed_record (
    seed_id text NOT NULL REFERENCES fastest_research.seed(id),
    kind text NOT NULL,
    id text NOT NULL,
    document jsonb NOT NULL,
    PRIMARY KEY (seed_id, kind, id)
);

REVOKE ALL ON ALL TABLES IN SCHEMA fastest_research FROM PUBLIC;

COMMIT;
