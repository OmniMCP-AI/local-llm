# 028 · Every Way to Get 256 GB of VRAM for Local AI at Full Context

> Original research summary and factual claim tables — NOT a transcript or authored script.

- Source: [Every Way to Get 256 GB of VRAM for Local AI at Full Context](https://www.youtube.com/watch?v=JPHT9AvoPSA) · Channel: Kai
- Caption language: en; automatic track. Retrieval: 2026-11-20T20:49:39.282488+08:00 (Asia/Shanghai).
- Coverage: returned caption track, not audio-verified; first 0.0 ms, final 1645869.0 ms. No visual charts or manufacturer specifications independently checked.

## Original research notes

This capacity-oriented buying discussion asks what a large memory budget actually enables, with quality and operating constraints taking precedence over an impressive capacity label.

- [0:58](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=58s): The presenter frames quantization as central to the purchase decision. The useful target is a model-and-quality configuration, rather than an undifferentiated quantity of nominal memory.
- [5:19](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=319s): Several compressed forms are associated with different memory requirements and quality compromises. Those estimates need the exact artifact and context assumptions before being reused in an advisor.
- [9:42](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=582s): A clustered-system example distinguishes ordinary generation from draft-assisted behavior. Workload and decoding method can produce materially different reported rates on what appears to be the same hardware.
- [14:05](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=845s): A mixed GPU, system-memory and storage build is offered as another route. The example reinforces that aggregate capacity does not describe where active computation and data movement occur.
- [23:25](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1405s): The creator invokes a user whose information must remain local when discussing cloud alternatives. This is an illustrative audience anecdote, not verified evidence of market size or adoption.

**Platform implication.** A fit advisor should start with acceptable quality, context and data-location requirements, then compare memory layouts. Keep architecture support, draft settings and bandwidth with each observation; do not rank ownership routes on cost per gigabyte alone.

## Hardware profile index

These are partial caption-evidence profiles,not LCZ-equivalent complete builds. No part from an LCZ reference has been inserted into a video configuration.

| Profile / role | Core evidence coverage | Linked observations |
| --- | --- | --- |
| [V028-HP-C001 — DDR4 expert-offloadbuild / RTX3090](hardware-profiles/V028-HP-C001.md) | configuration as explicitly narrated;creator/third-party claim,not independently verified;3/6corecategories,notcomplete | 4 |
| [V028-HP-C002 — large expert-offloadbuild / RTXPro6000](hardware-profiles/V028-HP-C002.md) | configuration as explicitly narrated;creator/third-party claim,not independently verified;2/6corecategories,notcomplete | 3 |
| [V028-HP-C003 — singleStrixHalobox](hardware-profiles/V028-HP-C003.md) | configuration as explicitly narrated;creator/third-party claim,not independently verified;1/6corecategories,notcomplete | 2 |
| [V028-HP-G002 — RTXPro5000](hardware-profiles/V028-HP-G002.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 0 |
| [V028-HP-G003 — V100](hardware-profiles/V028-HP-G003.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 0 |
| [V028-HP-G004 — AMDMI50](hardware-profiles/V028-HP-G004.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 0 |
| [V028-HP-E01 — TwoDGXSpark networked configuration](hardware-profiles/V028-HP-E01.md) | Caption-reported partial configuration /comparison;not a full build;1/6corecategories,notcomplete | 8 |
| [V028-HP-E02 — TwoStrixHalo comparison](hardware-profiles/V028-HP-E02.md) | Caption-reported partial configuration /comparison;not a full build;1/6corecategories,notcomplete | 4 |
| [V028-HP-E03 — FourMI50 32GB community preview](hardware-profiles/V028-HP-E03.md) | Caption-reported partial configuration /comparison;not a full build;1/6corecategories,notcomplete | 2 |
| [V028-HP-E04 — 80-coreMac mixed2/3bit case](hardware-profiles/V028-HP-E04.md) | Caption-reported partial configuration /comparison;not a full build;1/6corecategories,notcomplete | 2 |
| [V028-HP-E05 — 64-coreMac MLX case](hardware-profiles/V028-HP-E05.md) | Caption-reported partial configuration /comparison;not a full build;1/6corecategories,notcomplete | 2 |
| [V028-HP-E06 — FourR9700 Qwenconfiguration](hardware-profiles/V028-HP-E06.md) | Caption-reported partial configuration /comparison;not a full build;1/6corecategories,notcomplete | 1 |
| [V028-HP-E07 — FourV10016GB Qwenconfiguration](hardware-profiles/V028-HP-E07.md) | Caption-reported partial configuration /comparison;not a full build;1/6corecategories,notcomplete | 1 |

## Test series and run conditions

Only source-reported observations follow. Unknown conditions stay unknown;rows are not certified apples-to-apples comparisons. Single-request speed,aggregate throughput,prefill,TTFT,quality,memory,power and estimates use separate series. Ranges are preserved;no new sweep points,repeats,medians or statistics were created.

### V028-S01 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V028-HP-E04
- **Model / weights / quantization:** DeepSeekV4.1Flash; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** TensorFlow/TensorFold label varies in captions; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V028-P001; V028-HP-E04 | decode · 70–105 tokens/s | mixed2/3bit;draftheadon; citedrun | [7:46](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=466s) |

### V028-S02 · Prefill / input processing

- **Profile(s):** V028-HP-E04
- **Model / weights / quantization:** sameDeepSeek; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** samebackend; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V028-P002; V028-HP-E04 | long-prompt prefill · 1800 tokens/s | mixed2/3bit; citedrun | [7:52](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=472s) |

### V028-S03 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V028-HP-E05
- **Model / weights / quantization:** sameDeepSeek; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** MLX; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V028-P003; V028-HP-E05 | decode · 26–29 tokens/s | not samecorecountas80corecomparison; citedrun | [7:57](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=477s) |

### V028-S04 · Prefill / input processing

- **Profile(s):** V028-HP-E05
- **Model / weights / quantization:** sameDeepSeek; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** MLX; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V028-P004; V028-HP-E05 | prefill · under500 tokens/s | do notpresentasidenticalhardware; citedrun | [8:00](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=480s) |

### V028-S05 · Memory / fit (not throughput)

- **Profile(s):** V028-HP-C002, V028-HP-E01
- **Model / weights / quantization:** DeepSeek; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not isolated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V028-P005; V028-HP-E01 | observed/claimed model footprint · 196 GBaggregate | 2.9bitbuild; citedrun | [9:17](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=557s) |
| V028-P019; V028-HP-C002 | observed VRAM/RAM use · 89/346 GB | 89GPU;346systemRAM;differentmemorytypes; citedrun | [16:01](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=961s) |

### V028-S06 · Prefill / input processing

- **Profile(s):** V028-HP-C003, V028-HP-E01, V028-HP-E02
- **Model / weights / quantization:** DeepSeek; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not isolated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V028-P006; V028-HP-E01 | prefill · 2100 tokens/s | heldnear128Kcontext; MiAILab measurement cited | [9:26](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=566s) |
| V028-P012; V028-HP-E02 | prefill · 700–750 tokens/s | samecase; developerreport | [12:23](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=743s) |
| V028-P014; V028-HP-C003 | prefill · 1000 tokens/s | onebit; developerreport | [13:07](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=787s) |
| V028-P027; V028-HP-E01 | prefill elapsed time · 280 seconds | 479Kprompt; citedtiming | [21:19](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1279s) |
| V028-P031; Macconfigurationunspecified (profileunassigned) | cached/newturnprefill · 350 tokens/s | alreadycachedcontext;newtokensonly; ownermeasurement | [21:55](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1315s) |

### V028-S07 · TTFT / startup latency

- **Profile(s):** V028-HP-E01
- **Model / weights / quantization:** DeepSeek; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** samecase; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V028-P007; V028-HP-E01 | time to first token · 63 seconds | 128Kprompt; narratedresult | [9:34](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=574s) |

### V028-S08 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V028-HP-C002, V028-HP-C003, V028-HP-E01, V028-HP-E02
- **Model / weights / quantization:** DeepSeek; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not isolated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V028-P008; V028-HP-E01 | decode · 31 tokens/s | draftoff; ownerreport | [9:47](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=587s) |
| V028-P009; V028-HP-E01 | draft-assisteddecode · 87 tokens/s | code; ownerreport | [9:52](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=592s) |
| V028-P010; V028-HP-E01 | draft-assisteddecode · 131 tokens/s | structuredoutput;notregularprose; ownerreport | [9:56](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=596s) |
| V028-P011; V028-HP-E02 | decode · 27 tokens/s | networked; developerreport | [12:20](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=740s) |
| V028-P015; V028-HP-C003 | decode · 23–28 tokens/s | onebit;qualitynotassumed; developerreport | [13:10](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=790s) |
| V028-P020; V028-HP-C002 | single-user decode · 65 tokens/s | original4bitweights;source callsnoadditionalquantization,NOTFP16; citedrun | [16:08](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=968s) |

### V028-S09 · Other reported observations / stability (not a comparable speed benchmark)

- **Profile(s):** V028-HP-E02
- **Model / weights / quantization:** DeepSeek; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not isolated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V028-P013; V028-HP-E02 | incrementalsecondboxeffect · +23%decode/-13%prefill percent | short/freshprompts;notlinearscaling; developeranalysis | [12:32](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=752s) |

### V028-S10 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V028-HP-C001
- **Model / weights / quantization:** DeepSeekV4.1Flash; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** 0x0build as named; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V028-P016; V028-HP-C001 | decode · 26 tokens/s | singleuser; developerreport | [14:23](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=863s) |

### V028-S11 · Aggregate / concurrent throughput (not single-request speed)

- **Profile(s):** V028-HP-C001
- **Model / weights / quantization:** DeepSeekV4.1Flash; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** samebuild; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V028-P017; V028-HP-C001 | aggregate throughput · 41 tokens/s | fourusers; developerreport | [14:27](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=867s) |

### V028-S12 · Prefill / input processing

- **Profile(s):** V028-HP-C001
- **Model / weights / quantization:** DeepSeekV4.1Flash; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** samebuild; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V028-P018; V028-HP-C001 | prefill · 600–800 tokens/s | 262Kcontextconfigured; developerreport | [14:32](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=872s) |

### V028-S13 · Aggregate / concurrent throughput (not single-request speed)

- **Profile(s):** V028-HP-C002
- **Model / weights / quantization:** DeepSeek; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not isolated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V028-P021; V028-HP-C002 | aggregate throughput · 143 tokens/s | eightusers;original4bit; citedrun | [16:11](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=971s) |

### V028-S14 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V028-HP-E06
- **Model / weights / quantization:** Qwen3.8FlashNext; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not isolated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V028-P022; V028-HP-E06 | single-user decode · 236 tokens/s | notDeepSeektest; ownerbenchmark | [17:56](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1076s) |

### V028-S15 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V028-HP-E07
- **Model / weights / quantization:** Qwen3.8; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** communitysoftware; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V028-P023; V028-HP-E07 | decode · 219 tokens/s | 4bit;claimedmatch,specificmodelsizeomitted; communityclaim | [19:26](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1166s) |

### V028-S16 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V028-HP-E03
- **Model / weights / quantization:** DeepSeek; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** communitypreviewROCm; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V028-P024; V028-HP-E03 | decode · 50 tokens/s | 2bit; ownerreport | [20:03](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1203s) |

### V028-S17 · Prefill / input processing

- **Profile(s):** V028-HP-E03
- **Model / weights / quantization:** DeepSeek; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** sameROCm; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V028-P025; V028-HP-E03 | prefill · 275 tokens/s | 2bit; ownerreport | [20:05](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1205s) |

### V028-S18 · Prefill / input processing

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** DeepSeek; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** TensorFold; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V028-P026; Macconfigurationnotretied (profileunassigned) | prefill elapsed time · 740 seconds | 1Mprompt; citedtiming | [21:12](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1272s) |

### V028-S19 · Derived estimates / theoretical / ROI (not measured benchmarks)

- **Profile(s):** V028-HP-C001, V028-HP-E01, V028-HP-E02
- **Model / weights / quantization:** DeepSeek; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not isolated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V028-P028; V028-HP-E01 | 1Mprefilltimeestimate · 10 minutes | extrapolatedfrom479K; creatorcalculation | [21:22](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1282s) |
| V028-P029; V028-HP-E02 | 1Mprefilltimeestimate · atleast23 minutes | rate-based,notdirect1Mtest; creatorcalculation | [21:25](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1285s) |
| V028-P030; V028-HP-C001 | 1Mprefilltimeestimate · 22–29 minutes | rate-based; creatorcalculation | [21:32](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1292s) |

### V028-S20 · Derived estimates / theoretical / ROI (not measured benchmarks)

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** DeepSeek; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** costscenario; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V028-P032; 256GBMacStudio (profileunassigned) | equivalentAPIpurchase · 15.8 billion output tokens | off-peakpriceassumed;rate/date notstated; creatorROIcalculation | [22:40](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1360s) |
| V028-P033; sameMac (profileunassigned) | annualoutput · 1.1 billion tokens/year | 35tok/s24x7;no utilizationdiscount; creatorROIcalculation | [22:49](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1369s) |
| V028-P034; sameMac (profileunassigned) | break-even · 14 years | 35tok/s;off-peakAPI;electricityexcluded; creatorROIcalculation | [22:55](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1375s) |
| V028-P035; sameMac (profileunassigned) | break-even · 6 years | 80tok/sdraft;off-peakAPI;electricityexcluded; creatorROIcalculation | [22:59](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1379s) |

## Detailed hardware profiles

Minimum fields follow motherboard/CPU/RAMmodules+speed/GPUvariant+count+VRAM/PSU/storage. “Unknown”means not reported,not an invitation to fill from a different owner or manufacturer memory. Costs are quotes/paid/estimates only where identified;no fakeBOMtotal.

### V028-HP-C001 · DDR4 expert-offloadbuild / RTX3090

**Role:** configuration as explicitly narrated;creator/third-party claim,not independently verified. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=854s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** ~$6000buildestimate · Source-quoted price/estimate,not verified paid price · Keep literal currency;price date not established. Video publication date is not a purchase date.. No complete BOM total has been calculated.

**Evidence completeness:** 3/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=854s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=854s) |
| RAM | system/unspecified RAM: 256GBDDR4 | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=854s) |
| GPU | RTX3090 | qty 1; PerGPUVRAM:24GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=854s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=854s) |
| Storage | 200GBSSDmentioned;allocationversusfullcapacityunclear | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=854s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** 0x0 engineasnamed Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, psu; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V028-P016 / V028-S10 | DeepSeekV4.1Flash; not stated; 0x0build as named | decode: 26 tokens/s | singleuser; developerreport; [14:23](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=863s) |
| V028-P017 / V028-S11 | DeepSeekV4.1Flash; not stated; samebuild | aggregate throughput: 41 tokens/s | fourusers; developerreport; [14:27](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=867s) |
| V028-P018 / V028-S12 | DeepSeekV4.1Flash; not stated; samebuild | prefill: 600–800 tokens/s | 262Kcontextconfigured; developerreport; [14:32](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=872s) |
| V028-P030 / V028-S19 | DeepSeek; not stated; not isolated | 1Mprefilltimeestimate: 22–29 minutes | rate-based; creatorcalculation; [21:32](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1292s) |

---

### V028-HP-C002 · large expert-offloadbuild / RTXPro6000

**Role:** configuration as explicitly narrated;creator/third-party claim,not independently verified. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=955s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 2/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=955s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=955s) |
| RAM | system/unspecified RAM: 512GBDDR4 | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=955s) |
| GPU | RTXPro6000 | qty 1; PerGPUVRAM:96GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=955s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=955s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=955s) |

