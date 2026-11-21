# Private evidence intake

The collector's evidence bundle imports into the private `fastest_intake` PostgreSQL schema. A source may have a successful page check, a page without a price, restricted access, or no verified result. Price candidates identify the reporting source and retail channel separately. Capture time, source date, market, currency, condition, exact board and listing URL retain their own fields. Bundle, asking, coupon-adjusted and historical amounts retain different kinds.

Evaluations preserve the model identity, benchmark version, reported metric and scale, source locator, and evaluation settings where stated. The model-card revision in the source locator or context records which document was read. Leave the tested checkpoint revision unset unless the publisher supplies it.

Run from `production` with the development database selected:

```sh
export FASTEST_DATABASE_URL=postgresql://localhost/localdecode_catalog
python3 -B -m fastest_intake migrate
python3 -B -m fastest_intake ingest intake/your-capture.json
python3 -B -m fastest_intake stats
```

The input JSON has `checked_at`, `note`, `sources`, `prices` and `evaluations`, with optional `tariffs` and `inference_trials` arrays. Run `migrate` before ingesting with the updated CLI. See the schema for typed columns. The content hash identifies the batch and replay is idempotent. Earlier bundles keep their original hash when replayed as supplied. Keep capture bundles under the ignored intake directory.

Use the exact catalog board ID as `gpu_id` when it is known. The optional `seller_business_name` records the business named by the source. Use `listing_status` for the observed state (`in_stock`, `out_of_stock`, `preorder`, `sold`, `ended`, or `unknown`). Use `ended` when the source shows a closed listing without confirming a sale. Use `open_box` when the source explicitly identifies that condition.

Record separately stated `shipping_amount` and `tax_amount` as decimal strings in the row's `currency`. Use null or omit the field when the amount is unknown. Zero represents an explicitly zero charge.

- `asking_price` records a seller's quoted price.
- `completed_listing_price` records the amount shown for a listing marked `sold` or `ended`.
- `best_offer_accepted` records a listing marked `sold` that confirms an accepted offer and leaves the final amount undisclosed. Set `amount` to the displayed reference price when available or use null.
- `verified_settlement` records the final amount supported by transaction evidence for a listing marked `sold`. Use the source and locator to identify that evidence.

Record the listing wording, charges or exclusions, and evidence limits in `qualification`. The price rows appear in the private `price_candidates` total. Public price cohorts require their own editorial review.

Use one tariff row for each quoted rate component. Each row identifies the provider, exact offering, tariff revision, market, region, currency, amount, billing unit and component, source and locator. Use a decimal string for the amount. Electricity accepts `kwh` and `month`. Rental accepts `instance_hour` and `month`. API accepts `million_input_tokens`, `million_cached_input_tokens`, `million_output_tokens` and `month`. Record the published start date as `effective_from` and the exclusive end date as `effective_until` when known. The batch's `checked_at` records capture time. Use `qualification` for time bands, account eligibility, billing terms and exclusions.

