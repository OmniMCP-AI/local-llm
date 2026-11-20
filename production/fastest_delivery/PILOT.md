# Seven-day distribution pilot

Use seven consecutive Asia/Shanghai dates. Keep one trusted record of the scheduled slots and actual outcomes, including runner errors and no-story days. Retain the [editorial draft files](../fastest_editorial/README.md), the [X and YouTube Shorts approvals and handoffs](README.md), and the operator-verified post receipts. Keep the original handoff ZIPs with the receipts so the audit can verify the approved text, assets, and claim references.

For a partial failure, keep the observed channel error and the receipt for its successful counterpart. For replay, keep the retry log showing that the delivery command returned the original receipt. With an approved drill release, keep evidence that withdrawal blocked a queued export and retain the Shorts correction task for a published post tied to that release. Reconcile live corrections through the authorized operator using the delivery guide.

## Run the audit

Run from `production/` with Python 3.11 or later. Set `PILOT_START` to the first editorial date and `OPERATOR_LOG` to the file described below.

```sh
python3 -m fastest_delivery.pilot \
  --start "$PILOT_START" \
  --operator-log "$OPERATOR_LOG" > distribution-audit.json
```

The default input directories are `./editorial-drafts`, `./x-approvals`, `./x-deliveries`, `./shorts-approvals`, and `./shorts-deliveries`. Override them with `--draft-dir`, `--x-approvals`, `--x-deliveries`, `--shorts-approvals`, and `--shorts-deliveries`. The audit reads local records. Omit `--operator-log` to see what is already retained and which inputs are still due.

The report lists seven dates, drafts or no-story reasons, scheduled run outcomes, exact claim and evidence references, and each linked approval, delivery receipt and correction. A verified receipt counts toward the pilot only if its publication time falls within both its approved window and the seven Shanghai dates. The report identifies earlier approvals superseded by a retained handoff. An exported package awaiting reconciliation has its own status.

Check `status` and `gaps` in the JSON. A report with missing evidence exits successfully with `status: incomplete` so an operator can inspect the gaps. Invalid or mismatched evidence exits with a nonzero status. Completion requires reported schedules on all seven dates, a publication on each pilot channel, the three exercises, review time evidence, both observed engagement metrics, and assessments of every outstanding channel. A rehearsal report stays incomplete for the live pilot.

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
| `runs` | One entry per scheduled slot. Include `scheduled_at` with a UTC offset and `reference`. Add the resulting `draft_revision` for a story or no-story decision, or `error` for a failed run. Multiple distinct slots on the same date are allowed. The audit checks coverage by date. The operator checks the entries against the scheduler log. |
| `reviews` | One entry per distinct review session, with elapsed `minutes` as a nonnegative integer, `reference`, and either the reviewed `approval_id` or the `draft_revision` for a draft-only review. Include approval-specific time for each published package. |
| `metrics` | Optional entries named `qualified_evidence_visits` and `completed_comparisons`, each with a nonnegative integer `count` and a query or export `reference` for the pilot dates. Use first-party observations attributable to the pilot posts. Count a qualified visit when the visit reaches the pinned evidence. Count a completed comparison when that workflow reaches its result. Include an observed zero only when the source supports it. Missing entries appear as `null`. |
| `readiness` | One entry per outstanding channel. Use `tiktok`, `bilibili`, `weibo`, `wechat-official-account`, and `wechat-channels`. Each entry contains `access` (`available`, `unavailable`, or `unknown`), `readiness` (`ready`, `blocked`, or `unknown`), and `reference`. Check authorized account access, the required format, rights, and the delivery handoff. The report lists available, ready channels as expansion candidates. |

Each `exercises` entry includes `kind`, `occurred_at` with a UTC offset, and the `reference` to the exercise log. The additional fields depend on the exercise.

| Kind | Additional fields |
| --- | --- |
| `partial_failure` | `successful_approval_id` tied to a published receipt, `failed_channel` (`x` or `youtube-shorts`), and the observed `failure`. |
| `replay` | `approval_id` and the original `receipt_id` returned by the retry. |
| `withdrawal` | `queued_approval_id` for the blocked delivery and `correction_id` from the retained `correction.json` for the same release. |

The local fixture test exercises the audit and both handoffs with an isolated release fixture. Run it from `production/` with Pillow and FFmpeg installed.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_distribution_pilot.py -v
```