**Other component disclosures:** 89GBGPU/346GBRAMareusage,notphysicalcapacities

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V028-P019 / V028-S05 | DeepSeek; not stated; not isolated | observed VRAM/RAM use: 89/346 GB | 89GPU;346systemRAM;differentmemorytypes; citedrun; [16:01](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=961s) |
| V028-P020 / V028-S08 | DeepSeek; not stated; not isolated | single-user decode: 65 tokens/s | original4bitweights;source callsnoadditionalquantization,NOTFP16; citedrun; [16:08](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=968s) |
| V028-P021 / V028-S13 | DeepSeek; not stated; not isolated | aggregate throughput: 143 tokens/s | eightusers;original4bit; citedrun; [16:11](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=971s) |

---

### V028-HP-C003 · singleStrixHalobox

**Role:** configuration as explicitly narrated;creator/third-party claim,not independently verified. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=783s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=783s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=783s) |
| RAM | unified/shared RAM: 128GB memory;shared/unifiedclassificationnotexplicitinclause | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=783s) |
| GPU | — | PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=783s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=783s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=783s) |

**Other component disclosures:** do notsilentlybindthiscapacitytotwo-boxcomparison

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** one-bitmodel Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, gpu, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V028-P014 / V028-S06 | DeepSeek; not stated; not isolated | prefill: 1000 tokens/s | onebit; developerreport; [13:07](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=787s) |
| V028-P015 / V028-S08 | DeepSeek; not stated; not isolated | decode: 23–28 tokens/s | onebit;qualitynotassumed; developerreport; [13:10](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=790s) |

