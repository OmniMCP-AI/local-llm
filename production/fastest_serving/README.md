# Four-user serving comparison

Open **Team serving** from `/goals`. The built-in cohort shows both planned setups as unmeasured. A reviewed run can supply worst-user p95 response time, aggregate accepted tokens per second, and wall joules per accepted request. The exact table shows each user's sample count and p95, request outcomes, and the meter boundary. The pinned JSON includes the protocol, all captured attempts and raw meter readings.

## Capture the pinned workload

Use `four-user-fixed-token-serving@1` with the two verified Qwen GGUF shards, embedded tokenizer, and llama.cpp revision in the [text pilot pins](../fastest_text/plan.json). Build `llama-server` from that revision for the planned backend. Use one active accelerator and an otherwise quiet machine. Record the executable checksum, hardware, OS and driver, exact flags, effective backend and device placement in the retained run ledger. On the trusted test network, bind the dedicated server to its test IP and enable the slot-erasure endpoint with a private slot directory.

```sh
llama-server -m /path/to/first-verified-shard.gguf -np 4 -c 8192 -cb -t 8 \
  -b 1024 -ub 512 -ngl 99 -ctk f16 -ctv f16 \
  --host SERVER_IP --port 8080 --slot-save-path /path/to/private-slot-directory
```

Once `GET /health` returns `ok`, run the following from `production` on the separate client with Python 3.11 or later. Use the same client network boundary for each setup.

```sh
python3 -B -m fastest_serving.capture /path/to/new-private-run \
  --host SERVER_IP --port 8080 --notes 'Client host and test network boundary'
```

The client assigns users 1 through 4 and sends 1,024 integer token IDs per request to `POST /completion`. Token at zero-based index `i` is `1000 + ((i + 251 * user) % 1000)`. The request sets `n_predict: 128`, `temperature: 0`, `ignore_eos: true`, `cache_prompt: false`, `return_tokens: true` and `stream: false`. The client runs one untimed simultaneous batch after model load and confirms KV erasure for all four slots before starting the timed window. [Pinned llama-server documentation](https://github.com/ggml-org/llama.cpp/blob/84a9bf2fc2875205f0806fbbfbb66dc67204094c/examples/server/README.md)

The client schedules one request per user every six seconds for 24 batches and keeps the window open for 144 seconds. Requests that miss their 100 ms arrival tolerance are unrecorded and appear in the private trace. Timing starts as the client initiates the HTTP request and ends when the complete response body arrives. A single monotonic 5,000 ms deadline covers connection, queue, generation and transfer. A successful, valid complete response with exactly 128 returned token IDs counts as accepted. Each other response retains its outcome and reason. The private ledger `capture.json` contains the timed attempts, and `trace.jsonl` contains the warmup, slot erasures, raw timing, transport status and response filenames. The directory also preserves each exact request payload and received response body. Use `--diagnostic-reason` for deviations such as a loopback client. Keep diagnostic captures out of the reviewed cohort.

Use a calibrated cumulative energy meter at the AC input across every serving host power feed. Record meter identification and readings in joules at the start and end of the same 144-second window. Include idle gaps and unsuccessful work. The boundary excludes client power, network equipment and external cooling. Keep the meter log with the private capture and use the client's window origin to verify alignment. The client records an explicit missing reason by default. Use observed AC measurements in the reviewed record when the original meter log covers the complete window.

The least favorable of the four per-user p95 values drives the latency goal. Each p95 is the nearest rank among that user's accepted responses and requires 20 accepted responses. Capacity divides accepted output tokens by the full 144 seconds. Intensity divides the wall-meter delta by the accepted request count. Ratios are rounded to six decimal places. An incomplete schedule keeps its counts and outcomes and leaves the goal metrics unknown. A complete run can supply capacity even when its latency sample is too small or the wall meter is missing.

## Serve a reviewed run

Retain the original request trace, client and runtime logs and meter evidence. After confirming the cell, pinned inputs and protocol, copy the timed `attempts` and `duration_ms` from the private capture. Include the measured or explicitly missing `power` evidence and the reviewed runtime metadata. Use a public-safe locator with an immutable revision and a public-release allow decision covering each submitted field. Include serving records through `"serving_records": ["reviewed-serving-m4.json"]` in the [goals cohort manifest](../README.md#compare-setups-against-goals). Pass the manifest to `python3 -B -m fastest_release serve --goal-cohort PATH`. Paths are relative to the manifest. Include at most one ledger per planned setup. The JSON below illustrates an incomplete ledger. Replace every example value with reviewed evidence.

```json
{
  "kind": "measured",
  "cell_id": "apple-m4",
  "protocol": "four-user-fixed-token-serving@1",
  "artifact_sha256": ["dfce12e3862a5283ccfb88221b48480e58745165de856439950d0f22590580db", "539cf93f78e887edea1c04e2d7d8cdaca9d01dae9c9025bcb8accbe29df3d72a"],
  "runtime_revision": "84a9bf2fc2875205f0806fbbfbb66dc67204094c",
  "runtime_build": {
    "backend": "Metal",
    "binary_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "configuration": "Reviewed server, OS, driver, effective placement and hardware configuration."
  },
  "source": {"locator": "Cleared locator for the run ledger", "revision": "immutable revision"},
  "rights": {
    "decision_id": "ee436650-1a1d-45e4-995d-c3be9b443f0d",
    "destination": "public-release",
    "core": "allow",
    "basis": "Cleared allow decision covering the record."
  },
  "privacy": "local-only",
  "duration_ms": 5000,
  "attempts": [
    {"user": 1, "request": 1, "started_ms": 0, "outcome": "timeout", "elapsed_ms": 5000, "output_tokens": 0, "reason": "Client deadline elapsed."}
  ],
  "power": {"status": "missing", "reason": "The run stopped before the full meter window."}
}
```

Use `accepted`, `rejected`, `failed` or `timeout` as the outcome. Supply a reason for each unsuccessful attempt. Use the client deadline as the elapsed time for a timeout and list only the output tokens the client observed. Leave an uncaptured request out of the array so it is counted as unrecorded. Record `external` privacy if applicable. Use `rtx-4090` and `CUDA` for the other planned setup.

For measured wall energy, use this shape for `power` and replace the illustrative readings and identifier with the observed evidence.

```json
{"status":"measured","boundary":"serving-host-ac-input","meter":"Calibrated meter identifier","start_ms":0,"end_ms":144000,"start_joules":"2500","end_joules":"11800"}
```

Use `/api/v1/comparison?entry=serving` for the same decision and pinned link. The goal parameters are `user_p95` in milliseconds, `capacity` in tokens per second, and optional `wall_energy` in joules per accepted request. Use these same metric keys for `priority`, `x` and `y`. The goal manifest can be versioned and withdrawn through the same operator workflow as other goal cohorts.
