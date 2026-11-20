# 003 · I Tested Two $300 GPUs Against an RTX 5090 (Did NOT Expect This)

> Original research summary and factual claim tables — NOT a transcript or authored script.

- Source: [I Tested Two $300 GPUs Against an RTX 5090 (Did NOT Expect This)](https://www.youtube.com/watch?v=FVDEiBqFLBU) · Channel: Remy Runs
- Caption language: en; automatic track. Retrieval: 2026-11-20T20:49:39.282488+08:00 (Asia/Shanghai).
- Coverage: returned caption track, not audio-verified; first 200.0 ms, final 1806409.9999999998 ms. No visual charts or manufacturer specifications independently checked.

## Original research notes

A comparison of alternative ways to obtain useful model capacity shows why hardware shopping requires more than adding up advertised graphics memory.

- [1:15](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=75s): The presenter compares several ownership routes rather than only two graphics cards. The useful research question is which constraint each route solves, not which device wins universally.
- [6:06](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=366s): The demonstrated dual-card configuration operates near its available memory limit. Successful loading in one example does not establish comfortable headroom for larger caches or additional concurrent requests.
- [11:06](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=666s): The Mac discussion distinguishes installed unified memory from the allocation initially available to graphics workloads. A fit estimate needs an explicit usable-memory assumption rather than the purchase configuration alone.
- [20:27](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=1227s): A high-capacity alternative is criticized for its generation experience and energy use. The source separates having enough memory from achieving a satisfactory interactive workflow on that memory.
- [25:19](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=1519s): Cloud rental appears as an alternative for intermittent experiments. The presenter notes variable market pricing and the need to stop rented machines, making utilization central to the comparison.

**Platform implication.** Build ownership comparisons around usable capacity, sustained waiting time and utilization. The source provides scenarios to test, but its configurations, prices and performance should remain attributed claims until the original measurements are checked.

## Hardware profile index

These are partial caption-evidence profiles,not LCZ-equivalent complete builds. No part from an LCZ reference has been inserted into a video configuration.

| Profile / role | Core evidence coverage | Linked observations |
| --- | --- | --- |
| [V003-HP-G001 — P100](hardware-profiles/V003-HP-G001.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 0 |
| [V003-HP-G002 — RTX3090](hardware-profiles/V003-HP-G002.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 3 |
| [V003-HP-G003 — RTX5090](hardware-profiles/V003-HP-G003.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 1 |
| [V003-HP-G004 — R9700](hardware-profiles/V003-HP-G004.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 3 |
| [V003-HP-E01 — 48GB Macmini comparison](hardware-profiles/V003-HP-E01.md) | Caption-reported partial configuration /comparison;not a full build;2/6corecategories,notcomplete | 2 |
| [V003-HP-E02 — StrixHalo128GB comparison](hardware-profiles/V003-HP-E02.md) | Caption-reported partial configuration /comparison;not a full build;2/6corecategories,notcomplete | 3 |
| [V003-HP-E03 — DualP100 comparison](hardware-profiles/V003-HP-E03.md) | Caption-reported partial configuration /comparison;not a full build;1/6corecategories,notcomplete | 9 |

## Test series and run conditions

Only source-reported observations follow. Unknown conditions stay unknown;rows are not certified apples-to-apples comparisons. Single-request speed,aggregate throughput,prefill,TTFT,quality,memory,power and estimates use separate series. Ranges are preserved;no new sweep points,repeats,medians or statistics were created.

### V003-S01 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V003-HP-E03
- **Model / weights / quantization:** 27B; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** community llama.cpp fork; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V003-P001; V003-HP-E03 | decode · 31 tokens/s | context window over250K;output at this point not necessarily full window; narrated result;not independently verified | [5:51](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=351s) |

### V003-S02 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V003-HP-E03
- **Model / weights / quantization:** 27B; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** community fork; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V003-P002; V003-HP-E03 | decode · 23 tokens/s | 128K conversation; narrated result;not independently verified | [6:23](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=383s) |

### V003-S03 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V003-HP-E03
- **Model / weights / quantization:** 27B; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** upstream llama.cpp; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V003-P003; V003-HP-E03 | decode · 17.5 tokens/s | another owner;do not equate systems; narrated result;not independently verified | [6:52](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=412s) |

### V003-S04 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V003-HP-E03
- **Model / weights / quantization:** 27B; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** patched llama.cpp; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V003-P004; V003-HP-E03 | decode · 32.5 tokens/s | same owner upstream comparison; narrated result;not independently verified | [6:57](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=417s) |

### V003-S05 · Prefill / input processing

- **Profile(s):** V003-HP-E03
- **Model / weights / quantization:** not stated; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** P2P enabled; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V003-P005; V003-HP-E03 | prefill slowdown · more than10 times slower | driver showed working link; narrated result;not independently verified | [7:35](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=455s) |

### V003-S06 · Power / energy (boundary-dependent)

- **Profile(s):** V003-HP-G002
- **Model / weights / quantization:** not stated; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not stated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V003-P006; V003-HP-G002 | power saved · 70 W | 280W cap;under1% speed loss; narrated result;not independently verified | [9:47](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=587s) |

### V003-S07 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V003-HP-G002
- **Model / weights / quantization:** not stated; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not stated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V003-P007; V003-HP-G002 | speed loss · under1 percent | 280W power cap; narrated result;not independently verified | [9:50](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=590s) |

### V003-S08 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V003-HP-E01
- **Model / weights / quantization:** 32B dense; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not stated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V003-P008; V003-HP-E01 | decode · roughly12 tokens/s | usable GPU allocation differs from installedRAM; narrated result;not independently verified | [10:34](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=634s) |

### V003-S09 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V003-HP-E01
- **Model / weights / quantization:** sparse3B-active model; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not stated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V003-P009; V003-HP-E01 | decode · 43 tokens/s | listing claim,not creator test; narrated result;not independently verified | [11:40](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=700s) |

### V003-S10 · Prefill / input processing

- **Profile(s):** V003-HP-E03
- **Model / weights / quantization:** 27B; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not stated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V003-P010; V003-HP-E03 | prefill · 140 tokens/s | source owner configuration; narrated result;not independently verified | [14:34](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=874s) |

### V003-S11 · Derived estimates / theoretical / ROI (not measured benchmarks)

- **Profile(s):** V003-HP-E03
- **Model / weights / quantization:** 27B; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not stated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V003-P011; V003-HP-E03 | first-response wait estimate · 5 minutes | ~50K prompt;creator calculation; narrated result;not independently verified | [14:42](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=882s) |

### V003-S12 · Prefill / input processing

- **Profile(s):** V003-HP-E03
- **Model / weights / quantization:** not stated; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not stated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V003-P012; V003-HP-E03 | prefill relative rate · one third of usual speed | near-full context;owner test; narrated result;not independently verified | [15:07](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=907s) |

### V003-S13 · Derived estimates / theoretical / ROI (not measured benchmarks)

- **Profile(s):** V003-HP-E03
- **Model / weights / quantization:** not stated; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not stated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V003-P013; V003-HP-E03 | first-response wait estimate · 10 minutes | 100K prompt; narrated result;not independently verified | [15:10](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=910s) |

### V003-S14 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V003-HP-G002
- **Model / weights / quantization:** 30B/3B-active sparse; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** llama.cpp; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V003-P014; V003-HP-G002 | decode · 87 tokens/s | fully GPU resident; narrated result;not independently verified | [16:08](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=968s) |

### V003-S15 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V003-HP-G003
- **Model / weights / quantization:** 35B sparse; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not stated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V003-P015; V003-HP-G003 | decode · 194 tokens/s | owner result; narrated result;not independently verified | [17:48](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=1068s) |

### V003-S16 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V003-HP-E02
- **Model / weights / quantization:** GPT-OSS120B; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not stated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V003-P016; V003-HP-E02 | decode · 56 tokens/s | review cited; narrated result;not independently verified | [19:34](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=1174s) |

### V003-S17 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V003-HP-E02
- **Model / weights / quantization:** 70B dense; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not stated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V003-P017; V003-HP-E02 | decode · 5 tokens/s | not same model as56tok/s; narrated result;not independently verified | [20:21](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=1221s) |

### V003-S18 · Power / energy (boundary-dependent)

- **Profile(s):** V003-HP-E02
- **Model / weights / quantization:** GPT-OSS120B; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not stated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V003-P018; V003-HP-E02 | wall power · 196 W | while generating; narrated result;not independently verified | [20:39](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=1239s) |
| V003-P019; NVIDIA mini box;model not expressly named in clause (profileunassigned) | wall power · 53 W | similar speed;do not silently assume exact box SKU; narrated result;not independently verified | [20:44](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=1244s) |

### V003-S19 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V003-HP-G004
- **Model / weights / quantization:** model not established in reviewed clause; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not stated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V003-P020; V003-HP-G004 | generation · 30 words/s | source says words,not tokens; narrated result;not independently verified | [22:01](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=1321s) |

### V003-S20 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V003-HP-G004
- **Model / weights / quantization:** more compressed artifact; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not stated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V003-P021; V003-HP-G004 | generation · 40 words/s | different compression; narrated result;not independently verified | [22:06](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=1326s) |

### V003-S21 · Other reported observations / stability (not a comparable speed benchmark)

- **Profile(s):** V003-HP-G004
- **Model / weights / quantization:** not stated; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not stated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V003-P022; V003-HP-G004 | load/idle draw · 300/20 W | card versus whole-system measurement not established; narrated result;not independently verified | [22:08](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=1328s) |

### V003-S22 · Prefill / input processing

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** same test not fully specified; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not stated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V003-P023; R9700 versus5090 (profileunassigned) | long-prompt prefill · ~3 times slower | relative claim; narrated result;not independently verified | [22:50](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=1370s) |

## Detailed hardware profiles

Minimum fields follow motherboard/CPU/RAMmodules+speed/GPUvariant+count+VRAM/PSU/storage. “Unknown”means not reported,not an invitation to fill from a different owner or manufacturer memory. Costs are quotes/paid/estimates only where identified;no fakeBOMtotal.

### V003-HP-G001 · P100

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=795s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** ~$300/card in title,not verified · Source-quoted price/estimate,not verified paid price · Keep literal currency;price date not established. Video publication date is not a purchase date.. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | P100 | PerGPUVRAM:16GB percard;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=795s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** No performance row can be safely assigned to this exact profile. Product mention/recommendation is not a measured build.

---

### V003-HP-G002 · RTX3090

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=583s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | RTX3090 | PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=583s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** 280W cap;reported70W saved; reported product rating/recommendation;not whole-system measurement;NOT a PSU specification Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V003-P006 / V003-S06 | not stated; not stated; not stated | power saved: 70 W | 280W cap;under1% speed loss; narrated result;not independently verified; [9:47](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=587s) |
| V003-P007 / V003-S07 | not stated; not stated; not stated | speed loss: under1 percent | 280W power cap; narrated result;not independently verified; [9:50](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=590s) |
| V003-P014 / V003-S14 | 30B/3B-active sparse; not stated; llama.cpp | decode: 87 tokens/s | fully GPU resident; narrated result;not independently verified; [16:08](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=968s) |

---

### V003-HP-G003 · RTX5090

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=1076s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | RTX5090 | PerGPUVRAM:32GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=1076s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V003-P015 / V003-S15 | 35B sparse; not stated; not stated | decode: 194 tokens/s | owner result; narrated result;not independently verified; [17:48](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=1068s) |

---

### V003-HP-G004 · R9700

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=1328s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | R9700 | PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=1328s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** ~300Wload/~20Widle;measurement boundary unclear; reported product rating/recommendation;not whole-system measurement;NOT a PSU specification Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V003-P020 / V003-S19 | model not established in reviewed clause; not stated; not stated | generation: 30 words/s | source says words,not tokens; narrated result;not independently verified; [22:01](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=1321s) |
| V003-P021 / V003-S20 | more compressed artifact; not stated; not stated | generation: 40 words/s | different compression; narrated result;not independently verified; [22:06](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=1326s) |
| V003-P022 / V003-S21 | not stated; not stated; not stated | load/idle draw: 300/20 W | card versus whole-system measurement not established; narrated result;not independently verified; [22:08](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=1328s) |

---

### V003-HP-E01 · 48GB Macmini comparison

**Role:** Caption-reported partial configuration /comparison;not a full build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=634s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 2/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=634s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=634s) |
| RAM | 48GBmemory;type notretied in this comparison | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=634s) |
| GPU | AppleintegratedGPU;chip notretied here | PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=634s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=634s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=634s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V003-P008 / V003-S08 | 32B dense; not stated; not stated | decode: roughly12 tokens/s | usable GPU allocation differs from installedRAM; narrated result;not independently verified; [10:34](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=634s) |
| V003-P009 / V003-S09 | sparse3B-active model; not stated; not stated | decode: 43 tokens/s | listing claim,not creator test; narrated result;not independently verified; [11:40](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=700s) |

---

### V003-HP-E02 · StrixHalo128GB comparison

**Role:** Caption-reported partial configuration /comparison;not a full build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=1174s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 2/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=1174s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=1174s) |
| RAM | 128GBmemory;allocationnotprovided | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=1174s) |
| GPU | StrixHalo;exactSKU notstated | PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=1174s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=1174s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=1174s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V003-P016 / V003-S16 | GPT-OSS120B; not stated; not stated | decode: 56 tokens/s | review cited; narrated result;not independently verified; [19:34](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=1174s) |
| V003-P017 / V003-S17 | 70B dense; not stated; not stated | decode: 5 tokens/s | not same model as56tok/s; narrated result;not independently verified; [20:21](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=1221s) |
| V003-P018 / V003-S18 | GPT-OSS120B; not stated; not stated | wall power: 196 W | while generating; narrated result;not independently verified; [20:39](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=1239s) |

---

### V003-HP-E03 · DualP100 comparison

**Role:** Caption-reported partial configuration /comparison;not a full build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=351s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** About$270each used;source says$548pair. Not computed or reconciled. · Source marketquote;not creator paidpurchase · Literal$;price date/currencycode unconfirmed. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=351s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=351s) |
| RAM | — | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=351s) |
| GPU | P100 | qty 2; PerGPUVRAM:16GB each;aggregateVRAM:32GB explicitly stated | — | [source](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=351s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=351s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=351s) |