---

### V028-HP-G002 · RTXPro5000

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1065s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** ~$40000forfour · Source-quoted price/estimate,not verified paid price · Keep literal currency;price date not established. Video publication date is not a purchase date.. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | RTXPro5000 | PerGPUVRAM:72GB percard as narrated;notmanufacturerverified;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1065s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** No performance row can be safely assigned to this exact profile. Product mention/recommendation is not a measured build.

---

### V028-HP-G003 · V100

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1163s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | V100 | PerGPUVRAM:16GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1163s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** No performance row can be safely assigned to this exact profile. Product mention/recommendation is not a measured build.

---

### V028-HP-G004 · AMDMI50

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1188s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** $250–700 · Source-quoted price/estimate,not verified paid price · Keep literal currency;price date not established. Video publication date is not a purchase date.. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | AMDMI50 | PerGPUVRAM:32GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1188s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** No performance row can be safely assigned to this exact profile. Product mention/recommendation is not a measured build.

---

### V028-HP-E01 · TwoDGXSpark networked configuration

**Role:** Caption-reported partial configuration /comparison;not a full build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=557s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=557s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=557s) |
| RAM | — | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=557s) |
| GPU | DGXSpark;GPUcores notstated | PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=557s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=557s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=557s) |
| Interconnect | Two machines;link hardware notspecified | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=557s) |

