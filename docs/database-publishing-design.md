# fastest.ai database and publishing design

The [product specification](product-spec.md) defines scope, the five milestones and their acceptance criteria. [Tracking issue](https://github.com/OmniMCP-AI/local-llm/issues/1)

In the production design, PostgreSQL is the source of truth for catalog identities, measurements, prices, and what can be published. A released snapshot supplies the Markdown pages and chart data. The HTML renderer reads that release bundle. Graphify indexes the released Markdown to generate navigation and backlinks.

The review prototype bundles a pinned catalog, local Markdown, a Graphify index and illustrative scenarios. Its sample responses, browser-local feedback receipts and example quotes demonstrate the interface. A production benchmark, receipt or price history must pass the release and ingestion checks below.

## Research import and llmfit boundary

Use the pinned **llmfit-core** commit `26450cccaf3a3f14b1822875f2473847a744a718` for fit analysis and its contracts for interchange. The public request supplies selected profile, context, runtime and memory assumptions. Persist the result as an estimate keyed to those inputs and engine revision. Repeat on a worker with different physical hardware and require the same result. The prototype's upstream catalog import and the research's structural validation exercise different parts of this contract. [Native schema notes](Local-AI-Comparison-Platform/YouTube-Local-LLM-Transcripts/llmfit/schema.md) · [Mapping examples](Local-AI-Comparison-Platform/YouTube-Local-LLM-Transcripts/llmfit/mapping.md)

| Seed input | Invariant for the first import |
| --- | --- |
| 116 research profiles, 487 component rows, 99 original hardware fact rows | Preserve original IDs, BOM, raw units, locators and unknowns. Sixteen profiles have a schema-compatible `HardwareProfile` core. One hundred have partial cores. All 116 remain incomplete as reproducible builds. |
| 450 observations in 242 test series | Store an observation once. Preserve the 293 qualified profile associations and 157 unassigned observations. The 127 scalar `BenchmarkEntry` projections and 323 research-only observations exhaust the seed. A successful structural projection alone cannot enter a measured cohort. |
| 140 video-scoped model references | Preserve unresolved identities. The seed has zero complete native `LlmModel` records and zero native community submissions. The prototype's separate upstream snapshot has 19,192 model records. |
| Direct upstream imports | Pin commit, path, mapper, payload digest, provenance and notice per input. Use distinct fixtures for `HardwareProfile`, `LlmModel`, `BenchmarkEntry`/nested `HardwareInfo`, and the community submission schema. Preserve native field casing. Keep research extensions outside strict native payloads. A pinned loader and a real fit call are M1 acceptance checks. |

The retained validation report identifies schema checks already performed. Keep model weight terms, family heuristics, merged contributor measurements, and externally sourced benchmark caches separately attributable. Record reuse rights by field and destination. [Seed validation](Local-AI-Comparison-Platform/YouTube-Local-LLM-Transcripts/llmfit/validation-report.json) · [Upstream MIT notice](Local-AI-Comparison-Platform/YouTube-Local-LLM-Transcripts/llmfit/LICENSE.llmfit-MIT.txt)

## Relational schema

Use stable UUIDs for public identities and separate IDs for their immutable revisions. Human-readable slugs can change without changing an identity or invalidating an old link. `PK`, `FK`, and `UQ` denote primary, foreign, and unique keys.

### Catalog and reproducible configurations

| Table | Keys and scope |
| --- | --- |
| `component` and `component_revision` | `component.id` PK, with a kind such as GPU, CPU, RAM, motherboard, PSU, or chassis. GPU rows carry manufacturer, product family, SKU and form factor. `component_revision.component_id` FK and `UQ(component_id, revision_no)` pin specifications, source references, and board variants. A family-level listing alone does not identify a tested board. |
| `machine_profile` and `profile_revision` | `machine_profile.id` PK and unique slug. `profile_revision.profile_id` FK and `UQ(profile_id, revision_no)`. A revision fixes CPU and memory layout, discrete versus unified memory, tested device count and topology where known, cooling, power and OS assumptions. Keep partial catalog profiles and complete run-ready profiles separately identified. |
| `profile_part` | `PK(profile_revision_id, slot_key)` and FKs to the profile revision and component revision. Stores quantity and role, including inference versus display-only GPU. A missing part can have a null component revision with a reason. Creating a draft with a substitution creates a new revision and inherits no measurements. |
| `model_family`, `model_revision`, `model_artifact` | Family has stable ID and slug. Revision FK to family with `UQ(family_id, upstream_repository, upstream_revision)`. Artifact FK to revision with `UQ(model_revision_id, upstream_path)` and content digest where verified. Keep file format, quantization, tokenizer identity and maximum context. Record Hugging Face and GitHub links at the identity or revision they establish. Unresolved names remain source claims until matched. |
| `runtime`, `runtime_release`, `tuning_revision` | `runtime_release.runtime_id` FK with `UQ(runtime_id, upstream_ref, build_digest)`. A `tuning_revision` pins release, backend and versioned settings such as KV quantization, offload, batch, caching, device placement and parallelism. `UQ(runtime_release_id, tuning_schema_version, settings_digest)` deduplicates. |
| `execution_config` | FKs to profile revision, model artifact and tuning revision. `UQ(profile_revision_id, artifact_id, tuning_revision_id, environment_digest)` includes driver, OS, topology revision and active device placement in the digest. Unknown but necessary fields keep a configuration outside the reproducible cohort. |
| `compatibility_observation` | FKs to execution configuration, workload protocol, and evidence set. `UQ(config_id, protocol_id, evidence_set_id)` retains separate observed, inferred, and estimated compatibility reports, alongside outcome and failure reason. A fit estimate does not imply a successful run. |

### Single and multiple GPU topology

| Table | Keys and scope |
| --- | --- |
| `topology_revision` and `topology_node` | The topology revision references the profile revision, with `UQ(profile_revision_id, revision_no)`. Nodes use `UQ(topology_revision_id, node_key)` and identify each installed physical GPU, logical partition, CPU root complex, NUMA node or switch. A GPU has a physical slot and optional model/part reference; a partition references its parent GPU and has its own allocation and limits. Count installed and active physical GPUs separately from logical devices. |
| `topology_link` | Two endpoint FKs to nodes in the same topology, plus `link_key` unique within the topology. Record declared PCIe generation and lane width, NVLink or other interconnect type, and physical link count where verified. PCIe lanes, ports and accelerator links are different fields. Record whether paths are direct peer-to-peer, switch-routed, host-staged, or unknown, and their NUMA relationship. |
| `transport_observation` | FKs to topology revision and evidence set, optionally to a link and the observed run. `UQ(source_version_id, external_record_key)` deduplicates. Record observed endpoints, direction, actual negotiated PCIe generation/width/rate, P2P support and path actually used, when known. Keep theoretical link rate and measured application-copy throughput distinct. Measured bandwidth records the probe method, payload, direction pair, and unidirectional versus simultaneous bidirectional total; latency is a separate metric. Unknown values remain unknown. |

Store VRAM and memory bandwidth per device or partition and distinguish physical capacity, configured allocation, and runtime-usable capacity. A system can display its installed VRAM total as inventory, but copy, shard and offload behavior determine fit. Never treat the sum as usable model memory. Tuning pins backend and observed support for the selected devices, link utilization, placement, and parallel strategy such as tensor, pipeline or data parallelism. Physical links do not establish which path a backend uses.

Show single-to-multi-GPU scaling only for an eligible measured 1→N pair. Hold artifact, task and quality criteria, host configuration, precision, runtime/backend, batching, request load and measurement scope fixed. Report device placement and any planned parallel-strategy change as explicit treatment metadata. Throughput speedup is matched N-device throughput divided by matched single-device throughput; efficiency divides that speedup by the active physical device count. Compare like-for-like tail latency separately. If the single GPU cannot run the artifact or the scope differs, show the reason and omit scaling. Neither link bandwidth nor GPU count predicts a measured speedup.

### Protocols, data and comparisons

| Table | Keys and scope |
| --- | --- |
| `workload_protocol` | Immutable `UQ(protocol_key, version)` with modality, task and quality criteria, input/output and context, warmup and cache rules, and measurement boundaries. Serving protocols also fix concurrent users, load, duration and requests per user. Solo, four-user and throughput stress tests are separate protocols. |
| `raw_observation` | `UQ(source_version_id, external_record_key)` captures what the source actually said and any unresolved names, variants, workloads or units. Ingestion and review may link it to catalog entities and create typed records. A reported estimate or incomplete observation is not an exact run. |
| `benchmark_run` and `run_attempt` | Run FKs to `execution_config`, `workload_protocol`, and `evidence_set`. Unique import key deduplicates a replay. `run_attempt` has `UQ(run_id, attempt_no)` and records outcome, timing, and available request diagnostics. Preserve failed attempts as well as successful attempts, with OOM, timeout, and eligibility reasons. |
| `metric_definition` and `run_measure` | Definition has `UQ(metric_key, version)`, quantity, unit, direction, statistic, measurement boundary, subject scope and calculation or method reference. `run_measure` has `PK(run_id, metric_definition_id)` and stores value, status, sample count and optional uncertainty. Use attempt rows or a restricted sample file for per-request values. A changed statistic, boundary or formula gets a new definition version. |
| `price_observation` and `cost_scenario` | A price observation references exactly one component revision or profile revision. `UQ(source_version_id, external_record_key)` and explicit price scope, region, currency, observed time, condition, offer versus sale, and tax/shipping inclusion. Cost scenarios version inputs such as electricity rates, runtime, amortization and utilization. Whole-build quote, component quote, energy cost per request and modeled TCO stay distinct. Preserve original local prices and version currency conversions or display separate cohorts. |
| `cohort_policy` and `comparison_view` | Policy has `UQ(policy_key, version)` for exact-match fields, allowed differences, eligible evidence classes, minimum conditions and public metric definitions. A view references policy and release, plus a normalized hash of fixed filters, goals, display metrics and sort priority. Stable links can pin a view or request the latest published release explicitly. |

The metric catalog distinguishes decode from prefill, TTFT from end-to-end response time, per-user from aggregate throughput, and watts from Wh for a defined work item. For example, four-user latency p95 is a statistic over individual requests under the four-user protocol. It is separate from one-user throughput and cannot come from averaging already aggregated percentiles. Missing, not applicable, incompatible, failed, withheld, and estimated are explicit states. A missing result carries no numeric value and never substitutes zero. Outcomes and run status stay visible even when a metric cannot be computed.

Each chart uses one explicit cohort for a metric. If a page combines solo speed, team response time and energy, each value keeps its own matching workload context and evidence. The page compares machine choices across those workloads without claiming they were measured in the same run. A pinned model view compares machines for the exact artifact. A pinned machine view compares model artifacts only on an agreed task and quality criterion when ranking, keeping raw per-token diagnostics inspectable. A multi-goal view reports pass, miss or unknown against each threshold. Show nondominated options only when all selected objectives have eligible values. Sort by the visitor's chosen priority and keep missing data separate from contradicted goals.

### Workload, quality and cloud records

Extend the common protocol and evidence keys as each workload enters a release.

| Record | Fields that affect the decision |
| --- | --- |
| `workflow_revision`, `harness_revision` | For images, pin workflow hash, node/build versions, model assets, precision, resolution, steps, sampler, seed sequence and batch. Record queue/load/execute/save and client delivery boundaries, success and accepted outputs. For agents, pin harness, tool policy and fixtures, retry and reasoning budgets, quality rubric, task wall time and external calls. |
| `context_test`, `latency_event` | Record advertised maximum, configured capacity, tested input depth and verified retrieval quality as separate fields. Record tokenizer, actual prompt/output lengths, prefix-hit evidence and residency. Timestamp request, first token, first visible answer and completion at the stated client/server boundary. |
| `evaluation_protocol`, `evaluation_observation` | Store publisher, suite/release, task subset, rubric, judge/harness, scale and direction, defined baseline, language, sample/uncertainty and attempt. Link exact artifact, same revision with different quantization, family reference or unresolved identity. Keep model capability, preference, local execution and popularity in separate series. Local quality gates require applicable task evidence. |
| `provider_endpoint`, `tariff_version`, `privacy_policy_version` | Record endpoint/model revision, billing unit, cache tiers, effective interval, eligible region/account, storage/egress and data handling for that service. Pair token usage or image counts with the applicable tariff and accepted work. Team scenarios also version peak demand, queue/SLO, rework, labor, downtime and hybrid routing. |

For the four-cell pilot, use the same fixed text protocol and image workflow on two accessible machines. The research proposes 20 warm text samples for an initial distribution and at least 100 requests for a decision-grade tail test. Its image protocol proposes one warmup plus five timed runs with the same seed sequence across machines. Publish actual counts and failures even if a target is missed. For imagery, compare time and cost per accepted image. For text across tokenizers, compare time and cost per accepted task. Scope stability to the observation window and thermal or power measurements to the instrument used. [Measurement and pilot research](Local-AI-Comparison-Platform/Local-AI-Comparison-Platform.md)

### Evidence, intake and release control

| Table | Keys and scope |
| --- | --- |
| `source`, `source_version`, `rights_policy_revision` | Source identity includes type and stable external key. Source version has `UQ(source_id, revision_or_hash)` and holds URL, capture time, content digest and access class. Rights revision defines whether access, excerpts, numeric reuse, assets and export are allowed, and under what obligations and dates. Apply rights by intended destination and use. |
| `evidence_set`, `evidence_item`, `evidence_set_item` | Item references source version with locator, assertion method and validation status. Join table `PK(evidence_set_id, evidence_item_id)` links one public assertion to all supporting evidence. Interpret derived metrics through their input evidence and method. Use the same IDs in Markdown citations, widget tooltips and API/MCP responses. |
| `feedback_submission`, `submission_evidence`, `review_decision` | Feedback has an independent receipt ID and may reference an explicitly shared page and release. Responses acknowledge receipt and can suggest a next step immediately. Record category, workflow status, publication consent and separate private contact or attachments. Evidence submissions record the verified source, qualifier and review decision. GitHub public intake deduplicates on repository plus issue or PR ID and revision, validates webhook delivery, and stores only approved public links and redacted material. A reply, reaction, or merged contribution cannot publish metrics without evidence review. |
| `data_release`, typed release membership, and `publication_record` | Release ID pins schema, metric and cohort policy versions, cut-off, artifacts and digests. Typed membership joins track the exact approved catalog revisions, runs, price rows and rights decisions admitted to the snapshot. Publication records identify surfaces such as page, dataset or approved distribution, artifact hash, prior release and status. Keep one atomic current-release pointer. |

For each intake adapter keep the source item/event ID and revision, first-public, capture and review times, cursor, last successful fetch, next retry, deletion or withdrawal status and the extractor version. A cross-post can cite one original claim. An edited post supersedes its old version. On outage, expose the age and missing interval. In M3 demonstrate this with a configuration release, a regional feed and a performance submission. Discovery on social or video services may resolve only to a lead with a URL.

For M5, link story, claim and asset revisions to a release. An approval pins channel, account, payload hash and scheduled window. A delivery attempt records its idempotency key, provider acknowledgement or export receipt, and any correction. Recheck current rights and evidence before retry. Confirm an ambiguous remote outcome before sending again.

Index foreign keys used by the exporter and public lookup, particularly run `(execution_config_id, workload_protocol_id)`, price `(region, currency, observed_at)`, and the public catalog slug. Keep uploaded logs, unnecessary personal information and private review notes outside the public export.

## Editorial context and Graphify

A reader may ask for material *about* coding or for an observation that *tested* a coding task. Preserve both scopes through DB → Markdown → Graphify → library, chart/table or agent response. The released data still supplies all numeric claims.

| Record | Required fields and joins |
| --- | --- |
| Content revision | Identity and canonical URL, publisher, platform, format, source language, published/updated/first-known dates with nulls for unknowns, rights revision and editorial scope. Separate a cross-post from the article revision it cites. |
| Case reference | Attach a content revision to an observation, controlled run or test series with a stable ID and passage, table row or timestamp. One source can describe several cases and a case can have multiple attributable sources. Store task/fixture and protocol revisions, success criterion and evidence class where known. Keep stated, unreported and inapplicable conditions distinct. |
| Vocabulary | Stable facet and tag IDs, localized labels, approved aliases with locale, vocabulary version, scope, definition, deprecation and replacement. Keep hardware/model/runtime revision IDs and numeric conditions as typed fields. Reserve tags for useful retrieval categories. |
| Tag assignment | Key by subject revision, facet, tag and supporting locator. Exactly one subject per assignment: content revision **or** case reference. Store extraction method/rule version, assertion role, confidence when applicable, proposer, review decision, evidence ID, and release. Index both tag-to-subject and subject-to-tag. A correction supersedes the specific assignment. |

Recommended production facets include source format and modality, use case/domain, concrete task or dataset, workload and deployment setting, measurement dimension, and evidence class. A first-party test report also supplies its exact fixture, protocol, result and observation IDs. Context length, concurrency, power boundary and artifact revision belong to the referenced case. A pricing article may legitimately have zero test references. Coverage should report that explicitly. Article suggestions can use its reviewed title, body or cited passage. A case tag requires evidence at that case. A runtime being mentioned in a neighboring paragraph establishes no run-level fact.

The prototype uses these directed Graphify relations:

| Relation | Interpreted meaning |
| --- | --- |
| Publication → `has_format` / `discusses` → term | Content and editorial discovery. For video topics, the edge retains the cited timestamp. |
| Publication → `reports_series` → series → `contains_observation` → record | The attributed source chain. A series header links to the exact lines of the archived note. |
| Record → `describes_task` / `has_dimension` → term | A task annotation supported by that record or a mapped measurement family. Consult the record's evidence field to tell a projection from a reported run. |

The search projection traverses only these relations. Intersect task, dimension and record-text constraints on one observation before grouping by publication. Sorting, pagination, Markdown context and API results must use the same scoped relationships. For a saved view pin the taxonomy and data release. On withdrawal remove the affected claims/assignments from discovery even at an older URL. In the standalone prototype, URL filters operate on the bundled snapshot.

**Maintaining the vocabulary.** Version the mapping from upstream metric families and fail visibly on unmapped input. Review colloquial terms in context: TTFT can identify first-token latency, while an unqualified “tok/s” alone cannot identify prefill, decode or aggregate serving. Include a cited positive and a hard negative for each new ambiguous mapping. Split calibration and evaluation by source or cross-post family to avoid leakage. Before accepting machine-generated suggestions, measure per-facet accuracy, missed cases and incorrect scope transfers on a held-out set. Keep low-confidence assignments pending. A release includes the vocabulary, annotations and projection hashes. Exact extraction of an authored annotation describes its provenance, not the independent truth of a creator's test.

The checked-in prototype builds the index using `wiki/rebuild_graph.py` in the Graphify Python environment. Its reviewed inputs are the imported series and observations, video topic locators, case annotations, editorial references and wiki frontmatter. `node --test research-filter.test.mjs` in the prototype directory exercises scoped matches, abstentions, provenance and sparse dates. [Product and acceptance examples](product-spec.md#context-tags-for-articles-posts-and-test-records)

## Database to Markdown to HTML

1. **Approve inputs.** Review imported identities, runs, prices and evidence rights. Resolve aliases or keep a partial listing, and mark why a row cannot enter a measured or price cohort. Publication never imports arbitrary scripts, comments, or HTML as trusted code.
2. **Build an immutable data release.** Select a consistent approved cut. Lock entity revisions, metric definitions, cohort policies, rights decisions and artifact hashes. Generate stable, public widget datasets from parameterized, allowlisted queries against that cut. Each widget reads the same canonical row collection for its chart and accessible table. Legend units, missingness, sample size, row IDs and evidence references travel with the data. Keep precision in the dataset and round only in presentation.
3. **Generate Markdown.** Produce a page for each eligible GPU, machine profile, model and other public destination. Use deterministic templates for facts. Join reviewed editorial prose by stable ID. Frontmatter records page ID, canonical path, entity revision, evidence references, data release and widget IDs. Widget specifications pin version, cohort, metrics and units, named filters, renderer and dataset digest. Markdown owns the narrative and placement. It cannot introduce executable SQL, calculation code or unsourced numbers.
4. **Render and index the same bundle.** Render HTML, charts, accessible tables and printable fallback text from released Markdown and approved widget datasets. A chart may hydrate filters from the public dataset without exposing direct database access. Run Graphify over the released Markdown and asset links to generate navigation and backlinks. Treat inferred connections as suggestions subject to approval, never as measurements or rank inputs. Rebuild the index on the same release, then publish the bundle and advance the current pointer together.

For example, `/machines/<slug>` pins an exact profile revision, lists its parts and price scope, and points to a widget keyed by that profile revision. `/models/<slug>` pins the model artifact and uses the same reviewed run dataset with the artifact as its filter. The intersection uses the same row and evidence IDs on both pages. A chart rendered for a different release or metric definition cannot appear on either page under the original snapshot label.

Illustrative frontmatter emitted by the exporter, with short IDs for readability:

```yaml
---
page_id: machine-42
path: /machines/example-workstation
entity_revision: profile-42-r3
release: release-18
evidence: [evidence-100, evidence-103]
widgets:
  - id: model-decode
    view: matched-model-on-machine@1
    protocol: solo-4k@2
    metric: decode-tok-s@1
    filter: {profile_revision: profile-42-r3}
    presentation: [chart, table]
    data: /releases/release-18/widgets/machine-42-model-decode.json
---
```

The release manifest maps the widget path to its content hash. Its JSON rows carry IDs, value or missing status, sample counts and evidence references. The renderer checks the metric, protocol, and release match before mounting either presentation.

Machine pages can use a topology widget to show installed devices, physical and logical links, negotiated capabilities, and measured transport and scaling. Its chart and table label theoretical versus observed values and include the endpoint path and direction with any bandwidth number.

## Runtime release watch

A separate refresh reads the official llama.cpp, SGLang, vLLM and Ollama feeds
and records deduplicated revisions and refresh health in the PostgreSQL
`fastest_release_watch` schema.
The opt-in release origin reads that retained history for `/runtime-releases`,
`/runtime-releases.md` and `/runtime-releases.json`. The CLI and origin share the
projection of source links, release status and last successful refresh. Failed
upstream refreshes preserve the prior success and its history. All three
origin responses bypass caches and reflect the current database read.
The Pages runtime directory and matching catalog profiles read the official
watch summary at request time. The catalog keeps the pinned documentation
and version references from its released snapshot.

A reviewed applicability file attaches a technique to a retained release
revision and exact card, driver, runtime build and workload. For a verified
note the origin uses the benchmark reader to check rights and match the
baseline and tuned runs on every request. An unavailable store or ineligible
configured approval gives a service-unavailable response in each format.
[Runtime watch setup](../production/fastest_release_watch/README.md#serve-the-watch)

## Correction, validation and rollout

- **Correct and withdraw.** Replace claims by adding new source versions, revision rows and review decisions. Publish a new release linked to its predecessor. For withdrawn rights, immediately apply a denylist at every public read, then quarantine affected Markdown, chart payloads, graph links, search entries, downloads and project-controlled mirrors. Purge cached pages and CDN objects. Notify recipients of previously distributed files and record the affected hashes. External clones may retain an old snapshot. Old release URLs retain allowed content and show that evidence was withdrawn. They do not bypass the current rights check.
- **Validate before advancing current.** Check stable IDs and FKs, orphaned or unresolved sources, metrics in scope and unit, observation rights, pinned widget schema, asset licenses, snapshot digests and no private fields in the output. Chart and table must report the same rows and numbers. Machine, model, search and API views must resolve the same eligible overlap. A failed check keeps the previous bundle current.
- **Accept the MVP topology comparison.** Use an illustrative 1-card/2-card fixture with matching workload, artifact, backend and load, measured at 100 and 160 tok/s. The chart and table must agree on 1.60× scaling and 80% efficiency, distinguish the two physical cards from a logical partition, and never present 2×16 GiB as 32 GiB usable. Include a rated PCIe x16 slot that negotiates x8, a measured directional peer transfer, and a host-staged path with missing bandwidth. A separate unmatched 2-card result must show why scaling is unavailable.
- **Milestone sequence.** M1 proves the pinned fit call and the first DB → Markdown → chart/table release for the four-cell text/image pilot. M2 delivers reciprocal profiles, the first authorized regional price view, interactive comparisons, hosted wiki discovery and user feedback. M3 adds recurring feeds, controlled scaling and deeper metrics. M4 delivers agent access, advisor evaluation and team economics. M5 distributes approved evidence packages. Use the [product milestone gates](product-spec.md#milestones-and-acceptance) for release decisions.

## Crawler and agent discovery

Generate discovery files from the same public release manifest as the HTML and Markdown. Stable public routes need readable HTML and normal links before any interactive JavaScript runs.

| Surface | Published contract |
| --- | --- |
| `/robots.txt` | Serve UTF-8 text at the origin root under [RFC 9309](https://www.rfc-editor.org/rfc/rfc9309). Publish the crawler policy and sitemap pointer. Keep private and editorial routes behind access controls. Apply applicable crawl rules independently to source collectors. |
| `/sitemap.xml` and canonical HTML | List indexable public machine, model, catalog, runtime and method pages. Exclude drafts, private views and arbitrary filter combinations. Use stable alternate Markdown URLs, redirects for renamed pages, and release-aware cache validators. |
| `/llms.txt` and Markdown companions | Generate a concise index of public pages, methods, limitations and how to cite the release, following the [llms.txt proposal](https://llmstxt.org/). Serve companions as `text/markdown`, link them from HTML as `rel="alternate"`, and point to the index as `rel="describedby"`. |
| Discovery for live APIs | Publish the read-only OpenAPI description when the API is operational. Use [RFC 9727](https://www.rfc-editor.org/rfc/rfc9727) for `/.well-known/api-catalog` and list only endpoints that exist. Version and document the supported MCP transport, operations and limits. |

Rights are checked before discovery, rendering and export. Crawl guidance does not grant reuse permission or replace authentication. Each public response must identify the evidence release, and corrections and withdrawals flow to every affected representation and index. Treat emerging formats such as [WebMCP](https://developer.chrome.com/docs/ai/agents) as versioned optional adapters. Publish a new agent declaration only when there is a supported capability and a verified client. Gate launch on resolving each advertised route and verifying that a public entity has the same evidence IDs in HTML, Markdown, and the exposed API.

## Interactive technology illustrations

Use the same publishing contract for explanations. A reviewed Markdown page declares a technology widget and pins its diagram revision. The diagram has stable component IDs, labeled connection IDs, a sequence of explanatory steps, and links to wiki pages. Media placements map a rights-cleared `media_asset` and polygon or hotspot to a component and label that match as exact, representative, or conceptual. Clicking a photo and clicking its diagram node select the same component.

Render the same definition as a static accessible diagram or table before JavaScript, then hydrate play, pause, step, and inspect controls. Give keyboard users and users who reduce motion equivalent explanations. Any benchmark value linked from the diagram is resolved through the release-pinned evidence view. The visual animation has its own conceptual timing and does not depict a measured latency or imply a card supports the illustrated link.

The diagram projection takes the selected `topology_revision_id`, so node and link counts change with the setup rather than a fixed template. Multi-host diagrams group the reported accelerators by host. Mixed systems bind each physical slot to its own card revision. Resolve a reviewed photo per slot, keeping a representative family image explicitly labeled and showing an unidentified card placeholder when necessary. Layout supports larger graphs through grouped views with an expandable host or switch. Do not draw a specific peer path when the source only reports a card count.

Acceptance: switch from a one-card profile to a matching two-card profile and then to a four-card or mixed profile. The node count, selected-component details and photo bindings follow the selected revision, and unreported links stay unreported. Switching revisions cannot carry across stale photos, link rates, or benchmark results.

## Comparison methods and ownership scenarios

Use the [YouTube comparison methods review](youtube-comparison-methods.md) as the editorial starting point. A published method pins a versioned question, cohort policy, workload or cost inputs, metric definitions, renderer, and evidence eligibility rules. Inspectable evidence accompanies every point and table row. For a matched workload, store the tested configuration and protocol revision, held-constant fields, named treatment, measurement boundary, and missing or failed outcomes. Cross-model task comparison also pins task suite, rubric, attempts, and success definition. The method can illustrate a reported or hypothetical example using a separate evidence class.

Catalog highlights are reviewed editorial records that reference the specific card, machine, model, runtime, or comparison revision and its evidence, publication date, and release. Give each a source and a short explanation of the observed change. A highlight can direct visitors to a new benchmark, price movement, compatibility change, or illustrative guide. Its placement has no effect on benchmark eligibility or numerical ranking.

A cost scenario records date, region and currency, acquisition scope, priced parts and quantities or a whole-system quote, taxes and shipping where known, and whether parts are included, purchased, reused, or unknown. Store active and idle whole-system watts, hours, tariff, cooling estimate and its boundary, other recurring costs, horizon, workload volume and input/output split, and cloud comparison mode. API rates identify provider, model, region, observed date, and input, cached input, and output price semantics. GPU rental identifies effective billable hours, rate, billing granularity, and applicable storage or transfer. Optional maintenance, residual value, and discounting are disclosed inputs. Keep calculations versioned through the metric definitions and carry method version, formula version, and source IDs into the released scenario dataset.

Acceptance fixtures cover the same published scenario in chart and table. Changing from GPU-only to full build adds each CPU, memory, and platform item once and preserves unknowns. Raising idle power or cooling increases local operating cost without changing measured throughput. Lowering an otherwise matched cloud rate to or below local monthly operating cost removes the modeled payback. An over-capacity local workload is ineligible for an equivalent-service payback. A published comparison refuses a performance ratio when the denominator uses an incompatible artifact or workload. A catalog highlight can be removed without changing the underlying evidence or ranking.

## Languages, markets, and display currency

Give each public entity and metric a stable ID across translations. Store localized editorial text and a source language separately from observation payloads. The UI offers English, Simplified Chinese, Traditional Chinese, Spanish, Japanese, Korean, German, Hindi, French, and Arabic. Set language metadata on the page and source-language fallback sections. Use right-to-left layout for Arabic and retain quantitative axis direction. Production routes can advertise their translated equivalents with `hreflang`.

Resolve the first-visit language from the hosting edge's IP country. On Cloudflare Pages, the function uses `request.cf.country` to attach a supported language hint to the HTML. The app reads a saved language choice first, then the edge hint, then the browser's supported language preferences, then English. An automatic selection is recomputed on load. Multilingual or unmapped countries can fall back to browser preferences. The app receives only the recommended language and personalized HTML uses private, non-cacheable responses. [Cloudflare Pages middleware](https://developers.cloudflare.com/pages/functions/middleware/)

Simplified Chinese (`zh-Hans`, CNY) and Traditional Chinese (`zh-Hant`, TWD) have distinct language IDs. Use Taiwan terminology and `zh-TW` formatting for Traditional Chinese. The edge maps TW to Traditional and CN to Simplified. Hong Kong and Macao use browser preferences. For Chinese browser tags, honor an explicit script first, then infer the script from the region (TW/HK/MO → Hant, CN/SG → Hans), with bare zh defaulting to Hans. Preserve original research wording, model IDs, GitHub/Hugging Face URLs and quoted currency in either interface.

A market key drives quote eligibility and available offers. Its original currency records how a price was quoted. A separate display preference accepts either the language default or an explicit ISO currency. The formatter uses a versioned reference rate with source, base and date, or a visitor-entered rate. Conversions operate on presentation values. They preserve original quotes, raw chart data, and scenario calculations. A missing rate displays the original currency with an explanation. Apply the same conversion to all monetary values within a chart, including ticks, markers, and tooltips.

Acceptance checks cover Taiwan → 繁體中文 and TWD, zh-Hant-CN and zh-Hans-TW browser tags with no edge hint, independent HKD after switching Chinese scripts, Japan → Japanese and JPY, France → French and EUR, manual language and currency choices preserved across IP country changes, browser fallback for an unmapped country, a missing-rate currency with a visitor-entered rate, and identical market membership and cost break-even points before and after display conversion.
