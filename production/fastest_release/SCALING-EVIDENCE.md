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

## Evidence needed to publish

Use an authorized multi-CUDA-GPU host for both runs. Retain one physical host
revision and the [pinned text plan’s](../fastest_text/plan.json) two GGUF digests,
llama.cpp revision, decode boundary, fixed settings and quality rubric. Record
the binary digest, OS and drivers, effective device placement and 20 warm
samples per run. Capture the actual multi-GPU path with PCI endpoints,
direction, payload and method. Keep rated and under-load negotiated link
properties distinct and record unknowns. An editor can then review the
observations and rights, publish through the existing release store, and
configure the pair by release UUID.