**Selection / tradeoffs:** Unknown / not reported 196GB is model footprint,not physicalRAM;draft-on/off and structured/code rates are separate run modes.

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V028-P005 / V028-S05 | DeepSeek; not stated; not isolated | observed/claimed model footprint: 196 GBaggregate | 2.9bitbuild; citedrun; [9:17](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=557s) |
| V028-P006 / V028-S06 | DeepSeek; not stated; not isolated | prefill: 2100 tokens/s | heldnear128Kcontext; MiAILab measurement cited; [9:26](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=566s) |
| V028-P007 / V028-S07 | DeepSeek; not stated; samecase | time to first token: 63 seconds | 128Kprompt; narratedresult; [9:34](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=574s) |
| V028-P008 / V028-S08 | DeepSeek; not stated; not isolated | decode: 31 tokens/s | draftoff; ownerreport; [9:47](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=587s) |
| V028-P009 / V028-S08 | DeepSeek; not stated; not isolated | draft-assisteddecode: 87 tokens/s | code; ownerreport; [9:52](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=592s) |
| V028-P010 / V028-S08 | DeepSeek; not stated; not isolated | draft-assisteddecode: 131 tokens/s | structuredoutput;notregularprose; ownerreport; [9:56](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=596s) |
| V028-P027 / V028-S06 | DeepSeek; not stated; not isolated | prefill elapsed time: 280 seconds | 479Kprompt; citedtiming; [21:19](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1279s) |
| V028-P028 / V028-S19 | DeepSeek; not stated; not isolated | 1Mprefilltimeestimate: 10 minutes | extrapolatedfrom479K; creatorcalculation; [21:22](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1282s) |

