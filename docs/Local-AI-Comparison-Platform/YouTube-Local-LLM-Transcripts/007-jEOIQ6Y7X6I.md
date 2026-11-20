# 007 · Dual GPU local AI: 2 cheap cards vs 1 RTX 5090..

> Original research summary and factual claim tables — NOT a transcript or authored script.

- Source: [Dual GPU local AI: 2 cheap cards vs 1 RTX 5090..](https://www.youtube.com/watch?v=jEOIQ6Y7X6I) · Channel: KernelBrief
- Caption language: en; automatic track. Retrieval: 2026-11-20T20:49:39.282488+08:00 (Asia/Shanghai).
- Coverage: returned caption track, not audio-verified; first 320.0 ms, final 1200160.0 ms. No visual charts or manufacturer specifications independently checked.

## Original research notes

The source compares dual-card and single-card ownership through several jobs, exposing the difference between capacity aggregation and actual execution speed.

- [0:51](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=51s): The presenter places the comparison in a volatile graphics-card market. The quoted purchase conditions are a historical input to the argument, not a verified current shopping recommendation.
- [4:01](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=241s): An attributed comparison shows a dual-card arrangement trailing a larger single card on generation. Total memory and purchase savings do not automatically translate into proportional throughput.
- [7:03](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=423s): The video distinguishes splitting approaches and cites different outcomes from owner measurements. Multi-card results need the parallelism method recorded, rather than only the number and model of GPUs.
- [10:13](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=613s): PCIe slot arrangements are considered in response to upgrade questions. Whether the interconnect becomes important depends on what the selected execution strategy transfers between devices.
- [16:48](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=1008s): An upgrade example begins with a model that exceeds one card's capacity. Adding a device can therefore have a different effect from adding hardware to an already well-fitting workload.

**Platform implication.** The project should ask whether the objective is more capacity, faster single-user output or greater concurrent throughput. Represent card topology and split mode explicitly before comparing two-card builds with a flagship device.

## Hardware profile index

These are partial caption-evidence profiles,not LCZ-equivalent complete builds. No part from an LCZ reference has been inserted into a video configuration.

| Profile / role | Core evidence coverage | Linked observations |
| --- | --- | --- |
| [V007-HP-C001 — two-cardcomparison / RTX5060Ti](hardware-profiles/V007-HP-C001.md) | configuration as explicitly narrated;creator/third-party claim,not independently verified;1/6corecategories,notcomplete | 3 |
| [V007-HP-C002 — single-cardcomparison / RTX5090](hardware-profiles/V007-HP-C002.md) | configuration as explicitly narrated;creator/third-party claim,not independently verified;1/6corecategories,notcomplete | 3 |
| [V007-HP-G002 — RTX4070Super](hardware-profiles/V007-HP-G002.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 1 |
| [V007-HP-E01 — Mixed4070Super+5060Ti comparison](hardware-profiles/V007-HP-E01.md) | Caption-reported partial configuration /comparison;not a full build;1/6corecategories,notcomplete | 2 |

## Test series and run conditions

Only source-reported observations follow. Unknown conditions stay unknown;rows are not certified apples-to-apples comparisons. Single-request speed,aggregate throughput,prefill,TTFT,quality,memory,power and estimates use separate series. Ranges are preserved;no new sweep points,repeats,medians or statistics were created.

### V007-S01 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V007-HP-C002
- **Model / weights / quantization:** 27B comparison; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** llama.cpp/vLLM context;individual runtime not always isolated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V007-P001; V007-HP-C002 | decode · 75 tokens/s | same artifact/settings as pair;sharp slowdown beyond8K noted; narrated HardwareCorner measurement | [4:09](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=249s) |

### V007-S02 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V007-HP-C001, V007-HP-E01
- **Model / weights / quantization:** same27B; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** llama.cpp/vLLM context;individual runtime not always isolated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V007-P002; V007-HP-C001 | decode · 22.5 tokens/s | default/layer split; narrated measurement | [4:13](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=253s) |
| V007-P023; V007-HP-E01 | decode · 20.9 tokens/s | fourlanechipsetslot;defaultsplit; owner report | [17:08](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=1028s) |
| V007-P024; V007-HP-E01 | decode · about33 tokens/s | tensor split;manualratio; owner report | [17:12](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=1032s) |

### V007-S03 · Derived estimates / theoretical / ROI (not measured benchmarks)

- **Profile(s):** V007-HP-C001
- **Model / weights / quantization:** 18GB artifact;9GB/card in formula; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** llama.cpp/vLLM context;individual runtime not always isolated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V007-P003; V007-HP-C001 | decode ceiling · 25 tokens/s | 448GB/s percard; explicit theoretical bound | [5:44](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=344s) |

### V007-S04 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** same model;identity not given here; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** llama.cpp/vLLM context;individual runtime not always isolated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V007-P004; twoRTX3060 (profileunassigned) | decode · 33 to53 tokens/s | layer to tensor split; owner measurement | [7:09](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=429s) |

### V007-S05 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** same comparison; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** llama.cpp/vLLM context;individual runtime not always isolated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V007-P005; twoRX7900XTX (profileunassigned) | decode · 34 to47 tokens/s | layer to tensor split; owner measurement | [7:16](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=436s) |

### V007-S06 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V007-HP-G002
- **Model / weights / quantization:** 27B; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** llama.cpp/vLLM context;individual runtime not always isolated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V007-P006; twoRTX4090 (profileunassigned) | decode improvement · 21 percent | 4bit;tensor versus layer; owner measurement | [8:19](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=499s) |
| V007-P007; twoRTX4090 (profileunassigned) | decode improvement · 41 percent | 8bit;tensor versus layer; owner measurement | [8:23](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=503s) |
| V007-P022; V007-HP-G002 | decode · 11.6 tokens/s | systemRAMoffload; owner report | [17:00](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=1020s) |

### V007-S07 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** 70B dense; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** llama.cpp/vLLM context;individual runtime not always isolated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V007-P008; fourRTX4090 (profileunassigned) | decode · 21 to48 tokens/s | layer to tensor split; owner measurement | [8:29](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=509s) |

### V007-S08 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** MoE~3Bactive; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** llama.cpp/vLLM context;individual runtime not always isolated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V007-P009; multiGPU configuration not isolated (profileunassigned) | decode · 206 to141 tokens/s | tensor split hurts;do not borrow70B hardware uncritically; narrated test | [8:39](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=519s) |

### V007-S09 · Prefill / input processing

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** MoE; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** llama.cpp/vLLM context;individual runtime not always isolated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V007-P010; same MoE comparison;hardware not isolated (profileunassigned) | prefill · 4300 to2700 tokens/s | same setting transition; narrated test | [8:46](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=526s) |

### V007-S10 · Prefill / input processing

- **Profile(s):** V007-HP-C002
- **Model / weights / quantization:** 27B; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** llama.cpp/vLLM context;individual runtime not always isolated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V007-P011; V007-HP-C002 | prefill · 3750 tokens/s | short prompt; narrated measurement | [9:55](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=595s) |

### V007-S11 · Prefill / input processing

- **Profile(s):** V007-HP-C001
- **Model / weights / quantization:** same27B; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** llama.cpp/vLLM context;individual runtime not always isolated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V007-P012; V007-HP-C001 | prefill · 1168 tokens/s | defaultsplit;shortprompt; narrated measurement | [9:57](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=597s) |

### V007-S12 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** not stated; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** llama.cpp/vLLM context;individual runtime not always isolated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V007-P013; test hardware not stated (profileunassigned) | speed loss · 4–6 percent | link quartered;layer split context; tester report | [10:49](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=649s) |
| V007-P021; mixedcards;12GBcard overfilled (profileunassigned) | decode · 0.38 tokens/s | defaultsplit out-of-memory spill; owner report | [16:22](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=982s) |

### V007-S13 · Derived estimates / theoretical / ROI (not measured benchmarks)

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** not stated; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** llama.cpp/vLLM context;individual runtime not always isolated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V007-P014; PCIe4x4 theoretical link (profileunassigned) | transfer-time estimate · 5–10 seconds | 30Kprompt estimated40–80GBtraffic; creator bandwidth calculation | [11:09](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=669s) |
| V007-P015; PCIe5x8 theoretical link (profileunassigned) | transfer-time estimate · 1–2 seconds | same estimatedtraffic; creator calculation | [11:16](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=676s) |

### V007-S14 · Prefill / input processing

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** not stated; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** llama.cpp/vLLM context;individual runtime not always isolated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V007-P016; twoRTX3090 (profileunassigned) | prefill · 1616 to140 tokens/s | single-lanePCIe2;tensor split; narrated test | [11:28](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=688s) |

### V007-S15 · Aggregate / concurrent throughput (not single-request speed)

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** not stated; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** llama.cpp/vLLM context;individual runtime not always isolated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V007-P017; oneRTX3090 (profileunassigned) | aggregate throughput · 225 tokens/s | 8conversations; owner measurement | [14:33](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=873s) |

### V007-S16 · Aggregate / concurrent throughput (not single-request speed)

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** same comparison; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** llama.cpp/vLLM context;individual runtime not always isolated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V007-P018; twoRTX3090 (profileunassigned) | aggregate throughput · 519 tokens/s | multi-conversation scenario;exactconcurrency not restated; owner measurement | [14:38](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=878s) |

### V007-S17 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V007-HP-C002
- **Model / weights / quantization:** model fits eithercard;not identified; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** llama.cpp/vLLM context;individual runtime not always isolated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V007-P019; V007-HP-C002 | decode · 282 tokens/s | singlecard; engineer measurement | [15:08](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=908s) |

### V007-S18 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** same model; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** llama.cpp/vLLM context;individual runtime not always isolated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V007-P020; RTX5090+RTX4070 (profileunassigned) | decode · 204 tokens/s | mixedspeed pair; engineer measurement | [15:12](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=912s) |

## Detailed hardware profiles

Minimum fields follow motherboard/CPU/RAMmodules+speed/GPUvariant+count+VRAM/PSU/storage. “Unknown”means not reported,not an invitation to fill from a different owner or manufacturer memory. Costs are quotes/paid/estimates only where identified;no fakeBOMtotal.

### V007-HP-C001 · two-cardcomparison / RTX5060Ti

**Role:** configuration as explicitly narrated;creator/third-party claim,not independently verified. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=0s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** $1536pair in samevideo · Source-quoted price/estimate,not verified paid price · Keep literal currency;price date not established. Video publication date is not a purchase date.. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=0s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=0s) |
| RAM | — | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=0s) |
| GPU | RTX5060Ti | qty 2; PerGPUVRAM:16GBeach;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=0s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=0s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=0s) |

