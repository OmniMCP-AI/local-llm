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

Review rights, exact identity, methodology, and current offer status before preparing a release. The public pricing and benchmark endpoints read their existing reviewed stores.

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