---

### V028-HP-E02 · TwoStrixHalo comparison

**Role:** Caption-reported partial configuration /comparison;not a full build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=740s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=740s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=740s) |
| RAM | — | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=740s) |
| GPU | StrixHalo | qty IntegratedGPU count notexplicitlystated; PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=740s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=740s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=740s) |

**Selection / tradeoffs:** Unknown / not reported Two boxes;do not inherit128GB-per-node from separate one-box clause without explicit binding.

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V028-P011 / V028-S08 | DeepSeek; not stated; not isolated | decode: 27 tokens/s | networked; developerreport; [12:20](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=740s) |
| V028-P012 / V028-S06 | DeepSeek; not stated; not isolated | prefill: 700–750 tokens/s | samecase; developerreport; [12:23](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=743s) |
| V028-P013 / V028-S09 | DeepSeek; not stated; not isolated | incrementalsecondboxeffect: +23%decode/-13%prefill percent | short/freshprompts;notlinearscaling; developeranalysis; [12:32](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=752s) |
| V028-P029 / V028-S19 | DeepSeek; not stated; not isolated | 1Mprefilltimeestimate: atleast23 minutes | rate-based,notdirect1Mtest; creatorcalculation; [21:25](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1285s) |

---

### V028-HP-E03 · FourMI50 32GB community preview

**Role:** Caption-reported partial configuration /comparison;not a full build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1188s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1188s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1188s) |
| RAM | — | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1188s) |
| GPU | AMDMI50 | qty 4; PerGPUVRAM:32GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1188s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1188s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1188s) |

