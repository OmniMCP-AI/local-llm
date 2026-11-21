# Seven-day distribution pilot

Use seven consecutive Asia/Shanghai dates. Keep one trusted record of the scheduled slots and actual outcomes, including runner errors and no-story days. Retain the [editorial draft files](../fastest_editorial/README.md), the [X and YouTube Shorts approvals and handoffs](README.md), and the operator-verified post receipts. Keep the original handoff ZIPs with the receipts so the audit can verify the approved text, assets, and claim references.

For a partial failure, keep the observed channel error and the receipt for its successful counterpart. For replay, keep the retry log showing that the delivery command returned the original receipt. With an approved drill release, keep evidence that withdrawal blocked a queued export and retain the Shorts correction task for a published post tied to that release. Reconcile live corrections through the authorized operator using the delivery guide.

## Run a scheduled editorial slot

Configure GrokBot or an equivalent scheduler on a Unix host for the Asia/Shanghai timezone. Give it the read-only `FASTEST_EDITORIAL_DATABASE_URL` described in the [editorial guide](../fastest_editorial/README.md). Use one private, persistent pilot directory with write access restricted to the scheduler and authorized operators. Run from `production/` and pass the scheduler's planned timestamp, including its UTC offset, as `SCHEDULED_AT`.

```sh
umask 077
python3 -m fastest_delivery.run_slot \
  --scheduled-at "$SCHEDULED_AT" --mode live \
  --public-origin "$PUBLIC_ORIGIN" --locale en \
  --draft-dir "$PILOT_ROOT/editorial-drafts" \
  --run-dir "$PILOT_ROOT/scheduler"
```

The command prints the absolute path of the retained slot record. A story or no-story decision exits successfully and records its exact `draft_revision`. The draft is under `editorial-drafts/<editorial-date>/<draft_revision>.json`. Use that file for review. A failed attempt exits with code 1 and records the error and attempt times. Keep the slot records and any corresponding external scheduler logs with the pilot evidence.

Configure at most one retry with the original `SCHEDULED_AT` and the same pilot paths, locale and origin. Equivalent UTC offsets identify the same slot. A replay after success returns the same decision. If writing the draft is interrupted, the retry can recover the selected draft even after the current release changes. After two failed attempts, the slot retains the error. An interrupted slot with no recorded outcome remains due in the audit until it is reconciled. Review and delivery continue to check the pinned evidence before use.

A new live slot must already be due on the current Asia/Shanghai date. Use `--mode rehearsal` with separate storage for tests or historical fixture dates. The scheduler command only prepares and retains the draft for review.

## Run the audit

Run from `production/` with Python 3.11 or later. Set `PILOT_START` to the first editorial date. Retain the operator log and the first-party engagement export in the private pilot directory.

```sh
python3 -m fastest_delivery.pilot \
  --start "$PILOT_START" \
  --draft-dir "$PILOT_ROOT/editorial-drafts" \
  --run-dir "$PILOT_ROOT/scheduler" \
  --operator-log "$OPERATOR_LOG" \
  --engagement-export "$ENGAGEMENT_EXPORT" > distribution-audit.json
```

The default input directories are `./editorial-drafts`, `./x-approvals`, `./x-deliveries`, `./shorts-approvals`, and `./shorts-deliveries`. Override them with `--draft-dir`, `--x-approvals`, `--x-deliveries`, `--shorts-approvals`, and `--shorts-deliveries`. The audit reads local records. Omit `--operator-log` to see what is already retained and which inputs are still due.

The report lists seven dates, drafts or no-story reasons, scheduled run outcomes, exact claim and evidence references, and each linked approval, delivery receipt and correction. A verified receipt counts toward the pilot only if its publication time falls within both its approved window and the seven Shanghai dates. The report identifies earlier approvals superseded by a retained handoff. An exported package awaiting reconciliation has its own status.

Check `status` and `gaps` in the JSON. A report with missing evidence exits successfully with `status: incomplete` so an operator can inspect the gaps. Invalid or mismatched evidence exits with a nonzero status. Completion requires reported schedules on all seven dates, a publication on each pilot channel, the three exercises, review time evidence, both totals from the first-party engagement export, and assessments of every outstanding channel. A rehearsal report stays incomplete for the live pilot.

## First-party engagement export

Use the release origin for attributed pilot packages. The first-party link serves the approved, release-pinned benchmark and its citation. It can display the evidence while the operator reconciles the post or when collection is unavailable. It offers anonymous activity sharing only after the link is bound to that post's verified receipt.

### Enable collection

Use a separate libpq service for engagement than for the release reader. Keep the connection settings in a private `PGSERVICEFILE` and the password in `PGPASSFILE`. Use verified TLS for remote PostgreSQL. On the private operator host, select the schema-owner service and run from `production/`.

```sh
FASTEST_PILOT_ENGAGEMENT_DBSERVICE="$ENGAGEMENT_OWNER_SERVICE" \
  python3 -m fastest_delivery.engagement_capture migrate
```

