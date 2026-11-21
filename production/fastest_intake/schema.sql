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

CREATE TABLE IF NOT EXISTS fastest_intake.serving_capture_run (
    capture_sha256 text PRIMARY KEY CHECK (capture_sha256 ~ '^[0-9a-f]{64}$'),
    trace_sha256 text NOT NULL CHECK (trace_sha256 ~ '^[0-9a-f]{64}$'),
    protocol_id text NOT NULL CHECK (protocol_id = 'four-user-fixed-token-serving@1'),
    kind text NOT NULL CHECK (kind IN ('diagnostic', 'private-capture')),
    capture_status text NOT NULL CHECK (capture_status IN ('complete', 'partial', 'failed', 'interrupted')),
    duration_ms integer NOT NULL CHECK (duration_ms BETWEEN 0 AND 144000),
    window_started_at timestamptz,
    capture_finished_at timestamptz,
    review_status text NOT NULL CHECK (review_status = 'held'),
    separate_host_status text NOT NULL CHECK (separate_host_status = 'unverified'),
    power_status text NOT NULL CHECK (power_status = 'missing'),
    CHECK (capture_status NOT IN ('complete', 'partial') OR duration_ms = 144000)
);

CREATE TABLE IF NOT EXISTS fastest_intake.serving_capture_attempt (
    capture_sha256 text REFERENCES fastest_intake.serving_capture_run(capture_sha256),
    user_slot smallint CHECK (user_slot BETWEEN 1 AND 4),
    request_number smallint CHECK (request_number BETWEEN 1 AND 24),
    scheduled_ms integer NOT NULL CHECK (scheduled_ms = (request_number - 1) * 6000),
    started_ms bigint NOT NULL CHECK (started_ms >= scheduled_ms),
    outcome text NOT NULL CHECK (outcome IN ('accepted', 'rejected', 'failed', 'timeout', 'unrecorded')),
    elapsed_ms integer CHECK (elapsed_ms BETWEEN 1 AND 5000),
    observed_elapsed_ns bigint CHECK (observed_elapsed_ns >= 0),
    output_tokens integer CHECK (output_tokens >= 0),
    PRIMARY KEY (capture_sha256, user_slot, request_number),
    CHECK (
        (outcome = 'unrecorded' AND elapsed_ms IS NULL AND observed_elapsed_ns IS NULL AND output_tokens IS NULL)
        OR (outcome <> 'unrecorded' AND elapsed_ms IS NOT NULL AND observed_elapsed_ns IS NOT NULL
            AND output_tokens IS NOT NULL AND started_ms <= scheduled_ms + 100)
    ),
    CHECK (outcome <> 'accepted' OR output_tokens = 128),
    CHECK (outcome NOT IN ('failed', 'timeout') OR output_tokens = 0),
    CHECK (outcome <> 'timeout' OR elapsed_ms = 5000)
);

CREATE TABLE IF NOT EXISTS fastest_intake.scaling_capture_run (
    capture_sha256 text PRIMARY KEY CHECK (capture_sha256 ~ '^[0-9a-f]{64}$'),
    evidence_sha256 text NOT NULL CHECK (evidence_sha256 ~ '^[0-9a-f]{64}$'),
    capture_status text NOT NULL CHECK (capture_status IN ('complete', 'incomplete', 'failed', 'interrupted')),
    review_status text NOT NULL CHECK (review_status = 'held'),
    metadata jsonb NOT NULL CHECK (jsonb_typeof(metadata) = 'object')
);

CREATE TABLE IF NOT EXISTS fastest_intake.scaling_capture_attempt (
    capture_sha256 text REFERENCES fastest_intake.scaling_capture_run(capture_sha256),
    role text CHECK (role IN ('baseline', 'comparison')),
    run_id uuid NOT NULL UNIQUE,
    receipt_sha256 text NOT NULL CHECK (receipt_sha256 ~ '^[0-9a-f]{64}$'),
    outcome text NOT NULL CHECK (outcome IN ('complete', 'invalid-output', 'oom', 'failed',
                                             'timeout', 'interrupted', 'unavailable')),
    started_at timestamptz NOT NULL,
    finished_at timestamptz CHECK (finished_at >= started_at),
    exit_code integer,
    timeout_seconds numeric NOT NULL CHECK (timeout_seconds > 0),
    samples_ns bigint[] NOT NULL CHECK (
        cardinality(samples_ns) IN (0, 20) AND (array_ndims(samples_ns) = 1 OR cardinality(samples_ns) = 0)
        AND array_position(samples_ns, NULL) IS NULL AND 0 < ALL(samples_ns)
    ),
    metadata jsonb NOT NULL CHECK (jsonb_typeof(metadata) = 'object'),
    PRIMARY KEY (capture_sha256, role),
    CHECK (outcome <> 'complete' OR
           (exit_code IS NOT DISTINCT FROM 0 AND finished_at IS NOT NULL AND cardinality(samples_ns) = 20))
);

