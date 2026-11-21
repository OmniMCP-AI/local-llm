# Controlled inventory agent task

Compare completion and wall time for one fictional inventory subtotal. The bundle context exposes one combined read. The split context exposes one read per page. Both contexts use the same task, rubric, model, runtime, trial count and budgets. Each context has its own fingerprint and its own attempts and denominators.

From `production`, use Python 3.11 or later.

```sh
python3 -B -m fastest_agent_task plan
python3 -B -m fastest_agent_task tool bundle read_bundle inventory
python3 -B -m fastest_agent_task tool split read_page a
python3 -B -m fastest_agent_task build /path/to/agent-task-demo --demo
python3 -B -m fastest_agent_task build /path/to/agent-task-measured
```

Each build writes matching `agent-task.html`, `agent-task.md`, `agent-task.json`, the exact `task.json` fixture and a SHA-256 `manifest.json` into a new directory. The HTML and Markdown show trial counts, failures, every attempt's wall time, accepted answers, tool policy, evidence IDs and conditions. JSON includes the bounded tool reads and token counts. The release ID identifies the exact dataset. Use a new output directory when adding or correcting reviewed evidence.

The demo executes scripted turns against real fixture reads. Its timings are illustrative. It deliberately includes a failed split-context trial attempt and its successful retry. The default measured build has two missing contexts. No reviewed live model runs are included.

## Run the controlled task on an owned host

From `production`, use the included adapter with the pinned `llama-server` and
the first GGUF shard. Keep the second shard beside the first. Choose a short,
new destination under an operator-private parent to accommodate the Unix
socket path limit. Use the hardware, OS build, backend and device from the host
you are measuring. The values below illustrate the Apple M4 invocation.

```sh
python3 -B -m fastest_agent_task.measure /path/to/private/run \
  /path/to/llama-server \
  /path/to/qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf \
  --hardware "Apple M4, 24 GiB" --os "macOS 27.2.1 (26B131)" \
  --backend Metal --device Metal
```

The adapter verifies both shard sizes and digests, checks the runtime revision,
records the binary and adapter digests, and launches a single server on an
owner-only Unix socket. It runs one warmup per context and follows the pinned trial order. It
erases the server's KV slot before each attempt and closes the server when
finished. It writes private draft records, actual server and host logs, raw
model turns and the manifest digest in `review-pending.json`. Check the
offload and KV resets in the server log. The plan requires an idle host. Use the
ambient load snapshots to determine eligibility before approving measurements.

1. Save the plan and use its exact llama.cpp source revision and both GGUF shards from the [text pilot](../fastest_text/README.md). Verify the byte lengths and digests. Use one owned host and keep the runtime binary and adapter unchanged throughout the comparison. Record the hardware configuration, OS build and driver details in the private execution packet.
2. Use a local adapter to drive chat turns under the plan's settings. The opening user message is the pinned prompt, a newline, and `Allowed tool requests: ` followed by the context's compact JSON list. Send only this prompt and the permitted tool results to the model. Each reply must be a single JSON object with unique keys. For a tool request, pass the exact typed pair to `fastest_agent_task.harness.read_tool(context_id, tool, resource)`, and append the returned JSON as a user turn. The CLI `tool` command exposes the same fixture reads for inspection. If using it during a timed trial, use the same invocation method in both contexts and include its overhead.
3. Stop on acceptance, a final candidate, a denied call, invalid JSON, runtime error, or the first reached budget. A tool request consumes a call from the attempt's budget, and generated tokens are counted cumulatively across model turns. The capped output has zero separate reasoning tokens. A denial terminates the attempt. Retain denied requests privately and summarize them with the `tool_denied` outcome. Only successful allowlisted reads enter the public ledger.
4. Use the plan's warmup, attempt and trial order. Measure with a monotonic clock from submission of the initial task message until grading returns or the attempt aborts. Include runtime, tool and grading work. Exclude model startup, warmup, KV resets and waiting between attempts. Trial totals sum every recorded attempt, including failures and retries.
5. Keep raw turns, clocks, token counts, successful reads, tool denials, fixture/model/build hashes, adapter source and effective settings in the privately retained packet. Give the reviewed ledger its SHA-256 and an opaque evidence UUID. An authorized reviewer checks the actual packet against the context fingerprint, confirms completeness or a partial prefix, and clears every submitted field. Publish only data you own and have approved for release. Enter hardware models, memory and OS build, keeping hostnames, serial numbers, usernames and paths in the private packet.

To publish, the authorized reviewer takes the evidence ID and retained manifest
digest from `review-pending.json`, verifies the matching packet, and adds the
actual release decision to a copy of each draft. Use the following fields and
supply measured values throughout. The context SHA-256 comes from the matching measured `plan` context.

