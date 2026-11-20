# 059 · Apple did what NVIDIA wouldn't - Mac Studio Clustering with Exo

> Original research summary and factual claim tables — NOT a transcript or authored script.

- Source: [Apple did what NVIDIA wouldn't - Mac Studio Clustering with Exo](https://www.youtube.com/watch?v=4l4UWZGxvoc) · Channel: jakkuh
- Caption language: en; automatic track. Retrieval: 2026-11-20T20:49:39.282488+08:00 (Asia/Shanghai).
- Coverage: returned caption track, not audio-verified; first 1964.0 ms, final 1205280.0 ms. No visual charts or manufacturer specifications independently checked.

## Original research notes

A Mac-cluster experiment is useful for distinguishing aggregate model capacity from the latency and communication behavior of a distributed inference system.

- [0:54](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=54s): The presenter emphasizes the cluster's combined memory and keeping data outside cloud services. Capacity and data-location preferences explain the experiment, but do not establish cost-effectiveness or compliance.
- [7:23](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=443s): The discussion explains a dependency between machines during distributed generation. More nodes can add communication and synchronization overhead rather than providing an automatic proportional speed increase.
- [10:40](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=640s): The experiment proposes comparing an ordinary sharding path with an RDMA-enabled path. A meaningful result needs the same model and comparable workload on both configurations.
- [13:56](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=836s): The presenter reports a change in time to first token as well as throughput. Users can experience a meaningful improvement in waiting time even when headline generation rates tell only part of the story.
- [16:56](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=1016s): An application-level coding interaction is attempted through the local setup. This gives qualitative workflow context, but a generated artifact alone is not a comprehensive distributed-model quality evaluation.

**Platform implication.** Represent node count, interconnect, sharding method and first-response latency in the existing platform. Verify operating-system support and original measurement details before treating this experiment as a general purchasing recommendation for clustered Macs.

## Hardware profile index

These are partial caption-evidence profiles,not LCZ-equivalent complete builds. No part from an LCZ reference has been inserted into a video configuration.

| Profile / role | Core evidence coverage | Linked observations |
| --- | --- | --- |
| [V059-HP-TEST — FourM3Ultra MacStudio cluster /1.5TB aggregate unifiedmemory](hardware-profiles/V059-HP-TEST.md) | creator cluster experiment;different network modes must stay distinct;1/6corecategories,notcomplete | 10 |
| [V059-HP-G001 — H200](hardware-profiles/V059-HP-G001.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 1 |
| [V059-HP-E01 — SingleMacStudio baseline](hardware-profiles/V059-HP-E01.md) | Caption-reported partial configuration /comparison;not a full build;1/6corecategories,notcomplete | 2 |
| [V059-HP-E02 — TwoMacStudio subset](hardware-profiles/V059-HP-E02.md) | Caption-reported partial configuration /comparison;not a full build;1/6corecategories,notcomplete | 7 |

## Test series and run conditions

Only source-reported observations follow. Unknown conditions stay unknown;rows are not certified apples-to-apples comparisons. Single-request speed,aggregate throughput,prefill,TTFT,quality,memory,power and estimates use separate series. Ranges are preserved;no new sweep points,repeats,medians or statistics were created.

### V059-S01 · TTFT / startup latency

- **Profile(s):** V059-HP-E01
- **Model / weights / quantization:** Llama3.3 70B FP16; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Exo/MLX;modeinconditions; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V059-P001; V059-HP-E01 | time to first token · 2 seconds | ~150GBartifact; narrated result;not independently verified | [5:10](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=310s) |

### V059-S02 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V059-HP-E01, V059-HP-E02, V059-HP-TEST
- **Model / weights / quantization:** sameLlama; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Exo/MLX;modeinconditions; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V059-P002; V059-HP-E01 | decode · 5 tokens/s | baseline; narrated result;not independently verified | [5:13](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=313s) |
| V059-P004; V059-HP-E02 | decode · 5 tokens/s | pipeline; narrated result;not independently verified | [6:36](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=396s) |
| V059-P006; V059-HP-TEST | decode · 5 tokens/s | pipeline; narrated result;not independently verified | [6:51](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=411s) |
| V059-P008; V059-HP-E02 | decode · 9 tokens/s | MLXRDMA/tensorsharding; narrated result;not independently verified | [10:12](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=612s) |

### V059-S03 · TTFT / startup latency

- **Profile(s):** V059-HP-E02, V059-HP-TEST
- **Model / weights / quantization:** sameLlama; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Exo/MLX;modeinconditions; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V059-P003; V059-HP-E02 | time to first token · 2 seconds | pipeline;notRDMA; narrated result;not independently verified | [6:34](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=394s) |
| V059-P011; V059-HP-TEST | time to first token · justover1 seconds | RDMA; narrated result;not independently verified | [13:13](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=793s) |

### V059-S04 · Power / energy (boundary-dependent)

- **Profile(s):** V059-HP-E02
- **Model / weights / quantization:** sameLlama; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Exo/MLX;modeinconditions; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V059-P005; V059-HP-E02 | power pernode · 100 W | telemetryboundarynotverified; narrated result;not independently verified | [6:42](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=402s) |

### V059-S05 · Auxiliary transport / compute / embedding (not LLM decode)

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** notmodel-specific; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Exo/MLX;modeinconditions; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V059-P007; RDMAinterconnect (profileunassigned) | communication latency reduction · 99 percent | not99%fasterinference; narrated result;not independently verified | [9:45](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=585s) |

### V059-S06 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** Mistralcodingmodel notidentifiedinclause; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Exo/MLX;modeinconditions; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V059-P009; cluster,nodecountnotretied (profileunassigned) | decode · 22 tokens/s | Ethernet;RDMAattemptcrashes;noRDMAresulthere; narrated result;not independently verified | [11:11](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=671s) |

### V059-S07 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V059-HP-TEST
- **Model / weights / quantization:** Llama3.3 70B FP16; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Exo/MLX;modeinconditions; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V059-P010; V059-HP-TEST | decode · 15.5 tokens/s | RDMA;treatnodecountcontextasqualification; narrated result;not independently verified | [13:16](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=796s) |

### V059-S08 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V059-HP-E02
- **Model / weights / quantization:** KimiK2Instruct4bit; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Exo/MLX;modeinconditions; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V059-P012; V059-HP-E02 | decode · 25 tokens/s | pipeline/earlierEthernet-equivalent; narrated result;not independently verified | [13:43](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=823s) |

### V059-S09 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V059-HP-TEST
- **Model / weights / quantization:** sameKimi; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Exo/MLX;modeinconditions; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V059-P013; V059-HP-TEST | decode · nearly35 tokens/s | distributedconfiguration; narrated result;not independently verified | [13:47](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=827s) |

### V059-S10 · TTFT / startup latency

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** sameKimi; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Exo/MLX;modeinconditions; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V059-P014; two tofourMacStudios (profileunassigned) | time to first token · 6.5 to1.5 seconds | scalingcomparison; narrated result;not independently verified | [13:59](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=839s) |

### V059-S11 · TTFT / startup latency

- **Profile(s):** V059-HP-E02
- **Model / weights / quantization:** DeepSeekV3.1 671B/37Bactive; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Exo/MLX;modeinconditions; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V059-P015; V059-HP-E02 | time to first token · 3.5 seconds | precisionnotstated; narrated result;not independently verified | [15:24](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=924s) |

### V059-S12 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V059-HP-E02, V059-HP-TEST
- **Model / weights / quantization:** sameDeepSeek; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Exo/MLX;modeinconditions; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V059-P016; V059-HP-E02 | decode · 20 tokens/s | baseline; narrated result;not independently verified | [15:26](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=926s) |
| V059-P017; V059-HP-TEST | decode · 24 tokens/s | scalestopoorlyrelative dense; narrated result;not independently verified | [15:38](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=938s) |

### V059-S13 · TTFT / startup latency

- **Profile(s):** V059-HP-TEST
- **Model / weights / quantization:** sameDeepSeek; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Exo/MLX;modeinconditions; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V059-P018; V059-HP-TEST | time to first token · under2 seconds | comparedwith3.5; narrated result;not independently verified | [15:43](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=943s) |

### V059-S14 · Power / energy (boundary-dependent)

- **Profile(s):** V059-HP-TEST
- **Model / weights / quantization:** MoE atthispoint;exactmodelnotretied; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Exo/MLX;modeinconditions; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V059-P019; V059-HP-TEST | power pernode · 115–125 W | longstory; narrated result;not independently verified | [17:29](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=1049s) |

### V059-S15 · Power / energy (boundary-dependent)

- **Profile(s):** V059-HP-TEST
- **Model / weights / quantization:** sameMoE; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Exo/MLX;modeinconditions; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V059-P020; V059-HP-TEST | aggregate power · 480 W | creatorapproximatesnodesum; narrated result;not independently verified | [17:33](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=1053s) |

### V059-S16 · Power / energy (boundary-dependent)

- **Profile(s):** V059-HP-TEST
- **Model / weights / quantization:** Llama3.3 70B FP16; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Exo/MLX;modeinconditions; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V059-P021; V059-HP-TEST | aggregate power · 600 W | denseworkload; narrated result;not independently verified | [18:10](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=1090s) |

### V059-S17 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V059-HP-G001
- **Model / weights / quantization:** Llama3.3 70B FP8; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Exo/MLX;modeinconditions; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V059-P022; V059-HP-G001 | decode · 50 tokens/s | creatorreference,notmatchedprecision; narrated result;not independently verified | [18:18](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=1098s) |

### V059-S18 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V059-HP-TEST
- **Model / weights / quantization:** sameLlama FP8; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Exo/MLX;modeinconditions; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V059-P023; V059-HP-TEST | decode · 26 tokens/s | precisionchangedfromFP16; narrated result;not independently verified | [18:32](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=1112s) |

## Detailed hardware profiles

Minimum fields follow motherboard/CPU/RAMmodules+speed/GPUvariant+count+VRAM/PSU/storage. “Unknown”means not reported,not an invitation to fill from a different owner or manufacturer memory. Costs are quotes/paid/estimates only where identified;no fakeBOMtotal.

### V059-HP-TEST · FourM3Ultra MacStudio cluster /1.5TB aggregate unifiedmemory

**Role:** creator cluster experiment;different network modes must stay distinct. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=44s) · [additional disclosure](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=192s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=44s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=44s) |
| RAM | unified/shared RAM: 1.5terabytes aggregate explicitly stated;half nodes512GB,other half256gigs as narrated at3:16–3:22 | qty 2nodes×512GB;2nodes×256GB;internal module layout not reported; Modules:2nodes×512GB;2nodes×256GB;internal module layout not reported;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=44s) |
| GPU | — | PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=44s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=44s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=44s) |
| Interconnect | Thunderbolt5/RDMA experiments versus Ethernet/pipeline modes | — | — | [source](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=44s) |

