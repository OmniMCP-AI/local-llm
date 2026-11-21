# Two-machine text pilot

The default report covers an Apple M4 with Metal and a GeForce RTX 4090 with CUDA. The pinned runtime and exact model shards ran on a local 24 GiB Apple M4 under ambient desktop GPU load. The capture is private. The planned Apple M4 timing cell requires a quiet-host run and public release approval. A separate Chinese completion awaits independent rubric review. The RTX 4090 cell requires access to an authorized host or operator-run evidence. Both public cells currently have zero approved timing samples and quality ratings.

On the release origin, open `/text-pilot` from either machine's profile or the Qwen model profile. The default route redirects to the report pinned by the SHA-256 of its manifest. When the current goals cohort has reviewed records, the route opens that cohort's pinned report and checks its publication rights.

From the `production` directory with Python 3.11 or later, build to a new directory.

```sh
python3 -B -m fastest_text build /path/to/text-pilot-v1
```

The resulting `text-pilot.md`, `text-pilot.html`, and typed `text-pilot.json` describe the same two cells. `manifest.json` gives the SHA-256 of each file. The HTML page has a static table and links to the Markdown and JSON. The output is a static report bundle. An operator controls distribution and replaces or removes every published copy if a correction or rights withdrawal applies.

## Run the fixed-token protocol

