# Evidence review for single-to-multi-GPU scaling

Reviewed 2026-11-21 for [issue #25](https://github.com/OmniMCP-AI/local-llm/issues/25).
Both candidates are author-reported measurements. The project has no
independent reproduction or approved observation releases for either candidate.
The [scaling protocol](../README.md#compare-one-gpu-with-multiple-gpus)
requires the exact pinned artifact, CUDA runtime, run controls and documented
transport. Both candidates are excluded, so speedup and efficiency are
unavailable.

## Daimonion’s dual-linux benchmark, 2026-08-09

The author ran `llama-bench -p 512 -n 128 -r 3` on the same Linux rig with a
21 GB Qwen3.6-27B-uncensored-heretic-v2 i1-Q6_K model. The reported settings
include automatic flash attention, f16 KV cache and proportional layer
splitting. The NVIDIA-only Vulkan and dual Vulkan rows keep the benchmark and
backend family fixed. The CUDA-only row and mixed ROCm/CUDA row change the
backend mix along with GPU count.
[Original benchmark matrix](https://github.com/daimonionnn/multi-gpu-llm-toolkit/blob/387ed01ff2342665563703fc7df73176ceee1020/doc/benchmarks.md#L53-L70)

| Run | Active devices | Model placement | Reported tg128 (tok/s) |
| --- | --- | --- | --- |
| Vulkan baseline | 1, RTX PRO 6000 (`Vulkan1`) | Model on the NVIDIA device | 59.47 ± 0.20 |
| Dual Vulkan | 2, Radeon AI PRO R9700 (`Vulkan2`) and RTX PRO 6000 (`Vulkan1`) | Proportional layer split. Exact layer and KV placement unknown. | 42.66 ± 0.14 |

The source names llama.cpp revision `7ba604f1cb61cd14898138e9abc0b4ff2601f180`.
Its benchmark table formatter prints the arithmetic mean and standard
deviation. The three repetitions and published summaries cannot establish the
pinned median over 20 warm samples. The exact GGUF repository revision,
artifact and binary digests, controlled solo load evidence, and accepted
quality results are unavailable.
[llama-bench formatter](https://github.com/ggml-org/llama.cpp/blob/7ba604f1cb61cd14898138e9abc0b4ff2601f180/tools/llama-bench/llama-bench.cpp#L2039-L2044)

The contemporaneous host inventory names both discrete cards and lists the
NVIDIA link as PCIe Gen 5 ×16. The author later corrected the pre-rewire history
to Gen 5 ×8 with both cards on CPU lanes, then documented ×16 on the NVIDIA side
and a Gen 4 ×4 bottleneck on the AMD path after the August 17 move. The
correction supplies host history. The August 9 benchmark has no per-run PCI
address and link capture, direct-peer or host-staged classification, direction,
transfer payload, or bandwidth probe. The August 17 figures apply to a
different physical layout and workload.
[Initial host inventory](https://github.com/daimonionnn/multi-gpu-llm-toolkit/blob/387ed01ff2342665563703fc7df73176ceee1020/doc/systems.md#L41-L54),
[Rewiring and correction](https://github.com/daimonionnn/multi-gpu-llm-toolkit/blob/ab228f58924b3c3c55e1e172b71b6fbe5141d759/doc/benchmarks.md#L1519-L1573)

The original benchmark document’s SHA-256 is
`fc62da38f22fb06b0d206b5cb45ec40eee77efb55f9ffce80659999ab81cd540`.
Copyright © 2026 Daimonion. The source repository licenses its associated
documentation under MIT. The release workflow still requires an explicit rights
decision for the exact observation fields.
[Source license](https://github.com/daimonionnn/multi-gpu-llm-toolkit/blob/ab228f58924b3c3c55e1e172b71b6fbe5141d759/LICENSE)

## Andrew Leech’s dual V100 benchmark

The author’s f16-KV Gemma 4 26B-A4B table reports 99.0 tok/s on one active
V100, 90.4 tok/s with a two-V100 layer split and 76.0 tok/s with a two-V100
tensor split. The author places those rows in one `llama-bench` experiment
in Windows TCC mode and describes a dual-V100 card with PCIe ×8/×8
bifurcation and a two-link NVLink bridge. The separate single-card tables
use other runtime or KV settings. The exact solo-run binary and artifact
digests, active PCI device IDs, effective placement, warm samples, pinned
load and accepted quality results are unavailable. The author reports that
the Qwen3.6 35B-A3B entry exceeds single-card capacity. It supplies no
one-GPU throughput baseline.
[Solo benchmark tables](https://github.com/andrewleech/v100-llm-kit/blob/0ff9df3a2e7c2ad4bc14c6abffefca746b3fafdf/docs/benchmarks.md#L53-L99)

The source describes roughly 51 GB/s theoretical NVLink bandwidth and a
separate direct `cudaMemcpyPeer` probe at about 33 GB/s. The probe description
leaves payload, direction and per-link negotiation unknown. The concurrent
NCCL experiment reports a direct-pointer path and a separate host-staged
condition with P2P disabled. It uses two GPUs in both conditions with 16 or 32
parallel sequences, so it cannot identify the transport of the solo
one-to-two-GPU decode pair.
[NVLink probe](https://github.com/andrewleech/v100-llm-kit/blob/0ff9df3a2e7c2ad4bc14c6abffefca746b3fafdf/docs/07-dual-nvlink.md#L52-L69),
[Concurrent transport comparison](https://github.com/andrewleech/v100-llm-kit/blob/0ff9df3a2e7c2ad4bc14c6abffefca746b3fafdf/docs/benchmarks.md#L125-L151)

The benchmark document’s SHA-256 is
`9148e1e8efb6eb351393e200bb2beb4340e2c1a06e2c16771af1a967609a53e6`.
Copyright © 2026 Andrew Leech. The source repository licenses its associated
documentation under MIT. The release workflow still requires an explicit
rights decision for the exact observation fields.
[Source license](https://github.com/andrewleech/v100-llm-kit/blob/0ff9df3a2e7c2ad4bc14c6abffefca746b3fafdf/LICENSE)

## Capture a pair

Use Python 3.11+, `nvidia-smi` and an authorized, idle CUDA host with at least
two full physical NVIDIA GPUs. Keep the same physical host revision, OS,
drivers, libraries and host settings across both attempts. Record the revision
identifier and its machine configuration in the private evidence. Reserve the
selected GPUs and avoid simultaneous workloads. Keep the runner and weights
at stable local paths during the capture.

Build a Release CUDA `llama-bench` and `llama-server` from the clean llama.cpp
commit `84a9bf2fc2875205f0806fbbfbb66dc67204094c` (`b5163`), or verify the
official release asset against that commit. Retain the complete build revision,
configuration or asset provenance and linked-library digests in a private build
evidence file. For a local build with the CUDA toolkit installed, set
`llama_source` to the clean pinned checkout and `llama_build` to a fresh build
directory.

```sh
cmake -S "$llama_source" -B "$llama_build" -DGGML_CUDA=ON -DCMAKE_BUILD_TYPE=Release
cmake --build "$llama_build" --config Release --target llama-bench llama-server --parallel
```

Place both GGUF shards from the [exact Qwen revision](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/tree/bb5d59e06d9551d752d08b292a50eb208b07ab1f)
together under their original names. The collector checks both lengths and
digests against the [pinned text plan](../fastest_text/plan.json) before starting.
Use a model path without commas because b5163 interprets them as separators.

Get the physical GPU UUIDs and PCI addresses, then look up the corresponding
physical slot labels in the host inventory.

```sh
nvidia-smi --query-gpu=uuid,pci.bus_id,name,driver_version --format=csv,noheader
```

Create `devices.json` and replace the placeholders with those UUIDs and slot
labels. The first device is the one-GPU baseline and stays present in the
multi-GPU comparison. If an allocation uses `CUDA_VISIBLE_DEVICES`, it must
permit all selected devices by full UUID. Ask the host operator for a
UUID-form allocation if the scheduler supplies ordinal IDs.

```json
[
  {"uuid": "GPU-<first-full-uuid>", "slot": "<first-physical-slot>"},
  {"uuid": "GPU-<second-full-uuid>", "slot": "<second-physical-slot>"}
]
```

From `production/`, set `capture` to a new directory outside the repository
under a private parent. Set `bench`, `model_dir`, `devices`, and
`build_evidence` to the local paths prepared above and `host_revision` to
the stable physical host identifier.

```sh
python3 -B -m fastest_release.capture_scaling capture "$capture" \
  --bench "$bench" --model-dir "$model_dir" --devices "$devices" \
  --host-revision "$host_revision" --build-evidence "$build_evidence"
```

The b5163 runner uses the ordered UUID mask for local devices. Both invocations
use the same layer-split mode, with equal weights for the visible GPUs and
CUDA ordinal zero as the reference. The benchmark requests one 128-token
decode phase from empty KV, with one warmup token and 20 timed repetitions.
The capture runs the baseline first and continues to the comparison after a
benchmark failure. Set `--timeout` in seconds if the default 900-second budget
per attempt is insufficient. Use a new directory for a retry so the original
attempts remain available. [Pinned runner source](https://github.com/ggml-org/llama.cpp/blob/84a9bf2fc2875205f0806fbbfbb66dc67204094c/examples/llama-bench/llama-bench.cpp)

`capture.json` records shared controls, the binary digest and the build evidence
hash. Each run has a distinct ID, arguments and CUDA mask, a timestamped receipt
with the exit status, and the original JSONL and stderr with SHA-256 hashes.
Keep incomplete captures too. Compare the placement summaries with the
per-device model and KV buffers, layer placement, offload and errors in stderr.
The pinned runner emits a timing row only after the timed loop. Its progress
lines can identify a failed repetition when a timing row is absent.

## Attach an independently recorded transfer trace

Use an operator-supplied CUDA transfer trace or a documented instrumented
replay of the same decode invocation. Record the trace's run or replay
boundary, method, PCI endpoints, direction, and payload. Identify direct
peer transfers or both legs of a host-staged transfer from observations.
Record measured bandwidth where available. Use device or link specifications
for rated properties and under-load link evidence for negotiated properties.
Topology inventory and peer capability checks alone leave transfer path
unknown.

Create a JSON summary with `run_id` from `comparison/attempt.json` and a
`links` array in the [release transport shape](../README.md#compare-one-gpu-with-multiple-gpus).
Use the `scope` field to state whether the trace covers the decode itself or a
replay, and use null for unknown rated, negotiated or bandwidth data. Retain
the original trace file for review.

```sh
python3 -B -m fastest_release.capture_scaling attach-transport "$capture" \
  --trace "$trace" --links "$links"
```

The attachment validates the link schema and active PCI endpoints and retains
the trace and summary with hashes in `transport/`. The original capture
manifest records transport as unknown at collection. If no attachment exists,
the evidence still has an unknown path.

## Review and release

Use the [pinned quality task](../fastest_text/README.md#review-and-ingest-runner-evidence)
with the same model, runtime revision and each run's placement treatment.
Retain the completion and independent rubric results privately. Review
the timing logs and transfer evidence, then obtain an explicit public rights
decision for the exact fields to release.

Compute each successful run's median of `128 × 10⁹ / elapsed_ns` across its
20 timed samples. Limit the released decimal to 12 fractional digits and keep
the original sample integers in the private capture. Publish the two reviewed
observations through the [release workflow](../README.md#publish-correct-and-withdraw)
and configure the pair by release UUID. A failed baseline or unknown
multi-GPU path leaves speedup and efficiency unavailable.
