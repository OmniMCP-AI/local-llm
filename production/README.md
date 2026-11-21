# Benchmark release service

PostgreSQL stores reviewed observation revisions and the current release pointer. The service publishes one observation per release. Its Markdown page, HTML chart and table, JSON datasets, and SHA-256 manifest use the same approved row. The example is synthetic. Its value demonstrates the pipeline, and its artifact checksum refers to the checked-in fixture bytes.

The [shared CI CPU baseline](fastest_release/CPU-BASELINE.md) describes the measured decode capture and local publication procedure.

The [llama.cpp release watch](fastest_release_watch/README.md) tracks upstream releases and authored card applicability. It links matched retests to approved benchmark releases.

[Contributor benchmark intake](fastest_contributor/README.md) records private submissions, tracks editorial review, and releases eligible evidence with its source and comparison status.

[Regional price cohorts](fastest_prices/README.md) publish dated reviewed offers and a historical range when the sample qualifies.

[Discovery intake](fastest_discoveries/README.md) turns opt-in leads into attributed review candidates and protects withdrawn or restricted links.

[Text workload costs](fastest_cost/README.md) compare keeping a machine, upgrading, hourly rental, and a token-metered API at the same service targets.

[Controlled inventory agent comparison](fastest_agent_task/README.md#serve-the-pinned-comparison) links the two pinned fixture policies, their review status, and approved attempt outcomes through the release origin.

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

For an audited benchmark resolution, pass a private request JSON file to `python3 -m fastest_release.resolution`. Include `action`, the pinned `previousRelease`, `evidenceId`, and the exact published `sourceLocator`. A correction also carries the reviewed `correction` observation. The publisher transaction returns the resulting release and exact before and after hashes for affected benchmark artifacts. A retry returns the same audit result. When a benchmark shares the affected Pages source locator, the [Pages review command](../README.md#review-a-correction-or-rights-withdrawal) can run this transaction and collect the audit alongside the wiki and research changes.

The Python interfaces are `ReleaseStore.migrate()`, `publish(observation)`, `read(release_id=None)`, `artifact(release_id, name)`, and `withdraw(evidence_id, reason)`. `read()` resolves the current pointer and returns the released row or a withdrawal record. Keep the release ID to access the same snapshot in other formats.

## Query the public release API

Run `python3 -m fastest_release serve`. The OpenAPI 3.1 description is served at
`/api/v1/openapi.json`, and `/.well-known/api-catalog` links to it in
[API catalog format](https://www.rfc-editor.org/rfc/rfc9727). Discovery reflects
the readers configured on that listener. It includes the evidence operation
when the observation database is configured and historical offers when a
price reader is configured.

| GET path | Inputs and result |
| --- | --- |
| `/api/v1/search` | Optional `q`, `kind=machines\|models` and profile `revision`. Returns catalog IDs and pinned profile links. |
| `/api/v1/coverage` | `kind` and profile `id`. Returns cohort conditions, evidence references and exclusions. |
| `/api/v1/evidence` | `evidence_id=<UUID>` resolves the most recent revision of that evidence. Use `release=<UUID>` to replay a specific release. Supplying both verifies the evidence ID in that release. |
| `/api/v1/comparison` | The same selectors as the goals form, plus optional goals `revision`. Returns comparison values, gates, exclusions and the pinned page URL. |
| `/api/v1/comparison/profile` | `kind` and profile `id`. Returns the controlled cohort's measurements and exclusions in display order. |
| `/api/v1/historical-offers` | Price `release=<UUID>`. Returns reviewed quotes in their original currency, with freshness, eligibility, conditions and citations. |
| `/api/v1/advisor` | Structured configuration or cost decision with clarification, abstention, or a cited answer. See the [guided advisor](fastest_release/ADVISOR.md). |
| `/api/v1/calculator` | `scenario`, `monthly_accepted` and `months` match the cost page. An optional `revision` verifies the replayed calculation. Pass `scenario=illustrative` to reproduce the clearly labeled example. |

Search, coverage, profile comparisons and historical offers accept `limit`
(1–100, default 25) and `offset` (0–10,000). Reuse the same selectors and
resolved profile revision or price release with the returned `next_offset`.
A null offset ends paging. Quote listings reflect display and export rights.
Numeric aggregates require their own authorization. Missing values stay null
with the source's status or explanation. Decimal amounts are strings. A
listener accepts up to 120 API operation requests per rolling minute.

Run the observation and price migrations against the serving database as the
schema owner. A read-only login can resolve evidence IDs and dated offers with
the following additional grants where those operations are configured.

```sql
GRANT EXECUTE ON FUNCTION fastest_release.read_evidence(uuid) TO fastest_release_reader;
GRANT USAGE ON SCHEMA fastest_prices TO fastest_release_reader;
GRANT EXECUTE ON FUNCTION fastest_prices.read_release(uuid) TO fastest_release_reader;
```

Optional `rights.expires_at` on an observation and
`authorization.expires_at` on a price cohort accept UTC timestamps with
seconds, for example `2027-01-01T00:00:00Z`. At and after that instant the
canonical reader treats each affected release as withdrawn, including saved
releases. Evidence and historical-offer queries then return 410 with no
measurement or offer rows. Profile and goals pages reflect the resulting
coverage or budget gaps.

## Deploy the release origin

Build the image from a clean checkout at the repository root. It runs the
release listener as UID 10001 with Python and the PostgreSQL client. Run the
observation and price migrations from the checkout as the schema owner. Give
the serving login only the schema and function grants above.

```sh
docker build -f production/fastest_release/Dockerfile -t fastest-release .
docker run --rm --read-only --publish 127.0.0.1:8000:8000 \
  --env FASTEST_DATABASE_URL --env PGPASSFILE=/run/secrets/pgpass \
  --env PGSSLROOTCERT=/run/secrets/pg-ca.crt \
  --mount "type=bind,src=$FASTEST_READER_PGPASS,dst=/run/secrets/pgpass,readonly" \
  --mount "type=bind,src=$FASTEST_READER_CA,dst=/run/secrets/pg-ca.crt,readonly" \
  fastest-release --trusted-host "$FASTEST_RELEASE_HOST"
```

Use the reader connection settings in `FASTEST_DATABASE_URL`, with
`sslmode=verify-full` for remote PostgreSQL. Supply absolute host paths to
the password file and database CA. Make the password file readable by UID
10001 with mode 0600. The image listens on port 8000 by default. To use a
different container port, set `PORT` and update the port mapping. For reviewed
goals, cost scenarios and live rights files, mount the corresponding files
read-only and pass the existing `serve` flags. A deployment with fit enabled
also mounts the pinned fit executable and passes `--fit-engine`. To let
benchmark contributors check their review status, apply the [receipt route
setup](fastest_contributor/README.md#serve-receipt-links).
To publish retained llama.cpp releases, grant read access to the watcher
schema and enable the route. [Serve the watch](fastest_release_watch/README.md#serve-the-watch)

Terminate TLS in the reverse proxy and forward the canonical `Host` header
through to the listener. Set `FASTEST_RELEASE_HOST` to that header value,
including any explicit port. Preserve `Cache-Control: no-store` through
the proxy so withdrawals take effect on the next read.

Run the same readiness check that the image uses against the deployed HTTPS
origin. It follows the catalog to OpenAPI and verifies that the public
evidence and historical-offer routes can use their configured readers.

```sh
cd production
python3 -m fastest_release.healthcheck "$FASTEST_RELEASE_ORIGIN"
```

Use that verified HTTPS origin as `FASTEST_RELEASE_ORIGIN` in the Pages
build and Functions environments. To verify publication, replay an approved
evidence ID and price release from the API on that origin and compare their
returned values with the pinned pages linked in the responses. The Release
origin CI workflow checks that replay with PostgreSQL fixtures before and
after restarting the container, including reader permissions, pagination,
withdrawal and calculator parity.

## Connect an MCP client

The local adapter uses MCP **2025-11-25** over **stdio**. The verified client
is the official MCP Python SDK `ClientSession` from `mcp==1.30.0`, which is
also the adapter's SDK pin. Responses retain the public API `1.0.0` payload,
including revision IDs, citations, units, unknowns, exclusions and decimal
strings. [MCP stdio specification](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports) · [Python SDK release](https://github.com/modelcontextprotocol/python-sdk/releases/tag/v1.30.0)

From `production/`, start `python3 -m fastest_release serve` with the readers
you want to expose. Install the adapter dependencies into the Python environment
your client will launch using `python3 -m pip install -r fastest_mcp/requirements.txt`.
Configure the client to launch `python3 -m fastest_mcp --port 8000` with
`production/` as its working directory. Clients that take an executable and
argument list can use the following command, substituting absolute paths.

```json
{
  "command": "/path/to/python3",
  "args": ["/path/to/local-llm/production/fastest_mcp", "--port", "8000"]
}
```

| MCP operation | Released data |
| --- | --- |
| `v1_search` | Paginated benchmark profile directory |
| `v1_catalog` | Paginated Pages cards, machines, model repositories and runtimes, when `--catalog-origin` is configured |
| `v1_coverage` | Profile cohorts, evidence references and exclusions |
| `v1_evidence` | One evidence ID or release UUID, when the evidence reader is configured |
| `v1_comparison` | Goals comparison with its release ID and pinned page URL |
| `v1_profile_comparison` | Reviewed measurements and exclusions from a pinned profile cohort |
| `v1_historical_offers` | Authorized historical quotes, when the price reader is configured |
| `v1_calculator` | Deterministic cost projection for the same accepted workload |
| `fastest://v1/catalog` | First page of the public benchmark profile directory with its resolved revision |
| `fastest://v1/releases/{release_id}/evidence` | Evidence JSON by release UUID, when the evidence reader is configured |

Tools publish their supported arguments through `tools/list`. Save the returned
release or revision along with the selection to replay a comparison. For lists,
reuse the revision and filters with the returned `next_offset`. The evidence
tools and resources use the public listener on `127.0.0.1`. Its pagination,
rate limit and current rights checks apply on every read, including pinned
URIs.

To browse the PostgreSQL-backed Pages catalog as well, pass the public HTTPS
origin of that deployment when launching the adapter.

```sh
python3 -m fastest_mcp --port 8000 --catalog-origin https://fastest.ai
```

Supply the origin without credentials, a path or query parameters. An HTTP
loopback origin such as `http://127.0.0.1:8788` works with a local Pages preview.
The optional `v1_catalog` tool accepts `kind` (`cards`, `machines`, `models`, or
`runtimes`), an optional search `q` and a page limit of up to 25. Use an exact
`owner/repository` ID for model searches. Continue with the result's `revision`
and `pagination.nextOffset`. Catalog results retain the snapshot ID, manifest,
profile links and source URLs from Pages. Resolve relative links against the
configured Pages origin. The published endpoint checks withdrawal on every
request.

The adapter caps each upstream response at 2 MiB. It sends requests directly to
its configured origins, uses fixed GET paths and rejects redirects. Client
selectors cannot change the destination or run private queries.

The wire tests start disposable listeners and exercise the official client.
They compare profile evidence, exclusions, withdrawal and exact calculator
decimals, and check that catalog results equal the Pages API payload.

```sh
PYTHONDONTWRITEBYTECODE=1 uv run --isolated --with-requirements fastest_mcp/requirements.txt python -B -m unittest discover -s tests -k mcp -v
```

## Compare one GPU with multiple GPUs

The read-only topology report at `/topology/scaling` and its `.json` companion show
unavailable coverage until a reviewed pair is configured. Set the HTTPS
`FASTEST_RELEASE_ORIGIN` in the Pages build to link both the interactive and static
Technology views to this report.

Use the [operator capture instructions](fastest_release/SCALING-EVIDENCE.md#capture-a-pair)
to run the pinned decode protocol on an authorized CUDA host and retain a private
record of both attempts and the transfer trace.

To serve a pair, publish both reviewed observations, then give the release listener
their exact release UUIDs in baseline and comparison order.

```sh
python3 -m fastest_release serve --scaling-pair "$baseline_release" "$comparison_release"
```

Use workload ID `llama-bench-solo-gpu-scaling`, version 1, and the decode metric
from the [pinned text plan](fastest_text/plan.json). Both observations use the
same physical host revision, exact artifact and embedded tokenizer, CUDA runner
revision and binary, OS and driver, solo load, quality rubric and decode boundary.
Publish the standard allowed `run_id`, `backend`, `runtime_revision` and
`artifact_companion_sha256` fields. Include an allowed `gpu_scaling_v1` field
with a JSON-encoded value containing the following keys.

| Keys | Recorded evidence |
| --- | --- |
| `outcome` | `success`, `oom` or `failed`. A non-success observation may describe a measured attempt count rather than throughput. |
| `binary_sha256`, `os_driver`, `settings` | Exact runner build, OS and driver, and the text plan settings with `split_mode` and `main_gpu` recorded as placement treatment below. |
| `load`, `quality` | Load is `One foreground sequence on an otherwise idle host.` Quality contains the pinned rubric `protocol` and boolean `accepted`. |
| `devices`, `primary_device`, `strategy`, `treatment` | Each active physical GPU supplies PCI address `id`, `slot`, `card` and effective `placement`. Give the primary GPU's address, `single-device` for the baseline or llama.cpp `layer` or `row` splitting for multiple GPUs, and a short description of the change. |
| `transports` | Empty for the baseline. For the comparison record active GPU addresses `from` and `to`, `path` as `direct-peer` or `host-staged`, `interconnect`, `direction` as `one-way` or `bidirectional`, positive `payload_bytes`, `scope` and `method`. Supply rated and negotiated link properties as separate `rated` and `negotiated` objects with `generation`, `width` and `rate` with units. Use null where unknown. Supply measured `bandwidth_gb_s` as decimal text or null. |

The configured pair URL pins both observations and checks current public rights
on each request. The report gives exact rational speedup and efficiency and reports
a specific exclusion for a mismatched, failed or unavailable pair. Only a synthetic
test fixture is included for this protocol. A public measurement needs a reviewed
pair from an authorized GPU host.

[Scaling evidence review](fastest_release/SCALING-EVIDENCE.md) records two
source-reported candidates and the gaps that keep them out of this report.

## Test the integrated production code

The full Python suite requires Python 3.11+, PostgreSQL command-line tools, FFmpeg/ffprobe, Pillow 10.1–12 for channel packaging, and the MCP SDK. From `production/`, run this in a local environment with those tools. uv installs the Python dependencies in an isolated environment.

```sh
PYTHONDONTWRITEBYTECODE=1 uv run --isolated --with 'Pillow>=10.1,<13' --with-requirements fastest_mcp/requirements.txt python -B -m unittest discover -c -s tests -v
```

The HTTP fit cases need a pinned native binary. Run the [fit verification command](#estimate-fit-for-a-selected-machine) to exercise them. The standalone benchmark-release tests need only Python and the PostgreSQL tools.

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

Open [Estimate model fit](http://127.0.0.1:8000/fit). Preselect with
`?machine=llmfit-nvidia-rtx-4090` or `?machine=apple-mac-mini-m4-24gb-512gb`.
The hosted Mac mini catalog profile opens the same form through the configured
`FASTEST_RELEASE_ORIGIN`.
Use `GET /fit.json` for JSON. Pass `machine`, the artifact SHA-256 as
`artifact`, `runtime`, `context`, and `ram_reserved_gib`. Pass
`vram_reserved_gib` for a discrete GPU and supply its system `cpu_cores`
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

The Apple Mac mini M4 factory configuration MCYT4LL/A pairs a 10-core CPU and
10-core GPU with 24 GiB of nominal unified memory and a 512 GB SSD. The pinned
core runs its explicit llama.cpp path on Metal and checks the M4 bandwidth lookup
against Apple's 120 GB/s rating. The single reservation covers macOS and any
headroom the visitor wants to keep. Leave `vram_reserved_gib` absent or zero.
The assumed shared budget and unknown actual Metal working-set limit are shown
with the estimate. Apple does not supply FP16 throughput in the cited
specification, so prefill speed and time to first token are unavailable.

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
payload hashes, run both verifiers, and compare the reviewed CUDA, Metal and
CPU offload outputs. The [llmfit parity workflow](../.github/workflows/llmfit-parity.yml)
builds and verifies the pinned engine on Linux x64 and macOS arm64. It checks
that the complete `/fit.json` responses for CUDA, Metal, CPU offload, and missing input
are identical after sorting JSON keys. To reproduce the check on other
workers, run `python3 -m fastest_fit verify --report fit-report.json` on each
worker and compare the two reports with `diff -u`.

Keep the prior deployment and its revision-named executable together for
rollback. The server checks the executable's llmfit revision on startup.

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

## Build the two-machine image pilot

The [image pilot](fastest_image/README.md) uses the same planned Apple M4 and
GeForce RTX 4090 cells for one pinned ComfyUI workflow. It reports completion
time, accepted images and access blockers from the same ledger in Markdown,
HTML and typed JSON.

## Compare image team economics

The [image team comparison](fastest_image_team/README.md) models local, cloud
and hybrid capacity, labor and cash payback for one shared aggregate workload
and deadline. Its default report records the missing consented case. An
explicit fictional example exercises all three plans and the sensitivity cases.

## Browse reciprocal machine and model profiles

From `production`, run `python3 -B -m fastest_release serve` and open
[Machine and model comparisons](http://127.0.0.1:8000/profiles). The directory
and each HTML, Markdown and JSON profile URL pin the same profile release.
The two machine pages cover Apple M4 and GeForce RTX 4090. The two model pages
cover the exact Qwen2.5 7B Instruct GGUF and SDXL Turbo checkpoints from the
pilot plans. The current pilot records have access blockers, with no eligible
measured rows. Each profile lists the pinned protocol, runtime, artifact files,
ranking rules and cohort exclusions.

When reviewed runs are available, use the typed pilot report and its original
review evidence to prepare approved observation documents for the
[benchmark release service](#publish-correct-and-withdraw). Run `migrate` to
install the profile metric definitions before publishing. Use these pins in
the documents:

| Cohort | Workload ID and version | Primary metric | Map companion |
| --- | --- | --- | --- |
| Text | `llama-bench-solo-empty-kv@1` | `llama-bench-decode` v1, median tok/s, 20 successful samples | `llama-bench-prefill` v1, median tok/s, 20 successful samples |
| Image | `comfyui-sdxl-turbo-solo@1` | `comfyui-seconds-per-accepted-image` v1, ratio s/image, five measured repeats | `comfyui-median-completion` v1, median s, five successful repeats |

Use the measurement boundaries from the plans and the release metric
registry. Publish the first text shard as `artifact.path` and `artifact.sha256`,
with `format: GGUF` and `quantization: Q4_K_M`. Put the second digest in the
public, known `artifact_companion_sha256` field. For image, use the pinned
checkpoint, `format: Safetensors`, `quantization: FP16`, and public, known
`workflow_sha256`. Include the public, known fields `profile_cell`
(`apple-m4` or `rtx-4090`), `backend` (`Metal` or `CUDA`), `runtime_revision`
and `run_id` (a stable UUID per execution). Use identical hardware and artifact
identity in all observations from that run. Keep the original and reviewed
setup, denominators and evidence in the study record. A primary observation
qualifies for ranking on its own, while a map point requires both metrics
from the same run. The machine and backend change together in these cohorts.

Pass one `--profile-release RELEASE_UUID` flag per approved observation release
when starting the server with `FASTEST_DATABASE_URL`. The profile release ID
derives from those exact UUIDs and the pinned cohort definitions. To retain a
prior measured set on the same server with the same plans, pass
`--profile-archive UUID,UUID,...` with its prior observation UUIDs. Keep the
prior deployment for archives that use different plans. Reads check current
rights together on every request. Withdrawals remove affected values from both
profiles and their views, including held profile releases. Prototype and
synthetic observations are ineligible.

## Controlled agent-task comparison

The [inventory agent task](fastest_agent_task/README.md) compares time and success
for one pinned task under two read-only tool policies. Run the local inference
adapter on an owned host to collect a private evidence packet. Build a synthetic
demo or a measured release from reviewed operator-owned records, with matching
HTML, Markdown, JSON and a checksum manifest.

## Compare setups against goals

Run `python3 -B -m fastest_release serve` from `production/` and open
[Compare setups by goal](http://127.0.0.1:8000/goals). Machine, budget and expert
entry points use the same pinned text cohort. Start with minimum prefill and
decode rates and add a whole-build budget if applicable. Change the sort
preference and chart axes independently. Share the pinned URL to preserve the
selection. Each chart marker links to its exact table row. The built-in cohort
lists the two planned cells and their access blockers.

To serve reviewed records, pass `--goal-cohort PATH` and `--goal-rights RIGHTS.json`. Use a trusted operator
manifest using this shape. The identifiers in this example illustrate the
format.

```json
{
  "schema_version": 1,
  "records": ["reviewed-m4.json"],
  "market": {
    "market": "US",
    "destination": "US-CA, ZIP 95814",
    "currency": "USD",
    "condition": "new"
  },
  "candidates": {
    "apple-m4": {
      "build_revision": "reviewed-m4-build-revision",
      "price_release": "ee436650-1a1d-45e4-995d-c3be9b443f0d",
      "privacy": {
        "value": "local-only",
        "source": "public locator for the approved execution/privacy review"
      }
    }
  }
}
```

Record paths are relative to the manifest. Use the
[reviewed text intake](fastest_text/README.md) for the two planned cells.
A public-safe privacy review of the exact text workflow reports `local-only`
or `external`. Quality passes when every reviewed output passes the pinned
rubric. A successful partial run can supply the phase it measured. Only rows
with reviewed measurements and passing quality and privacy gates can compete
on the chart. Chart points also require values on both selected axes.

Choose **Team serving** to set limits for response time under four-user load,
aggregate accepted output and wall energy per accepted request. The built-in
serving rows start unmeasured. The [serving capture and intake instructions](fastest_serving/README.md)
specify the workload, meter boundary and reviewed records for the same goals
page and comparison API.

Add a price UUID only after matching the tested machine to that exact
whole-build revision. Configure `FASTEST_DATABASE_URL` with permission to
execute `fastest_prices.read_release(uuid)`. Budget uses the lowest eligible
individual landed asking quote in the pinned release, compared in its original
currency. Each response reads price rights again. Quote freshness is relative
to the dated price release. Keep price pins current by publishing a new cohort
when authorized quotes change. A withdrawn quote becomes unknown on its next
read. Fit links open the separate fit estimator when configured.

Repeat `--goal-cohort` to retain earlier reviewed manifests and their pinned
URLs. The last manifest becomes current. Keep each retained manifest with its
exact reviewed records. For each reviewed cohort, inspect the digests from
`GoalService(Path("cohort.json")).observation_digests` in an operator Python
session under `production/`. Supply `price_reader=PriceStore(database_url).read`
when the cohort has a price pin. After rights review, create a trusted file
with `schema_version` set to 1 and an `observations` object that maps each
approved digest to `"allow"`. Keep entries for any retained releases that are
still authorized.

Replace that file atomically to set a withdrawn observation's digest to
`"withdrawn"` or remove its entry. The next read of an affected text or
serving lane returns 410 across the site, API, and MCP, including pinned
text companions. Missing or malformed configured policy files make measured
goal reads unavailable. The built-in plan and unmeasured serving cohort
remain available.

## Price and evaluation source intake

Capture source checks, GPU price and tariff candidates, published model evaluations, and private image-pilot timings in PostgreSQL before editorial review. [Private intake workflow](fastest_intake/README.md)
