# llama.cpp release watch

Refresh one official GitHub releases page into PostgreSQL. Use the
review report to see the last successful refresh, upstream edits and superseded
releases, and authored notes for exact card configurations.

## Run a fixture replay

Run from `production/` with Python 3.11 or later. The supplied fixture contains
synthetic releases and a sample suggested technique. The explicit `--db PATH`
option also opens existing SQLite histories.

```sh
python3 -B -m fastest_release_watch --db watch-demo.sqlite3 refresh \
  --fixture fixtures/release-watch/releases.json --observed-at 2026-11-20T01:00:00Z
python3 -B -m fastest_release_watch --db watch-demo.sqlite3 report \
  --notes fixtures/release-watch/applicability.json --as-of 2026-11-20T01:00:00Z --format html
```

The reporter writes to standard output. Select `html`, `markdown`, or `json`.
Save or publish those public review views through the project's normal
publishing process. `--as-of` sets the freshness check clock.

## Refresh the live feed in PostgreSQL

Run from `production/` with `psql` on your path. Point `FASTEST_DATABASE_URL` at
the project PostgreSQL database using a libpq connection string or configured
service. The initial migration needs permission to create the watcher schema.
Refreshes need write access to that schema.

```sh
export FASTEST_DATABASE_URL='service=fastest-publisher'
python3 -B -m fastest_release_watch --postgres migrate
python3 -B -m fastest_release_watch --postgres refresh
python3 -B -m fastest_release_watch --postgres report
```

The migration creates the `fastest_release_watch` schema. Reports can use a
read-only login with `USAGE` on the schema and `SELECT` on `source_status` and
`release_revision`. Use separate databases for PostgreSQL fixture replays and
live refreshes.

The source allowlist contains the public [llama.cpp GitHub releases
endpoint](https://api.github.com/repos/ggml-org/llama.cpp/releases?per_page=10&page=1).
GitHub permits unauthenticated access to published releases. Use the optional
`FASTEST_RELEASE_WATCH_GITHUB_TOKEN` environment variable for a least-privilege
token with Contents read access when required by your environment. GitHub
applies [rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api).
The adapter uses one HTTPS GET, up to ten releases and 4 MiB, with an
eight-second socket timeout and a body read deadline. An hourly schedule uses
one request per hour. A failed request stops that refresh. For a quota
error, wait until the reset or retry time before running it again. [GitHub
list releases documentation](https://docs.github.com/en/rest/releases/releases#list-releases)

The receipt takes the observation time from the start of the request. Reports
show the last attempt, any latest error, and the last successful refresh. A
success older than 24 hours is stale. Late replay cannot advance the success
timestamp or re-promote a previously recorded revision. The bounded feed window
covers releases observed by the watcher. Older releases already observed remain
in the database as they fall out of the page.

Each retained revision is keyed by repository, release ID and a digest of
selected release fields. Changes to the tag, notes, release properties or
selected asset metadata can produce a new revision. Download counters are
excluded. The database keeps normalized release metadata, digests and source
links. It discards upstream body text, author information, binary assets and
credentials. Current means latest observed stable release by publication time.
Prereleases, superseded releases and previous edits have distinct statuses.
Historical source links open the upstream release, whose visible text can
change after the watcher captured its revision digest.

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

## Test

The PostgreSQL cases use the PostgreSQL command-line tools and a temporary
Unix-socket cluster.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_release_watch.py -v
```
