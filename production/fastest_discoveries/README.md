# Discovery intake

Editors can record opt-in forum, social, and video leads and queue the
reviewed YouTube metadata snapshot. Exports contain approved source links
and fixed withholding reasons. PostgreSQL retains discoveries, review
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
GRANT EXECUTE ON FUNCTION fastest_discoveries.intake_youtube_metadata(text, jsonb)
    TO discoveries_editor;
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

## Queue reviewed YouTube metadata

Apply the PostgreSQL schema with the owner connection, including on an existing
installation, and grant the metadata intake function to the editor before
running the intake. From `production/`, run the following with the editor login.

```sh
FASTEST_DISCOVERIES_DATABASE_URL='service=discoveries-editor' \
  python3 -B -m fastest_discoveries intake-youtube-metadata \
  ../opendesign/mockups/llm-observatory/battle-title-sample.json
```

The command accepts the exact [reviewed title sample](../../opendesign/mockups/llm-observatory/battle-title-sample.json)
observed on 2026-11-21. It verifies the sample against SHA-256
`e0de59de5686414466374d3a68c0e05d957c085ee2a935e01e4c46574eb01842`
before writing. A modified snapshot requires a new review and digest.
The intake uses only video IDs from the local file, including the three
videos excluded from title-based matchup rankings. All 12 identities are
eligible for discovery. X and Reddit intake requires separate source
authorization and operator support.

Expect `{"discoveries": 12}` on the first run and on an exact retry. The private
queue shows each canonical YouTube watch URL with `published_at: null`,
`consent: null`, and the `youtube_metadata_discovery_only_v1` policy alongside
the sample path, digest, and per-video locator. The observation date describes
the sample. The sample provides no publication times.

On an empty database, the public export shows 12 `discovery_only` reasons
after intake. The operator can record a deletion through `withdraw`.
A `source_deleted` withdrawal appears as a fixed withholding reason, including
after replay. Source URLs and metadata provenance stay in the private queue.

If a creator opts in for the same canonical permalink, use `submit` with a
verified grant. The queue retains both the metadata provenance and the grant.
An eligible opt-in needs an explicit review to appear in the public export.
Existing decisions and withdrawals continue to apply, regardless of when the
metadata is queued.
For the separate opt-in fixture replay, the public export still contains the
reviewed original and the fixed cross-post, deletion and discovery-only reasons.

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
