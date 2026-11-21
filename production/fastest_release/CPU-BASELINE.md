# Shared CI CPU baseline

The CPU baseline captures one standalone decode measurement on a GitHub-hosted Ubuntu 24.04 x86-64 runner. The receipt records the CPU model and runner image version. The runner shares physical hardware, so this result describes the specific run attempt. The quiet-host 7B text pilot uses its own model, hardware and comparison cohort.

- Model artifact: Qwen2.5 0.5B Instruct GGUF Q4_K_M at revision `9217f5db79a29953eb74d5343926648285ec7e67`. The capture checks the catalog's SHA-256 against the downloaded bytes. [Pinned GGUF](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/blob/9217f5db79a29953eb74d5343926648285ec7e67/qwen2.5-0.5b-instruct-q4_k_m.gguf)
- Runtime: official llama.cpp b5163 Ubuntu x64 archive at commit `84a9bf2fc2875205f0806fbbfbb66dc67204094c`. The capture checks both the archive and executable SHA-256 and verifies the reported build and CPU placement. [Official release](https://github.com/ggml-org/llama.cpp/releases/tag/b5163)
- Workload: one CPU thread, zero prompt tokens, a one-token warmup, then seven timed repetitions of 128 synchronized single-token steps using synthetic tokens. llama-bench clears KV before timing each repetition. The metric is the median of the seven per-sample rates `128 × 10⁹ / elapsed_ns`, expressed in tok/s with up to 12 decimal places. [Pinned benchmark source](https://github.com/ggml-org/llama.cpp/blob/84a9bf2fc2875205f0806fbbfbb66dc67204094c/examples/llama-bench/llama-bench.cpp)

## Capture and verify

The [CPU baseline workflow](../../.github/workflows/cpu-baseline.yml) runs on relevant trusted same-repository pull requests targeting `main`. Maintainers can also dispatch the registered workflow. The job checks the capture boundary, then downloads the pinned inputs and runs and replays the capture. The workflow retains only the receipt, unsigned candidate and two benchmark logs in a 14-day GitHub Actions artifact. The receipt lists the timed nanoseconds, exact invocation, input digests, runner's source commit, attempt locator and log hashes. Wall power and physical host revision have explicit missing values.

Choose a successful run, confirm the source commit and exact attempt in the run view, and download its named artifact.

```sh
gh run download "$run_id" --repo OmniMCP-AI/local-llm \
  --name "cpu-baseline-$run_id-$run_attempt" --dir "$packet"
cd production
python3 -B -m fastest_release.capture_cpu verify "$packet"
```

Match the SHA-256 of `receipt.json` with the value printed in that attempt's `Acquire, check and replay the CPU capture` step. The same digest appears in `candidate.json` as `source.revision`. This check ties the downloaded bytes to the observed Actions run. Keep the verified packet with the editorial review record before artifact expiry. A fresh workflow execution creates a new evidence ID and reports measurements from its allocated runner.

## Approve and publish locally

An editor authorized by the project to approve public benchmark rights reviews the exact run, source locator, hashes, values, hardware and optional fields. After review, copy the candidate to a reviewed observation file. Add a core `rights` object with a canonical UUID `decision_id`, `destination: public-release`, `core: allow` and the editorial `basis`. Set an explicit `rights: allow` or `rights: deny` on each optional field. Approved missing fields keep their reason. Record the decision with the retained packet. The capture job produces an unsigned candidate and uses read-only repository permissions.

Use a local benchmark publication database with the publisher connection. The publisher validates the reviewed document against the PostgreSQL metric registry. After publishing, repeat the exact command to replay the same release ID. A correction keeps the evidence UUID and follows the reviewed correction procedure.

```sh
export FASTEST_DATABASE_URL='dbname=fastest_release_cpu_baseline'
python3 -B -m fastest_release migrate
release_id=$(python3 -B -m fastest_release publish "$reviewed_observation")
python3 -B -m fastest_release publish "$reviewed_observation"
python3 -B -m fastest_release read "$release_id"
for file in benchmark.md benchmark.html chart.json table.json manifest.json; do
  python3 -B -m fastest_release artifact "$release_id" "$file" > "$release_dir/$file"
done
```

Check that the Markdown, HTML, chart and table report the same evidence ID, value and units. Compare the manifest digests with the exported files. The [benchmark release guide](../README.md#publish-correct-and-withdraw) covers correction and withdrawal.