As the schema owner, grant the following privileges to the dedicated origin, binder, and export roles. Substitute your actual role names.

```sql
GRANT USAGE ON SCHEMA fastest_pilot_engagement TO pilot_origin, pilot_binder, pilot_auditor;
GRANT SELECT ON fastest_pilot_engagement.available TO pilot_origin;
GRANT EXECUTE ON FUNCTION fastest_pilot_engagement.arrive(uuid, text, uuid) TO pilot_origin;
GRANT EXECUTE ON FUNCTION fastest_pilot_engagement.complete(uuid, text, uuid, uuid) TO pilot_origin;
GRANT SELECT, INSERT, UPDATE (attribution_key) ON fastest_pilot_engagement.binding TO pilot_binder;
GRANT SELECT ON fastest_pilot_engagement.binding, fastest_pilot_engagement.journey TO pilot_auditor;
```

Give the release origin its `FASTEST_PILOT_ENGAGEMENT_DBSERVICE` name and a private, stable `FASTEST_PILOT_ENGAGEMENT_SIGNING_KEY` of 32 random bytes in lowercase hexadecimal. Generate it with `openssl rand -hex 32` and store it in the hosting secret store. For a container, mount the libpq service and password files read-only and set `PGSERVICEFILE` and `PGPASSFILE` to their mounted paths. Enable the release server with `--pilot-engagement-origin "$PUBLIC_ORIGIN"` and allow that origin's Host header with `--trusted-host`. Use the same lowercase HTTPS origin, without a trailing slash, when generating drafts. Disable proxy and load balancer access logging for `/pilot/evidence/` and keep POST bodies out of request logs, tracing, and analytics.

The comparison uses the existing goals cohort and its current rights checks. Configure the release origin with `--goal-cohort` and `--goal-rights` for two approved measured setups before expecting completed comparison events. Planned and unavailable rows remain visible in the goal results. A pilot comparison counts after the server evaluates the submitted minimum decode and prefill goals and renders results containing at least two comparable reviewed points. One consented evidence journey can contribute one visit and one result. Reloading or retrying its form preserves the original event IDs and timestamps. The public evidence and regular goal comparison remain accessible without participating. The capture stores neither comparison inputs nor visitor cookies.

### Attribute an approved post