**Selection / tradeoffs:** Pool memory for large local dense/MoE models and test communication scaling. Pipeline and RDMA results differ;dense andMoE scaling/power differ. Model precision changes are not speedups at equal quality.

**Expansion / compatibility:** Unknown / not reported RDMA requires the discussed OS/beta path;an unsuccessful model/RDMA attempt is not a successful benchmark. No reproducible driver/firmware matrix supplied.

**Deployment:** macOS26.2beta;Exo/MLX paths;exact commits not stated Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** One/two/four-node modes use different subsets;which512GB/256GBnodes are in each two-node subset is not stated.

**Unknowns:** motherboard, cpu, gpu, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V059-P006 / V059-S02 | sameLlama; not stated; Exo/MLX;modeinconditions | decode: 5 tokens/s | pipeline; narrated result;not independently verified; [6:51](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=411s) |
| V059-P010 / V059-S07 | Llama3.3 70B FP16; not stated; Exo/MLX;modeinconditions | decode: 15.5 tokens/s | RDMA;treatnodecountcontextasqualification; narrated result;not independently verified; [13:16](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=796s) |
| V059-P011 / V059-S03 | sameLlama; not stated; Exo/MLX;modeinconditions | time to first token: justover1 seconds | RDMA; narrated result;not independently verified; [13:13](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=793s) |
| V059-P013 / V059-S09 | sameKimi; not stated; Exo/MLX;modeinconditions | decode: nearly35 tokens/s | distributedconfiguration; narrated result;not independently verified; [13:47](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=827s) |
| V059-P017 / V059-S12 | sameDeepSeek; not stated; Exo/MLX;modeinconditions | decode: 24 tokens/s | scalestopoorlyrelative dense; narrated result;not independently verified; [15:38](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=938s) |
| V059-P018 / V059-S13 | sameDeepSeek; not stated; Exo/MLX;modeinconditions | time to first token: under2 seconds | comparedwith3.5; narrated result;not independently verified; [15:43](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=943s) |
| V059-P019 / V059-S14 | MoE atthispoint;exactmodelnotretied; not stated; Exo/MLX;modeinconditions | power pernode: 115–125 W | longstory; narrated result;not independently verified; [17:29](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=1049s) |
| V059-P020 / V059-S15 | sameMoE; not stated; Exo/MLX;modeinconditions | aggregate power: 480 W | creatorapproximatesnodesum; narrated result;not independently verified; [17:33](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=1053s) |
| V059-P021 / V059-S16 | Llama3.3 70B FP16; not stated; Exo/MLX;modeinconditions | aggregate power: 600 W | denseworkload; narrated result;not independently verified; [18:10](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=1090s) |
| V059-P023 / V059-S18 | sameLlama FP8; not stated; Exo/MLX;modeinconditions | decode: 26 tokens/s | precisionchangedfromFP16; narrated result;not independently verified; [18:32](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=1112s) |