**Other component disclosures:** 32GBaggregateexplicitlystated;separatefrom5090host

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V007-P002 / V007-S02 | same27B; not stated; llama.cpp/vLLM context;individual runtime not always isolated | decode: 22.5 tokens/s | default/layer split; narrated measurement; [4:13](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=253s) |
| V007-P003 / V007-S03 | 18GB artifact;9GB/card in formula; not stated; llama.cpp/vLLM context;individual runtime not always isolated | decode ceiling: 25 tokens/s | 448GB/s percard; explicit theoretical bound; [5:44](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=344s) |
| V007-P012 / V007-S11 | same27B; not stated; llama.cpp/vLLM context;individual runtime not always isolated | prefill: 1168 tokens/s | defaultsplit;shortprompt; narrated measurement; [9:57](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=597s) |

---

### V007-HP-C002 · single-cardcomparison / RTX5090

**Role:** configuration as explicitly narrated;creator/third-party claim,not independently verified. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=9s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** $7488as quotedthisweek · Source-quoted price/estimate,not verified paid price · Keep literal currency;price date not established. Video publication date is not a purchase date.. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=9s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=9s) |
| RAM | — | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=9s) |
| GPU | RTX5090 | qty 1; PerGPUVRAM:32GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=9s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=9s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=9s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V007-P001 / V007-S01 | 27B comparison; not stated; llama.cpp/vLLM context;individual runtime not always isolated | decode: 75 tokens/s | same artifact/settings as pair;sharp slowdown beyond8K noted; narrated HardwareCorner measurement; [4:09](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=249s) |
| V007-P011 / V007-S10 | 27B; not stated; llama.cpp/vLLM context;individual runtime not always isolated | prefill: 3750 tokens/s | short prompt; narrated measurement; [9:55](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=595s) |
| V007-P019 / V007-S17 | model fits eithercard;not identified; not stated; llama.cpp/vLLM context;individual runtime not always isolated | decode: 282 tokens/s | singlecard; engineer measurement; [15:08](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=908s) |

