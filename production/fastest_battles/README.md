# Comparison popularity

The Pages endpoint ranks up to ten GPU or machine pairs for the active PostgreSQL-backed catalog release. A ranking covers the current UTC date and the 29 previous UTC dates. Counts are sorted from highest to lowest, with ties ordered by the two canonical hardware IDs. Each accepted opt-in counts once, regardless of selection order or a retry. Counts measure submitted comparisons.

## Provision PostgreSQL and Hyperdrive

Apply the migration in the database holding the catalog snapshot published by the Pages deployment. Set `FASTEST_BATTLES_MIGRATION_DATABASE_URL` to an operator connection that can own the popularity schema, read the catalog tables and reference `fastest_catalog.snapshot`. The snapshot and hardware catalog schema must already exist.

```sh
psql -Xw -v ON_ERROR_STOP=1 "$FASTEST_BATTLES_MIGRATION_DATABASE_URL" -f production/fastest_battles/schema.sql
```

Provision a dedicated login named `battles_pages` through the database operator. Run these grants as the migration owner, and set the role options as the operator.

```sql
ALTER ROLE battles_pages SET log_parameter_max_length = 0;
ALTER ROLE battles_pages SET log_parameter_max_length_on_error = 0;
ALTER ROLE battles_pages SET lock_timeout = '3s';
ALTER ROLE battles_pages SET statement_timeout = '5s';
GRANT USAGE ON SCHEMA fastest_battles TO battles_pages;
GRANT EXECUTE ON FUNCTION fastest_battles.rank_comparisons(text, text),
    fastest_battles.record_comparison(text, text, text, text, uuid) TO battles_pages;
```

Create a Hyperdrive configuration for that login with query caching disabled. Bind it as `BATTLES_PG` in Cloudflare Pages and redeploy with Node.js compatibility. Give preview deployments their own database, catalog snapshot and login. Use the exact snapshot ID carried by the deployment manifest. [Pages Hyperdrive bindings](https://developers.cloudflare.com/pages/functions/bindings/#hyperdrive-configs) · [Hyperdrive query caching](https://developers.cloudflare.com/hyperdrive/concepts/query-caching/#disable-caching)

The endpoint returns `503` when its storage is unavailable. A catalog built from static fixtures has no PostgreSQL snapshot pin. A release quarantined in the deployment's evidence policy returns `410`. The comparison itself works without popularity storage.

## API and retained data

- `GET /api/battle-popularity?release=v1-<pin16>&kind=cards` returns `{"pairs":[{"left":"id-a","right":"id-b","count":1}]}`. A valid release with no submissions returns `{"pairs":[]}`. The other supported kind is `machines`.
- `POST /api/battle-popularity` requires the same-origin `Origin` header and JSON with `release`, `kind`, `left`, `right` and a random v4 `requestId`. Reuse the same ID when retrying. An accepted comparison returns `201` and `{"recorded":true}`. An identical retry returns `200`. Reusing an ID with a different accepted selection returns `409`.

PostgreSQL retains per-date counts by exact snapshot, kind and unordered pair. It retains each random request UUID and a digest of the exact selection for deduplication. The endpoint stores no account, cookie, IP address or client identifier. The Pages role accesses only the two stored functions. The owner may delete expired daily totals without affecting deduplication.

```sql
DELETE FROM fastest_battles.daily_comparison
WHERE recorded_on < (now() AT TIME ZONE 'UTC')::date - 29;
```

## Hosted integration test

Apply `opendesign/mockups/llm-observatory/catalog-pg.sql` and this schema to a disposable database and grant the restricted test login. From `opendesign/mockups/llm-observatory`, point `FASTEST_TEST_DATABASE_URL` to the disposable catalog owner and `FASTEST_TEST_BATTLES_DATABASE_URL` to the restricted test login. Run `node --test battle-popularity.test.mjs` to exercise the Pages endpoint with local Wrangler and PostgreSQL. The test imports two snapshots and sets fixtures to check the reporting window.