---

### V059-HP-G001 · H200

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=1109s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** ~$30000 US asspoken · Source-quoted price/estimate,not verified paid price · Keep literal currency;price date not established. Video publication date is not a purchase date.. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | H200 | PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=1109s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V059-P022 / V059-S17 | Llama3.3 70B FP8; not stated; Exo/MLX;modeinconditions | decode: 50 tokens/s | creatorreference,notmatchedprecision; narrated result;not independently verified; [18:18](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=1098s) |

---

### V059-HP-E01 · SingleMacStudio baseline

**Role:** Caption-reported partial configuration /comparison;not a full build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=299s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=299s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=299s) |
| RAM | — | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=299s) |
| GPU | AppleM3Ultra in cluster family;exactnode notidentified | PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=299s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=299s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=299s) |

**Selection / tradeoffs:** Unknown / not reported Which512GB/256GBnode is used is unknown. Do not assign1.5TBaggregate to one node.

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V059-P001 / V059-S01 | Llama3.3 70B FP16; not stated; Exo/MLX;modeinconditions | time to first token: 2 seconds | ~150GBartifact; narrated result;not independently verified; [5:10](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=310s) |
| V059-P002 / V059-S02 | sameLlama; not stated; Exo/MLX;modeinconditions | decode: 5 tokens/s | baseline; narrated result;not independently verified; [5:13](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=313s) |

