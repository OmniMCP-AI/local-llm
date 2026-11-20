# 021 · 11 GPUs You Should Get for Local AI Before Qwen 4's Release!

> Original research summary and factual claim tables — NOT a transcript or authored script.

- Source: [11 GPUs You Should Get for Local AI Before Qwen 4's Release!](https://www.youtube.com/watch?v=6YMHMU_x4Rc) · Channel: Bruno Vega and Kai
- Caption language: en; automatic track. Retrieval: 2026-11-20T20:49:39.282488+08:00 (Asia/Shanghai).
- Coverage: returned caption track, not audio-verified; first 100.0 ms, final 1343605.0 ms. No visual charts or manufacturer specifications independently checked.

## Original research notes

This forward-looking hardware discussion is most useful as an example of recommendation under model uncertainty, rather than as a settled shopping list.

- [0:46](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=46s): The creator separates information believed to be established from expectations about an upcoming model. An advisor needs an evidence-status field for forecasts instead of presenting them as released specifications.
- [4:05](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=245s): Prompt-processing performance is related to computational work and an attributed measurement. Derived estimates should retain their assumptions, not acquire the status of a direct hardware observation.
- [7:55](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=475s): The discussion explains why producing a shorter answer does not eliminate the need to process the input. Long agent requests can therefore change the preferred hardware characteristics.
- [15:12](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=912s): A price difference is interpreted as paying for faster input processing rather than simply buying more memory. This illustrates a workload-dependent tradeoff, not a universal upgrade recommendation.
- [19:00](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=1140s): A compact system is described as having a different balance between generation and prompt handling. One impressive capacity figure cannot stand in for the whole interaction experience.

**Platform implication.** Keep prospective model assumptions separate from current, measured compatibility. Present recommendations as scenarios with clearly identified input-processing and generation requirements, and refresh the underlying prices rather than copying the video's forward-looking ranking.

## Hardware profile index

These are partial caption-evidence profiles,not LCZ-equivalent complete builds. No part from an LCZ reference has been inserted into a video configuration.

| Profile / role | Core evidence coverage | Linked observations |
| --- | --- | --- |
| [V021-HP-C001 — two3060guideconfiguration / RTX3060](hardware-profiles/V021-HP-C001.md) | configuration as explicitly narrated;creator/third-party claim,not independently verified;1/6corecategories,notcomplete | 1 |
| [V021-HP-G001 — RTX4090](hardware-profiles/V021-HP-G001.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 2 |
| [V021-HP-G002 — RX7900XTX](hardware-profiles/V021-HP-G002.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 3 |
| [V021-HP-G003 — R9700 as captioned97000](hardware-profiles/V021-HP-G003.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 3 |
| [V021-HP-G004 — ArcProB70](hardware-profiles/V021-HP-G004.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 4 |
| [V021-HP-G006 — Tesla V1 32GB as captioned;SKUuncertain](hardware-profiles/V021-HP-G006.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 0 |
| [V021-HP-E01 — Two5060Ti16GB tensor-split configuration](hardware-profiles/V021-HP-E01.md) | Caption-reported partial configuration /comparison;not a full build;1/6corecategories,notcomplete | 1 |
| [V021-HP-E02 — TwoP100 long-prompt comparison](hardware-profiles/V021-HP-E02.md) | Caption-reported partial configuration /comparison;not a full build;1/6corecategories,notcomplete | 3 |

## Test series and run conditions

Only source-reported observations follow. Unknown conditions stay unknown;rows are not certified apples-to-apples comparisons. Single-request speed,aggregate throughput,prefill,TTFT,quality,memory,power and estimates use separate series. Ranges are preserved;no new sweep points,repeats,medians or statistics were created.

### V021-S01 · Derived estimates / theoretical / ROI (not measured benchmarks)

- **Profile(s):** V021-HP-G001
- **Model / weights / quantization:** currentQwen3.8 27B unless stated;futureclaims separately marked; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** llama.cpp unless otherwise noted; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V021-P001; RTX3090 (profileunassigned) | decode ceiling · 57 tokens/s | 936GB/s modelsizeformula; theoreticalbound | [3:46](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=226s) |
| V021-P011; RTX3090 (profileunassigned) | agentturntime · 132 seconds | 64Kcoldinput+2000output;73read+59write; creator model/calculation | [6:59](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=419s) |
| V021-P012; RTX3090 (profileunassigned) | future agentturntime · 82 seconds | Qwen4 hypothetical50read+31write;roundingretained; explicit forecast,notmeasured | [7:15](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=435s) |
| V021-P015; V021-HP-G001 | agentturntimeestimate · 48 seconds | versus3090 82second hypotheticalscenario; creatorcalculation | [10:52](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=652s) |
| V021-P017; RTX5090 (profileunassigned) | decode ceiling · 108 tokens/s | 27B; theoreticalbound | [11:29](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=689s) |
| V021-P035; samepair (profileunassigned) | decode ceiling · 54 tokens/s | observed~70%ofceiling; theoreticalbound | [16:24](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=984s) |

### V021-S02 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V021-HP-C001, V021-HP-E01, V021-HP-G002, V021-HP-G003, V021-HP-G004
- **Model / weights / quantization:** currentQwen3.8 27B unless stated;futureclaims separately marked; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** llama.cpp unless otherwise noted; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V021-P002; RTX3090 (profileunassigned) | decode · 40 tokens/s | current27B; narratedmeasurement | [3:49](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=229s) |
| V021-P006; RTX4090 versus3090 (profileunassigned) | decode improvement · 15 percent | not specbandwidthratio; narratedmeasurement | [4:53](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=293s) |
| V021-P008; RTX3090 (profileunassigned) | decode · 40 to34 tokens/s | contextgrows; narratedmeasurement | [5:30](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=330s) |
| V021-P009; RTX5090 (profileunassigned) | decode · 75 to23 tokens/s | 4K to128K;llama.cpp; narratedmeasurement | [5:37](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=337s) |
| V021-P013; RTX3090 (profileunassigned) | MTP decode · 63 tokens/s | current27B; narratedmeasurement | [10:10](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=610s) |
| V021-P018; RTX5090 (profileunassigned) | MTP decode · 155 tokens/s | communityrun; narratedmeasurement | [11:32](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=692s) |
| V021-P021; V021-HP-G002 | decode · 41 tokens/s | Vulkan; narratedmeasurement | [12:26](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=746s) |
| V021-P022; V021-HP-G002 | MTP decode · up to85 tokens/s | ownerrun; ownerreport | [12:28](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=748s) |
| V021-P024; V021-HP-G003 | decode · 27–34 tokens/s | 27Bfamily; narratedresult | [13:16](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=796s) |
| V021-P025; V021-HP-G003 | MTP decode · 43–62 tokens/s | samefamily; narratedresult | [13:18](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=798s) |
| V021-P028; V021-HP-G004 | decode · 20 tokens/s | same27B; reporesultcited | [14:14](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=854s) |
| V021-P029; V021-HP-G004 | decode · 23 tokens/s | Qwen3.8;Windows; narratedtest | [14:17](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=857s) |
| V021-P030; V021-HP-G004 | SYCL/Vulkan decode ratio · 2.2 times | samecard; reporesultcited | [14:24](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=864s) |
| V021-P032; V021-HP-E01 | decode · 38 tokens/s | tensorsplit; communityresult | [15:54](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=954s) |
| V021-P033; samepair (profileunassigned) | MTP decode · 66–76 tokens/s | communityruns; narratedresult | [15:54](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=954s) |
| V021-P036; V021-HP-C001 | decode · 30–34 tokens/s | 24GBaggregate; communityresult | [16:44](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=1004s) |
| V021-P037; samepair (profileunassigned) | MTP decode · 53–59 tokens/s | 131Kfitreported; communityresult | [16:48](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=1008s) |
| V021-P040; samechapter;countnotisolated (profileunassigned) | decode · 33;48withMTP tokens/s | spokenconstructionambiguous;not33–48range; narratedresult;ASRreview | [17:42](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=1062s) |
| V021-P044; DGXSpark (profileunassigned) | decode · 12 tokens/s | 27Bdiscussion;artifactnotexplicitlyretied; creatorownrun | [19:08](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=1148s) |

### V021-S03 · Prefill / input processing

- **Profile(s):** V021-HP-E02, V021-HP-G001, V021-HP-G002, V021-HP-G003, V021-HP-G004
- **Model / weights / quantization:** currentQwen3.8 27B unless stated;futureclaims separately marked; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** llama.cpp unless otherwise noted; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V021-P003; RTX3090 (profileunassigned) | prefill · 1308 tokens/s | 4Kprompt; HardwareCorner measurement cited | [4:12](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=252s) |
| V021-P004; RTX4090 versus3090 (profileunassigned) | prefill ratio · 2.27 times | samecomparison; narratedmeasurement | [4:34](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=274s) |
| V021-P005; RTX5090 versus4090 (profileunassigned) | prefill ratio · 1.27 times | samecomparison; narratedmeasurement | [4:45](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=285s) |
| V021-P007; RTX3090 (profileunassigned) | prefill · 1308 to767 tokens/s | 4K to64K; narratedmeasurement | [5:22](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=322s) |
| V021-P014; V021-HP-G001 | prefill · ~3000 tokens/s | 27B; narratedmeasurement | [10:46](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=646s) |
| V021-P016; RTX5090 (profileunassigned) | prefill · 3750 tokens/s | 27B; communitymeasurement | [11:25](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=685s) |
| V021-P023; V021-HP-G002 | prefill · 700–900 tokens/s | Qwen3.6 27B,not3.8; narratedmeasurement | [12:32](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=752s) |
| V021-P026; V021-HP-G003 | prefill · 940 tokens/s | samefamily; narratedresult | [13:22](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=802s) |
| V021-P027; V021-HP-G004 | prefill · 718 tokens/s | 27B; reporesultcited | [14:12](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=852s) |
| V021-P031; ArcProB65 (profileunassigned) | prefill slowdown · 37.5 percent | relativeB70basedcorecount; explicit unmeasured assumption | [15:02](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=902s) |
| V021-P034; samepair (profileunassigned) | prefill · 1170 tokens/s | communityruns; narratedresult | [15:59](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=959s) |
| V021-P039; TeslaV1/V100labeluncertainpair (profileunassigned) | prefill · 1200–1400 tokens/s | tensor split pair;sourceSKUuncertain; citedwriteup | [17:36](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=1056s) |
| V021-P041; V021-HP-E02 | prefill · 130–145 tokens/s | 100Kexample; citedmeasurement | [18:28](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=1108s) |
| V021-P045; DGXSpark (profileunassigned) | prefill · 800 tokens/s | samecase; creatorownrun | [19:11](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=1151s) |

### V021-S04 · TTFT / startup latency

- **Profile(s):** V021-HP-E02
- **Model / weights / quantization:** currentQwen3.8 27B unless stated;futureclaims separately marked; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** llama.cpp unless otherwise noted; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V021-P010; RTX5090 (profileunassigned) | time to first token · 30 minutes | full262K;softwarecliff; TomHardware claim cited | [5:43](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=343s) |
| V021-P042; V021-HP-E02 | time to first token · 11.5 minutes | 100Kprompt; citedmeasurement | [18:33](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=1113s) |

### V021-S05 · TTFT / startup latency

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** currentQwen3.8 27B unless stated;futureclaims separately marked; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** vLLM/SGLang named in owner discussion;exact engine not isolated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V021-P019; RTX5090 (profileunassigned) | time to first token · 0.12 seconds | 32agents scenario;runtimevLLM/SGLangnotuniquelytied; ownerreport | [11:55](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=715s) |

### V021-S06 · Aggregate / concurrent throughput (not single-request speed)

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** currentQwen3.8 27B unless stated;futureclaims separately marked; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** vLLM/SGLang named in owner discussion;exact engine not isolated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V021-P020; RTX5090 (profileunassigned) | aggregate throughput · 970 tokens/s | 32agents,notper-user; ownerreport | [11:58](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=718s) |

### V021-S07 · Elapsed workflow / phase time (not TTFT unless explicit)

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** currentQwen3.8 27B unless stated;futureclaims separately marked; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** llama.cpp unless otherwise noted; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V021-P038; samepair (profileunassigned) | 129Kprompt elapsed time · 4.5 minutes | end-to-end;do notlabelTTFT; citedmeasurement | [17:00](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=1020s) |

### V021-S08 · Power / energy (boundary-dependent)

- **Profile(s):** V021-HP-E02
- **Model / weights / quantization:** currentQwen3.8 27B unless stated;futureclaims separately marked; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** llama.cpp unless otherwise noted; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V021-P043; V021-HP-E02 | electrical power · up to500 W | pair;notfullsystemboundaryverified; creatorhardwareclaim | [18:48](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=1128s) |

## Detailed hardware profiles

Minimum fields follow motherboard/CPU/RAMmodules+speed/GPUvariant+count+VRAM/PSU/storage. “Unknown”means not reported,not an invitation to fill from a different owner or manufacturer memory. Costs are quotes/paid/estimates only where identified;no fakeBOMtotal.

### V021-HP-C001 · two3060guideconfiguration / RTX3060

**Role:** configuration as explicitly narrated;creator/third-party claim,not independently verified. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=998s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** $332each;$664pair · Source-quoted price/estimate,not verified paid price · Keep literal currency;price date not established. Video publication date is not a purchase date.. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=998s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=998s) |
| RAM | — | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=998s) |
| GPU | RTX3060 | qty 2; PerGPUVRAM:12GB each;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=998s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=998s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=998s) |

**Other component disclosures:** 24GBaggregateexplicitlystated

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V021-P036 / V021-S02 | currentQwen3.8 27B unless stated;futureclaims separately marked; not stated; llama.cpp unless otherwise noted | decode: 30–34 tokens/s | 24GBaggregate; communityresult; [16:44](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=1004s) |

---

### V021-HP-G001 · RTX4090

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=631s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** $3479 · Source-quoted price/estimate,not verified paid price · Keep literal currency;price date not established. Video publication date is not a purchase date.. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | RTX4090 | PerGPUVRAM:24GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=631s) |

**Other component disclosures:** 1008GB/s

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** 450W; reported product rating/recommendation;not whole-system measurement;NOT a PSU specification Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V021-P014 / V021-S03 | currentQwen3.8 27B unless stated;futureclaims separately marked; not stated; llama.cpp unless otherwise noted | prefill: ~3000 tokens/s | 27B; narratedmeasurement; [10:46](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=646s) |
| V021-P015 / V021-S01 | currentQwen3.8 27B unless stated;futureclaims separately marked; not stated; llama.cpp unless otherwise noted | agentturntimeestimate: 48 seconds | versus3090 82second hypotheticalscenario; creatorcalculation; [10:52](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=652s) |

---

### V021-HP-G002 · RX7900XTX

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=734s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** $1244 · Source-quoted price/estimate,not verified paid price · Keep literal currency;price date not established. Video publication date is not a purchase date.. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | RX7900XTX | PerGPUVRAM:24GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=734s) |

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
| V021-P021 / V021-S02 | currentQwen3.8 27B unless stated;futureclaims separately marked; not stated; llama.cpp unless otherwise noted | decode: 41 tokens/s | Vulkan; narratedmeasurement; [12:26](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=746s) |
| V021-P022 / V021-S02 | currentQwen3.8 27B unless stated;futureclaims separately marked; not stated; llama.cpp unless otherwise noted | MTP decode: up to85 tokens/s | ownerrun; ownerreport; [12:28](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=748s) |
| V021-P023 / V021-S03 | currentQwen3.8 27B unless stated;futureclaims separately marked; not stated; llama.cpp unless otherwise noted | prefill: 700–900 tokens/s | Qwen3.6 27B,not3.8; narratedmeasurement; [12:32](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=752s) |

---

### V021-HP-G003 · R9700 as captioned97000

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=775s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** $1700retail;$2500eBay · Source-quoted price/estimate,not verified paid price · Keep literal currency;price date not established. Video publication date is not a purchase date.. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | R9700 as captioned97000 | PerGPUVRAM:32GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=775s) |

