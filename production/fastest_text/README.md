# Two-machine text pilot

The default report covers an Apple M4 with Metal and a GeForce RTX 4090 with CUDA. The pinned runtime and exact model shards ran on a local 24 GiB Apple M4 under ambient desktop GPU load. The capture is private. The planned Apple M4 timing cell requires a quiet-host run and public release approval. A separate Chinese completion awaits independent rubric review. The RTX 4090 cell requires access to an authorized host or operator-run evidence. Both public cells currently have zero approved timing samples and quality ratings.

From the `production` directory with Python 3.11 or later, build to a new directory.

```sh
python3 -B -m fastest_text build /path/to/text-pilot-v1
```

The resulting `text-pilot.md`, `text-pilot.html`, and typed `text-pilot.json` describe the same two cells. `manifest.json` gives the SHA-256 of each file. The HTML page has a static table and links to the Markdown and JSON. The output is a static report bundle. An operator controls distribution and replaces or removes every published copy if a correction or rights withdrawal applies.

## Run the fixed-token protocol

[The protocol and artifact pins](plan.json) identify the official Qwen repository revision, both Q4_K_M shard paths and digests, the embedded tokenizer, and llama.cpp commit `84a9bf2fc2875205f0806fbbfbb66dc67204094c` (`b5163`). Build `llama-bench` and `llama-server` from that clean commit for Metal or CUDA, or use the [official b5163 release](https://github.com/ggml-org/llama.cpp/releases/tag/b5163) and verify its target commit. Save the build configuration or release asset metadata, the package checksum if applicable, and the executable and linked library checksums. Match the benchmark row's build commit and the server version to the pinned revision.

Download the shards from the [pinned Qwen revision](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/tree/bb5d59e06d9551d752d08b292a50eb208b07ab1f) and verify both exact byte lengths and SHA-256 values. The published bundle includes model identity and source metadata. Read Qwen's artifact license and notices before distributing any weights.

Use a quiet host and an explicit single visible CUDA device for the RTX 4090. Check the logs for the actual backend, GPU SKU, active device and offload. Run these phases sequentially and keep the raw JSONL, stderr, exit status, command and environment details. Run from a directory dedicated to the private run records. Set `model` to the first verified shard and `bench` to the verified executable.

```sh
"$bench" -m "$model" -p 1024 -n 0 -b 1024 -ub 512 -t 8 -ngl 99 -ctk f16 -ctv f16 \
  -nkvo 0 -fa 0 -mmp 1 -sm layer -mg 0 -r 20 --progress -v -o jsonl \
  > prefill.jsonl 2> prefill.stderr
"$bench" -m "$model" -p 0 -n 128 -b 1024 -ub 512 -t 8 -ngl 99 -ctk f16 -ctv f16 \
  -nkvo 0 -fa 0 -mmp 1 -sm layer -mg 0 -r 20 --progress -v -o jsonl \
  > decode.jsonl 2> decode.stderr
```

The runner warms each phase once and clears KV before every timed repetition. Decode starts with empty KV. Context capacity is requested as the total token count for each phase, subject to runtime allocation padding. Token lengths and the sampling method match across hosts. The runtime generates token IDs with platform-specific RNG. Timing starts after model load and KV clear, covers the selected synchronized phase and ends before unloading. Prefill and decode use separate microbenchmarks, so latency fields carry an explicit missing status. A future request-timing probe would need its own protocol and recorded client boundary. [Pinned runner implementation](https://github.com/ggml-org/llama.cpp/blob/84a9bf2fc2875205f0806fbbfbb66dc67204094c/examples/llama-bench/llama-bench.cpp)

## Review and ingest runner evidence

Keep the original logs and output under the applicable access rights. Check the reported build commit, each shard digest, the fixed lengths and the runtime settings before reviewing records. Confirm the actual device placement in the run logs. The runner can show timings despite runtime errors, so check stderr before treating timing entries as successful. Record OS, driver, hardware configuration, device placement, backend and binary provenance. Retain incomplete phases as such. When a process stops before producing valid output, capture any identifiable timed failure with its phase, ordinal and reason. The planned total is a target.

Use the [synthetic fixture](../fixtures/synthetic-text-pilot.json) as the JSON shape for the reviewed record. Use `kind: measured` for actual runs and use real values throughout. Submit at most one reviewed ledger per machine. List attempts in per-phase order, numbered from 1. Copy every eligible successful `samples_ns` integer from the appropriate runner row into its own attempt. Give OOM, timeout and other observed failures their own attempts and a short reviewed reason. Keep earlier successful observations when adding later attempts. Preserve the source locator and immutable revision for the retained execution and review evidence.

The Chinese product-copy prompt and rubric are original. Capture one completion per run from the same verified GGUF and llama.cpp revision under the pinned settings in the plan. Save the prompt, exact output, request options, runtime flags, source and output checksum in the private evaluation ledger. Present each output to independent reviewers under an opaque ID before disclosing the machine. Submit each rubric rating with that output ID, its SHA-256, a pseudonymous reviewer ID and a cleared note. A repeated completion can have its own output ID even when its text matches a previous run. The report counts reviewed outputs, individual ratings, disagreements and outputs that pass every criterion for every reviewer.

For the quality run, start the pinned `llama-server` on loopback or an owned Unix socket with `--jinja --parallel 1`. Keep the model's embedded chat template. Send one user message to `/v1/chat/completions` with `temperature: 0` and `max_tokens: 256`. Retain the request and response, the resolved prompt from `/apply-template`, and the SHA-256 of the UTF-8 bytes of `choices[0].message.content` as returned, without a trailing newline added by the capture tool. Stop the server after capturing the response.

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
