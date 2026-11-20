# 012 · Basalt Runs Qwen 3.8 Flash Next At 224 Token/sec

> Original research summary and factual claim tables — NOT a transcript or authored script.

- Source: [Basalt Runs Qwen 3.8 Flash Next At 224 Token/sec](https://www.youtube.com/watch?v=wC6jsOU4jII) · Channel: Kai
- Caption language: en; automatic track. Retrieval: 2026-11-20T20:49:39.282488+08:00 (Asia/Shanghai).
- Coverage: returned caption track, not audio-verified; first 100.0 ms, final 1575007.0 ms. No visual charts or manufacturer specifications independently checked.

## Original research notes

This runtime comparison is especially useful for understanding how speed gains can depend on compatibility restrictions and quality-affecting execution settings.

- [0:55](https://www.youtube.com/watch?v=wC6jsOU4jII&t=55s): The presenter separates changing engines from changing an existing configuration option. Attribution matters: a benefit from one setting should not automatically be credited to a different runtime.
- [5:13](https://www.youtube.com/watch?v=wC6jsOU4jII&t=313s): The compatibility discussion limits which devices can act as the main accelerator. A capacity contribution from a secondary card is different from full support for that architecture.
- [9:18](https://www.youtube.com/watch?v=wC6jsOU4jII&t=558s): The video questions whether a favorable optimization was deliberately enabled or selected implicitly. Default settings can change what an apparently equivalent comparison is actually measuring.
- [13:24](https://www.youtube.com/watch?v=wC6jsOU4jII&t=804s): The presenter relates skipped work to file choice and available graphics memory. Speed increases may therefore interact with compression and capacity rather than representing a free improvement.
- [22:02](https://www.youtube.com/watch?v=wC6jsOU4jII&t=1322s): Rapid releases and changing flags are presented as an operational burden. A result tied to a moving runtime needs configuration history, not merely the latest project name.

**Platform implication.** Model the benchmark unit as a runtime version plus explicit settings and model artifact. For the platform, expose quality-affecting shortcuts and compatibility boundaries before offering a headline speedup or automatic migration recommendation.

## Hardware profile index

These are partial caption-evidence profiles,not LCZ-equivalent complete builds. No part from an LCZ reference has been inserted into a video configuration.

| Profile / role | Core evidence coverage | Linked observations |
| --- | --- | --- |
| [V012-HP-C001 — owner comparative machine / RTX5090](hardware-profiles/V012-HP-C001.md) | configuration as explicitly narrated;creator/third-party claim,not independently verified;2/6corecategories,notcomplete | 0 |
| [V012-HP-G001 — RTX5080](hardware-profiles/V012-HP-G001.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 2 |
| [V012-HP-G002 — RTX5060Ti](hardware-profiles/V012-HP-G002.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 1 |
| [V012-HP-G003 — RTXPro1000Blackwell laptop](hardware-profiles/V012-HP-G003.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 1 |
| [V012-HP-E01 — Different Windows11 owner:Ryzen9 5950X/RTX5080/128GB](hardware-profiles/V012-HP-E01.md) | Caption-reported partial configuration /comparison;not a full build;3/6corecategories,notcomplete | 4 |

## Test series and run conditions

Only source-reported observations follow. Unknown conditions stay unknown;rows are not certified apples-to-apples comparisons. Single-request speed,aggregate throughput,prefill,TTFT,quality,memory,power and estimates use separate series. Ranges are preserved;no new sweep points,repeats,medians or statistics were created.

### V012-S01 · TTFT / startup latency

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** Qwen3.8FlashNext125B family;artifact varies; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Basalt/Strata; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V012-P001; owner setup not isolated (profileunassigned) | time to first token · 20.4 to13.5 seconds | Strata toBasalt;same prompt; narrated test | [3:06](https://www.youtube.com/watch?v=wC6jsOU4jII&t=186s) |

### V012-S02 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V012-HP-E01, V012-HP-G002, V012-HP-G003
- **Model / weights / quantization:** Qwen3.8FlashNext125B family;artifact varies; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Basalt/Strata; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V012-P002; same owner (profileunassigned) | decode · 158–208 vs223–231 tokens/s | Strata vsBasalt;samecodingtask;IQ3; narrated test | [3:38](https://www.youtube.com/watch?v=wC6jsOU4jII&t=218s) |
| V012-P003; same owner (profileunassigned) | decode · 223–259 vs377–400 tokens/s | Strata vsBasalt;Q2; narrated test | [3:46](https://www.youtube.com/watch?v=wC6jsOU4jII&t=226s) |
| V012-P006; V012-HP-E01 | decode · 80–90 tokens/s | initialswitch;sameapproxasStrata; owner report | [9:53](https://www.youtube.com/watch?v=wC6jsOU4jII&t=593s) |
| V012-P007; V012-HP-E01 | Strata decode · 80 to66 tokens/s | tailskip disabled; owner report | [10:22](https://www.youtube.com/watch?v=wC6jsOU4jII&t=622s) |
| V012-P008; V012-HP-E01 | full-model decode · 93 vs66 tokens/s | Basalt vsStrata;skipoff; owner report | [10:41](https://www.youtube.com/watch?v=wC6jsOU4jII&t=641s) |
| V012-P009; V012-HP-E01 | Basalt decode · 120 tokens/s | root-tail-skip enabled,not equivalentlyfullmodel; owner report | [11:09](https://www.youtube.com/watch?v=wC6jsOU4jII&t=669s) |
| V012-P010; RTX5090 capped to16GB (profileunassigned) | decode · 192 to299 tokens/s | skip+routingbias test;qualityfell5.2points; narrated test | [13:53](https://www.youtube.com/watch?v=wC6jsOU4jII&t=833s) |
| V012-P017; RTX5070Ti/Windowsissue (profileunassigned) | decode · 124 to17.7 tokens/s | taggedrelease versusNov13build;samehardware; ownerregressionreport | [19:02](https://www.youtube.com/watch?v=wC6jsOU4jII&t=1142s) |
| V012-P018; two5070Ti as captioned (profileunassigned) | decode · 25 vs100 tokens/s | Basalt vsStrata;Windows; owner report;ASRcardcountneedscheck | [19:25](https://www.youtube.com/watch?v=wC6jsOU4jII&t=1165s) |
| V012-P019; V012-HP-G003 | decode · 16–17 vs24–27 tokens/s | Basalt vsStrata;PowerSaverCPU15Wafter27s; owner measurement | [20:03](https://www.youtube.com/watch?v=wC6jsOU4jII&t=1203s) |
| V012-P022; V012-HP-G002 | decode · 107.5 vs137 tokens/s | NVFP4 vsIQ3 artifact;notidenticalquant; communityreport | [21:02](https://www.youtube.com/watch?v=wC6jsOU4jII&t=1262s) |
| V012-P023; RX9070XT (profileunassigned) | decode regression · 50 to14 tokens/s | Strataengine0.1.57 as captioned;SSDmaxed; owner report | [22:29](https://www.youtube.com/watch?v=wC6jsOU4jII&t=1349s) |

### V012-S03 · Reported generation throughput (concurrency scope unreported unless row states it)

- **Profile(s):** V012-HP-G001
- **Model / weights / quantization:** Qwen3.8FlashNext125B family;artifact varies; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Basalt/Strata; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V012-P004; V012-HP-G001 | mixed-task headline throughput · 218.6 tokens/s | communityLinuxrow; creator sourcecorrection | [5:50](https://www.youtube.com/watch?v=wC6jsOU4jII&t=350s) |
| V012-P016; RTX5080/Linux (profileunassigned) | mixed-task versus prose throughput · 218.6 vs158.2 tokens/s | samecommunityrow;notallprose224; narrated table explanation | [18:31](https://www.youtube.com/watch?v=wC6jsOU4jII&t=1111s) |

### V012-S04 · Other reported observations / stability (not a comparable speed benchmark)

- **Profile(s):** V012-HP-G001
- **Model / weights / quantization:** Qwen3.8FlashNext125B family;artifact varies; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Basalt/Strata; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V012-P005; V012-HP-G001 | resident experts · 4529 of24576 experts | 3bit;~18%resident;~75%lookups hit; narrated configuration measurement | [7:15](https://www.youtube.com/watch?v=wC6jsOU4jII&t=435s) |
| V012-P024; RTX5070Ti/48GBDDR4 (profileunassigned) | stability · 4days;>30M inputtokens total | agent-sessionanecdote,notthroughput; owner report | [23:34](https://www.youtube.com/watch?v=wC6jsOU4jII&t=1414s) |

### V012-S05 · Elapsed workflow / phase time (not TTFT unless explicit)

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** Qwen3.8FlashNext125B family;artifact varies; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Basalt/Strata; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V012-P011; Akira comparison;GPU not isolated (profileunassigned) | coding-task completion · 7.2 to5.4 minutes | Strata toBasalt;4turns36hiddentests,bothpass; narrated test | [16:52](https://www.youtube.com/watch?v=wC6jsOU4jII&t=1012s) |
| V012-P013; same comparison (profileunassigned) | coding-task completion · 12.1 to9 minutes | 3bit;Strata toBasalt; narrated test | [17:37](https://www.youtube.com/watch?v=wC6jsOU4jII&t=1057s) |
| V012-P014; 59D as captioned;identityuncertain (profileunassigned) | task-time reduction · 7 percent | 18tasks;differentfileoneachengine; owner report,non-equivalentartifact | [17:48](https://www.youtube.com/watch?v=wC6jsOU4jII&t=1068s) |
| V012-P015; RTX5070Ti (profileunassigned) | task-time reduction · 10 percent | taskconditionsnotgiven; ownerreport | [17:56](https://www.youtube.com/watch?v=wC6jsOU4jII&t=1076s) |
| V012-P020; setupnotisolated (profileunassigned) | 8requestcompletion · 187 vs352 seconds | 127Ktokens/request;serial versusparallel; narrated concurrencytest | [20:27](https://www.youtube.com/watch?v=wC6jsOU4jII&t=1227s) |

### V012-S06 · Prefill / input processing

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** Qwen3.8FlashNext125B family;artifact varies; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Basalt/Strata; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V012-P012; same task comparison (profileunassigned) | prefill · 6233 to8196 tokens/s | Strata toBasalt; narrated test | [17:15](https://www.youtube.com/watch?v=wC6jsOU4jII&t=1035s) |
| V012-P021; same8requesttest (profileunassigned) | parallel prefill · 2000 vs5100 tokens/s | Basalt vsStrata;8parallel; narrated concurrencytest | [20:36](https://www.youtube.com/watch?v=wC6jsOU4jII&t=1236s) |

## Detailed hardware profiles

Minimum fields follow motherboard/CPU/RAMmodules+speed/GPUvariant+count+VRAM/PSU/storage. “Unknown”means not reported,not an invitation to fill from a different owner or manufacturer memory. Costs are quotes/paid/estimates only where identified;no fakeBOMtotal.

### V012-HP-C001 · owner comparative machine / RTX5090

**Role:** configuration as explicitly narrated;creator/third-party claim,not independently verified. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=wC6jsOU4jII&t=170s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 2/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=wC6jsOU4jII&t=170s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=wC6jsOU4jII&t=170s) |
| RAM | system/unspecified RAM: 64GB | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=wC6jsOU4jII&t=170s) |
| GPU | RTX5090 | qty 1; PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=wC6jsOU4jII&t=170s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=wC6jsOU4jII&t=170s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=wC6jsOU4jII&t=170s) |

**Other component disclosures:** same128Kprompt

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Strata versus Basalt Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** No performance row can be safely assigned to this exact profile. Product mention/recommendation is not a measured build.

---

### V012-HP-G001 · RTX5080

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=wC6jsOU4jII&t=432s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | RTX5080 | PerGPUVRAM:16GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=wC6jsOU4jII&t=432s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V012-P004 / V012-S03 | Qwen3.8FlashNext125B family;artifact varies; not stated; Basalt/Strata | mixed-task headline throughput: 218.6 tokens/s | communityLinuxrow; creator sourcecorrection; [5:50](https://www.youtube.com/watch?v=wC6jsOU4jII&t=350s) |
| V012-P005 / V012-S04 | Qwen3.8FlashNext125B family;artifact varies; not stated; Basalt/Strata | resident experts: 4529 of24576 experts | 3bit;~18%resident;~75%lookups hit; narrated configuration measurement; [7:15](https://www.youtube.com/watch?v=wC6jsOU4jII&t=435s) |

---

### V012-HP-G002 · RTX5060Ti

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=wC6jsOU4jII&t=1258s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | RTX5060Ti | PerGPUVRAM:16GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=wC6jsOU4jII&t=1258s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V012-P022 / V012-S02 | Qwen3.8FlashNext125B family;artifact varies; not stated; Basalt/Strata | decode: 107.5 vs137 tokens/s | NVFP4 vsIQ3 artifact;notidenticalquant; communityreport; [21:02](https://www.youtube.com/watch?v=wC6jsOU4jII&t=1262s) |

---

### V012-HP-G003 · RTXPro1000Blackwell laptop

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=wC6jsOU4jII&t=1197s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | RTXPro1000Blackwell laptop | PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=wC6jsOU4jII&t=1197s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** CPU15W PowerSaver,not GPU TDP; reported product rating/recommendation;not whole-system measurement;NOT a PSU specification Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V012-P019 / V012-S02 | Qwen3.8FlashNext125B family;artifact varies; not stated; Basalt/Strata | decode: 16–17 vs24–27 tokens/s | Basalt vsStrata;PowerSaverCPU15Wafter27s; owner measurement; [20:03](https://www.youtube.com/watch?v=wC6jsOU4jII&t=1203s) |

---

### V012-HP-E01 · Different Windows11 owner:Ryzen9 5950X/RTX5080/128GB

**Role:** Caption-reported partial configuration /comparison;not a full build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=wC6jsOU4jII&t=577s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 3/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=wC6jsOU4jII&t=577s) |
| CPU | Ryzen9 5950X | — | — | [source](https://www.youtube.com/watch?v=wC6jsOU4jII&t=577s) |
| RAM | 128GBDDR4-3200 as narrated | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=wC6jsOU4jII&t=577s) |
| GPU | RTX5080 | PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=wC6jsOU4jII&t=577s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=wC6jsOU4jII&t=577s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=wC6jsOU4jII&t=577s) |

**Selection / tradeoffs:** Unknown / not reported Separate from5090/64GB owner and Linux5080 rows.

**Expansion / compatibility:** Unknown / not reported Tail-skip mismatch found inStrata config;setting it tozero reduces speed but changes completeness. Do not compare skipped-model speed as same execution.

**Deployment:** Windows11;Strata versus Basalt Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V012-P006 / V012-S02 | Qwen3.8FlashNext125B family;artifact varies; not stated; Basalt/Strata | decode: 80–90 tokens/s | initialswitch;sameapproxasStrata; owner report; [9:53](https://www.youtube.com/watch?v=wC6jsOU4jII&t=593s) |
| V012-P007 / V012-S02 | Qwen3.8FlashNext125B family;artifact varies; not stated; Basalt/Strata | Strata decode: 80 to66 tokens/s | tailskip disabled; owner report; [10:22](https://www.youtube.com/watch?v=wC6jsOU4jII&t=622s) |
| V012-P008 / V012-S02 | Qwen3.8FlashNext125B family;artifact varies; not stated; Basalt/Strata | full-model decode: 93 vs66 tokens/s | Basalt vsStrata;skipoff; owner report; [10:41](https://www.youtube.com/watch?v=wC6jsOU4jII&t=641s) |
| V012-P009 / V012-S02 | Qwen3.8FlashNext125B family;artifact varies; not stated; Basalt/Strata | Basalt decode: 120 tokens/s | root-tail-skip enabled,not equivalentlyfullmodel; owner report; [11:09](https://www.youtube.com/watch?v=wC6jsOU4jII&t=669s) |


## Scope

Caption-only evidence;no chart/video viewing or independent hardware validation. ASR and source contradictions are retained. Full original caption text is not included. Original450claim records and99hardwarefact records are preserved byte-for-byte in their originalCSVs;new profiles/series are a separately typed organization layer.

## llmfit-aligned machine-readable records

Upstreamcommit`26450cccaf3a3f14b1822875f2473847a744a718`. Thisvideo has5losslessresearchprofiles;2have a minimalcore passingthe actualupstreamHardwareProfileJSONschema. Otherprofilesremain explicitlypartial,not paddedwithdefaults. Modelcatalogmetadata is incomplete;runconditions/prefill/concurrency/BOM/provenance remainnamespacedextensions. See[contract](llmfit/schema.md),[fieldmapping](llmfit/mapping.md),[validation](llmfit/validation-report.json). NativecompatibilityisNOTa completebuild,independentmeasurement or testedimport.
