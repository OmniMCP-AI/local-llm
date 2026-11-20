# 029 · I listened to your advice and bought two 2080Ti 22GBs! Dual cards + NVLink for AI, the value for ...

> Original research summary and factual claim tables — NOT a transcript or authored script.

- Source: [I listened to your advice and bought two 2080Ti 22GBs! Dual cards + NVLink for AI, the value for ...](https://www.youtube.com/watch?v=1xmOTSUpBL0) · Channel: 司波图
- Caption language: en-US; automatic track. Retrieval: 2026-11-20T20:49:39.282488+08:00 (Asia/Shanghai).
- Coverage: returned caption track, not audio-verified; first 100.0 ms, final 1232530.0 ms. No visual charts or manufacturer specifications independently checked.

## Original research notes

A dual modified-card experiment explores how interconnects and runtime features interact, rather than supporting a simple claim that adding a bridge always accelerates local AI.

- [0:53](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=53s): The creator discloses purchasing modified cards and an interconnect for the test. Such hardware has different acquisition and support characteristics from standard new products with ordinary warranties.
- [3:55](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=235s): Gaming compatibility is discussed separately from inference. A benefit or limitation in one software ecosystem should not be transferred automatically into another workload category.
- [7:03](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=423s): The inference discussion relates context length to cache pressure and out-of-memory behavior. Peak generation rate without its context and memory headroom is an incomplete result.
- [10:19](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=619s): A runtime parameter changes reported single-stream and multi-stream behavior even without a bridge. Software configuration can confound an apparent hardware-interconnect comparison if it is not held constant.
- [16:59](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=1019s): An attention implementation is identified as important to the old architecture's usefulness. Runtime-version support can change the practical value of hardware long after the original product release.

**Platform implication.** Store modification status, connection topology, concurrency, context and runtime settings together. Use the video to design a controlled comparison matrix, not to infer a universal recommendation for modified cards or a guaranteed benefit from NVLink.

## Hardware profile index

These are partial caption-evidence profiles,not LCZ-equivalent complete builds. No part from an LCZ reference has been inserted into a video configuration.

| Profile / role | Core evidence coverage | Linked observations |
| --- | --- | --- |
| [V029-HP-C001 — Purchased Colorful2080Ti22GB modified pair /optionalNVLink](hardware-profiles/V029-HP-C001.md) | configuration as explicitly narrated;creator/third-party claim,not independently verified;1/6corecategories,notcomplete | 24 |

Only1 grounded profile is available;additional complete machines cannot be invented from this source.

## Test series and run conditions

Only source-reported observations follow. Unknown conditions stay unknown;rows are not certified apples-to-apples comparisons. Single-request speed,aggregate throughput,prefill,TTFT,quality,memory,power and estimates use separate series. Ranges are preserved;no new sweep points,repeats,medians or statistics were created.

### V029-S01 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** 27Bdense discussion; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not isolated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V029-P001; ArcB65 reference (profileunassigned) | decode · 30 toover40 tokens/s | without/with MPP as captioned; creator narrates tests;ASR/configuration caveats retained | [5:45](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=345s) |

### V029-S02 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** 27Bdense; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** vLLMdiscussion;AutoRoundGPTQ; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V029-P002; one2080Ti;VRAMlabels conflict (profileunassigned) | decode · 28 tokens/s | 4K;INT4;source elsewhere11/22/24GBconflict; creator narrates tests;ASR/configuration caveats retained | [6:58](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=418s) |

### V029-S03 · TTFT / startup latency

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** same27B; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** same; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V029-P003; samecard (profileunassigned) | time to first token · over4 seconds | 4Kinput; creator narrates tests;ASR/configuration caveats retained | [7:00](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=420s) |

### V029-S04 · Prefill / input processing

- **Profile(s):** V029-HP-C001
- **Model / weights / quantization:** same27B; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** same; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V029-P004; samecard (profileunassigned) | prefill · ~1000 tokens/s | 4Kinput; creator narrates tests;ASR/configuration caveats retained | [7:03](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=423s) |
| V029-P008; V029-HP-C001 | prefill · ~1000 to>1200 tokens/s | single todualcard; creator narrates tests;ASR/configuration caveats retained | [8:50](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=530s) |

### V029-S05 · Memory / fit (not throughput)

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** same27B; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** same; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V029-P005; samecard (profileunassigned) | KVcapacity · 74 Ktokens | notGPUmemoryGB; creator narrates tests;ASR/configuration caveats retained | [7:05](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=425s) |

### V029-S06 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** 35B-A3BMoE; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not isolated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V029-P006; onecard (profileunassigned) | decode · 100 tokens/s | ~64Kcontext;INT4;artifact~19GB;caption24GBcontradicts22GBintro; creator narrates tests;ASR/configuration caveats retained | [7:52](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=472s) |

### V029-S07 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V029-HP-C001
- **Model / weights / quantization:** 27Bdense; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** vLLMdiscussion; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V029-P007; V029-HP-C001 | decode · 45 tokens/s | 4K;INT4;nobridge; creator narrates tests;ASR/configuration caveats retained | [8:45](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=525s) |

### V029-S08 · Power / energy (boundary-dependent)

- **Profile(s):** V029-HP-C001
- **Model / weights / quantization:** same27B; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** same; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V029-P009; one2080Ti (profileunassigned) | prefill power · 236 W | card/systemmeasurementboundarynotstated; creator narrates tests;ASR/configuration caveats retained | [9:04](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=544s) |
| V029-P010; V029-HP-C001 | prefill power · 435 W | sameboundarycaveat; creator narrates tests;ASR/configuration caveats retained | [9:06](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=546s) |

### V029-S09 · Aggregate / concurrent throughput (not single-request speed)

- **Profile(s):** V029-HP-C001
- **Model / weights / quantization:** same27B; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** same; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V029-P011; V029-HP-C001 | aggregate/per-user throughput · 251/31 tokens/s | 8users; creator narrates tests;ASR/configuration caveats retained | [9:23](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=563s) |
| V029-P012; V029-HP-C001 | aggregate/per-user throughput · 376/~23 tokens/s | 16users; creator narrates tests;ASR/configuration caveats retained | [9:27](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=567s) |
| V029-P014; V029-HP-C001 | aggregate throughput · 376 to584 tokens/s | 16streams;speculationenabled; creator narrates tests;ASR/configuration caveats retained | [10:26](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=626s) |

### V029-S10 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V029-HP-C001
- **Model / weights / quantization:** same27B; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** same; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V029-P013; V029-HP-C001 | decode · 45 to71 tokens/s | Medusaparameter3;nobridge; creator narrates tests;ASR/configuration caveats retained | [10:22](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=622s) |

### V029-S11 · Auxiliary transport / compute / embedding (not LLM decode)

- **Profile(s):** V029-HP-C001
- **Model / weights / quantization:** transporttest; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** notLLMruntime; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V029-P015; V029-HP-C001 | read-write link throughput · 74 GB/s | notprefilltokens/s; creator narrates tests;ASR/configuration caveats retained | [11:29](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=689s) |
| V029-P016; V029-HP-C001 | linkthroughputmax · 87.5 GB/s | extrememultipath;notLLMthroughput; creator narrates tests;ASR/configuration caveats retained | [11:34](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=694s) |

### V029-S12 · Prefill / input processing

- **Profile(s):** V029-HP-C001
- **Model / weights / quantization:** 27B; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** same; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V029-P017; V029-HP-C001 | long-prompt prefill · 122 to175 unitnotexplicitlyrepeated | nobridgetobridge;do notcomparewith4K1200withoutconditions; creator narrates tests;ASR/configuration caveats retained | [12:00](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=720s) |

### V029-S13 · Aggregate / concurrent throughput (not single-request speed)

- **Profile(s):** V029-HP-C001
- **Model / weights / quantization:** 27B; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** same; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V029-P018; V029-HP-C001 | 8-user throughput gain · 24 percent | NVLink; creator narrates tests;ASR/configuration caveats retained | [12:18](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=738s) |
| V029-P019; V029-HP-C001 | 16-user throughput gain · 25 percent | NVLink; creator narrates tests;ASR/configuration caveats retained | [12:20](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=740s) |
| V029-P020; V029-HP-C001 | aggregate throughput · 584 to846 tokens/s | 16users;speculation;NVLinkadded; creator narrates tests;ASR/configuration caveats retained | [12:36](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=756s) |

### V029-S14 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V029-HP-C001
- **Model / weights / quantization:** 27B; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** same; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V029-P021; V029-HP-C001 | decode · 92.5 tokens/s | 4K;speculationenabled; creator narrates tests;ASR/configuration caveats retained | [13:22](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=802s) |
| V029-P022; V029-HP-C001 | decode · 114 tokens/s | 16K;speculationenabled; creator narrates tests;ASR/configuration caveats retained | [13:22](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=802s) |
| V029-P023; V029-HP-C001 | decode · over70 tokens/s | 256K;captionATP/MDP/MTPnamesvary; creator narrates tests;ASR/configuration caveats retained | [13:27](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=807s) |
| V029-P025; V029-HP-C001 | FP8 decode · 32.4 tokens/s | speculationoff; creator narrates tests;ASR/configuration caveats retained | [14:13](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=853s) |
| V029-P026; V029-HP-C001 | FP8 decode · 74 tokens/s | speculationon; creator narrates tests;ASR/configuration caveats retained | [14:21](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=861s) |

### V029-S15 · Memory / fit (not throughput)

- **Profile(s):** V029-HP-C001
- **Model / weights / quantization:** 27B; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** same; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V029-P024; V029-HP-C001 | KVcapacity · 650K to310K tokens | INT4 toFP8 weights discussion; creator narrates tests;ASR/configuration caveats retained | [14:08](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=848s) |

### V029-S16 · Other reported observations / stability (not a comparable speed benchmark)

- **Profile(s):** V029-HP-C001
- **Model / weights / quantization:** 27B; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** same; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V029-P027; V029-HP-C001 | stability failure · 16 concurrentusers | FP8crash;notcapacityguarantee; creator narrates tests;ASR/configuration caveats retained | [14:34](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=874s) |

### V029-S17 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V029-HP-C001
- **Model / weights / quantization:** 27B; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Medusa2; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V029-P028; V029-HP-C001 | decode · 233 tokens/s | 3.6GBdraftmodel;scenario-specific/unstable; creator narrates tests;ASR/configuration caveats retained | [15:02](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=902s) |

### V029-S18 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V029-HP-C001
- **Model / weights / quantization:** lightermodel;captionF8unclear; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** vLLM; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V029-P029; V029-HP-C001 | decode · 128 tokens/s | 4K;modelidentityunresolved; creator narrates tests;ASR/configuration caveats retained | [15:18](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=918s) |

### V029-S19 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V029-HP-C001
- **Model / weights / quantization:** sameunresolvedmodel; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** vLLM; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V029-P030; V029-HP-C001 | speculative/single-streamgeneration · over200 tokens/s | methodnotcleanlycaptioned; creator narrates tests;ASR/configuration caveats retained | [15:22](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=922s) |

### V029-S20 · Aggregate / concurrent throughput (not single-request speed)

- **Profile(s):** V029-HP-C001
- **Model / weights / quantization:** sameunresolvedmodel; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** vLLM; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V029-P031; V029-HP-C001 | aggregate throughput · ~1800 tokens/s | 116concurrentasASR;possibly16,notcorrected; creator narrates tests;ASR/configuration caveats retained | [15:25](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=925s) |

## Detailed hardware profiles

Minimum fields follow motherboard/CPU/RAMmodules+speed/GPUvariant+count+VRAM/PSU/storage. “Unknown”means not reported,not an invitation to fill from a different owner or manufacturer memory. Costs are quotes/paid/estimates only where identified;no fakeBOMtotal.

### V029-HP-C001 · Purchased Colorful2080Ti22GB modified pair /optionalNVLink

**Role:** configuration as explicitly narrated;creator/third-party claim,not independently verified. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=53s) · [additional disclosure](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=74s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** 2599each;5198pair;bridge nearly400 separately;not complete system cost · Reported paid GPU/bridge amounts;not independently verified receipts · Yuan explicit later in the hardware discussion;price date not stated. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | Colorful modifiedRTX2080Ti22GB | qty 2; 300non-Achip;22GBintro;latercaptioncapacityconflicts | unit 2599yuan each;dateunknown; subtotal 5198yuan source-statedpair; Creator says bought; Reported paid amount | [source](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=53s) |
| Interconnect | NVLinkbridge | qty 1; Optionalon/off comparison | subtotal Nearly400;not exact; Creator says bought; Reported paid amount;not included in GPUsubtotal | [source](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=57s) |
| GPU cooling/mechanics | Dual-slotblower;exactcooler modelunknown | qty 2cards; 26.7×11cm;dual8pin;serverpowerconnectororientation matters | — | [source](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=74s) |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=53s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=53s) |
| RAM | — | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=53s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=53s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=53s) |
| Cooling | Dual-slot blower;26.7cm length/11cm height;dual8-pin power connectors,as narrated | — | — | [source](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=53s) |