1. Generate a unique key for each candidate intended for first-party attribution with `python3 -c 'from uuid import uuid4; print(uuid4())'`. Pass it as `--engagement-key` when preparing the package. Review, approve, and publish the resulting text and assets as usual. Existing packages use their direct citation URLs.
2. After posting, verify the exact link on the exact published post and give the `receipt` command its existing arguments plus `--observed-engagement-url "$APPROVED_LINK"`. Retain the approval, original handoff, and receipt. YouTube Shorts descriptions expose the approved URL as text. Verify how the audience can open it before claiming coverage for that post. [YouTube link placement guide](https://support.google.com/youtube/answer/13748639)
3. Bind the reconciled receipt using the private binder service. The command checks the retained draft, approval and handoff against the receipt. The binding is immutable and the key and post can each be bound once.

```sh
FASTEST_PILOT_ENGAGEMENT_DBSERVICE="$ENGAGEMENT_BINDER_SERVICE" \
  python3 -m fastest_delivery.engagement_capture bind \
  --start "$PILOT_START" --mode live --receipt-id "$RECEIPT_ID" \
  --draft-dir "$PILOT_ROOT/editorial-drafts" \
  --x-approvals "$PILOT_ROOT/x-approvals" --x-deliveries "$PILOT_ROOT/x-deliveries" \
  --shorts-approvals "$PILOT_ROOT/shorts-approvals" --shorts-deliveries "$PILOT_ROOT/shorts-deliveries"
```

Use `--mode rehearsal`, `--pilot-engagement-mode rehearsal`, and a disposable PostgreSQL service, signing key, and operator directory when testing the whole flow. Never route rehearsal traffic to the live database.

### Write the audit input

```sh
FASTEST_PILOT_ENGAGEMENT_DBSERVICE="$ENGAGEMENT_AUDITOR_SERVICE" \
  python3 -m fastest_delivery.engagement_capture export \
  --start "$PILOT_START" --mode live --output "$ENGAGEMENT_EXPORT" \
  --draft-dir "$PILOT_ROOT/editorial-drafts" \
  --x-approvals "$PILOT_ROOT/x-approvals" --x-deliveries "$PILOT_ROOT/x-deliveries" \
  --shorts-approvals "$PILOT_ROOT/shorts-approvals" --shorts-deliveries "$PILOT_ROOT/shorts-deliveries"
```

The private export uses the retained [PostgreSQL projection](engagement-export.sql) and includes only events for exact reconciled posts during the seven Shanghai dates and at or after publication. Pass the file to the existing pilot command using `--engagement-export "$ENGAGEMENT_EXPORT"`.

The exporter leaves coverage empty unless the operator supplies `--coverage-evidence`. The separate JSON file has a `reference` to retained independent evidence and arrays named `qualified_evidence_visits` and `completed_comparisons` in the coverage format below. Supply rows only for closed dates and intervals for which the approved post path, attribution binding, collection and requested comparison workflow were independently verified available. If reconciliation happened after publication, omit that first day whenever the delay leaves any eligible interval unobserved. The collector cannot infer availability from the events it received.

| Event `kind` | Include when | Additional fields |
| --- | --- | --- |
| `evidence_arrival` | A visit reaches the pinned evidence and citation represented by the approved draft's `evidence_destination`. | `visit_id` and the exact `evidence_destination`, including its citation anchor. |
| `comparison_result` | The attributed comparison workflow actually delivers its result. | `comparison_id` for that specific result-producing workflow run. |

For both kinds include `receipt_id`, the exact `post_url` from the receipt, and `occurred_at` with its UTC offset. Use separate random UUIDv4 identifiers scoped to the pilot for visits and comparison runs. Use the same identifier and original occurrence time in repeat exports. A reload of the same visit or comparison result counts once. Equivalent UTC offsets are treated as the same occurrence. Reuse of the same identifier with conflicting attribution or time fails validation. Keep raw log fields, IP addresses, cookie or account identifiers, credentials and comparison inputs out of the export.

Save a single JSON object with these fields.

| Field | Value |
| --- | --- |
| `schema_version` | Integer `1`. |
| `mode` | `live` for an observed pilot or `rehearsal` for a fixture, matching the operator log and scheduler records. |
| `start_date` | The first Shanghai date passed to `--start`. |
| `reference` | A resolvable identifier for the retained first-party query or projection. |
| `coverage` | An object with arrays for `qualified_evidence_visits` and `completed_comparisons`. Each array contains `{"date": "YYYY-MM-DD", "receipt_id": "..."}` for each Shanghai date and exact receipt where that source observed the full eligible period. The eligible period starts at publication on the first day and at midnight on later days. |
| `events` | An array of the first-party observations described above. |

Omit a coverage row when attribution or measurement was unavailable for any part of that eligible period. Keep eligible events that were observed on partially covered dates. An empty event array with full coverage produces an observed zero. If coverage is missing or no eligible receipt exists, the metric is `null`. The `engagement_evidence` result lists coverage and missing receipt-days, the number of unique events in the supplied export, and its path and SHA-256 digest. It keeps event identifiers out of the audit output. Retain the export privately with the report.

## Operator log

Start with this JSON and replace `YYYY-MM-DD` with the actual starting date. Use `live` for an observed pilot and `rehearsal` for a fixture run. Add only observed records. Keep the referenced logs or exports with the report. A `reference` is a meaningful file, log, or query identifier the reviewing team can resolve. Keep account credentials and raw visitor data out of the log.

```json
{
  "schema_version": 1,
  "start_date": "YYYY-MM-DD",
  "mode": "live",
  "runs": [],
  "reviews": [],
  "exercises": [],
  "metrics": {},
  "readiness": {}
}
```

| Field | What to record |
| --- | --- |
| `runs` | One entry per slot that the audit does not already read through `--run-dir`. Include `scheduled_at` with a UTC offset and `reference`. Add the resulting `draft_revision` for a story or no-story decision, or `error` for a failed run. Multiple distinct slots on the same date are allowed. The audit checks coverage by date. The operator checks the entries against the scheduler log. |
| `reviews` | One entry per distinct review session, with elapsed `minutes` as a nonnegative integer, `reference`, and either the reviewed `approval_id` or the `draft_revision` for a draft-only review. Include approval-specific time for each published package. |
| `metrics` | Optional historical entries named `qualified_evidence_visits` and `completed_comparisons`, each with a nonnegative integer `count` and a `reference`. The audit can display these manually recorded values when there is no export. A live audit in that case reports `engagement_evidence_unreported`. If an export is supplied, its totals and missing coverage determine both reported metrics. |
| `readiness` | One entry per outstanding channel. Use `tiktok`, `bilibili`, `weibo`, `wechat-official-account`, and `wechat-channels`. Each entry contains `access` (`available`, `unavailable`, or `unknown`), `readiness` (`ready`, `blocked`, or `unknown`), and `reference`. Check authorized account access, the required format, rights, and the delivery handoff. The report lists available, ready channels as expansion candidates. |

Each `exercises` entry includes `kind`, `occurred_at` with a UTC offset, and the `reference` to the exercise log. The additional fields depend on the exercise.

| Kind | Additional fields |
| --- | --- |
| `partial_failure` | `successful_approval_id` tied to a published receipt, `failed_channel` (`x` or `youtube-shorts`), and the observed `failure`. |
| `replay` | `approval_id` and the original `receipt_id` returned by the retry. |
| `withdrawal` | `queued_approval_id` for the blocked delivery and `correction_id` from the retained `correction.json` for the same release. |

The local fixture test exercises the audit and both handoffs with an isolated release fixture. Run it from `production/` with Pillow, FFmpeg and the local PostgreSQL executables on `PATH`. The engagement test starts and removes its own PostgreSQL cluster.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_distribution_pilot.py -v
```