**Selection / tradeoffs:** Unknown / not reported 2bitDeepSeek;not a manufacturer-supported reproducibility claim.

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** CommunityROCm preview;commit not stated Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V028-P024 / V028-S16 | DeepSeek; not stated; communitypreviewROCm | decode: 50 tokens/s | 2bit; ownerreport; [20:03](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1203s) |
| V028-P025 / V028-S17 | DeepSeek; not stated; sameROCm | prefill: 275 tokens/s | 2bit; ownerreport; [20:05](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1205s) |

---

### V028-HP-E04 · 80-coreMac mixed2/3bit case

**Role:** Caption-reported partial configuration /comparison;not a full build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=466s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=466s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=466s) |
| RAM | — | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=466s) |
| GPU | AppleGPU;80cores as narrated | PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=466s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=466s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=466s) |

**Selection / tradeoffs:** Unknown / not reported RAM capacity not explicitly tied to this row;do not inherit64-core machine results.

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** TensorFold/TensorFlow naming varies in ASR;drafthead enabled Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V028-P001 / V028-S01 | DeepSeekV4.1Flash; not stated; TensorFlow/TensorFold label varies in captions | decode: 70–105 tokens/s | mixed2/3bit;draftheadon; citedrun; [7:46](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=466s) |
| V028-P002 / V028-S02 | sameDeepSeek; not stated; samebackend | long-prompt prefill: 1800 tokens/s | mixed2/3bit; citedrun; [7:52](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=472s) |

---

### V028-HP-E05 · 64-coreMac MLX case

**Role:** Caption-reported partial configuration /comparison;not a full build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=477s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=477s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=477s) |
| RAM | — | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=477s) |
| GPU | AppleGPU;64cores as narrated | PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=477s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=477s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=477s) |

**Selection / tradeoffs:** Unknown / not reported Different GPU corecount and backend from80-corecase;not a controlled same-hardware test.

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** MLX;versionnotstated Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V028-P003 / V028-S03 | sameDeepSeek; not stated; MLX | decode: 26–29 tokens/s | not samecorecountas80corecomparison; citedrun; [7:57](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=477s) |
| V028-P004 / V028-S04 | sameDeepSeek; not stated; MLX | prefill: under500 tokens/s | do notpresentasidenticalhardware; citedrun; [8:00](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=480s) |

---

### V028-HP-E06 · FourR9700 Qwenconfiguration

**Role:** Caption-reported partial configuration /comparison;not a full build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1076s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1076s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1076s) |
| RAM | — | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1076s) |
| GPU | R9700;captionR19700variantuncertain | qty 4; PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1076s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1076s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1076s) |

**Selection / tradeoffs:** Unknown / not reported Qwen3.8FlashNext236tok/sclaim,not a DeepSeek8cardresult.

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V028-P022 / V028-S14 | Qwen3.8FlashNext; not stated; not isolated | single-user decode: 236 tokens/s | notDeepSeektest; ownerbenchmark; [17:56](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1076s) |

---

### V028-HP-E07 · FourV10016GB Qwenconfiguration

**Role:** Caption-reported partial configuration /comparison;not a full build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1163s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1163s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1163s) |
| RAM | — | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1163s) |
| GPU | V100 | qty 4; PerGPUVRAM:16GB each;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1163s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1163s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1163s) |

**Selection / tradeoffs:** Unknown / not reported Qwen4bit comparison,notDeepSeekcapacityproof.

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V028-P023 / V028-S15 | Qwen3.8; not stated; communitysoftware | decode: 219 tokens/s | 4bit;claimedmatch,specificmodelsizeomitted; communityclaim; [19:26](https://www.youtube.com/watch?v=JPHT9AvoPSA&t=1166s) |


## Scope

Caption-only evidence;no chart/video viewing or independent hardware validation. ASR and source contradictions are retained. Full original caption text is not included. Original450claim records and99hardwarefact records are preserved byte-for-byte in their originalCSVs;new profiles/series are a separately typed organization layer.

## llmfit-aligned machine-readable records

Upstreamcommit`26450cccaf3a3f14b1822875f2473847a744a718`. Thisvideo has13losslessresearchprofiles;2have a minimalcore passingthe actualupstreamHardwareProfileJSONschema. Otherprofilesremain explicitlypartial,not paddedwithdefaults. Modelcatalogmetadata is incomplete;runconditions/prefill/concurrency/BOM/provenance remainnamespacedextensions. See[contract](llmfit/schema.md),[fieldmapping](llmfit/mapping.md),[validation](llmfit/validation-report.json). NativecompatibilityisNOTa completebuild,independentmeasurement or testedimport.