**Other component disclosures:** 640GB/s

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** 300W; reported product rating/recommendation;not whole-system measurement;NOT a PSU specification Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V021-P024 / V021-S02 | currentQwen3.8 27B unless stated;futureclaims separately marked; not stated; llama.cpp unless otherwise noted | decode: 27–34 tokens/s | 27Bfamily; narratedresult; [13:16](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=796s) |
| V021-P025 / V021-S02 | currentQwen3.8 27B unless stated;futureclaims separately marked; not stated; llama.cpp unless otherwise noted | MTP decode: 43–62 tokens/s | samefamily; narratedresult; [13:18](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=798s) |
| V021-P026 / V021-S03 | currentQwen3.8 27B unless stated;futureclaims separately marked; not stated; llama.cpp unless otherwise noted | prefill: 940 tokens/s | samefamily; narratedresult; [13:22](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=802s) |

---

### V021-HP-G004 · ArcProB70

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=818s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** $949launch · Source-quoted price/estimate,not verified paid price · Keep literal currency;price date not established. Video publication date is not a purchase date.. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | ArcProB70 | PerGPUVRAM:32GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=818s) |

**Other component disclosures:** 608GB/s

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V021-P027 / V021-S03 | currentQwen3.8 27B unless stated;futureclaims separately marked; not stated; llama.cpp unless otherwise noted | prefill: 718 tokens/s | 27B; reporesultcited; [14:12](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=852s) |
| V021-P028 / V021-S02 | currentQwen3.8 27B unless stated;futureclaims separately marked; not stated; llama.cpp unless otherwise noted | decode: 20 tokens/s | same27B; reporesultcited; [14:14](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=854s) |
| V021-P029 / V021-S02 | currentQwen3.8 27B unless stated;futureclaims separately marked; not stated; llama.cpp unless otherwise noted | decode: 23 tokens/s | Qwen3.8;Windows; narratedtest; [14:17](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=857s) |
| V021-P030 / V021-S02 | currentQwen3.8 27B unless stated;futureclaims separately marked; not stated; llama.cpp unless otherwise noted | SYCL/Vulkan decode ratio: 2.2 times | samecard; reporesultcited; [14:24](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=864s) |

