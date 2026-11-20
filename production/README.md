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

## Estimate fit for a selected machine

From this directory, build the native adapter with an installed Rust 1.98.0
toolchain, then pass the executable to the release server. The fit routes can
run on their own. Set `FASTEST_DATABASE_URL` to serve benchmark releases on
the same listener.

```sh
export PYTHONDONTWRITEBYTECODE=1
python3 -m fastest_fit build /tmp/fastest-fit-26450cc
python3 -m fastest_release serve --fit-engine /tmp/fastest-fit-26450cc
```

Open [Estimate model fit](http://127.0.0.1:8000/fit). The form accepts
`?machine=llmfit-nvidia-rtx-4090` to preselect that catalog profile.
Use `GET /fit.json` for JSON. Pass `machine`, the artifact SHA-256 as
`artifact`, `runtime`, `context`, `ram_reserved_gib`, and
`vram_reserved_gib`. Supply `cpu_cores` from the selected configuration
for CPU offload. The result ID hashes the selected inputs, provenance,
calculation settings, and engine revision. The endpoint serves estimates
without recording a benchmark or a successful model run.

The first supported recipe is the upstream RTX 4090 example preset with one
CUDA GPU, the reviewed GGUF catalog files, and llama.cpp. The preset supplies
system RAM and bandwidth assumptions. NVIDIA supplies the 24 GiB GPU size.
The form starts at 4,096 tokens with 8 GiB of system RAM and 2 GiB of VRAM
reserved. Adjust these assumptions for the intended use. The JSON includes
the pinned sources, both available memory pools, runtime release,
quantization, fit level, run mode, context, and nullable speed and latency.
Throughput comes from a model of hardware capability. It can differ greatly
from an actual run.

Partial profiles, missing inputs, and unsupported runtime or format
combinations return a qualification. When the core recommends another
quantization or shortens context, the response gives a separate estimate of
the selected artifact's memory and withholds the exact fit verdict.

Run the fit fixtures when evaluating an upstream upgrade.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m fastest_fit verify
```

The build uses the same archive pin and checked Cargo lockfile as the research
contract verifier. A candidate update must review the preset and catalog
payload hashes, run both verifiers, and compare the reviewed GPU and CPU
offload outputs. The fixtures exercise the same real HTTP path with different
worker bandwidth and model settings on one physical host. For a cross-host
check, run the verifier on a second worker. Keep the prior deployment and
its revision-named executable together for rollback. The server checks the
executable's llmfit revision on startup.

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
