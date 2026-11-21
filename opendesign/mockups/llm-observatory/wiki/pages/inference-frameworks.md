---
title: Inference frameworks
status: published
kind: page
summary: Compare local engines, serving frameworks, and companion projects by workload, artifact format, and platform.
---

An engine executes a model. A serving framework schedules requests and exposes an API. Interfaces, orchestration tools, and kernel libraries support specific parts of that stack. The links below describe upstream support. Check the exact release, model, backend, and card when choosing a setup.

## Local and on-device engines

- **llama.cpp** runs compatible GGUF text models via CPU or a selected GPU backend such as CUDA, Metal, or Vulkan. [Pinned release](https://github.com/ggml-org/llama.cpp/releases/tag/v1.0.0) · [Build and backend docs](https://github.com/ggml-org/llama.cpp/blob/v1.0.0/docs/build.md)
- **MLX LM** runs supported language models on Apple Silicon. **MLX Swift LM** provides Swift libraries for text and vision-language models with registered architectures and MLX-loadable SafeTensors. [MLX LM release](https://github.com/ml-explore/mlx-lm/releases/tag/v0.32.2) · [MLX Swift LM release](https://github.com/ml-explore/mlx-swift-lm/releases/tag/3.33.0) · [Swift model compatibility](https://github.com/ml-explore/mlx-swift-lm/blob/3.33.0/Libraries/MLXLMCommon/Documentation.docc/model-compatibility.md)
- **MNN** provides an on-device LLM engine and model export tools. MNN documents mobile GPU paths through Metal, OpenCL, and Vulkan. [Pinned release](https://github.com/alibaba/MNN/releases/tag/3.6.2) · [LLM engine and export tools](https://github.com/alibaba/MNN/tree/3.6.2/transformers/llm)
- **CTranslate2** runs supported Transformer models for translation, text generation, and speech recognition using converted model directories. Its prebuilt hardware scope includes x86-64 and Arm CPUs, NVIDIA CUDA, AMD RDNA 2 and RDNA 3 via ROCm, and experimental Apple MPS. [Pinned release](https://github.com/OpenNMT/CTranslate2/releases/tag/v4.9.0) · [Hardware support](https://github.com/OpenNMT/CTranslate2/blob/v4.9.0/docs/hardware_support.md)
- **whisper.cpp** is a speech recognition engine. It loads converted Whisper weights in custom ggml format and documents CPU, Apple Metal, NVIDIA CUDA, and Vulkan builds. [Pinned release](https://github.com/ggml-org/whisper.cpp/releases/tag/v1.9.5) · [Artifact format](https://github.com/ggml-org/whisper.cpp/blob/v1.9.5/models/README.md)

## Request serving

- **SGLang** serves supported generation models and documents prefix-cache reuse and continuous batching. [Pinned release](https://github.com/sgl-project/sglang/releases/tag/v0.5.23) · [Upstream documentation](https://docs.sglang.io/)
- **vLLM** serves supported models with continuous batching and configurable memory and parallelism. [Pinned release](https://github.com/vllm-project/vllm/releases/tag/v0.34.0) · [Optimization and tuning](https://docs.vllm.ai/en/latest/configuration/optimization/)
- **TensorRT-LLM** targets optimized inference and serving on supported NVIDIA GPUs. [Pinned release](https://github.com/NVIDIA/TensorRT-LLM/releases/tag/v1.3.0) · [Support matrix](https://nvidia.github.io/TensorRT-LLM/reference/support-matrix.html)

## Interfaces, orchestration, and kernels

- **Open WebUI** is a self-hosted interface for Ollama and OpenAI-compatible endpoints. The selected inference server defines language-model format and accelerator support. [Pinned release](https://github.com/open-webui/open-webui/releases/tag/v0.13.4) · [Upstream documentation](https://docs.openwebui.com/)
- **exo** orchestrates distributed inference. Its pinned release documents MLX GPU execution on macOS and CPU execution on Linux. [Pinned release](https://github.com/exo-explore/exo/releases/tag/v1.0.71) · [Platform notes](https://github.com/exo-explore/exo/blob/v1.0.71/README.md)
- **AMD AITER** supplies ROCm kernels to compatible frameworks. Its applicability depends on the operator, GPU target, and serving integration. [Pinned release](https://github.com/ROCm/aiter/releases/tag/v0.1.29.post1) · [Upstream integration and GPU targets](https://github.com/ROCm/aiter/blob/v0.1.29.post1/README.md)

The [runtime catalog](#catalog/runtimes) includes further projects and pinned versions. For platform-specific cases, see [Inference runtimes and tuning](#wiki/runtimes). For a hardware and model comparison, read the [benchmark method](#wiki/benchmark-method).