**Other component disclosures:** VRAM conflict prevents a clean normalizedcapacity;bridge/no-bridgerunsremainseparate

**Selection / tradeoffs:** Investigates whether popular modified2080Ti value/performance claims survive direct tests. Modified/refurbished/mining-history risk discussed. Stock card11GB is a separate product;later11/24GBcaption clauses remain inconsistent with22GBintro.

**Expansion / compatibility:** Unknown / not reported For server chassis choose rear power-connector orientation to avoid ducts/other parts. No PSU model is supplied.

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** ~250W/cardrating; rating/limit unless measurement expressly stated;NOT a PSU specification Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Single versus dualcard and bridge on/off are distinct test modes. INT4/FP8/speculation variations are run settings,not proof of the same memory footprint.

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V029-P007 / V029-S07 | 27Bdense; not stated; vLLMdiscussion | decode: 45 tokens/s | 4K;INT4;nobridge; creator narrates tests;ASR/configuration caveats retained; [8:45](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=525s) |
| V029-P008 / V029-S04 | same27B; not stated; same | prefill: ~1000 to>1200 tokens/s | single todualcard; creator narrates tests;ASR/configuration caveats retained; [8:50](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=530s) |
| V029-P010 / V029-S08 | same27B; not stated; same | prefill power: 435 W | sameboundarycaveat; creator narrates tests;ASR/configuration caveats retained; [9:06](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=546s) |
| V029-P011 / V029-S09 | same27B; not stated; same | aggregate/per-user throughput: 251/31 tokens/s | 8users; creator narrates tests;ASR/configuration caveats retained; [9:23](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=563s) |
| V029-P012 / V029-S09 | same27B; not stated; same | aggregate/per-user throughput: 376/~23 tokens/s | 16users; creator narrates tests;ASR/configuration caveats retained; [9:27](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=567s) |
| V029-P013 / V029-S10 | same27B; not stated; same | decode: 45 to71 tokens/s | Medusaparameter3;nobridge; creator narrates tests;ASR/configuration caveats retained; [10:22](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=622s) |
| V029-P014 / V029-S09 | same27B; not stated; same | aggregate throughput: 376 to584 tokens/s | 16streams;speculationenabled; creator narrates tests;ASR/configuration caveats retained; [10:26](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=626s) |
| V029-P015 / V029-S11 | transporttest; not stated; notLLMruntime | read-write link throughput: 74 GB/s | notprefilltokens/s; creator narrates tests;ASR/configuration caveats retained; [11:29](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=689s) |
| V029-P016 / V029-S11 | transporttest; not stated; notLLMruntime | linkthroughputmax: 87.5 GB/s | extrememultipath;notLLMthroughput; creator narrates tests;ASR/configuration caveats retained; [11:34](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=694s) |
| V029-P017 / V029-S12 | 27B; not stated; same | long-prompt prefill: 122 to175 unitnotexplicitlyrepeated | nobridgetobridge;do notcomparewith4K1200withoutconditions; creator narrates tests;ASR/configuration caveats retained; [12:00](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=720s) |
| V029-P018 / V029-S13 | 27B; not stated; same | 8-user throughput gain: 24 percent | NVLink; creator narrates tests;ASR/configuration caveats retained; [12:18](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=738s) |
| V029-P019 / V029-S13 | 27B; not stated; same | 16-user throughput gain: 25 percent | NVLink; creator narrates tests;ASR/configuration caveats retained; [12:20](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=740s) |
| V029-P020 / V029-S13 | 27B; not stated; same | aggregate throughput: 584 to846 tokens/s | 16users;speculation;NVLinkadded; creator narrates tests;ASR/configuration caveats retained; [12:36](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=756s) |
| V029-P021 / V029-S14 | 27B; not stated; same | decode: 92.5 tokens/s | 4K;speculationenabled; creator narrates tests;ASR/configuration caveats retained; [13:22](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=802s) |
| V029-P022 / V029-S14 | 27B; not stated; same | decode: 114 tokens/s | 16K;speculationenabled; creator narrates tests;ASR/configuration caveats retained; [13:22](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=802s) |
| V029-P023 / V029-S14 | 27B; not stated; same | decode: over70 tokens/s | 256K;captionATP/MDP/MTPnamesvary; creator narrates tests;ASR/configuration caveats retained; [13:27](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=807s) |
| V029-P024 / V029-S15 | 27B; not stated; same | KVcapacity: 650K to310K tokens | INT4 toFP8 weights discussion; creator narrates tests;ASR/configuration caveats retained; [14:08](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=848s) |
| V029-P025 / V029-S14 | 27B; not stated; same | FP8 decode: 32.4 tokens/s | speculationoff; creator narrates tests;ASR/configuration caveats retained; [14:13](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=853s) |
| V029-P026 / V029-S14 | 27B; not stated; same | FP8 decode: 74 tokens/s | speculationon; creator narrates tests;ASR/configuration caveats retained; [14:21](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=861s) |
| V029-P027 / V029-S16 | 27B; not stated; same | stability failure: 16 concurrentusers | FP8crash;notcapacityguarantee; creator narrates tests;ASR/configuration caveats retained; [14:34](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=874s) |
| V029-P028 / V029-S17 | 27B; not stated; Medusa2 | decode: 233 tokens/s | 3.6GBdraftmodel;scenario-specific/unstable; creator narrates tests;ASR/configuration caveats retained; [15:02](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=902s) |
| V029-P029 / V029-S18 | lightermodel;captionF8unclear; not stated; vLLM | decode: 128 tokens/s | 4K;modelidentityunresolved; creator narrates tests;ASR/configuration caveats retained; [15:18](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=918s) |
| V029-P030 / V029-S19 | sameunresolvedmodel; not stated; vLLM | speculative/single-streamgeneration: over200 tokens/s | methodnotcleanlycaptioned; creator narrates tests;ASR/configuration caveats retained; [15:22](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=922s) |
| V029-P031 / V029-S20 | sameunresolvedmodel; not stated; vLLM | aggregate throughput: ~1800 tokens/s | 116concurrentasASR;possibly16,notcorrected; creator narrates tests;ASR/configuration caveats retained; [15:25](https://www.youtube.com/watch?v=1xmOTSUpBL0&t=925s) |


## Scope

Caption-only evidence;no chart/video viewing or independent hardware validation. ASR and source contradictions are retained. Full original caption text is not included. Original450claim records and99hardwarefact records are preserved byte-for-byte in their originalCSVs;new profiles/series are a separately typed organization layer.

## llmfit-aligned machine-readable records

Upstreamcommit`26450cccaf3a3f14b1822875f2473847a744a718`. Thisvideo has1losslessresearchprofiles;0have a minimalcore passingthe actualupstreamHardwareProfileJSONschema. Otherprofilesremain explicitlypartial,not paddedwithdefaults. Modelcatalogmetadata is incomplete;runconditions/prefill/concurrency/BOM/provenance remainnamespacedextensions. See[contract](llmfit/schema.md),[fieldmapping](llmfit/mapping.md),[validation](llmfit/validation-report.json). NativecompatibilityisNOTa completebuild,independentmeasurement or testedimport.
