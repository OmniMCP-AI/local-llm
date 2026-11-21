# Public GitHub issue intake

The operator receiver records benchmark requests and result corrections from the public `OmniMCP-AI/local-llm` repository. It recognizes the `[Benchmark request]` and `[Result correction]` title prefixes used by the issue forms and keeps the initial category on later edits. Leave the prefix on an issue until its first delivery has been recorded. A title prefix is a triage category and grants no editorial approval.

## Run the operator receiver

Run from `production/` with Python 3.11 or later and `psql` on the path. Set `FASTEST_GITHUB_INTAKE_DATABASE_URL` to the operator PostgreSQL connection and apply the schema with a migration login.

```sh
python3 -B -m fastest_github_intake migrate
```

The receiver login can use these privileges. Keep the release origin's login separate.

```sql
GRANT USAGE ON SCHEMA fastest_github_intake TO intake_webhook;
GRANT SELECT, INSERT, UPDATE (status, revision) ON fastest_github_intake.issue TO intake_webhook;
```

With the receiver connection and `FASTEST_GITHUB_WEBHOOK_SECRET` set through the operator's secret configuration, start the listener.

```sh
python3 -B -m fastest_github_intake serve
```

It listens on `127.0.0.1:8081`. Put the webhook URL behind an operator-controlled HTTPS proxy with a 1 MiB request limit. Forward only `POST /webhooks/github/issues` with the original JSON bytes, one `Content-Length`, `X-GitHub-Event` and `X-Hub-Signature-256`. Configure a repository webhook for **Issues**, select `application/json` and set the same secret. Disable request body and signature logging at the proxy. GitHub documents signature verification and delivery recovery. [Validating webhook deliveries](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries) · [Redelivering failed webhooks](https://docs.github.com/en/webhooks/testing-and-troubleshooting-webhooks/redelivering-failed-webhook-deliveries)

## Triage issues

```sql
SELECT url, kind, status, revision
FROM fastest_github_intake.issue
ORDER BY revision DESC, issue_number DESC;
```

GitHub's `issue.updated_at` orders snapshots for each repository and stable issue ID. The receiver keeps one row per issue. Repeated and late issue updates leave the row unchanged. A closed snapshot takes precedence over an open snapshot with the same second of timestamp precision. A newer reopened snapshot sets the status back to open. A deletion is terminal for that issue ID and retains the highest observed revision.

The row contains the repository, GitHub issue ID and number, category, status, revision and a canonical GitHub URL derived from that identity. The receiver forwards no issue text, user details, private receipts or submitted URLs. A valid delivery returns 204 after the write, or when there is nothing to record. A database failure returns 503 so the operator can redeliver it. Use the canonical URL as `intake.issue` in a [separate correction review](../../README.md#review-a-correction-or-rights-withdrawal). Evidence and rights review still govern publication.
