# Hosted feedback

The Pages endpoint writes private feedback to PostgreSQL and returns a receipt after the insert commits. A retry with the same request ID and content returns the original receipt. The request can include opt-in page, entity and release context. The status endpoint returns the review status and a public evidence update, when published.

## Deploy the binding

Apply the schema with the PostgreSQL feedback owner. Use separate databases and logins for production and preview.

```sh
psql -Xw -v ON_ERROR_STOP=1 "$FASTEST_FEEDBACK_DATABASE_URL" -f production/fastest_feedback/schema.sql
```

Provision a dedicated login named `feedback_pages` through the database operator and grant it these privileges.

```sql
ALTER ROLE feedback_pages SET log_parameter_max_length = 0;
ALTER ROLE feedback_pages SET log_parameter_max_length_on_error = 0;
GRANT USAGE ON SCHEMA fastest_feedback TO feedback_pages;
GRANT EXECUTE ON FUNCTION fastest_feedback.submit_feedback(uuid, text, text, jsonb),
    fastest_feedback.read_feedback_receipt(uuid) TO feedback_pages;
```

Create a Hyperdrive configuration using that login with query caching disabled. Add it to the Pages project as `FEEDBACK_PG` and use the project's documented Functions compatibility date, which enables Node.js compatibility. Redeploy after adding the binding. The endpoint returns a retryable error if storage is unavailable, and the dialog keeps the draft. [Pages Hyperdrive bindings](https://developers.cloudflare.com/pages/functions/bindings/#hyperdrive-configs) · [Hyperdrive query caching](https://developers.cloudflare.com/hyperdrive/concepts/query-caching/#disable-caching)

Keep the Pages login distinct from the release reader and the feedback owner. Treat receipt URLs as private links. Redact receipt query strings wherever access logs are retained and leave PostgreSQL query parameter logging disabled for the Pages login. The endpoint returns generic storage errors to callers. [Pages Functions logging](https://developers.cloudflare.com/pages/functions/debugging-and-logging/)

## Link a public resolution

The feedback owner can read the opted-in context using `context_json::text` from `fastest_feedback.feedback_submission`. Put the receipt ID, category, status and that context string into the private review request. Once the staged resolution is live and verified, apply the private report's `receiptUpdate` to the original feedback database. Run this from the prototype directory.

```sh
node -e 'process.stdout.write(require("./review-output/review.json").receiptUpdate ?? "")' \
  | psql -Xw -v ON_ERROR_STOP=1 "$FASTEST_FEEDBACK_DATABASE_URL"
```

The update returns `linked = true` when the stored correction matches the receipt and context. It marks the receipt reviewed and links the approved wiki path in one transaction. A separate review operator can be granted `USAGE` on this schema and `EXECUTE` on `fastest_feedback.link_feedback_resolution(uuid, jsonb, text)`.

## Verify locally

Apply the schema and grant the Pages role in an isolated PostgreSQL test database. From `opendesign/mockups/llm-observatory`, set `FASTEST_TEST_DATABASE_URL` to the test owner connection and `FASTEST_TEST_FEEDBACK_DATABASE_URL` to the restricted test role connection. Run the hosted Wrangler test with `node --test feedback.test.mjs`.

The previous [D1 schema](../../opendesign/mockups/llm-observatory/feedback-schema.sql) remains available for disposable legacy previews. Set the `FEEDBACK_DB` binding and `FEEDBACK_STORAGE=legacy-d1` for a preview that needs it. If `FEEDBACK_PG` is present, all feedback reads and writes use it.

## Migrate existing D1 receipts

Pause submissions and editor updates for the old deployment before export. Export the two D1 tables to private CSV files with headers and unquoted empty fields for SQL NULL. Preserve the receipt and request IDs and copy the tables in order in one PostgreSQL transaction.

```sql
BEGIN;
SET LOCAL TIME ZONE 'UTC';
\copy fastest_feedback.feedback_submission (id, request_id, category, message, context_json, created_at, status) FROM 'feedback_submission.csv' WITH (FORMAT csv, HEADER true)
\copy fastest_feedback.feedback_resolution (receipt_id, public_path) FROM 'feedback_resolution.csv' WITH (FORMAT csv, HEADER true)
UPDATE fastest_feedback.feedback_submission AS submission SET status = 'reviewed'
WHERE EXISTS (SELECT FROM fastest_feedback.feedback_resolution WHERE receipt_id = submission.id);
COMMIT;
```

Reconcile the row counts and verify an existing receipt link after switching Pages to `FEEDBACK_PG`. Remove the legacy binding after the cutover and handle the private export according to the feedback retention policy.