[The protocol and artifact pins](plan.json) identify the official Qwen repository revision, both Q4_K_M shard paths and digests, the embedded tokenizer, and llama.cpp commit `84a9bf2fc2875205f0806fbbfbb66dc67204094c` (`b5163`). Build `llama-bench` and `llama-server` from that clean commit for Metal or CUDA, or use the [official b5163 release](https://github.com/ggml-org/llama.cpp/releases/tag/b5163) and verify its target commit. Save the build configuration or release asset metadata, the package checksum if applicable, and the executable and linked library checksums. Match the benchmark row's build commit and the server version to the pinned revision.

Download the shards from the [pinned Qwen revision](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/tree/bb5d59e06d9551d752d08b292a50eb208b07ab1f) and verify both exact byte lengths and SHA-256 values. The published bundle includes model identity and source metadata. Read Qwen's artifact license and notices before distributing any weights.

On an authorized, otherwise idle machine, place the two local shards in one directory. Prepare a private build evidence file with the clean checkout or official release asset provenance, build flags, linked-library paths and checksums, machine configuration, and OS/driver details. Use a stable operator-assigned host revision for the physical configuration. Start from the `production` directory.

Apple M4 with Metal

```sh
python3 -B -m fastest_text capture /path/to/private/m4-run-01 \
  --cell apple-m4 --bench /path/to/b5163/llama-bench \
  --model-dir /path/to/shards --host-revision m4-host-1 \
  --build-evidence /path/to/private/m4-build.txt --quiet-host
```

GeForce RTX 4090 with CUDA

```sh
CUDA_VISIBLE_DEVICES=GPU-00000000-1111-2222-3333-444444444444 \
  python3 -B -m fastest_text capture /path/to/private/rtx4090-run-01 \
    --cell rtx-4090 --bench /path/to/b5163/llama-bench \
    --model-dir /path/to/shards --host-revision rtx4090-host-1 \
    --build-evidence /path/to/private/cuda-build.txt --quiet-host
```

Replace the example CUDA UUID with the allocated card's UUID from `nvidia-smi -L`. A single allocated device ordinal also works. The tool preserves the chosen mask. The `--quiet-host` flag records the operator's attestation. Run two commands at different times if they share a host or other resources.

The capture records the executable SHA-256 and checks its b5163 build footer with a zero-work probe. It checks both shard sizes and streams their SHA-256 digests before either benchmark phase. It then runs 20 warm prefill repetitions and 20 warm decode repetitions in that order, with a 900-second deadline per phase by default. Review the copied build evidence alongside the runner's self-reported build commit. Both benchmark rows must match the verified build and pinned settings.

The runner warms each phase once and clears KV before every timed repetition. Decode starts with empty KV. Context capacity is requested as the total token count for each phase, subject to runtime allocation padding. Token lengths and the sampling method match across hosts. The runtime generates token IDs with platform-specific RNG. Timing starts after model load and KV clear, covers the selected synchronized phase and ends before unloading. Both latency fields retain an explicit missing status with zero samples. A request-timing probe would need its own protocol and client boundary. [Pinned runner implementation](https://github.com/ggml-org/llama.cpp/blob/84a9bf2fc2875205f0806fbbfbb66dc67204094c/examples/llama-bench/llama-bench.cpp)

Inspect `capture.json` for the verified build and artifact, phase outcomes and actual sample counts. The private phase folders hold the command, exit status, raw JSONL and stderr hashes, logged accelerator model and buffer placement, progress ordinals, and eligible timings. Metal and CUDA require one matching device, positive model and KV allocations on that device, full layer offload and the expected context. Host model buffers can still appear alongside accelerator buffers. If progress survives a timeout or early exit, the ledger records the repetitions that had started. Only verified durations count as samples. An attributable runtime error remains tied to its repetition, even if the runner emits a duration for it.

An incomplete capture returns a nonzero status and keeps its evidence. Correct the blocker and use a new output directory for a retry. Keep the capture directory and build evidence private until reviewing the fields intended for release.

## Capture private streaming latency

The Chinese task has a separate latency protocol. On the same authorized quiet host, use the pinned b5163 `llama-server` binary and the same two verified shards. Use a short output path to fit the Unix socket path limit.

```sh
python3 -B -m fastest_text capture-latency /path/to/private/m4-latency-01 \
  --cell apple-m4 --server /path/to/b5163/llama-server \
  --model-dir /path/to/shards --host-revision m4-host-1 \
  --build-evidence /path/to/private/m4-build.txt --quiet-host
```

For `--cell rtx-4090`, set the same single-device `CUDA_VISIBLE_DEVICES` mask as for the fixed-token run. The command launches one private server on an owned Unix socket, resolves the embedded chat template through `/apply-template`, then sends the resulting prompt to native `/completion`. It uses greedy decoding with a 256-token cap and records the actual prompt and output token counts reported by the server. It checks for a full accelerator offload, clears slot 0 before each request and disables prefix reuse. One warmup precedes the single timed request. Model loading, template resolution, the warmup and KV resets occur outside the timing boundary.

Time starts immediately before submitting the request. TTFT ends when the client receives a complete SSE event containing the token ID for generated ordinal 1. b5163 can buffer partial UTF-8 before emitting it, so a stream whose first emitted ordinal is higher has no TTFT sample. The first visible answer measurement ends at the first complete frame with printable non-whitespace answer text, before any browser rendering. The HTTP header and control frames supply no token timings. A complete request can yield either, both, or neither measurement. A timeout or missing terminal event can retain observed timestamps but yields zero eligible samples. [Pinned sampling and stream serializer](https://github.com/ggml-org/llama.cpp/blob/84a9bf2fc2875205f0806fbbfbb66dc67204094c/examples/server/server.cpp)

The private directory keeps `latency.json`, the byte-exact request, raw received SSE lines, the effective template input, startup and runtime verification logs, and SHA-256 hashes. A complete, nonempty answer also produces `response.json` for the existing `review-packet` command. The quality judgment still requires independent reviewers. This operator capture leaves the fixed-token phases, publication workflow and current public results as recorded.

## Review and ingest runner evidence

Keep the original logs and output under the applicable access rights. Check the reported build commit, each shard digest, the fixed lengths and the runtime settings before reviewing records. Confirm the actual device placement in the run logs. The runner can show timings despite runtime errors, so check stderr before treating timing entries as successful. Record OS, driver, hardware configuration, device placement, backend and binary provenance. Retain incomplete phases as such. When a process stops before producing valid output, capture any identifiable timed failure with its phase, ordinal and reason. The planned total is a target.

Use the [synthetic fixture](../fixtures/synthetic-text-pilot.json) as the JSON shape for the reviewed record. Use `kind: measured` for actual runs and use real values throughout. Submit at most one reviewed ledger per machine. List attempts in per-phase order, numbered from 1. Copy every eligible successful `samples_ns` integer from the appropriate runner row into its own attempt. Give OOM, timeout and other observed failures their own attempts and a short reviewed reason. Keep earlier successful observations when adding later attempts. Preserve the source locator and immutable revision for the retained execution and review evidence.

The Chinese product-copy prompt and rubric are original. Capture one completion per run from the same verified GGUF and llama.cpp revision under the pinned settings in the plan. Save the prompt, exact output, request options, runtime flags, source and output checksum in the private evaluation ledger. Present each output to independent reviewers under an opaque ID before disclosing the machine. Submit each rubric rating with that output ID, its SHA-256, a pseudonymous reviewer ID and a cleared note. A repeated completion can have its own output ID even when its text matches a previous run. The report counts reviewed outputs, individual ratings, disagreements and outputs that pass every criterion for every reviewer.

For the quality run, start the pinned `llama-server` on loopback or an owned Unix socket with `--jinja --parallel 1`. Keep the model's embedded chat template. Send one user message to `/v1/chat/completions` with `temperature: 0` and `max_tokens: 256`. Retain the request and response, the resolved prompt from `/apply-template`, and the SHA-256 of the UTF-8 bytes of `choices[0].message.content` as returned, without a trailing newline added by the capture tool. Stop the server after capturing the response.

Prepare the independent review from one retained response file per completion. Pass both machines' responses together when available.

```sh
python3 -B -m fastest_text review-packet /path/to/private/quality-review-01 \
  --response /path/to/private/m4-response.json \
  --response /path/to/private/rtx4090-response.json
```

Give reviewers a copy of `review-packet.json`. It contains the original prompt, the criteria and randomly ordered responses with opaque IDs, exact text hashes and blank rating forms. Keep `private-map.json` with the operator's raw evaluation evidence. After independent reviewers return their ratings, use that map to join them to the correct machine.

Use a public release allow decision covering every field in the submitted record, including the operational notes, source locator, raw durations and pseudonymous reviews. Use public-safe locators and phrasing. Raw logs may include usernames, paths, identifiers or private remarks. Keep them in their original private location when the rights decision does not cover those details.

```sh
python3 -B -m fastest_text build /path/to/text-pilot-v2 \
  --record reviewed-m4.json --record reviewed-rtx4090.json
```

When a cell still has no reviewed record, omit its `--record` argument. Exact artifact, protocol, build settings and rights checks run before output generation. The same successful attempt collection supplies the raw data and median phase throughput. Missing phases and all captured failures stay visible. The fixture is accepted only in explicit demo mode.

```sh
python3 -B -m fastest_text build /path/to/text-pilot-demo \
  --demo --record fixtures/synthetic-text-pilot.json
```
