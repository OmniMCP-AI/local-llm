BEGIN;

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
    amount numeric CHECK (amount >= 0 AND amount < 1e12),
    kind text NOT NULL,
    condition text NOT NULL,
    source_date date,
    listing_url text CHECK (listing_url ~ '^https://'),
    qualification text NOT NULL CHECK (qualification <> ''),
    PRIMARY KEY (batch_id, id),
    FOREIGN KEY (batch_id, source) REFERENCES fastest_intake.source_probe(batch_id, source)
);

-- Add retail provenance to existing captures without replacing the table or its rows.
ALTER TABLE fastest_intake.price_candidate
    ADD COLUMN IF NOT EXISTS seller_business_name text CHECK (seller_business_name ~ '[^[:space:]]'),
    ADD COLUMN IF NOT EXISTS listing_status text
        CHECK (listing_status IN ('in_stock', 'out_of_stock', 'preorder', 'sold', 'ended', 'unknown')),
    ADD COLUMN IF NOT EXISTS shipping_amount numeric CHECK (shipping_amount >= 0 AND shipping_amount < 1e12),
    ADD COLUMN IF NOT EXISTS tax_amount numeric CHECK (tax_amount >= 0 AND tax_amount < 1e12);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_constraint
        WHERE conrelid = 'fastest_intake.price_candidate'::regclass
            AND conname = 'price_candidate_kind_status_check'
    ) THEN
        ALTER TABLE fastest_intake.price_candidate
            ALTER COLUMN amount DROP NOT NULL,
            DROP CONSTRAINT IF EXISTS price_candidate_kind_check,
            DROP CONSTRAINT IF EXISTS price_candidate_condition_check,
            ADD CONSTRAINT price_candidate_condition_check
                CHECK (condition IN ('new', 'used', 'open_box', 'refurbished', 'unknown')),
            ADD CONSTRAINT price_candidate_amount_required
                CHECK (kind = 'best_offer_accepted' OR amount IS NOT NULL),
            ADD CONSTRAINT price_candidate_kind_status_check CHECK (
                kind IN ('asking_price', 'editorial_quote', 'bundle_quote', 'aggregate_low',
                         'historical_low', 'social_claim')
                OR (kind = 'completed_listing_price' AND coalesce(listing_status IN ('sold', 'ended'), false))
                OR (kind IN ('best_offer_accepted', 'verified_settlement') AND listing_status IS NOT DISTINCT FROM 'sold')
            );
    END IF;
END;
$$;

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

CREATE TABLE IF NOT EXISTS fastest_intake.inference_trial (
    batch_id text,
    id text CHECK (id ~ '[^[:space:]]'),
    source text NOT NULL,
    locator text NOT NULL CHECK (locator ~ '[^[:space:]]'),
    outcome text NOT NULL CHECK (outcome IN ('measured', 'failed', 'oom', 'unknown')),
    gpu_count integer CHECK (gpu_count > 0),
    gpu_ids text[] CHECK (
        array_ndims(gpu_ids) = 1 AND cardinality(gpu_ids) > 0
        AND array_position(gpu_ids, NULL) IS NULL AND array_position(gpu_ids, '') IS NULL
        AND (gpu_count IS NULL OR cardinality(gpu_ids) <= gpu_count)
    ),
    model text,
    model_revision text,
    artifact text,
    artifact_revision text,
    runtime text,
    runtime_revision text,
    backend text,
    quantization text,
    context_tokens integer CHECK (context_tokens > 0),
    observed_on date,
    metric text CHECK (metric ~ '[^[:space:]]'),
    amount numeric CHECK (amount >= 0 AND amount < 'Infinity'::numeric),
    unit text CHECK (unit ~ '[^[:space:]]'),
    statistic text CHECK (statistic ~ '[^[:space:]]'),
    sample_count integer CHECK (sample_count > 0),
    reported_uncertainty numeric CHECK (reported_uncertainty >= 0 AND reported_uncertainty < 'Infinity'::numeric),
    uncertainty_kind text CHECK (uncertainty_kind ~ '[^[:space:]]'),
    placement text CHECK (placement ~ '[^[:space:]]'),
    transport text CHECK (transport ~ '[^[:space:]]'),
    context jsonb CHECK (jsonb_typeof(context) = 'object'),
    qualification text NOT NULL CHECK (qualification ~ '[^[:space:]]'),
    CONSTRAINT inference_trial_outcome_measurement_check CHECK (
        (outcome = 'measured' AND metric IS NOT NULL AND amount IS NOT NULL AND unit IS NOT NULL)
        OR (outcome <> 'measured' AND metric IS NULL AND amount IS NULL AND unit IS NULL
            AND statistic IS NULL AND reported_uncertainty IS NULL)
    ),
    CHECK (uncertainty_kind IS NULL OR reported_uncertainty IS NOT NULL),
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

COMMIT;
