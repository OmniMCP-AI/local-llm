# 001 · Best GPU for local AI: the only GPUs worth buying (October 2026)..

> Original research summary and factual claim tables — NOT a transcript or authored script.

- Source: [Best GPU for local AI: the only GPUs worth buying (October 2026)..](https://www.youtube.com/watch?v=2L_RB-XqisE) · Channel: KernelBrief
- Caption language: en; manual track. Retrieval: 2026-11-20T20:49:39.282488+08:00 (Asia/Shanghai).
- Coverage: returned caption track, not audio-verified; first 280.0 ms, final 1277240.0 ms. No visual charts or manufacturer specifications independently checked.

## Original research notes

A purchasing discussion that is useful mainly for understanding how a hardware recommendation changes when the workload and market snapshot change.

- [0:46](https://www.youtube.com/watch?v=2L_RB-XqisE&t=46s): The presenter constructs a shortlist by comparing price, memory capacity and speed together. Treat this as a decision framework, rather than a durable ranking of particular cards.
- [4:14](https://www.youtube.com/watch?v=2L_RB-XqisE&t=254s): The discussion relates generation throughput to memory bandwidth, while acknowledging a software-dependent efficiency gap. A specification-derived ceiling is therefore different from an observed application result.
- [10:59](https://www.youtube.com/watch?v=2L_RB-XqisE&t=659s): Hardware eliminated by a generation-only comparison becomes competitive again when prompt processing matters. The source illustrates why one combined speed score can conceal opposing workload advantages.
- [14:14](https://www.youtube.com/watch?v=2L_RB-XqisE&t=854s): The presenter evaluates incremental throughput against the additional purchase price. These are source-specific value calculations, not independently checked quotations or transferable estimates for every model.
- [17:37](https://www.youtube.com/watch?v=2L_RB-XqisE&t=1057s): The closing market discussion emphasizes supply disruption and rapidly changing used-card prices. Historical recommendations need dated price evidence rather than an assumption that the same bargains persist.

**Platform implication.** For the existing comparison project, preserve separate capacity, prefill, decode and price observations. Allow users to choose their workload before displaying a shortlist; do not import the video's numerical rankings as verified benchmark rows.

## Hardware profile index

These are partial caption-evidence profiles,not LCZ-equivalent complete builds. No part from an LCZ reference has been inserted into a video configuration.

| Profile / role | Core evidence coverage | Linked observations |
| --- | --- | --- |
| [V001-HP-G001 — Arc A770](hardware-profiles/V001-HP-G001.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 1 |
| [V001-HP-G002 — RTX5060Ti](hardware-profiles/V001-HP-G002.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 2 |
| [V001-HP-G003 — RX9070](hardware-profiles/V001-HP-G003.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 2 |
| [V001-HP-G004 — RTX5070](hardware-profiles/V001-HP-G004.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 1 |
| [V001-HP-G005 — RTX3060](hardware-profiles/V001-HP-G005.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 1 |
| [V001-HP-G006 — RTX5070Ti](hardware-profiles/V001-HP-G006.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 1 |
| [V001-HP-G007 — RX7900XTX](hardware-profiles/V001-HP-G007.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 5 |
| [V001-HP-G008 — RTX3090](hardware-profiles/V001-HP-G008.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 7 |
| [V001-HP-G009 — RTX4090](hardware-profiles/V001-HP-G009.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 4 |
| [V001-HP-G010 — Arc Pro B60](hardware-profiles/V001-HP-G010.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 1 |
| [V001-HP-G011 — R9700](hardware-profiles/V001-HP-G011.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 2 |
| [V001-HP-G012 — Arc Pro B70](hardware-profiles/V001-HP-G012.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 1 |
| [V001-HP-G013 — RX9060XT](hardware-profiles/V001-HP-G013.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 0 |

## Test series and run conditions

Only source-reported observations follow. Unknown conditions stay unknown;rows are not certified apples-to-apples comparisons. Single-request speed,aggregate throughput,prefill,TTFT,quality,memory,power and estimates use separate series. Ranges are preserved;no new sweep points,repeats,medians or statistics were created.

### V001-S01 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V001-HP-G001, V001-HP-G002, V001-HP-G003, V001-HP-G005, V001-HP-G007, V001-HP-G008, V001-HP-G009
- **Model / weights / quantization:** 7B scoreboard model (~4GB);exact identity not stated; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** llama.cpp community scoreboard; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V001-P001; V001-HP-G001 | decode · 53 tokens/s | prompt/context/batch not fully stated; narrated result;not independently verified | [5:01](https://www.youtube.com/watch?v=2L_RB-XqisE&t=301s) |
| V001-P002; V001-HP-G002 | decode · 97 tokens/s | prompt/context/batch not fully stated; narrated result;not independently verified | [5:11](https://www.youtube.com/watch?v=2L_RB-XqisE&t=311s) |
| V001-P003; V001-HP-G003 | decode · 119 tokens/s | prompt/context/batch not fully stated; narrated result;not independently verified | [5:51](https://www.youtube.com/watch?v=2L_RB-XqisE&t=351s) |
| V001-P004; RX9070XT (profileunassigned) | decode · 131 tokens/s | prompt/context/batch not fully stated; narrated result;not independently verified | [6:15](https://www.youtube.com/watch?v=2L_RB-XqisE&t=375s) |
| V001-P005; V001-HP-G005 | decode · 81 tokens/s | prompt/context/batch not fully stated; narrated result;not independently verified | [6:39](https://www.youtube.com/watch?v=2L_RB-XqisE&t=399s) |
| V001-P006; Arc B580 (profileunassigned) | decode · 72 tokens/s | prompt/context/batch not fully stated; narrated result;not independently verified | [6:44](https://www.youtube.com/watch?v=2L_RB-XqisE&t=404s) |
| V001-P007; V001-HP-G007 | decode · 191 tokens/s | prompt/context/batch not fully stated; narrated result;not independently verified | [7:21](https://www.youtube.com/watch?v=2L_RB-XqisE&t=441s) |
| V001-P008; V001-HP-G008 | decode · 172 tokens/s | prompt/context/batch not fully stated; narrated result;not independently verified | [7:44](https://www.youtube.com/watch?v=2L_RB-XqisE&t=464s) |
| V001-P009; V001-HP-G009 | decode · 190 tokens/s | prompt/context/batch not fully stated; narrated result;not independently verified | [8:03](https://www.youtube.com/watch?v=2L_RB-XqisE&t=483s) |
| V001-P010; RTX5080 (profileunassigned) | decode · 192 tokens/s | prompt/context/batch not fully stated; narrated result;not independently verified | [8:20](https://www.youtube.com/watch?v=2L_RB-XqisE&t=500s) |

### V001-S02 · Prefill / input processing

- **Profile(s):** V001-HP-G002, V001-HP-G003, V001-HP-G004, V001-HP-G006, V001-HP-G007, V001-HP-G008, V001-HP-G009, V001-HP-G010
- **Model / weights / quantization:** 7B scoreboard model (~4GB);exact identity not stated; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** llama.cpp scoreboard; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V001-P011; V001-HP-G002 | prefill · 3913 tokens/s | scoreboard run;prompt/context/batch and runtime version not fully stated; narrated result;not independently verified | [10:43](https://www.youtube.com/watch?v=2L_RB-XqisE&t=643s) |
| V001-P012; V001-HP-G003 | prefill · 2860 tokens/s | scoreboard run;prompt/context/batch and runtime version not fully stated; narrated result;not independently verified | [10:48](https://www.youtube.com/watch?v=2L_RB-XqisE&t=648s) |
| V001-P013; V001-HP-G004 | prefill · 5783 tokens/s | scoreboard run;prompt/context/batch and runtime version not fully stated; narrated result;not independently verified | [10:54](https://www.youtube.com/watch?v=2L_RB-XqisE&t=654s) |
| V001-P014; RX9070XT (profileunassigned) | prefill · 5048 tokens/s | scoreboard run;prompt/context/batch and runtime version not fully stated; narrated result;not independently verified | [10:59](https://www.youtube.com/watch?v=2L_RB-XqisE&t=659s) |
| V001-P015; V001-HP-G007 | prefill · 3890 tokens/s | scoreboard run;prompt/context/batch and runtime version not fully stated; narrated result;not independently verified | [11:09](https://www.youtube.com/watch?v=2L_RB-XqisE&t=669s) |
| V001-P016; V001-HP-G006 | prefill · 7568 tokens/s | scoreboard run;prompt/context/batch and runtime version not fully stated; narrated result;not independently verified | [11:14](https://www.youtube.com/watch?v=2L_RB-XqisE&t=674s) |
| V001-P017; V001-HP-G008 | prefill · 5201 tokens/s | scoreboard run;prompt/context/batch and runtime version not fully stated; narrated result;not independently verified | [11:14](https://www.youtube.com/watch?v=2L_RB-XqisE&t=674s) |
| V001-P018; V001-HP-G009 | prefill · 10830 tokens/s | scoreboard run;prompt/context/batch and runtime version not fully stated; narrated result;not independently verified | [11:20](https://www.youtube.com/watch?v=2L_RB-XqisE&t=680s) |
| V001-P019; V001-HP-G010 | prefill · 275 tokens/s | B60 explicitly flash-attention on;other settings not fully stated; narrated result;not independently verified | [12:26](https://www.youtube.com/watch?v=2L_RB-XqisE&t=746s) |

### V001-S03 · Prefill / input processing

- **Profile(s):** V001-HP-G008
- **Model / weights / quantization:** Qwen3.8 27B; Exactrepository/filehash not reported unless source conditions state it; 4bit in setup discussion. KVprecision:row-specific or unknown.
- **Engine / version / execution:** runtime not isolated for these runs; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V001-P020; V001-HP-G008 | prefill · 977 tokens/s | scoreboard run;prompt/context/batch and runtime version not fully stated; narrated measurement | [11:42](https://www.youtube.com/watch?v=2L_RB-XqisE&t=702s) |

### V001-S04 · TTFT / startup latency

- **Profile(s):** V001-HP-G007, V001-HP-G008, V001-HP-G009
- **Model / weights / quantization:** Qwen3.8 27B; Exactrepository/filehash not reported unless source conditions state it; 4bit in setup discussion. KVprecision:row-specific or unknown.
- **Engine / version / execution:** runtime not isolated for these runs; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V001-P021; V001-HP-G008 | time to first token · 31 seconds | fresh30K prompt; creator calculated/example wait | [11:48](https://www.youtube.com/watch?v=2L_RB-XqisE&t=708s) |
| V001-P022; V001-HP-G009 | time to first token · 13 seconds | fresh30K prompt; creator example;measurement provenance not isolated | [11:52](https://www.youtube.com/watch?v=2L_RB-XqisE&t=712s) |
| V001-P023; V001-HP-G007 | time to first token · 40 seconds | fresh30K prompt; explicit creator estimate,not measurement | [12:02](https://www.youtube.com/watch?v=2L_RB-XqisE&t=722s) |

### V001-S05 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V001-HP-G007, V001-HP-G008, V001-HP-G009
- **Model / weights / quantization:** Qwen3.8 27B; Exactrepository/filehash not reported unless source conditions state it; 4bit in setup discussion. KVprecision:row-specific or unknown.
- **Engine / version / execution:** runtime not isolated for these runs; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V001-P024; V001-HP-G008 | decode · 40 tokens/s | short conversation; narrated measurement | [13:39](https://www.youtube.com/watch?v=2L_RB-XqisE&t=819s) |
| V001-P025; V001-HP-G008 | decode · 37 tokens/s | 32K context; narrated measurement | [13:45](https://www.youtube.com/watch?v=2L_RB-XqisE&t=825s) |
| V001-P026; V001-HP-G008 | decode · 34 tokens/s | 64K context; narrated measurement | [13:45](https://www.youtube.com/watch?v=2L_RB-XqisE&t=825s) |
| V001-P027; V001-HP-G007 | decode · 36 tokens/s | same27B;owner run; narrated owner measurement | [13:55](https://www.youtube.com/watch?v=2L_RB-XqisE&t=835s) |
| V001-P028; V001-HP-G009 | decode · 46 tokens/s | context not restated; narrated result | [14:17](https://www.youtube.com/watch?v=2L_RB-XqisE&t=857s) |
| V001-P029; RTX5090 (profileunassigned) | decode · 75 tokens/s | short conversation; narrated result | [14:30](https://www.youtube.com/watch?v=2L_RB-XqisE&t=870s) |

### V001-S06 · Memory / fit (not throughput)

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** Qwen3.8 27B; Exactrepository/filehash not reported unless source conditions state it; 4bit. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not isolated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V001-P030; hardware-independent requirement (profileunassigned) | reported model+context memory requirement · 18 GB | short conversation; creator cites HardwareCorner | [13:06](https://www.youtube.com/watch?v=2L_RB-XqisE&t=786s) |
| V001-P031; hardware-independent requirement (profileunassigned) | reported model+context memory requirement · 22 GB | 64K context; creator cites HardwareCorner | [13:10](https://www.youtube.com/watch?v=2L_RB-XqisE&t=790s) |
| V001-P032; hardware-independent requirement (profileunassigned) | reported model+context memory requirement · 26 GB | 128K context; creator cites HardwareCorner | [13:10](https://www.youtube.com/watch?v=2L_RB-XqisE&t=790s) |

### V001-S07 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V001-HP-G011
- **Model / weights / quantization:** Qwen3.6 27B; Exactrepository/filehash not reported unless source conditions state it; 5bit. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not stated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V001-P033; V001-HP-G011 | decode · 25 tokens/s | owner result;different model from primary27B comparison; narrated result;not independently verified | [15:15](https://www.youtube.com/watch?v=2L_RB-XqisE&t=915s) |

### V001-S08 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V001-HP-G012
- **Model / weights / quantization:** Qwen3.5 27B; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not stated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V001-P034; V001-HP-G012 | decode · about12 tokens/s | tester result in April;year not provided; narrated result;not independently verified | [15:46](https://www.youtube.com/watch?v=2L_RB-XqisE&t=946s) |

### V001-S09 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** 27B comparison model; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not stated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V001-P035; two RTX5060Ti16GB (profileunassigned) | decode · 22 tokens/s | 32GB aggregate;compared with single3090 at40; narrated result;not independently verified | [16:02](https://www.youtube.com/watch?v=2L_RB-XqisE&t=962s) |

### V001-S10 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V001-HP-G011
- **Model / weights / quantization:** 7B scoreboard model (~4GB);exact identity not stated; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** llama.cpp Vulkan versus ROCm; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V001-P036; V001-HP-G011 | decode · 153 versus120 tokens/s | same scoreboard comparison;Vulkan first; narrated result;not independently verified | [17:07](https://www.youtube.com/watch?v=2L_RB-XqisE&t=1027s) |

### V001-S11 · Derived estimates / theoretical / ROI (not measured benchmarks)

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** ~4GB model; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not stated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V001-P037; hypothetical448GB/s card (profileunassigned) | decode ceiling · 117 tokens/s | bandwidth/model-size estimate; theoretical estimate | [4:09](https://www.youtube.com/watch?v=2L_RB-XqisE&t=249s) |

### V001-S12 · Derived estimates / theoretical / ROI (not measured benchmarks)

- **Profile(s):** V001-HP-G007
- **Model / weights / quantization:** 7B scoreboard model (~4GB);exact identity not stated; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not stated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V001-P038; V001-HP-G007 | decode ceiling · 250 tokens/s | 960GB/s divided by~4GB; theoretical estimate | [8:46](https://www.youtube.com/watch?v=2L_RB-XqisE&t=526s) |

## Detailed hardware profiles

Minimum fields follow motherboard/CPU/RAMmodules+speed/GPUvariant+count+VRAM/PSU/storage. “Unknown”means not reported,not an invitation to fill from a different owner or manufacturer memory. Costs are quotes/paid/estimates only where identified;no fakeBOMtotal.

### V001-HP-G001 · Arc A770

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=2L_RB-XqisE&t=264s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** $399 · Source-quoted price/estimate,not verified paid price · Keep literal currency;price date not established. Video publication date is not a purchase date.. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | Arc A770 | PerGPUVRAM:16GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=2L_RB-XqisE&t=264s) |

**Other component disclosures:** 560GB/s

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V001-P001 / V001-S01 | 7B scoreboard model (~4GB);exact identity not stated; not stated; llama.cpp community scoreboard | decode: 53 tokens/s | prompt/context/batch not fully stated; narrated result;not independently verified; [5:01](https://www.youtube.com/watch?v=2L_RB-XqisE&t=301s) |

---

### V001-HP-G002 · RTX5060Ti

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=2L_RB-XqisE&t=342s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** $765 · Source-quoted price/estimate,not verified paid price · Keep literal currency;price date not established. Video publication date is not a purchase date.. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | RTX5060Ti | PerGPUVRAM:16GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=2L_RB-XqisE&t=342s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V001-P002 / V001-S01 | 7B scoreboard model (~4GB);exact identity not stated; not stated; llama.cpp community scoreboard | decode: 97 tokens/s | prompt/context/batch not fully stated; narrated result;not independently verified; [5:11](https://www.youtube.com/watch?v=2L_RB-XqisE&t=311s) |
| V001-P011 / V001-S02 | 7B scoreboard model (~4GB);exact identity not stated; not stated; llama.cpp scoreboard | prefill: 3913 tokens/s | scoreboard run;prompt/context/batch and runtime version not fully stated; narrated result;not independently verified; [10:43](https://www.youtube.com/watch?v=2L_RB-XqisE&t=643s) |

---

### V001-HP-G003 · RX9070

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=2L_RB-XqisE&t=346s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** $699 · Source-quoted price/estimate,not verified paid price · Keep literal currency;price date not established. Video publication date is not a purchase date.. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | RX9070 | PerGPUVRAM:16GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=2L_RB-XqisE&t=346s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V001-P003 / V001-S01 | 7B scoreboard model (~4GB);exact identity not stated; not stated; llama.cpp community scoreboard | decode: 119 tokens/s | prompt/context/batch not fully stated; narrated result;not independently verified; [5:51](https://www.youtube.com/watch?v=2L_RB-XqisE&t=351s) |
| V001-P012 / V001-S02 | 7B scoreboard model (~4GB);exact identity not stated; not stated; llama.cpp scoreboard | prefill: 2860 tokens/s | scoreboard run;prompt/context/batch and runtime version not fully stated; narrated result;not independently verified; [10:48](https://www.youtube.com/watch?v=2L_RB-XqisE&t=648s) |

---

### V001-HP-G004 · RTX5070

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=2L_RB-XqisE&t=365s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** $849 · Source-quoted price/estimate,not verified paid price · Keep literal currency;price date not established. Video publication date is not a purchase date.. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | RTX5070 | PerGPUVRAM:12GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=2L_RB-XqisE&t=365s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V001-P013 / V001-S02 | 7B scoreboard model (~4GB);exact identity not stated; not stated; llama.cpp scoreboard | prefill: 5783 tokens/s | scoreboard run;prompt/context/batch and runtime version not fully stated; narrated result;not independently verified; [10:54](https://www.youtube.com/watch?v=2L_RB-XqisE&t=654s) |

---

### V001-HP-G005 · RTX3060

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=2L_RB-XqisE&t=394s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** $300 used · Source-quoted price/estimate,not verified paid price · Keep literal currency;price date not established. Video publication date is not a purchase date.. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | RTX3060 | PerGPUVRAM:12GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=2L_RB-XqisE&t=394s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V001-P005 / V001-S01 | 7B scoreboard model (~4GB);exact identity not stated; not stated; llama.cpp community scoreboard | decode: 81 tokens/s | prompt/context/batch not fully stated; narrated result;not independently verified; [6:39](https://www.youtube.com/watch?v=2L_RB-XqisE&t=399s) |

---

### V001-HP-G006 · RTX5070Ti

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=2L_RB-XqisE&t=414s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** $1189 · Source-quoted price/estimate,not verified paid price · Keep literal currency;price date not established. Video publication date is not a purchase date.. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | RTX5070Ti | PerGPUVRAM:16GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=2L_RB-XqisE&t=414s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V001-P016 / V001-S02 | 7B scoreboard model (~4GB);exact identity not stated; not stated; llama.cpp scoreboard | prefill: 7568 tokens/s | scoreboard run;prompt/context/batch and runtime version not fully stated; narrated result;not independently verified; [11:14](https://www.youtube.com/watch?v=2L_RB-XqisE&t=674s) |

---

### V001-HP-G007 · RX7900XTX

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=2L_RB-XqisE&t=435s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** $950 used · Source-quoted price/estimate,not verified paid price · Keep literal currency;price date not established. Video publication date is not a purchase date.. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | RX7900XTX | PerGPUVRAM:24GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=2L_RB-XqisE&t=435s) |

**Other component disclosures:** 960GB/s

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V001-P007 / V001-S01 | 7B scoreboard model (~4GB);exact identity not stated; not stated; llama.cpp community scoreboard | decode: 191 tokens/s | prompt/context/batch not fully stated; narrated result;not independently verified; [7:21](https://www.youtube.com/watch?v=2L_RB-XqisE&t=441s) |
| V001-P015 / V001-S02 | 7B scoreboard model (~4GB);exact identity not stated; not stated; llama.cpp scoreboard | prefill: 3890 tokens/s | scoreboard run;prompt/context/batch and runtime version not fully stated; narrated result;not independently verified; [11:09](https://www.youtube.com/watch?v=2L_RB-XqisE&t=669s) |
| V001-P023 / V001-S04 | Qwen3.8 27B; 4bit in setup discussion; runtime not isolated for these runs | time to first token: 40 seconds | fresh30K prompt; explicit creator estimate,not measurement; [12:02](https://www.youtube.com/watch?v=2L_RB-XqisE&t=722s) |
| V001-P027 / V001-S05 | Qwen3.8 27B; 4bit in setup discussion; runtime not isolated for these runs | decode: 36 tokens/s | same27B;owner run; narrated owner measurement; [13:55](https://www.youtube.com/watch?v=2L_RB-XqisE&t=835s) |
| V001-P038 / V001-S12 | 7B scoreboard model (~4GB);exact identity not stated; not stated; not stated | decode ceiling: 250 tokens/s | 960GB/s divided by~4GB; theoretical estimate; [8:46](https://www.youtube.com/watch?v=2L_RB-XqisE&t=526s) |

---

### V001-HP-G008 · RTX3090

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=2L_RB-XqisE&t=459s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** $1399 used · Source-quoted price/estimate,not verified paid price · Keep literal currency;price date not established. Video publication date is not a purchase date.. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | RTX3090 | PerGPUVRAM:24GB as recommendation context;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=2L_RB-XqisE&t=459s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V001-P008 / V001-S01 | 7B scoreboard model (~4GB);exact identity not stated; not stated; llama.cpp community scoreboard | decode: 172 tokens/s | prompt/context/batch not fully stated; narrated result;not independently verified; [7:44](https://www.youtube.com/watch?v=2L_RB-XqisE&t=464s) |
| V001-P017 / V001-S02 | 7B scoreboard model (~4GB);exact identity not stated; not stated; llama.cpp scoreboard | prefill: 5201 tokens/s | scoreboard run;prompt/context/batch and runtime version not fully stated; narrated result;not independently verified; [11:14](https://www.youtube.com/watch?v=2L_RB-XqisE&t=674s) |
| V001-P020 / V001-S03 | Qwen3.8 27B; 4bit in setup discussion; runtime not isolated for these runs | prefill: 977 tokens/s | scoreboard run;prompt/context/batch and runtime version not fully stated; narrated measurement; [11:42](https://www.youtube.com/watch?v=2L_RB-XqisE&t=702s) |
| V001-P021 / V001-S04 | Qwen3.8 27B; 4bit in setup discussion; runtime not isolated for these runs | time to first token: 31 seconds | fresh30K prompt; creator calculated/example wait; [11:48](https://www.youtube.com/watch?v=2L_RB-XqisE&t=708s) |
| V001-P024 / V001-S05 | Qwen3.8 27B; 4bit in setup discussion; runtime not isolated for these runs | decode: 40 tokens/s | short conversation; narrated measurement; [13:39](https://www.youtube.com/watch?v=2L_RB-XqisE&t=819s) |
| V001-P025 / V001-S05 | Qwen3.8 27B; 4bit in setup discussion; runtime not isolated for these runs | decode: 37 tokens/s | 32K context; narrated measurement; [13:45](https://www.youtube.com/watch?v=2L_RB-XqisE&t=825s) |
| V001-P026 / V001-S05 | Qwen3.8 27B; 4bit in setup discussion; runtime not isolated for these runs | decode: 34 tokens/s | 64K context; narrated measurement; [13:45](https://www.youtube.com/watch?v=2L_RB-XqisE&t=825s) |

---

### V001-HP-G009 · RTX4090

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=2L_RB-XqisE&t=479s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** $3300 used · Source-quoted price/estimate,not verified paid price · Keep literal currency;price date not established. Video publication date is not a purchase date.. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | RTX4090 | PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=2L_RB-XqisE&t=479s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V001-P009 / V001-S01 | 7B scoreboard model (~4GB);exact identity not stated; not stated; llama.cpp community scoreboard | decode: 190 tokens/s | prompt/context/batch not fully stated; narrated result;not independently verified; [8:03](https://www.youtube.com/watch?v=2L_RB-XqisE&t=483s) |
| V001-P018 / V001-S02 | 7B scoreboard model (~4GB);exact identity not stated; not stated; llama.cpp scoreboard | prefill: 10830 tokens/s | scoreboard run;prompt/context/batch and runtime version not fully stated; narrated result;not independently verified; [11:20](https://www.youtube.com/watch?v=2L_RB-XqisE&t=680s) |
| V001-P022 / V001-S04 | Qwen3.8 27B; 4bit in setup discussion; runtime not isolated for these runs | time to first token: 13 seconds | fresh30K prompt; creator example;measurement provenance not isolated; [11:52](https://www.youtube.com/watch?v=2L_RB-XqisE&t=712s) |
| V001-P028 / V001-S05 | Qwen3.8 27B; 4bit in setup discussion; runtime not isolated for these runs | decode: 46 tokens/s | context not restated; narrated result; [14:17](https://www.youtube.com/watch?v=2L_RB-XqisE&t=857s) |

---

### V001-HP-G010 · Arc Pro B60

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=2L_RB-XqisE&t=738s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** $650 · Source-quoted price/estimate,not verified paid price · Keep literal currency;price date not established. Video publication date is not a purchase date.. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | Arc Pro B60 | PerGPUVRAM:24GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=2L_RB-XqisE&t=738s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V001-P019 / V001-S02 | 7B scoreboard model (~4GB);exact identity not stated; not stated; llama.cpp scoreboard | prefill: 275 tokens/s | B60 explicitly flash-attention on;other settings not fully stated; narrated result;not independently verified; [12:26](https://www.youtube.com/watch?v=2L_RB-XqisE&t=746s) |

---

### V001-HP-G011 · R9700

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=2L_RB-XqisE&t=900s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** $1299 list;$1683eBay · Source-quoted price/estimate,not verified paid price · Keep literal currency;price date not established. Video publication date is not a purchase date.. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | R9700 | PerGPUVRAM:32GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=2L_RB-XqisE&t=900s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V001-P033 / V001-S07 | Qwen3.6 27B; 5bit; not stated | decode: 25 tokens/s | owner result;different model from primary27B comparison; narrated result;not independently verified; [15:15](https://www.youtube.com/watch?v=2L_RB-XqisE&t=915s) |
| V001-P036 / V001-S10 | 7B scoreboard model (~4GB);exact identity not stated; not stated; llama.cpp Vulkan versus ROCm | decode: 153 versus120 tokens/s | same scoreboard comparison;Vulkan first; narrated result;not independently verified; [17:07](https://www.youtube.com/watch?v=2L_RB-XqisE&t=1027s) |

---

### V001-HP-G012 · Arc Pro B70

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=2L_RB-XqisE&t=940s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** $1300 · Source-quoted price/estimate,not verified paid price · Keep literal currency;price date not established. Video publication date is not a purchase date.. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | Arc Pro B70 | PerGPUVRAM:32GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=2L_RB-XqisE&t=940s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V001-P034 / V001-S08 | Qwen3.5 27B; not stated; not stated | decode: about12 tokens/s | tester result in April;year not provided; narrated result;not independently verified; [15:46](https://www.youtube.com/watch?v=2L_RB-XqisE&t=946s) |

---

### V001-HP-G013 · RX9060XT

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=2L_RB-XqisE&t=1129s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** $519 · Source-quoted price/estimate,not verified paid price · Keep literal currency;price date not established. Video publication date is not a purchase date.. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | RX9060XT | PerGPUVRAM:16GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=2L_RB-XqisE&t=1129s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** No performance row can be safely assigned to this exact profile. Product mention/recommendation is not a measured build.


## Scope

Caption-only evidence;no chart/video viewing or independent hardware validation. ASR and source contradictions are retained. Full original caption text is not included. Original450claim records and99hardwarefact records are preserved byte-for-byte in their originalCSVs;new profiles/series are a separately typed organization layer.

## llmfit-aligned machine-readable records

Upstreamcommit`26450cccaf3a3f14b1822875f2473847a744a718`. Thisvideo has13losslessresearchprofiles;0have a minimalcore passingthe actualupstreamHardwareProfileJSONschema. Otherprofilesremain explicitlypartial,not paddedwithdefaults. Modelcatalogmetadata is incomplete;runconditions/prefill/concurrency/BOM/provenance remainnamespacedextensions. See[contract](llmfit/schema.md),[fieldmapping](llmfit/mapping.md),[validation](llmfit/validation-report.json). NativecompatibilityisNOTa completebuild,independentmeasurement or testedimport.