---

### V021-HP-G006 · Tesla V1 32GB as captioned;SKUuncertain

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=1041s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** $843 · Source-quoted price/estimate,not verified paid price · Keep literal currency;price date not established. Video publication date is not a purchase date.. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | Tesla V1 32GB as captioned;SKUuncertain | PerGPUVRAM:32GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=1041s) |

**Other component disclosures:** 900GB/s

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** No performance row can be safely assigned to this exact profile. Product mention/recommendation is not a measured build.

---

### V021-HP-E01 · Two5060Ti16GB tensor-split configuration

**Role:** Caption-reported partial configuration /comparison;not a full build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=954s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=954s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=954s) |
| RAM | — | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=954s) |
| GPU | RTX5060Ti | qty 2; PerGPUVRAM:16GBeach;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=954s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=954s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=954s) |

**Selection / tradeoffs:** Unknown / not reported Concurrentusers can eliminate speculationgains;not guaranteed76tok/sfor everyworkload.

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Tensor split;MTP variants Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V021-P032 / V021-S02 | currentQwen3.8 27B unless stated;futureclaims separately marked; not stated; llama.cpp unless otherwise noted | decode: 38 tokens/s | tensorsplit; communityresult; [15:54](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=954s) |

---

### V021-HP-E02 · TwoP100 long-prompt comparison

