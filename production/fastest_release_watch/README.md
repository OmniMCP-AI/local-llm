# Runtime release watch

Refresh official GitHub release pages for llama.cpp, SGLang, vLLM and Ollama
into PostgreSQL. The watch shows the last successful refresh of each feed,
upstream edits, superseded releases and reviewed notes for exact card
configurations.

## Run a fixture replay

Run from `production/` with Python 3.11 or later. The supplied fixture contains
synthetic releases and a sample suggested technique. The explicit `--db PATH`
option also opens existing SQLite histories. Choose a different fixture's
feed with `--source sglang`, `--source vllm` or `--source ollama`.

```sh
python3 -B -m fastest_release_watch --db watch-demo.sqlite3 refresh \
  --fixture fixtures/release-watch/releases.json --observed-at 2026-11-20T01:00:00Z
python3 -B -m fastest_release_watch --db watch-demo.sqlite3 report \
  --notes fixtures/release-watch/applicability.json --as-of 2026-11-20T01:00:00Z --format html
```

The reporter writes to standard output. Select `html`, `markdown`, or `json`.
Use `--as-of` to set the freshness check clock. The release origin serves the
current public view from a live PostgreSQL history. [Serve the watch](#serve-the-watch)

## Refresh the live feeds in PostgreSQL

Run from `production/` with `psql` on your path. Point `FASTEST_DATABASE_URL` at
the project PostgreSQL database using a libpq connection string or configured
service. The initial migration needs permission to create the watcher schema.
Refreshes need write access to that schema.

```sh
export FASTEST_DATABASE_URL='service=fastest-publisher'
python3 -B -m fastest_release_watch --postgres migrate
python3 -B -m fastest_release_watch --postgres refresh --source all
python3 -B -m fastest_release_watch --postgres report
```

The migration creates or upgrades the `fastest_release_watch` schema and
preserves existing runtime release history. Reports can use the same
[read-only grants as the release origin](#serve-the-watch). Use separate
databases for PostgreSQL fixture replays and live refreshes.

Choose a single feed with `--source llama.cpp`, `--source sglang`,
`--source vllm` or `--source ollama`. The original `refresh` command without
`--source` refreshes llama.cpp. The adapter uses these exact endpoints.

- [llama.cpp](https://api.github.com/repos/ggml-org/llama.cpp/releases?per_page=10&page=1)
- [SGLang](https://api.github.com/repos/sgl-project/sglang/releases?per_page=10&page=1)
- [vLLM](https://api.github.com/repos/vllm-project/vllm/releases?per_page=10&page=1)
- [Ollama](https://api.github.com/repos/ollama/ollama/releases?per_page=10&page=1)

GitHub permits unauthenticated access to published releases. Use the optional
`FASTEST_RELEASE_WATCH_GITHUB_TOKEN` environment variable for a least-privilege
token with Contents read access when required by your environment. GitHub
applies [rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api).
Each feed uses one HTTPS GET for up to ten releases and 4 MiB, with an
eight-second socket timeout and a body read deadline. A refresh of all feeds
still attempts each feed when another fails, saves the successful responses,
and exits nonzero if a feed fails. For a quota error, wait until the reset or
retry time before running it again. [GitHub
list releases documentation](https://docs.github.com/en/rest/releases/releases#list-releases)

The receipt takes the observation time from the start of each request. Reports
show the last attempt, any latest error, and the last successful refresh for
each feed. JSON exposes these fields under `sources` keyed by runtime ID.
The original top-level source summary still describes llama.cpp. A
success older than 24 hours is stale. Late replay cannot advance the success
timestamp or re-promote a previously recorded revision. The bounded feed window
covers releases observed by the watcher. Older releases already observed remain
in the database as they fall out of the page.

Each retained revision is keyed by repository, release ID and a digest of
selected release fields. Changes to the tag, notes, release properties or
selected asset metadata can produce a new revision. Download counters are
excluded. The database keeps normalized release metadata, digests and source
links. It discards upstream body text, author information, binary assets and
credentials. Current means the latest observed stable release of each runtime
by publication time.
Prereleases, superseded releases and previous edits have distinct statuses.
Historical source links open the upstream release, whose visible text can
change after the watcher captured its revision digest.

## Serve the watch

Apply the watcher migration as the publisher and refresh the live feeds
separately. Give the release origin's existing reader these additional grants.
The example role is `fastest_reader`.

```sql
GRANT USAGE ON SCHEMA fastest_release_watch TO fastest_reader;
GRANT SELECT ON fastest_release_watch.source_status,
    fastest_release_watch.release_revision TO fastest_reader;
GRANT EXECUTE ON FUNCTION fastest_release_watch.read_applicability(text) TO fastest_reader;
```

The function grant is needed when serving a notes revision. A verified note
also uses the origin's existing `fastest_release.read_release(uuid)` grant.

From `production/`, start the release origin with the reader connection.

```sh
FASTEST_DATABASE_URL='service=fastest-reader' \
  python3 -B -m fastest_release serve --runtime-release-watch
```

The origin index links to the watch and its Markdown and JSON companions at
`/runtime-releases.md` and `/runtime-releases.json`. [Open the local watch](http://127.0.0.1:8000/runtime-releases)

Set `FASTEST_RELEASE_ORIGIN` in the Pages Functions environment to the HTTPS
origin serving the watch. **Catalog → Runtimes** and the matching HTML and
Markdown profiles show the last observed stable release and refresh status
for official feeds with a successful capture. Links on `/wiki/runtimes/`
and `/wiki/runtimes.md` lead to the matching watch format.

For an origin container, append `--runtime-release-watch` to the deployment
command. To include a reviewed PostgreSQL revision, pass its exact digest.

```sh
FASTEST_DATABASE_URL='service=fastest-reader' \
  python3 -B -m fastest_release serve --runtime-release-watch \
    --runtime-release-watch-notes-revision "$NOTES_REVISION"
```

For existing file-backed deployments, mount the approval JSON read-only and
pass `--runtime-release-watch-notes /path/to/reviewed-applicability.json` as the
notes source. The origin reads the configured revision or file and checks the
permissions of cited benchmark releases on each request.
[Deploy the release origin](../README.md#deploy-the-release-origin)

The three views use the same stored release history. An upstream refresh
failure leaves the last successful data and timestamp visible alongside the
latest error. A missing or stale refresh is shown in all three views.
Fixture histories are available through the CLI reporter for review.
An unavailable database, unknown applicability revision or ineligible
configured note yields a 503 in the requested format. Keep the origin's
`Cache-Control: no-store` header through the proxy.

## Add reviewed applicability

Use [the example note](../fixtures/release-watch/applicability.json) as the input
shape. Editorial review clears each note and its public source. Pin the
`revision_id` from a release report and an exact card ID from the
[hardware catalog](../../opendesign/mockups/llm-observatory/catalog-hardware.json).
Record the configuration ID, board variant, OS, driver, backend, runtime commit,
model artifact reference, workload ID and version, and argument list. Record the
technique, prerequisites, limits and failure modes. The watcher attaches notes
only to their specified release revision and card. Its links lead to the source
record, card attribution and the author's full runtime commit.

Use `suggested`, `upstream_documented`, `contributor_reported`,
`unsupported` or `unresolved` to convey evidence status. Release metadata
alone establishes discovery. Editors establish applicability and use the
approved benchmark service to publish measurements.

For `fastest_ai_verified`, add a `retest` object with canonical
`baseline_release_id` and `tuned_release_id` UUIDs for two existing measured
benchmark releases. The PostgreSQL report login also needs access to the
approved release reader. With SQLite watcher history, set `FASTEST_DATABASE_URL`
to the read-only release-service login. For a review document served separately
from its evidence, use `--evidence-origin https://benchmarks.example`. Both
observations must have the same
hardware revision and configuration, exact artifact, workload and metric
contract. Their public fields must include matching `runtime_id`,
`runtime_build`, `card_id`, `configuration_id`, `os_version`,
`driver_version` and `backend`. Provide public `runtime_flags` as a JSON array
encoded as text. The tuned arguments must match the note and differ from the
baseline. The report links the separate baseline and tuned records. The
benchmark service provides their measurements and handles withdrawal. Re-render
or remove distributed review copies after an evidence withdrawal.

### Store the reviewed document in PostgreSQL

From `production/`, use the watcher schema owner login after the migration and
after the cited runtime revisions and benchmark releases are available.

```sh
NOTES_REVISION=$(FASTEST_DATABASE_URL='service=fastest-publisher' \
  python3 -B -m fastest_release_watch --postgres ingest-notes \
    --notes /path/to/reviewed-applicability.json)

FASTEST_DATABASE_URL='service=fastest-reader' \
  python3 -B -m fastest_release_watch --postgres report --notes-revision "$NOTES_REVISION"
```

The import checks the notes, tracked review lines and any matched retests
before writing. It retains the reviewed JSON under the SHA-256 digest of its
UTF-8 JSON with sorted keys and compact separators. Reimporting the same
document with different whitespace or object key order yields the same digest.
Changed contents create another revision. Select its digest explicitly in
reports, reviews and the origin configuration. Reports without a selection
contain only feed history.

## Review a runtime update

To track an exact configuration across releases, add a stable `review_line`
ID to its authored applicability note. Reuse that ID on later decisions for
the same technique and keep the earlier notes. Give each note its own `id`
and pin it to the revision it assesses. The line must match the runtime,
card and all configuration fields except `build_sha`. A change to the driver,
OS, backend, arguments, workload or model artifact needs its own reviewed
history. The build SHA can advance when a reviewer records a new observation.

After refreshing the feed, run this read-only command from `production/` using
the pinned notes and PostgreSQL history.

```sh
FASTEST_DATABASE_URL='service=fastest-reader' \
  python3 -B -m fastest_release_watch --postgres review --notes-revision "$NOTES_REVISION"
```

The CLI also accepts `--notes /path/to/reviewed-applicability.json` for
file-backed reports and reviews.

The JSON shows each tracked line whose runtime's latest revision is newer
than a prior authored note in the same release lane. A note pinned to a stable
release follows stable releases. A note pinned to a prerelease follows
prereleases, including runtimes that publish only prereleases. A later release
or an edit to the latest release in that lane can trigger review. Each row
preserves the prior note's status and exact conditions, and identifies the
target revision, first-seen time, and official source. The `review_id` is
derived from the line, exact conditions and target revision, so replays and
changes to the target's assessment keep the same ID. Retained releases and
authored notes hold the history behind the current view.

A fresh `review_due` row is actionable after a successful refresh. A stale
feed or latest refresh error keeps the row visible and sets `actionable` to
false. A `suggested` or `unresolved` decision keeps review due. A decision on
the exact target records `assessed` or `unsupported` alongside its editorial
status. The `report` command continues to show only the notes explicitly pinned
to each revision. Only approved matched measurements establish a comparison.

## Test

The PostgreSQL cases use the PostgreSQL command-line tools and a temporary
Unix-socket cluster.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_release_watch.py -v
```