CREATE TABLE IF NOT EXISTS fastest_intake.scaling_capture_transport (
    comparison_run_id uuid PRIMARY KEY REFERENCES fastest_intake.scaling_capture_attempt(run_id),
    receipt_sha256 text NOT NULL CHECK (receipt_sha256 ~ '^[0-9a-f]{64}$'),
    trace_sha256 text NOT NULL CHECK (trace_sha256 ~ '^[0-9a-f]{64}$'),
    links_sha256 text NOT NULL CHECK (links_sha256 ~ '^[0-9a-f]{64}$'),
    links jsonb NOT NULL CHECK (jsonb_typeof(links) = 'array' AND jsonb_array_length(links) > 0),
    attached_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS fastest_intake.text_capture_run (
    capture_sha256 text PRIMARY KEY CHECK (capture_sha256 ~ '^[0-9a-f]{64}$'),
    evidence_sha256 text NOT NULL CHECK (evidence_sha256 ~ '^[0-9a-f]{64}$'),
    capture_status text NOT NULL CHECK (capture_status IN ('complete', 'incomplete', 'blocked', 'interrupted')),
    packet_kind text NOT NULL CHECK (packet_kind IN ('fixed-token-v1', 'ambient-m4-legacy')),
    cell_id text NOT NULL CHECK (cell_id IN ('apple-m4', 'rtx-4090')),
    review_status text NOT NULL CHECK (review_status = 'held'),
    started_at timestamptz NOT NULL,
    finished_at timestamptz NOT NULL CHECK (finished_at >= started_at),
    metadata jsonb NOT NULL CHECK (jsonb_typeof(metadata) = 'object')
);

CREATE TABLE IF NOT EXISTS fastest_intake.text_capture_phase (
    capture_sha256 text REFERENCES fastest_intake.text_capture_run(capture_sha256),
    phase text CHECK (phase IN ('prefill', 'decode')),
    outcome text NOT NULL CHECK (outcome IN ('complete', 'partial', 'failed', 'oom', 'invalid-output', 'incomplete',
                                             'timeout', 'interrupted', 'not-run', 'unavailable')),
    receipt_sha256 text CHECK (receipt_sha256 ~ '^[0-9a-f]{64}$'),
    placement jsonb CHECK (jsonb_typeof(placement) = 'object'),
    files jsonb CHECK (jsonb_typeof(files) = 'object'),
    PRIMARY KEY (capture_sha256, phase),
    CHECK (outcome IN ('not-run', 'unavailable') OR (receipt_sha256 IS NOT NULL AND placement IS NOT NULL))
);

CREATE TABLE IF NOT EXISTS fastest_intake.text_capture_attempt (
    capture_sha256 text,
    phase text,
    attempt_number integer CHECK (attempt_number BETWEEN 1 AND 20),
    outcome text NOT NULL CHECK (outcome IN ('success', 'failed', 'oom', 'timeout', 'interrupted', 'unmeasured')),
    elapsed_ns bigint CHECK (elapsed_ns > 0),
    PRIMARY KEY (capture_sha256, phase, attempt_number),
    FOREIGN KEY (capture_sha256, phase) REFERENCES fastest_intake.text_capture_phase(capture_sha256, phase),
    CHECK ((outcome = 'success') = (elapsed_ns IS NOT NULL))
);

CREATE TABLE IF NOT EXISTS fastest_intake.text_latency_run (
    capture_sha256 text PRIMARY KEY CHECK (capture_sha256 ~ '^[0-9a-f]{64}$'),
    cell_id text NOT NULL CHECK (cell_id IN ('apple-m4', 'rtx-4090')),
    capture_status text NOT NULL CHECK (capture_status IN ('complete', 'incomplete', 'blocked', 'interrupted')),
    started_at timestamptz NOT NULL,
    finished_at timestamptz NOT NULL CHECK (finished_at >= started_at),
    protocol text NOT NULL CHECK (protocol = 'llama-server-native-zh-copy-latency@1'),
    quiet_host boolean NOT NULL,
    warmup_status text NOT NULL CHECK (warmup_status IN ('not-run', 'complete', 'incomplete', 'failed', 'timeout', 'interrupted')),
    attempt_status text NOT NULL CHECK (attempt_status IN ('not-run', 'complete', 'incomplete', 'failed', 'timeout', 'interrupted')),
    prompt_tokens integer CHECK (prompt_tokens BETWEEN 1 AND 2048),
    output_tokens integer CHECK (output_tokens BETWEEN 0 AND 256),
    token_events integer NOT NULL CHECK (token_events BETWEEN 0 AND 256),
    ttft_ns bigint CHECK (ttft_ns > 0),
    first_visible_answer_ns bigint CHECK (first_visible_answer_ns > 0),
    binary_sha256 text CHECK (binary_sha256 ~ '^[0-9a-f]{64}$'),
    CHECK ((capture_status = 'complete') = (attempt_status = 'complete')),
    CHECK (attempt_status = 'not-run' OR warmup_status = 'complete'),
    CHECK (attempt_status <> 'complete' OR (prompt_tokens IS NOT NULL AND output_tokens IS NOT NULL
                                            AND binary_sha256 IS NOT NULL)),
    CHECK (ttft_ns <= first_visible_answer_ns)
);

CREATE OR REPLACE VIEW fastest_intake.eligible_text_latency AS
SELECT capture_sha256, cell_id, binary_sha256, prompt_tokens, output_tokens, ttft_ns, first_visible_answer_ns
FROM fastest_intake.text_latency_run
WHERE capture_status = 'complete' AND quiet_host;

REVOKE ALL ON ALL TABLES IN SCHEMA fastest_intake FROM PUBLIC;

COMMIT;
