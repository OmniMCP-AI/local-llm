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

The input JSON has `checked_at`, `note`, `sources`, `prices` and `evaluations`, with an optional `tariffs` array. Run `migrate` before ingesting with the updated CLI. See the schema for typed columns. The content hash identifies the batch and replay is idempotent. Earlier bundles keep their original hash when replayed as supplied. Keep capture bundles under the ignored intake directory.

Use one tariff row for each quoted rate component. Each row identifies the provider, exact offering, tariff revision, market, region, currency, amount, billing unit and component, source and locator. Use a decimal string for the amount. Electricity accepts `kwh` and `month`. Rental accepts `instance_hour` and `month`. API accepts `million_input_tokens`, `million_cached_input_tokens`, `million_output_tokens` and `month`. Record the published start date as `effective_from` and the exclusive end date as `effective_until` when known. The batch's `checked_at` records capture time. Use `qualification` for time bands, account eligibility, billing terms and exclusions.

Every tariff candidate must reference a `captured` source probe in the same bundle. Use a `no_quote` probe by itself when the source provides no applicable rate. With an intake operator connection, join `fastest_intake.tariff_candidate`, `fastest_intake.source_probe` and `fastest_intake.batch` on batch and source to inspect the terms, cited URL and check time. Tariffs enter public cost calculations through the existing publication review. [Cost operator guide](../fastest_cost/README.md#configure-reviewed-evidence)

Review rights, exact identity, methodology, and current offer status before preparing a release. The public pricing and benchmark endpoints read their existing reviewed stores.

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
