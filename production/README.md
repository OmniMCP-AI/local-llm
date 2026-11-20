# Benchmark release service

PostgreSQL stores reviewed observation revisions and the current release pointer. The service publishes one observation per release. Its Markdown page, HTML chart and table, JSON datasets, and SHA-256 manifest use the same approved row. The example is synthetic. Its value demonstrates the pipeline, and its artifact checksum refers to the checked-in fixture bytes.

## Run the example

Use Python 3.11 or later, PostgreSQL 13 or later, and `psql` on your path. From this directory, point the publisher at a writable PostgreSQL database. The connection can use libpq keyword syntax, a service name, or a PostgreSQL URL. Keep passwords in a libpq password file or service configuration.

```sh
export FASTEST_DATABASE_URL='dbname=fastest_release'
python3 -m fastest_release migrate
release_id=$(python3 -m fastest_release publish fixtures/synthetic-observation.json)
python3 -m fastest_release read "$release_id"
python3 -m fastest_release artifact "$release_id" benchmark.md
python3 -m fastest_release serve
```

Open [the current benchmark](http://127.0.0.1:8000/releases/current/benchmark.html). The redirect pins the release ID so the page and its companion links stay on the same revision even if a correction arrives while someone is reading. Each pinned route offers `benchmark.md`, `benchmark.html`, `chart.json`, `table.json`, and `manifest.json`. The store keeps decimal values as PostgreSQL `numeric` and serializes their exact text in the datasets.

The default listener is loopback and accepts the bound address and port as its HTTP Host header. For a deployment behind a proxy, pass the proxy's canonical Host header with `--trusted-host` and use a database login that can execute only the public read function. As schema owner, grant a dedicated login these permissions as needed.

```sql
GRANT USAGE ON SCHEMA fastest_release TO fastest_release_reader;
GRANT EXECUTE ON FUNCTION fastest_release.read_release(uuid) TO fastest_release_reader;
```

## Publish, correct, and withdraw

Publish a reviewed JSON document in the shape of [the example](fixtures/synthetic-observation.json). Provide a stable evidence UUID, hardware revision, exact artifact identity and digest, workload, versioned metric, source locator, and explicit rights decision for the public release. The included metric definition is decode throughput in tok/s. Its version fixes the statistic and measurement boundary. Every optional field has its own allow or deny decision. Use `status: missing` with a reason for an approved field whose value is unknown.

Replaying the exact document returns its existing release ID and leaves the current pointer where it is. For a correction, retain the evidence UUID and publish the amended document with its reviewed source and rights decision. PostgreSQL advances the current pointer in the transaction that records the revision.

For a rights withdrawal, run `python3 -m fastest_release withdraw EVIDENCE_UUID "editorial reason"` using the publisher login. All affected routes, including historical revisions and manifests, return an HTTP 410 withdrawal notice on the next read. The editorial reason is private. Every served response is marked `no-store`. Any separately distributed copies need their own withdrawal handling.

The Python interfaces are `ReleaseStore.migrate()`, `publish(observation)`, `read(release_id=None)`, `artifact(release_id, name)`, and `withdraw(evidence_id, reason)`. `read()` resolves the current pointer and returns the released row or a withdrawal record. Keep the release ID to access the same snapshot in other formats.

## Test locally

These boundary tests start private PostgreSQL clusters on temporary Unix sockets, and the HTTP test opens one loopback listener on an available port. The tests stop the owned processes and remove their temporary clusters after use.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -c -s tests -v
```

## Reconcile the private video research seed

From this directory, use the release database's schema owner to run the import
and capture its seed ID. The ID is a digest of the mapper version, coverage, and
source file hashes. Replaying the same input returns the same ID and leaves each
record stored once. The import checks the retained views against their originals
before writing the snapshot in one transaction.

```sh
export PYTHONDONTWRITEBYTECODE=1
python3 -m fastest_release migrate
python3 -m fastest_release research-import
python3 -m fastest_release research-read SEED_ID
python3 -m fastest_release research-read SEED_ID observation V001-P001
python3 -m fastest_release research-read SEED_ID profile_association V001-P001
```

Use a record kind by itself to list that kind in the snapshot. The kinds are
`profile`, `component`, `legacy_hardware`, `series`, `observation`,
`profile_association`, and `model_reference`. Each source locator points to a
CSV line or JSON record relative to the
[transcript seed](../docs/Local-AI-Comparison-Platform/YouTube-Local-LLM-Transcripts/).
BOM component IDs use the original CSV line number. Inspect a component's
`original.profile_id` for the parent profile. An observation's original metric,
value, unit, timestamp, and conditions stay in `original`. The observation
carries its test series ID and any reported profile ID. The corresponding
association supplies the original qualifying wording. Each partial model
reference keeps the reported video-scoped label and the missing fields.

Native records and partial projections have separate fields. The 16
`HardwareProfile` cores are schema-compatible and all 116 builds are incomplete.
The 127 `BenchmarkEntry` projections remain unverified creator reports. The
research manifest includes the upstream commit and the retained
[llmfit MIT notice](../docs/Local-AI-Comparison-Platform/YouTube-Local-LLM-Transcripts/llmfit/LICENSE.llmfit-MIT.txt).
The importer writes only to the private `fastest_research` schema. Publication
continues through the reviewed observation and rights checks above.

### Verify the pinned llmfit contracts

Run the native regression with Rust and Cargo through rustup, plus `curl` and
`tar`. The verifier downloads the pinned source archive, prints the upstream
input hashes, and uses the upstream Cargo lockfile in a disposable workspace.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 tests/verify_research_llmfit.py --toolchain 1.98.0
```

The tests cover the 16 strict hardware cores, 127 structural benchmarks and
their nested hardware data, and 103 separately retained `HardwareInfo`
projections. The pinned model deserializer reads 19,192 raw catalog records
and the embedded loader returns 18,044 after normalization. The upstream
community loader supplies 546 submissions that pass its Draft 7 schema. The
140 video-scoped model references remain partial and the seed emits zero
native models and zero community submissions.

## Build the two-machine text pilot

The [text pilot](fastest_text/README.md) builds a public report for the planned
Apple M4 and GeForce RTX 4090 cells. It documents the pinned throughput protocol,
Chinese task rubric, machine access blockers and reviewed runner intake.