---

### V007-HP-G002 · RTX4070Super

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=1010s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | RTX4070Super | PerGPUVRAM:12GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=1010s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V007-P022 / V007-S06 | 27B; not stated; llama.cpp/vLLM context;individual runtime not always isolated | decode: 11.6 tokens/s | systemRAMoffload; owner report; [17:00](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=1020s) |

---

### V007-HP-E01 · Mixed4070Super+5060Ti comparison

**Role:** Caption-reported partial configuration /comparison;not a full build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=1028s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=1028s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=1028s) |
| RAM | — | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=1028s) |
| GPU | RTX4070Super +RTX5060Ti | qty 2 heterogeneous cards; PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=1028s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=1028s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=1028s) |

**Selection / tradeoffs:** Unknown / not reported Capacity and workload placement cannot be treated as a uniform sharedVRAMpool.

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V007-P023 / V007-S02 | same27B; not stated; llama.cpp/vLLM context;individual runtime not always isolated | decode: 20.9 tokens/s | fourlanechipsetslot;defaultsplit; owner report; [17:08](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=1028s) |
| V007-P024 / V007-S02 | same27B; not stated; llama.cpp/vLLM context;individual runtime not always isolated | decode: about33 tokens/s | tensor split;manualratio; owner report; [17:12](https://www.youtube.com/watch?v=jEOIQ6Y7X6I&t=1032s) |


## Scope

Caption-only evidence;no chart/video viewing or independent hardware validation. ASR and source contradictions are retained. Full original caption text is not included. Original450claim records and99hardwarefact records are preserved byte-for-byte in their originalCSVs;new profiles/series are a separately typed organization layer.

## llmfit-aligned machine-readable records

Upstreamcommit`26450cccaf3a3f14b1822875f2473847a744a718`. Thisvideo has4losslessresearchprofiles;0have a minimalcore passingthe actualupstreamHardwareProfileJSONschema. Otherprofilesremain explicitlypartial,not paddedwithdefaults. Modelcatalogmetadata is incomplete;runconditions/prefill/concurrency/BOM/provenance remainnamespacedextensions. See[contract](llmfit/schema.md),[fieldmapping](llmfit/mapping.md),[validation](llmfit/validation-report.json). NativecompatibilityisNOTa completebuild,independentmeasurement or testedimport.