| Field | Required value |
| --- | --- |
| `kind` | `measured` |
| `context_id`, `context_sha256` | Exact context ID and fingerprint |
| `environment` | Object with `hardware`, `os`, `backend` (`Metal` or `CUDA`), `runtime_binary_sha256`, and `adapter_sha256` |
| `review` | Object with `decision_id` and `evidence_id` canonical UUIDs, `retained_sha256`, `ownership` set to `operator-owned`, `destination` set to `public-release`, and `decision` set to `allow` |
| `attempts` | Ordered list of entries with integer `trial`, `attempt`, `wall_ns`, `generated_tokens`, `reasoning_tokens`, plus `termination`, `answer`, and `tool_reads`. Trial and attempt numbering start at 1. Record the structured `answer` only for `answered`. Use JSON null for answers on all other terminations and for unavailable generation counts after timeout/runtime interruption. Each tool read has exactly `tool` and `resource`. |

Set `termination` to `answered`, `timeout`, `runtime_error`, `tool_denied`, `invalid_output`, or `budget_exhausted`. The publisher checks the exact rubric and required page reads and derives `accepted` or `rubric_mismatch` from answered attempts. It only publishes accepted answers. Keep snapshots of incomplete work as a valid prefix. Use `timeout` when elapsed time reaches the wall deadline and `runtime_error` for interruptions before the deadline. A recorded failure with an outstanding retry is `pending_retry`. An empty context is `missing`.

```sh
python3 -B -m fastest_agent_task build /path/to/agent-task-release \
  --record reviewed-bundle.json --record reviewed-split.json
```

The build accepts at most one reviewed ledger per context and requires matching execution environments across contexts. It validates the supplied review declaration and record against the protocol. The operator and reviewer verify the private evidence packet and actual execution controls. A changed tool policy, budget, task or runtime requires a new comparison context and fingerprint. With two planned trials per context, report individual outcomes and denominators.

## Serve the pinned comparison

The release origin links to `/agent-task`. Its default report pins the two planned contexts and shows zero observed attempts. The manifest links the same HTML, Markdown, JSON, and fictional fixture bytes as the offline build.

Use the benchmark publisher's database to publish sanitized records with the approved fields described above.

```sh
python3 -B -m fastest_release migrate
task_release=$(python3 -B -m fastest_release publish-agent-task \
  --record reviewed-bundle.json --record reviewed-split.json)
```

Run the release origin with `serve --agent-task-release "$task_release"` to make this report the default. For a dedicated serving login, grant only the read function in addition to its existing permissions.

```sql
GRANT USAGE ON SCHEMA fastest_release TO fastest_release_reader;
GRANT EXECUTE ON FUNCTION fastest_release.read_agent_task_artifact(text, text) TO fastest_release_reader;
```

The report URL pins the SHA-256 of its artifact manifest. PostgreSQL stores the rendered public artifact bytes with the associated evidence IDs and an optional `--expires-at` UTC timestamp. Replays with the same approval return the same pin. Expiry or `python3 -B -m fastest_release withdraw EVIDENCE_UUID "Editorial reason"` retires the report on its next read, including old links and the manifest. The database read returns only the requested public artifact. Keep the capture directory and raw transcripts private.

## Shared CI CPU comparison

The [hosted capture workflow](../../.github/workflows/agent-task-cpu.yml) runs
both policies on one GitHub-hosted Ubuntu 24.04 x64 guest. The shared CI CPU
plan has its own context fingerprints. It uses four guest vCPUs and no GPU
offload. It preserves the fixture, rubric, exact Qwen2.5 7B GGUF shards, b5163
runtime revision, warmups, trial order, budgets and timing boundary.

```sh
python3 -B -m fastest_agent_task.capture_hosted plan
```

The job checks the official runtime archive and executable, both model
shards, effective context and batch sizes, CPU-only buffer placement, guest
affinity and cgroup quotas. It uses one Unix socket and confirms an empty KV
slot before each warmup and timed attempt. It samples guest idle and steal
time before and after the session. Physical host load is unknown, and shared
infrastructure can affect timing. The results describe this run attempt.

The job verifies the attempt sequence and monotonic elapsed times with its
private data before removing that data. It uploads the verifier receipt and
two unsigned candidates. The receipt records the source revision, run attempt,
guest checks, policy order, candidate digests and evidence IDs. Candidate
records contain reviewed-field inputs, including successful allowlisted tool
IDs and the rubric-approved fictional answer when accepted. Raw turns,
unaccepted answers, host logs and server logs stay within the job.

Choose a successful same-repository run. Verify its checkout and run attempt
using the Actions run view. Match the receipt SHA-256 with the digest printed
by the acquisition step, and replay the packet from that checkout.

```sh
gh run download "$run_id" --repo OmniMCP-AI/local-llm \
  --name "agent-task-cpu-$run_id-$run_attempt" --dir "$packet"
python3 -B -m fastest_agent_task.capture_hosted verify "$packet"
```

An authorized reviewer records the release decision separately. Copy each
candidate and add the existing `review` fields. Use its context's evidence ID
from the receipt, the verified receipt digest for `retained_sha256`, and a
canonical UUID for the actual decision. Publish those reviewed records with
`publish-agent-task` and keep the returned pin with the review. The publisher
renders the CPU cohort from those reviewed fields. The quiet-host plan keeps
its own default report and existing release pins.