Every tariff candidate must reference a `captured` source probe in the same bundle. Use a `no_quote` probe by itself when the source provides no applicable rate. With an intake operator connection, join `fastest_intake.tariff_candidate`, `fastest_intake.source_probe` and `fastest_intake.batch` on batch and source to inspect the terms, cited URL and check time. Operator review can approve [tariff references for public display](../fastest_cost/README.md#configure-reviewed-tariff-references) or [workload-specific calculation inputs](../fastest_cost/README.md#configure-reviewed-evidence).

Intake migration installs the tariff approval tables and the origin's
rights-filtered function. Intake stats count retained reviews and withdrawals.

Review rights, exact identity, methodology, and current offer status before preparing a release. The public pricing and benchmark endpoints read their existing reviewed stores.

## Benchmark collection sources

**Local LLM Benchmarks**, maintained by Donato Capitella, is a candidate for source-reported local inference and agent-task data. Keep its release eligibility pending source review. [Benchmark hub](https://local-llm-benchmarks.dev/)

| Collection | Intake fields | Access and review |
| --- | --- | --- |
| [Speed by context depth](https://local-llm-benchmarks.dev/speed) | Keep prompt processing and token generation separate. Preserve the run ID, backend/build, model revision and quantization, hardware and device count, context depth, serving mode, concurrency, request rate, repeats, and run-specific settings. Distinguish cached-prefix extensions and post-first-token timing from native full-prefix runs. | Direct automated access to the Speed page returned HTTP 403 on November 21, 2026. The site advertises reference use and excludes training. Prefer a publisher-provided export with reviewed collection and display terms. [Robots policy](https://local-llm-benchmarks.dev/robots.txt) |
| [Terminal-Bench-Local Core-19](https://kyuz0.github.io/terminal-bench-mini/) | Preserve the suite manifest, scores and denominator, publisher model label, and known engine, backend, agent, and settings. | A commit-pinned structured import is available for private evidence review. Public reuse is pending a separate review. |

## Import source-reported Core-19 scores

From `production`, select the private PostgreSQL intake database and run `python3 -B -m fastest_intake migrate`.
Set `checked_at` to the source check time with a time zone and record it for replay. Use the same
timestamp and files to replay the same batch.

```sh
(
  set -eu
  packet=$(mktemp -d "${TMPDIR:-/tmp}/fastest-core19.XXXXXX")
  trap 'rm -rf "$packet"' EXIT
  trap 'exit 1' HUP INT TERM
  repo=kyuz0/terminal-bench-mini
  revision=f28e1a024df97d40470a5e10a0147a56650b6457
  suite=results/suites/core19-8db507125de192b10b0930110efe9e014696fa30c274dc8e76c8337a84e23cf7
  checked_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  gh api -H 'Accept: application/vnd.github.raw+json' "repos/$repo/contents/$suite/index.json?ref=$revision" > "$packet/index.json"
  gh api -H 'Accept: application/vnd.github.raw+json' "repos/$repo/contents/docs/data.json?ref=$revision" > "$packet/data.json"
  printf 'Source check time %s\n' "$checked_at"
  python3 -B -m fastest_intake ingest-core19 "$packet" --checked-at "$checked_at"
)
```

The importer verifies both file digests and checks the full Core-19 1.0.0 suite index against the
publisher's Explorer v2 summary. It retains two `publisher_reported` scores per complete profile
in `fastest_intake.model_evaluation`. The integer `amount` is the number of tasks passed on the first
attempt or within the recorded attempts, with a denominator of 19 for both. The 27 profiles in this
snapshot yield 46 observations from 23 profiles. The captured source note records the four deferred
incomplete profiles. Completed profiles can include attempted tasks that ended in counted failures
without a completed task flag. The context records this count along with the number of recorded attempts.
Projected legacy scores are outside the pinned suite.

Each row cites the publisher's immutable result summary and retains the run profile hash, platform,
and known runtime, agent, and settings. The model is the publisher's label and the tested checkpoint
revision stays unset. The import retains run-level facts in the private schema. Task instructions,
transcripts, and endpoint metadata stay out of the database. The repository declares Apache-2.0, and
the provenance notice describes the vendored tasks separately from the locally produced results.
Public reuse remains pending review. [Suite index](https://github.com/kyuz0/terminal-bench-mini/blob/f28e1a024df97d40470a5e10a0147a56650b6457/results/suites/core19-8db507125de192b10b0930110efe9e014696fa30c274dc8e76c8337a84e23cf7/index.json) · [Explorer data](https://github.com/kyuz0/terminal-bench-mini/blob/f28e1a024df97d40470a5e10a0147a56650b6457/docs/data.json) · [Provenance notice](https://github.com/kyuz0/terminal-bench-mini/blob/f28e1a024df97d40470a5e10a0147a56650b6457/NOTICE.md)

## Import source-reported GPU inference trials

Use one `inference_trials` row per source-reported metric or outcome. Every row needs a distinct `id`, a `source` that refers to a captured probe in the same bundle, the exact table, row or section `locator`, an `outcome`, and `qualification` describing what the evidence can establish. The probe records the source URL. Use a pinned document or revision URL when available.

- `outcome` is `measured` when the source supplies a numeric result. Record `metric`, `amount` and `unit` with the original phase, numeric precision and unit spelling. Use a decimal string for `amount`. Record `statistic`, `sample_count` and `reported_uncertainty` when reported. Use `uncertainty_kind` when the source identifies what the numeric uncertainty represents. Place ranges or other source information in `context`.
- Use `oom` for an explicit out-of-memory result, `failed` for another reported failure, and `unknown` when the outcome is unavailable. Leave `metric`, `amount`, `unit`, `statistic`, `reported_uncertainty` and `uncertainty_kind` unset for these outcomes. Use `qualification` for the reported reason or gap.
- `gpu_count` is the number of active physical GPUs reported for the trial. Use `gpu_ids` for known source-reported GPU identities, preserving order where the source states it. Repeat the same identity for multiple known identical GPUs and omit individual identities that the source leaves unknown. A source label may identify only a GPU family.
- Record `model`, `model_revision`, `artifact`, `artifact_revision`, `runtime`, `runtime_revision`, `backend` and `quantization` as reported. Use `observed_on` for a stated trial date and `context_tokens` for the configured context window. Keep prompt length, generation length, KV format, artifact digests, and other reported settings in the `context` object.
- Use `placement` for the reported model or KV distribution and `transport` for a transfer path observed for this trial. Keep topology inventory and separate transfer probes in `context`, with the scope of each observation. Omit optional fields or use null when evidence is unavailable.

A synthetic bundle with a partial transport record:

```json
{
  "checked_at": "2026-11-20T00:00:00Z",
  "note": "Operator captured the source's decode table.",
  "sources": [
    {
      "source": "example-benchmark",
      "url": "https://benchmark.example/benchmarks#decode",
      "status": "captured",
      "note": "The results include summary statistics and a host inventory."
    }
  ],
  "prices": [],
  "evaluations": [],
  "inference_trials": [
    {
      "id": "two-gpu-vulkan-tg128",
      "source": "example-benchmark",
      "locator": "Decode table, dual Vulkan row",
      "outcome": "measured",
      "gpu_count": 2,
      "gpu_ids": ["Example Board A", "Example Board B"],
      "model": "Example 27B",
      "artifact": "example-27b-q6_k.gguf",
      "runtime": "llama.cpp",
      "backend": "Vulkan",
      "quantization": "Q6_K",
      "metric": "tg128",
      "amount": "42.60",
      "unit": "tok/s",
      "statistic": "arithmetic_mean",
      "sample_count": 3,
      "reported_uncertainty": "0.10",
      "uncertainty_kind": "standard_deviation",
      "placement": "Proportional layer split.",
      "context": {"generated_tokens": 128, "topology": "Host inventory lists PCIe Gen 4."},
      "qualification": "Artifact revision, raw samples and the run's transfer path are unavailable."
    }
  ]
}
```

`ingest` and `stats` report the private `inference_trials` count. With an intake operator connection, inspect capture time and provenance alongside the trial:

```sql
SELECT batch.checked_at, probe.url, trial.*
FROM fastest_intake.inference_trial AS trial
JOIN fastest_intake.source_probe AS probe USING (batch_id, source)
JOIN fastest_intake.batch AS batch ON batch.id = trial.batch_id
ORDER BY batch.checked_at, trial.batch_id, trial.id;
```

Source-reported rows are review candidates. The [scaling evidence review](../fastest_release/SCALING-EVIDENCE.md) describes the protocol, exact identity, quality, transport, and rights evidence needed to publish a scaling pair.

## Import private image-pilot timing

Run from `production` with `FASTEST_DATABASE_URL` set to the operator database.

```sh
python3 -B -m fastest_intake migrate
python3 -B -m fastest_intake ingest-image-pilot /path/to/private-pilot-packet
```

The packet directory contains `provenance.json`, `run/attempts.json` and `SHA256SUMS`. The importer verifies both JSON files against the manifest, checks the protocol, model, workflow, runtime and dependency lock against the pinned plan, and checks each successful attempt's recorded output digest against its manifest entry. Keep the packet and original images in private storage. The importer reads the two JSON files and manifest and stores only selected provenance, fingerprints, the private directory locator and the timing rows.

The receipt reports the manifest digest and persisted attempt counts, including the warmup. Replaying the same manifest preserves one run and one row per attempt. Intake marks timing evidence exploratory and quality pending. The receipt counts successful requests. The accepted-image rate requires a separate blind review.

Query runs and attempts with an intake operator connection.

```sql
SELECT run.cell_id, run.started_at, attempt.phase, attempt.seed,
       attempt.outcome, attempt.elapsed_ns, attempt.phase_end_ns, attempt.failure_reason
FROM fastest_intake.image_pilot_run AS run
JOIN fastest_intake.image_pilot_attempt AS attempt USING (manifest_sha256)
ORDER BY run.started_at, manifest_sha256, attempt.attempt_index;
```

## Import a private four-user serving capture

Run from `production` with `FASTEST_DATABASE_URL` set to the intake operator database.

```sh
python3 -B -m fastest_intake migrate
python3 -B -m fastest_intake ingest-serving-capture /path/to/private-serving-run
python3 -B -m fastest_intake stats
```

Pass the directory from [the serving collector](../fastest_serving/README.md#capture-the-pinned-workload). The importer reads `capture.json` and `trace.jsonl`, checks the pinned workload, and matches the timed request outcomes, latency, and output counts against the trace. The receipt identifies the exact input bytes with both SHA-256 digests. Replaying the same files preserves one run and one row per recorded slot. Reusing the same ledger with different trace bytes is rejected.

Finalized partial, failed, and interrupted captures can be stored when their ledger and trace agree. A missed slot explicitly logged in the trace has outcome `unrecorded` and null response fields. Slots that were never reached have no attempt row. The receipt's `unrecorded` count covers both cases. Captures still marked starting, armed, or capturing need a finalized ledger before import.

The receipt distinguishes `diagnostic` and `private-capture`. Every import is held for review, with separate-host provenance unverified and power missing. A non-loopback address alone cannot establish a dedicated second host. A meter-window announcement identifies the sampling window. Calibration, feed coverage, and actual samples are established through the separate [meter evidence workflow](../fastest_serving/README.md#retain-calibrated-ac-meter-evidence). Publication requires a [reviewed serving record](../fastest_serving/README.md#serve-a-reviewed-run).

Keep the original packet and server provenance in private storage. PostgreSQL keeps protocol and capture status, file digests, window timing, and numeric workload slots with their outcomes, latencies, and output counts. Host identifiers, private paths, free-text notes and reasons, request payloads, and response content stay in the packet.

```sql
SELECT run.capture_sha256, run.kind, run.capture_status, run.power_status,
       attempt.request_number, attempt.user_slot, attempt.outcome, attempt.started_ms,
       attempt.elapsed_ms, attempt.observed_elapsed_ns, attempt.output_tokens
FROM fastest_intake.serving_capture_run AS run
LEFT JOIN fastest_intake.serving_capture_attempt AS attempt USING (capture_sha256)
ORDER BY run.window_started_at, run.capture_sha256, attempt.request_number, attempt.user_slot;
```

`elapsed_ms` is the collector's original reported latency, capped at the client deadline for timeouts. `observed_elapsed_ns` is the monotonic difference recorded in the trace. The receipt counts accepted output tokens only for accepted requests. The private attempt table also preserves reported token counts from rejected responses.

## Import a private GPU scaling capture

Run from `production` with `FASTEST_DATABASE_URL` set to the intake operator database.

```sh
python3 -B -m fastest_intake migrate
python3 -B -m fastest_intake ingest-scaling-capture /path/to/private-scaling-pair
python3 -B -m fastest_intake stats
```

Pass the unedited directory from the [scaling collector](../fastest_release/SCALING-EVIDENCE.md#capture-a-pair).
The importer checks the pinned artifact, runtime and benchmark controls, verifies the build evidence
and the inventory and runner output digests, and reconciles both attempts with the recorded GPU masks,
placement, process status, and original runner timing row. Keep the packet in restricted storage.
PostgreSQL keeps the selected host, protocol, device and placement metadata, file digests, and
ordered `bigint[]` nanoseconds. Keep raw build evidence, full runner logs, local paths, environment
values and original trace bytes in the packet for the operator to inspect.

The receipt identifies the capture by the SHA-256 of `capture.json`. Replay preserves the existing
capture and attempts. Conflicting evidence for an already imported capture or attempt is rejected.
Finalized failed or interrupted captures retain any verifiable attempt receipts. An unreferenced
successful runner result stays `unavailable`. Inspect each attempt's `outcome` alongside its
`samples_ns` array. A failed attempt can report durations if a valid timing row survived the failure.
An empty array means there was no valid full timing row.

If a sealed [transport attachment](../fastest_release/SCALING-EVIDENCE.md#attach-an-independently-recorded-transfer-trace)
is available, ingest checks its digests and links against the comparison run and retains the
structured links, attachment timestamp, and exact receipt and file digests. A capture without an
attachment starts with transport `unknown`. Replay the same capture after attaching a trace to
retain that evidence, after which the receipt reports `supplied`. Keep the attached trace available
for operator review.

Every import stays held for review. A complete collector attempt describes timing availability.
The operator still reviews the build and physical host provenance, run isolation, accepted quality,
transport and field-level rights through the existing [scaling release workflow](../fastest_release/SCALING-EVIDENCE.md#review-and-release).

```sql
SELECT run.capture_sha256, run.capture_status, run.review_status, attempt.role,
       attempt.outcome, attempt.samples_ns, transport.receipt_sha256 AS transport_receipt_sha256,
       transport.links
FROM fastest_intake.scaling_capture_run AS run
LEFT JOIN fastest_intake.scaling_capture_attempt AS attempt USING (capture_sha256)
LEFT JOIN fastest_intake.scaling_capture_transport AS transport
    ON transport.comparison_run_id = attempt.run_id
ORDER BY run.capture_sha256, attempt.role;
```

## Import private fixed-token text timing

Run from `production` with `FASTEST_DATABASE_URL` set to the intake operator database.

```sh
python3 -B -m fastest_intake migrate
python3 -B -m fastest_intake ingest-text-capture /path/to/private/fixed-token-run
python3 -B -m fastest_intake stats
```

Pass the directory from the [fixed-token collector](../fastest_text/README.md#run-the-fixed-token-protocol).
The importer checks the pinned protocol and shard claims, verifies the build evidence and runner file
digests, and reconciles the phase and repetition outcomes with the invocation, JSONL, and logged
accelerator placement. Replay preserves the same run and attempts. Both phase rows remain visible
in finalized blocked and interrupted captures. A phase that was never entered has outcome
`not-run`. A subsection without a verifiable phase outcome has status `unavailable`. An observed
failed, timed-out, interrupted, or unmeasured repetition has an outcome and a null `elapsed_ns`.

The original ambient-load M4 packet uses its earlier `sources.sha256` inventory. To import that
packet, use `python3 -B -m fastest_intake ingest-text-ambient-m4 /path/to/private/ambient-m4-run`.
The importer checks the sealed benchmark events, pinned build and model checksums, and the two
runner logs. It identifies this evidence as ambient desktop load and records the quiet-host
attestation as false.

PostgreSQL retains exact provenance, observed placement, SHA-256 digests, and integer nanoseconds.
Keep the original packet, build evidence, raw logs, command lines, environment values, and
completion content in restricted storage. Client latency remains missing under the fixed-token
protocol. Imported runs stay held for review and Chinese-task quality stays unreviewed. Follow
the [text-pilot review workflow](../fastest_text/README.md#review-and-ingest-runner-evidence)
for the public two-machine comparison.

```sql
SELECT run.capture_sha256, run.cell_id, run.capture_status, run.review_status,
       phase.phase, phase.outcome, phase.placement,
       attempt.attempt_number, attempt.outcome, attempt.elapsed_ns
FROM fastest_intake.text_capture_run AS run
JOIN fastest_intake.text_capture_phase AS phase USING (capture_sha256)
LEFT JOIN fastest_intake.text_capture_attempt AS attempt USING (capture_sha256, phase)
ORDER BY run.started_at, run.capture_sha256, phase.phase, attempt.attempt_number;
```
