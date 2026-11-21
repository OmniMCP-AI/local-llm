# Contributor benchmark intake

Contributors send a scoped JSON result through the operator's private intake
channel. The operator verifies the contributor and records the file. Each
submission gets a shareable receipt with the state of every version and a
pinned evidence link after publication. Share the receipt link privately with
the verified contributor so they can follow decisions and amendments.

Run the commands from `production/` with a database login authorized to write
benchmark releases. Set `FASTEST_DATABASE_URL` to the same database used by the
release service.

```sh
python3 -m fastest_release migrate
python3 -m fastest_contributor migrate
python3 -m fastest_contributor submit submission.json
python3 -m fastest_contributor status RECEIPT_UUID
python3 -m fastest_contributor inspect RECEIPT_UUID 1
python3 -m fastest_contributor review RECEIPT_UUID 1 review.json
```

`submit` and `review` also accept `-` for standard input. Outputs from
`submit`, `status`, and `review` include a relative `status_url`. Prefix it
with the HTTPS release origin to share a browser link. The existing receipt
UUID works as a private link key and stays the same across amendments. Anyone
with the link can see the version numbers, status, intake issue labels, and
links to published evidence or withdrawal notices. Keep it out of public
issues and shared logs. `inspect` is for operators and includes the original
input, evidence ID, and editorial decision details.

## Serve receipt links

Run the contributor migration as the release schema owner and grant the
release listener's dedicated reader just the receipt lookup function.
The intake tables and review functions stay private.

```sql
GRANT EXECUTE ON FUNCTION fastest_release.read_contributor_receipt(uuid) TO fastest_release_reader;
```

Start the release server with `serve --contributor-receipts`, or pass
`--contributor-receipts` to the release container. The route uses the
release reader connection and returns a no-store, noindex page. The
server log omits the receipt query. Configure the proxy and any request
logging or analytics to omit query strings for `/contributors/receipt`.

## Submission format

Use one UTF-8 JSON object of up to 64 KiB. The fields under `hardware`,
`artifact`, `workload` and `metric` use the same shapes as the
[synthetic benchmark example](../fixtures/synthetic-observation.json).
Use the other fields below in place of the example's `evidence_id`, `kind`,
`source`, `rights` and `fields`.

| Field | Required values |
| --- | --- |
| `submission_id`, `version` | A contributor-provided UUID retained across amendments, and a positive integer version. Change the version when anything in the submission changes. |
| `authorization` | A private `contributor_id`, a `consent` boolean, `scope`, and a private `reference` to the claimed grant. For publication, consent must be true and scope must be `public-release`. Optional `expires_at` is a UTC timestamp with seconds, such as `2027-01-01T00:00:00Z`. |
| `hardware`, `artifact`, `workload`, `metric` | The exact machine revision and configuration, model revision and SHA-256, workload version, and a versioned metric. Keep the original value as a decimal string. The unit, statistic and measurement boundary must match the release service's registered definition. |
| `conditions` | `runtime_revision`, `runtime_sha256`, `os_driver`, and `settings`. Include the effective test settings such as active devices, context, batch size and warm-up when applicable. |
| `source` | `label`, `locator`, `revision`, and `sha256`. Use an HTTPS link to the exact result, with a fragment when the document contains multiple results. Use a citation free of credentials and query parameters. The digest identifies the cited source bytes. |

A receipt starts as `pending_review` when the record passes intake checks.
Missing or ambiguous identities, conditions, units, locators, or reuse scope
yield `quarantined` and shareable issue codes. A contributor can send an
amendment with the same submission and contributor IDs and a higher version.
Retry the original file byte for byte to replay that import. A changed file
with the same version returns a conflict and leaves the retained version intact.

## Editorial decision

Inspect the exact version and verify the grant, digest, citation and benchmark
conditions against the source. Authorize the machine, workload, values,
conditions and citation together before choosing `publish`. The intake
records and checks the submitted metadata without fetching linked resources.

```json
{
  "decision_id": "d4802ee6-20aa-4612-b344-6af48ea348bd",
  "editor_id": "editor-account",
  "outcome": "publish",
  "reason": "Reviewed the source result and confirmed its publication scope.",
  "authorization_reference": "private-grant-record"
}
```

Use a new decision UUID for each version. To decline a version, use
`outcome: "reject"` and set `authorization_reference` to null when no grant
was found. Only the latest submitted version can be newly published.
Submitting a later version leaves prior releases available according to their
rights. Replaying the same review returns its existing decision.

Approved versions use one evidence ID and a new release ID for each approved
amendment. HTML, Markdown, chart and table data, and the evidence API identify
the result as contributor-reported and show its exclusion from controlled
comparisons. The scope covers that evidence release. For a rights withdrawal,
use the [release withdrawal command](../README.md#publish-correct-and-withdraw).
The receipt then reports the affected releases as withdrawn.

The [integration tests](../tests/test_contributor.py) use synthetic source
records and an isolated database.