---

### V059-HP-E02 · TwoMacStudio subset

**Role:** Caption-reported partial configuration /comparison;not a full build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=394s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=394s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=394s) |
| RAM | — | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=394s) |
| GPU | AppleM3Ultra cluster family;subsetnotidentified | PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=394s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=394s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=394s) |
| Interconnect | Pipeline/Ethernet versus RDMA modes separately reported | — | — | [source](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=394s) |

**Selection / tradeoffs:** Unknown / not reported Exact two nodes and total installed memory not stated;do not halve1.5TB as an assumed configuration.

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V059-P003 / V059-S03 | sameLlama; not stated; Exo/MLX;modeinconditions | time to first token: 2 seconds | pipeline;notRDMA; narrated result;not independently verified; [6:34](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=394s) |
| V059-P004 / V059-S02 | sameLlama; not stated; Exo/MLX;modeinconditions | decode: 5 tokens/s | pipeline; narrated result;not independently verified; [6:36](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=396s) |
| V059-P005 / V059-S04 | sameLlama; not stated; Exo/MLX;modeinconditions | power pernode: 100 W | telemetryboundarynotverified; narrated result;not independently verified; [6:42](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=402s) |
| V059-P008 / V059-S02 | sameLlama; not stated; Exo/MLX;modeinconditions | decode: 9 tokens/s | MLXRDMA/tensorsharding; narrated result;not independently verified; [10:12](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=612s) |
| V059-P012 / V059-S08 | KimiK2Instruct4bit; not stated; Exo/MLX;modeinconditions | decode: 25 tokens/s | pipeline/earlierEthernet-equivalent; narrated result;not independently verified; [13:43](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=823s) |
| V059-P015 / V059-S11 | DeepSeekV3.1 671B/37Bactive; not stated; Exo/MLX;modeinconditions | time to first token: 3.5 seconds | precisionnotstated; narrated result;not independently verified; [15:24](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=924s) |
| V059-P016 / V059-S12 | sameDeepSeek; not stated; Exo/MLX;modeinconditions | decode: 20 tokens/s | baseline; narrated result;not independently verified; [15:26](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=926s) |


## Scope

Caption-only evidence;no chart/video viewing or independent hardware validation. ASR and source contradictions are retained. Full original caption text is not included. Original450claim records and99hardwarefact records are preserved byte-for-byte in their originalCSVs;new profiles/series are a separately typed organization layer.

## llmfit-aligned machine-readable records

Upstreamcommit`26450cccaf3a3f14b1822875f2473847a744a718`. Thisvideo has4losslessresearchprofiles;0have a minimalcore passingthe actualupstreamHardwareProfileJSONschema. Otherprofilesremain explicitlypartial,not paddedwithdefaults. Modelcatalogmetadata is incomplete;runconditions/prefill/concurrency/BOM/provenance remainnamespacedextensions. See[contract](llmfit/schema.md),[fieldmapping](llmfit/mapping.md),[validation](llmfit/validation-report.json). NativecompatibilityisNOTa completebuild,independentmeasurement or testedimport.