**Selection / tradeoffs:** Unknown / not reported Unitquote is approximate and does not multiply exactly to the narrated pairtotal. HostCPU/RAM/PSU not stated.

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V003-P001 / V003-S01 | 27B; not stated; community llama.cpp fork | decode: 31 tokens/s | context window over250K;output at this point not necessarily full window; narrated result;not independently verified; [5:51](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=351s) |
| V003-P002 / V003-S02 | 27B; not stated; community fork | decode: 23 tokens/s | 128K conversation; narrated result;not independently verified; [6:23](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=383s) |
| V003-P003 / V003-S03 | 27B; not stated; upstream llama.cpp | decode: 17.5 tokens/s | another owner;do not equate systems; narrated result;not independently verified; [6:52](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=412s) |
| V003-P004 / V003-S04 | 27B; not stated; patched llama.cpp | decode: 32.5 tokens/s | same owner upstream comparison; narrated result;not independently verified; [6:57](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=417s) |
| V003-P005 / V003-S05 | not stated; not stated; P2P enabled | prefill slowdown: more than10 times slower | driver showed working link; narrated result;not independently verified; [7:35](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=455s) |
| V003-P010 / V003-S10 | 27B; not stated; not stated | prefill: 140 tokens/s | source owner configuration; narrated result;not independently verified; [14:34](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=874s) |
| V003-P011 / V003-S11 | 27B; not stated; not stated | first-response wait estimate: 5 minutes | ~50K prompt;creator calculation; narrated result;not independently verified; [14:42](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=882s) |
| V003-P012 / V003-S12 | not stated; not stated; not stated | prefill relative rate: one third of usual speed | near-full context;owner test; narrated result;not independently verified; [15:07](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=907s) |
| V003-P013 / V003-S13 | not stated; not stated; not stated | first-response wait estimate: 10 minutes | 100K prompt; narrated result;not independently verified; [15:10](https://www.youtube.com/watch?v=FVDEiBqFLBU&t=910s) |


## Scope

Caption-only evidence;no chart/video viewing or independent hardware validation. ASR and source contradictions are retained. Full original caption text is not included. Original450claim records and99hardwarefact records are preserved byte-for-byte in their originalCSVs;new profiles/series are a separately typed organization layer.
