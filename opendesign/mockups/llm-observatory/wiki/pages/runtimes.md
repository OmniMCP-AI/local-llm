---
title: Inference runtimes and tuning
status: published
kind: page
summary: Follow framework releases and hardware-specific changes with their version and applicability in view.
---

A runtime, backend, driver and set of flags describe a benchmark configuration together. A newer release or a card-specific workaround can change what's possible.

## Upstream documented scope

- **NVIDIA RTX 3090 and RTX 4090.** NVIDIA lists the RTX 3090 under compute capability 8.6 and the RTX 4090 under 8.9. Check the target architecture in the runtime build when comparing a CUDA kernel or quantized backend on these cards. See [CUDA compute capability](https://developer.nvidia.com/cuda/gpus), the [RTX 3090 profile](#machines/rtx-3090), and the [RTX 4090 profile](#machines/rtx-4090).
- **AMD Instinct MI300X.** AMD's AITER example tests DeepSeek-V3 multi-head latent attention on MI300X. For the Radeon family, check the exact GPU and OS in the applicable ROCm matrix. See [AMD's MI300X example](https://rocm.blogs.amd.com/software-tools-optimization/aiter-mla/README.html) and the [ROCm compatibility matrix](https://rocm.docs.amd.com/en/latest/compatibility/compatibility-matrix.html).
- **Intel Arc B580.** The upstream llama.cpp v1.0.0 SYCL guide lists Arc B-series GPUs. Record the driver and build when testing this path on the B580. See [llama.cpp SYCL support](https://github.com/ggml-org/llama.cpp/blob/v1.0.0/docs/backend/SYCL.md) and the [B580 profile](#machines/arc-b580).
- **Apple Silicon clusters.** MLX documents JACCL over Thunderbolt 5 with macOS 26.2 or later. Record the actual Mac models, memory per node, and interconnect when comparing distributed runs. See [MLX distributed communication](https://ml-explore.github.io/mlx/build/html/usage/distributed.html) and [GPU topology](#wiki/gpu-topology).

## Reported claims awaiting verification

- **GPU-UNLOCK in video note 014.** The project identity and a matched before-and-after run are unresolved. Keep this video claim separate from vGPU virtualization projects and exclude it from performance comparisons. See the [evidence guide](#wiki/evidence-guide).

## What a usable tuning note includes

- Name the exact card, OS, driver, runtime release, model artifact, quantization, and workload.
- Record the settings that changed. Compare against the same hardware, context, and concurrency before treating a reported change as a performance improvement.
- Keep upstream documentation, community reports and matched local results distinguishable.

Browse [Inference frameworks](#wiki/inference-frameworks) for engine and serving choices, the [source catalog](#catalog) for related hardware and models, or [Compare by goals](#goals) to find evidence for the workload you plan to run.
