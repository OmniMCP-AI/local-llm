---
title: awesome-local-llm
status: published
kind: guide
summary: A curated guide to local inference software, GPU resources, small models, and benchmark evidence.
---

## Inference engines

- [Inference frameworks](#wiki/inference-frameworks) covers local engines, high-concurrency servers, and companion projects.
- [llama.cpp](https://github.com/ggml-org/llama.cpp) runs compatible GGUF models. [SGLang](https://github.com/sgl-project/sglang) and [vLLM](https://github.com/vllm-project/vllm) serve supported models with batching. Check each project's backend and model documentation for the release you use.

## GPU resources

- [NVIDIA CUDA GPU list](https://developer.nvidia.com/cuda/gpus) maps card names to compute capabilities. [AMD ROCm compatibility matrix](https://rocm.docs.amd.com/en/latest/compatibility/compatibility-matrix.html) lists supported GPU and OS combinations by release.
- [Intel Compute Runtime](https://github.com/intel/compute-runtime) documents the oneAPI Level Zero and OpenCL driver. [Apple MLX](https://github.com/ml-explore/mlx) documents its Apple Silicon array framework.
- [GPU topology](#wiki/gpu-topology) shows how installed cards, active devices, memory pools, and transport differ across builds.

## Small models

- [SmolLM2-360M-Instruct](https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct) is a 360M-parameter text model. [Qwen3-0.6B](https://huggingface.co/Qwen/Qwen3-0.6B) is a 0.6B-parameter text model with thinking and non-thinking modes.
- [Granite 4.2 3B](https://huggingface.co/ibm-granite/granite-4.2-3b) is a dense text model from IBM. Explore the [model library](#models) and check the exact artifact, quantization, and context before estimating fit.

## Card-specific tuning

- [Inference runtimes and tuning](#wiki/runtimes) links documented cases for NVIDIA, AMD, Intel, and Apple, with the scope of each source.
- [vLLM optimization and tuning](https://docs.vllm.ai/en/latest/configuration/optimization/) covers memory, batching, and parallelism settings. Use the [benchmark method](#wiki/benchmark-method) to compare a change against a matching baseline.

## Start here

- [Browse the research library](#wiki/research) by use case and inspect the specific test records behind each source.

- [Read a benchmark](#wiki/benchmark-method) to understand workload, context, runtime, and measurement boundaries.
- [Explore 20 comparison methods](#wiki/comparison-methods) for hardware, performance, model evaluation, and ownership.
- [Plan a local build](#wiki/build-guide) from component compatibility and a region-specific price basis.
- [Read an evidence record](#wiki/evidence-guide) before treating a result as comparable.

## Explore the catalog

- Browse the [source catalog](#catalog), [compare by goals](#goals), or [suggest an addition](#wiki/community).

- Browse [machine profiles](#machines) by build, or start in the [model library](#models).

- [Find a viable setup](#explorer), [compare ownership and payback](#costs), or use [Price watch](#prices) for comparable whole-build quotes.
- Open the [RTX 4090 build](#machines/rtx-4090) or [Mac mini M4 Pro profile](#machines/m4-pro).
- Start from [Qwen2.5 7B Instruct](#models/qwen25-7b), [Qwen2.5 14B Instruct](#models/qwen25-14b), or [Llama 3.1 8B Instruct](#models/llama31-8b) to compare machines.

Open [Technology in motion](#wiki/technology) to explore the conceptual data path and its components.
