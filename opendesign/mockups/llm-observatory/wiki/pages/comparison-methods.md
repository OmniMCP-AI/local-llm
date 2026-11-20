---
title: Comparison methods
kind: guide
use_cases: hardware-selection, model-fit, model-evaluation, retrieval, multi-user-serving, distributed-inference, runtime-tuning, ownership-cost
summary: Twenty ways to compare hardware, inference, model quality, and ownership costs.
---

Start with the decision you need to make. The [method explorer](#methods) shows how to read each type of chart. Change purchase scope, usage, and cloud assumptions in the [cost and payback lab](#costs). The chart controls illustrate the methods using labeled examples. The video links give the research context for those methods.

## Purchase and fit

- **1. Budget and capability shortlist.** Filter by price, workload, and usable memory, then compare speed within the shortlist. [GPU buying comparison, 0:46](https://www.youtube.com/watch?v=2L_RB-XqisE&t=46s)
- **2. Single-card vs multi-card acquisition.** Compare total card spend and the parts needed to install and power each layout. [Dual-card experiment, 0:51](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=51s)
- **3. Itemized build vs upgrade budget.** Separate the GPU, CPU, board, memory, storage, cooling, and reused parts. Keep bundles from counting twice. [Budget server, 2:23](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=143s)
- **4. New, used and modified purchase.** Preserve market, quote date and condition, then compare warranty, support, and replacement assumptions. [New-purchase and warranty example, 10:58](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=658s)
- **5. Performance for the upgrade premium.** Measure the extra performance and price from a named baseline. Give prefill and decode separate views. [Upgrade comparison, 15:12](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=912s)
- **6. Usable memory and context headroom.** Compare runtime-usable memory with weights, cache, and workspace on each memory tier. [Unified-memory example, 11:06](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=666s)

## Inference performance

- **7. Prefill by input length.** Plot how quickly the system processes prompts of different lengths and distinguish cached from uncached prompts. [Prefill ranking example, 10:59](https://www.youtube.com/watch?v=2L_RB-XqisE&t=659s)
- **8. Single-stream decode.** Measure sustained output under a fixed workload. Label bandwidth-derived estimates and speculative decoding separately. [Bandwidth and decode, 4:14](https://www.youtube.com/watch?v=2L_RB-XqisE&t=254s)
- **9. Time to first token.** Compare how long a user waits to see output. Warm requests, cold startup, and sustained decode answer different questions. [Cold request example, 6:01](https://www.youtube.com/watch?v=MhZABCEOUWY&t=361s)
- **10. Concurrency and serving capacity.** Compare total output, per-user output, and latency as request load rises. [Eight- and sixteen-user example, 9:23](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=563s)
- **11. GPU scaling and split strategy.** Pair matched runs by card count and identify the runtime's split and active links. [Intra-host splitting, 7:03](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=423s)
- **12. Host scaling and network transport.** Track throughput and first-token latency by node count, protocol, and sharding strategy. [Mac-cluster experiment, 10:40](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=640s)
- **13. Runtime and optimization changes.** Record what changes between a baseline and an alternative. Keep release, artifact, quantization, offload, and quality settings visible. [Runtime comparison caveats, 2:55](https://www.youtube.com/watch?v=GW56S3LVb2g&t=175s)

## Evaluation and ownership

- **14. Task quality and failure categories.** Count successes, substantive errors, and unfinished attempts separately. Describe agreement with a reference model as its own metric. [Compact-model task evaluation, 3:08](https://www.youtube.com/watch?v=YcosZPh-kcI&t=188s)
- **15. Retrieval across context.** Vary input length and target placement and show repeated attempts. Leave untested cases blank. [Retrieval example, 3:46](https://www.youtube.com/watch?v=09GB4LtXUok&t=226s)
- **16. Time and effort per completed workflow.** Include startup, reasoning, tools, retries, human correction, and success under a task rubric. [Iterative task example, 18:15](https://www.youtube.com/watch?v=qW2E2ay47dw&t=1095s)
- **17. Wall energy, electricity, and cooling.** Account for active and idle system watts, hours, local electricity, and separately modeled external cooling. [Wall-power test, 20:39](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=1239s)
- **18. Cost per delivered unit.** Normalize ownership cost by delivered tokens or successful tasks under the same workload and quality requirement. [Machine cost expressed as API output volume, 22:40](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1360s)
- **19. Local purchase vs GPU rental.** Compare upfront and ongoing local spend with hourly rental and hours actually billed. [Hourly-rental discussion, 25:19](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=1519s)
- **20. Local purchase vs API spend and payback.** Track cumulative costs over time using a stated token mix, throughput, usage pattern, and electricity assumptions. [Creator's off-peak API estimate, 22:40](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1360s)

## Check what the chart can support

- Verify workload, model artifact, and test conditions before ranking measured results. Review the [benchmark method](#wiki/benchmark-method) and [evidence guide](#wiki/evidence-guide).
- Treat creator claims and power readings as attributed observations. The archived notes are selective caption-based summaries and do not establish controlled results across videos. [Research inventory](https://github.com/OmniMCP-AI/local-llm/blob/e8202e7dec1634b1529db4c123e7b3bfc2a1072b/docs/Local-AI-Comparison-Platform/YouTube-Local-LLM-Transcripts/README.md)
- Payback needs enough local capacity and an equivalent workload. The creator's API example assumes sustained use and excludes electricity. Change the assumptions in the [cost lab](#costs) to see when a crossover moves beyond the horizon or disappears.
- Inspect [GPU topology](#wiki/gpu-topology) before interpreting split or transfer performance. [Technology in motion](#wiki/technology) illustrates how a path changes.
