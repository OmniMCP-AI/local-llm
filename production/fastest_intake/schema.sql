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

CREATE TABLE IF NOT EXISTS fastest_intake.model_evaluation (
    batch_id text,
    id text CHECK (id <> ''),
    source text NOT NULL,
    locator text NOT NULL CHECK (locator <> ''),
    model text NOT NULL CHECK (model <> ''),
    revision text,
    benchmark text NOT NULL CHECK (benchmark <> ''),
    benchmark_version text,
    metric text NOT NULL CHECK (metric <> ''),
    amount numeric NOT NULL CHECK (amount >= 0 AND amount < 1e12),
    unit text NOT NULL CHECK (unit IN ('percent', 'index_points', 'reported_score', 'rating')),
    CHECK (unit <> 'percent' OR amount <= 100),
    evidence_class text NOT NULL CHECK (evidence_class IN ('publisher_reported', 'independent_evaluation')),
    context jsonb NOT NULL CHECK (jsonb_typeof(context) = 'object'),
    PRIMARY KEY (batch_id, id),
    FOREIGN KEY (batch_id, source) REFERENCES fastest_intake.source_probe(batch_id, source)
);

CREATE TABLE IF NOT EXISTS fastest_intake.tariff_candidate (
    batch_id text,
    id text CHECK (id <> ''),
    source text NOT NULL,
    locator text NOT NULL CHECK (locator <> ''),
    kind text NOT NULL,
    provider text NOT NULL CHECK (provider <> ''),
    offering text NOT NULL CHECK (offering <> ''),
    revision text NOT NULL CHECK (revision <> ''),
    market text NOT NULL CHECK (market ~ '^[A-Z]{2}$'),
    region text NOT NULL CHECK (region <> ''),
    currency text NOT NULL CHECK (currency ~ '^[A-Z]{3}$'),
    amount numeric NOT NULL CHECK (amount >= 0 AND amount < 1e12),
    unit text NOT NULL,
    component text NOT NULL CHECK (component <> ''),
    effective_from date,
    effective_until date,
    qualification text NOT NULL CHECK (qualification <> ''),
    CHECK ((kind = 'electricity' AND unit IN ('kwh', 'month'))
        OR (kind = 'rental' AND unit IN ('instance_hour', 'month'))
        OR (kind = 'api' AND unit IN ('million_input_tokens', 'million_cached_input_tokens',
                                      'million_output_tokens', 'month'))),
    CHECK (effective_until > effective_from),
    PRIMARY KEY (batch_id, id),
    FOREIGN KEY (batch_id, source) REFERENCES fastest_intake.source_probe(batch_id, source)
);

CREATE TABLE IF NOT EXISTS fastest_intake.image_pilot_run (
    manifest_sha256 text PRIMARY KEY CHECK (manifest_sha256 ~ '^[0-9a-f]{64}$'),
    provenance_sha256 text NOT NULL CHECK (provenance_sha256 ~ '^[0-9a-f]{64}$'),
    ledger_sha256 text NOT NULL CHECK (ledger_sha256 ~ '^[0-9a-f]{64}$'),
    packet_locator text NOT NULL CHECK (packet_locator <> ''),
    started_at timestamptz NOT NULL,
    cell_id text NOT NULL CHECK (cell_id <> ''),
    plan_sha256 text NOT NULL CHECK (plan_sha256 ~ '^[0-9a-f]{64}$'),
    protocol_id text NOT NULL CHECK (protocol_id <> ''),
    workflow_sha256 text NOT NULL CHECK (workflow_sha256 ~ '^[0-9a-f]{64}$'),
    artifact_sha256 text NOT NULL CHECK (artifact_sha256 ~ '^[0-9a-f]{64}$'),
    artifact_repository text NOT NULL CHECK (artifact_repository <> ''),
    artifact_revision text NOT NULL CHECK (artifact_revision <> ''),
    runtime_revision text NOT NULL CHECK (runtime_revision <> ''),
    lock_sha256 text NOT NULL CHECK (lock_sha256 ~ '^[0-9a-f]{64}$'),
    eligibility text NOT NULL CHECK (eligibility = 'exploratory'),
    quality_status text NOT NULL CHECK (quality_status = 'pending')
);

CREATE TABLE IF NOT EXISTS fastest_intake.image_pilot_attempt (
    manifest_sha256 text REFERENCES fastest_intake.image_pilot_run(manifest_sha256),
    attempt_index smallint CHECK (attempt_index >= 0),
    phase text NOT NULL CHECK (phase IN ('warmup', 'repeat')),
    seed bigint NOT NULL,
    outcome text NOT NULL CHECK (outcome IN ('success', 'oom', 'timeout', 'interrupted', 'failed')),
    elapsed_ns bigint NOT NULL CHECK (elapsed_ns > 0),
    phase_end_ns jsonb NOT NULL CHECK (jsonb_typeof(phase_end_ns) = 'object'),
    output_sha256 text CHECK (output_sha256 ~ '^[0-9a-f]{64}$'),
    failure_reason text CHECK (failure_reason <> ''),
    PRIMARY KEY (manifest_sha256, attempt_index),
    CHECK ((attempt_index = 0) = (phase = 'warmup')),
    CHECK ((outcome = 'success' AND output_sha256 IS NOT NULL AND failure_reason IS NULL)
        OR (outcome <> 'success' AND output_sha256 IS NULL AND failure_reason IS NOT NULL))
);

REVOKE ALL ON ALL TABLES IN SCHEMA fastest_intake FROM PUBLIC;