**Role:** Caption-reported partial configuration /comparison;not a full build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=1108s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=1108s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=1108s) |
| RAM | — | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=1108s) |
| GPU | P100 | qty 2; PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=1108s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=1108s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=1108s) |

**Selection / tradeoffs:** Unknown / not reported Lowdecodecost does not remove long cold-prefillwaits;hostPSUunknown.

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V021-P041 / V021-S03 | currentQwen3.8 27B unless stated;futureclaims separately marked; not stated; llama.cpp unless otherwise noted | prefill: 130–145 tokens/s | 100Kexample; citedmeasurement; [18:28](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=1108s) |
| V021-P042 / V021-S04 | currentQwen3.8 27B unless stated;futureclaims separately marked; not stated; llama.cpp unless otherwise noted | time to first token: 11.5 minutes | 100Kprompt; citedmeasurement; [18:33](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=1113s) |
| V021-P043 / V021-S08 | currentQwen3.8 27B unless stated;futureclaims separately marked; not stated; llama.cpp unless otherwise noted | electrical power: up to500 W | pair;notfullsystemboundaryverified; creatorhardwareclaim; [18:48](https://www.youtube.com/watch?v=6YMHMU_x4Rc&t=1128s) |


## Scope

Caption-only evidence;no chart/video viewing or independent hardware validation. ASR and source contradictions are retained. Full original caption text is not included. Original450claim records and99hardwarefact records are preserved byte-for-byte in their originalCSVs;new profiles/series are a separately typed organization layer.

## llmfit-aligned machine-readable records

Upstreamcommit`26450cccaf3a3f14b1822875f2473847a744a718`. Thisvideo has8losslessresearchprofiles;0have a minimalcore passingthe actualupstreamHardwareProfileJSONschema. Otherprofilesremain explicitlypartial,not paddedwithdefaults. Modelcatalogmetadata is incomplete;runconditions/prefill/concurrency/BOM/provenance remainnamespacedextensions. See[contract](llmfit/schema.md),[fieldmapping](llmfit/mapping.md),[validation](llmfit/validation-report.json). NativecompatibilityisNOTa completebuild,independentmeasurement or testedimport.
