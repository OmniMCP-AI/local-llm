CREATE SCHEMA IF NOT EXISTS fastest_intake;
REVOKE ALL ON SCHEMA fastest_intake FROM PUBLIC;

CREATE TABLE IF NOT EXISTS fastest_intake.batch (
    id text PRIMARY KEY CHECK (id ~ '^[0-9a-f]{64}$'),
    checked_at timestamptz NOT NULL,
    note text NOT NULL
);

CREATE TABLE IF NOT EXISTS fastest_intake.source_probe (
    batch_id text REFERENCES fastest_intake.batch(id),
    source text CHECK (source <> ''),
    url text NOT NULL CHECK (url ~ '^https://'),
    status text NOT NULL CHECK (status IN ('captured', 'no_quote', 'restricted', 'no_verified_result')),
    note text NOT NULL,
    PRIMARY KEY (batch_id, source)
);

CREATE TABLE IF NOT EXISTS fastest_intake.price_candidate (
    batch_id text,
    id text CHECK (id <> ''),
    source text NOT NULL,
    locator text NOT NULL CHECK (locator <> ''),
    gpu_id text NOT NULL CHECK (gpu_id <> ''),
    board text,
    channel text NOT NULL CHECK (channel <> ''),
    market text NOT NULL CHECK (market ~ '^[A-Z]{2}$'),
    currency text NOT NULL CHECK (currency ~ '^[A-Z]{3}$'),
    amount numeric NOT NULL CHECK (amount >= 0 AND amount < 1e12),
    kind text NOT NULL CHECK (kind IN ('asking_price', 'editorial_quote', 'bundle_quote', 'aggregate_low', 'historical_low', 'social_claim')),
    condition text NOT NULL CHECK (condition IN ('new', 'used', 'refurbished', 'unknown')),
    source_date date,
    listing_url text CHECK (listing_url ~ '^https://'),
    qualification text NOT NULL CHECK (qualification <> ''),
    PRIMARY KEY (batch_id, id),
    FOREIGN KEY (batch_id, source) REFERENCES fastest_intake.source_probe(batch_id, source)
);
