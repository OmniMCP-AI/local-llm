# Discovery intake

Editors can record opt-in forum, social, and video leads, then export approved
source links and withholding reasons. PostgreSQL retains submissions, review
decisions, and withdrawals in the private `fastest_discoveries` schema. Treat
the `queue` output and write receipts as private.

## Configure PostgreSQL

Run from `production/` with Python 3.11+, PostgreSQL 13+, and `psql` on your path.
Apply the schema using the login that owns the discovery schema and its objects.
Grant this migration login `CREATE` on the target database to install the schema.
Keep connection settings and passwords in private libpq service and password
files.

```sh
FASTEST_DISCOVERIES_DATABASE_URL='service=discoveries-owner' \
  python3 -B -m fastest_discoveries migrate
```

Provision a dedicated editor login and a separate export login. With the
schema owner, grant them the corresponding operations.

```sql
GRANT USAGE ON SCHEMA fastest_discoveries TO discoveries_editor, discoveries_reader;
GRANT EXECUTE ON FUNCTION fastest_discoveries.submit(jsonb),
    fastest_discoveries.review(text, text, text, text),
    fastest_discoveries.withdraw(text, text),
    fastest_discoveries.queue_entries() TO discoveries_editor;
GRANT EXECUTE ON FUNCTION fastest_discoveries.public_report()
    TO discoveries_editor, discoveries_reader;
```

Set `FASTEST_DISCOVERIES_DATABASE_URL` to the editor's libpq connection for
`submit`, `review`, `withdraw`, and `queue`. Select the export login to run
`python3 -B -m fastest_discoveries public`. Keep query and error-statement
logging for editor and import connections free of private consent references
and review reasons. Use a separate database for fixture runs.

## Submit an opt-in lead

Start with the [submission fixture](../fixtures/discoveries/original.json).
Use the exact public HTTPS post permalink as `source_url`, the upstream
permalink as `original_url`, and the source's UTC publication time or `null`
when unknown. For an original, set both URLs to the same permalink. For a
repost, use the original's permalink even if the original arrives later. Use a
consistent canonical permalink for each post. Simple post anchors and YouTube
watch permalinks with a single video ID are accepted.

Before submitting, verify the rights holder or authorized representative
opted in, that the URLs identify the intended public posts, and that
`consent.reference` points to the retained grant. Use an opaque reference from
the private consent record. Use `discovery_only` for private editorial
discovery and `public_source_link` when the grant allows an approved public
link and its publication timestamp. The editor-run adapter reads one bounded
local JSON record. Source text, captions, attachments, and credentials are
outside the accepted fields. Automated X and Reddit access requires separate
platform approval and would use a separately authorized adapter.

`submit` retains one candidate per permalink. Exact retries return the
original intake record. `queue` shows the cross-post relationship, consent,
review, and any recorded withdrawal. `review` takes `approve` or `withhold`,
an editor identity, and a private reason. A recorded choice is immutable.
`public` exports approved original links with their publication times and
fixed reasons. A withheld entry contains only its status and a fixed reason.

Use `withdraw` when the source is deleted or redisplay permission is revoked.
It immediately suppresses the link on subsequent exports and retains the
prior review in the private history. Withdrawals take effect even if an
earlier submission is replayed or the withdrawal arrives before intake.
Regenerate or remove any separately distributed copy after a withdrawal.

## Import existing SQLite history

Pause legacy writers and retain the history in its private directory. Apply
the PostgreSQL schema, then run the import with its owner connection.

```sh
FASTEST_DISCOVERIES_DATABASE_URL='service=discoveries-owner' \
  python3 -B -m fastest_discoveries import-sqlite /private/path/history.sqlite3
```

The command reads a consistent snapshot of the three SQLite history tables
and reports their counts. It retains timestamps and prior decisions,
including withdrawals recorded before a submission arrived. Exact
overlapping rows are replayable. A conflicting row rolls back the import as
a whole. Compare the private queue and public export across the two stores
before moving the editor and export jobs to PostgreSQL. Existing SQLite
callers can select their file explicitly with `--db PATH`.

## Replay the fixtures

Point `FASTEST_DISCOVERIES_REPLAY_DATABASE_URL` at the owner connection for a
disposable PostgreSQL database.

```sh
(
  set -eu
  export FASTEST_DISCOVERIES_DATABASE_URL="${FASTEST_DISCOVERIES_REPLAY_DATABASE_URL:?Set a disposable database connection}"
  discoveries() { python3 -B -m fastest_discoveries "$@"; }
  discoveries migrate > /dev/null
  discoveries submit fixtures/discoveries/original.json > /dev/null
  discoveries review https://forum.example/topics/local-models/18 approve \
    --reviewer fixture-editor --reason 'Verified the fixture grant and original post.' > /dev/null
  for fixture in cross-post discovery-only deleted; do
    discoveries submit "fixtures/discoveries/$fixture.json" > /dev/null
  done
  discoveries review https://forum.example/topics/local-models/24 approve \
    --reviewer fixture-editor --reason 'Verified the fixture grant.' > /dev/null
  discoveries withdraw https://forum.example/topics/local-models/24 \
    --reason source_deleted > /dev/null
  discoveries public
)
```

The replay exports one link and the withholding reasons `cross_post`,
`source_deleted`, and `discovery_only`. The CLI tests start and clean up a
disposable PostgreSQL cluster on a local Unix socket. Run them with
`python3 -B -m unittest discover -s tests -p test_discoveries.py -v`.
