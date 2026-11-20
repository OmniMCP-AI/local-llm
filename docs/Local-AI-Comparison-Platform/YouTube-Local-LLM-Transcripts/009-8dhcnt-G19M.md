# 009 · Splash 1.6.1 is INSANELY FAST! Local AI on M6 Mac Mini

> Original research summary and factual claim tables — NOT a transcript or authored script.

- Source: [Splash 1.6.1 is INSANELY FAST! Local AI on M6 Mac Mini](https://www.youtube.com/watch?v=8dhcnt-G19M) · Channel: Execute Automation
- Caption language: en; automatic track. Retrieval: 2026-11-20T20:49:39.282488+08:00 (Asia/Shanghai).
- Coverage: returned caption track, not audio-verified; first 0.0 ms, final 988202.0 ms. No visual charts or manufacturer specifications independently checked.

## Original research notes

A hands-on Mac runtime demonstration is useful for separating observed responsiveness from broader claims about model intelligence or universal hardware performance.

- [0:37](https://www.youtube.com/watch?v=8dhcnt-G19M&t=37s): The creator describes different generation rates for a dense model and notes sensitivity to context and reasoning settings. A model name alone does not identify a comparable workload.
- [3:22](https://www.youtube.com/watch?v=8dhcnt-G19M&t=202s): A sparse architecture is contrasted with using all model parameters for each output step. The demonstration illustrates why parameter counts alone can mislead hardware comparisons.
- [5:57](https://www.youtube.com/watch?v=8dhcnt-G19M&t=357s): The presenter explicitly limits the intelligence comparison while showing generated output. Visible speed and a plausible answer do not establish task quality or correctness across a wider evaluation suite.
- [8:32](https://www.youtube.com/watch?v=8dhcnt-G19M&t=512s): Changing the reasoning setting changes the displayed throughput. An advisor should preserve that control rather than treating the fastest displayed configuration as the model's representative operating point.
- [13:49](https://www.youtube.com/watch?v=8dhcnt-G19M&t=829s): A repository-related task is introduced with an expectation of slower response than a smaller sparse model. More realistic tasks may expose latency that a short chat demonstration hides.

**Platform implication.** Capture runtime version, model architecture, context and reasoning mode together. Use demonstrations as qualitative workflow evidence; require repeatable tasks and output-quality checks before turning their on-screen rates into comparative benchmark data.

## Hardware profile index

These are partial caption-evidence profiles,not LCZ-equivalent complete builds. No part from an LCZ reference has been inserted into a video configuration.

| Profile / role | Core evidence coverage | Linked observations |
| --- | --- | --- |
| [V009-HP-TEST — Apple M6 Mac Mini (caption label; not independently verified)](hardware-profiles/V009-HP-TEST.md) | creator demonstration machine; RAM and GPU-core count not stated;0/6corecategories,notcomplete | 12 |

Only1 grounded profile is available;additional complete machines cannot be invented from this source.

## Test series and run conditions

Only source-reported observations follow. Unknown conditions stay unknown;rows are not certified apples-to-apples comparisons. Single-request speed,aggregate throughput,prefill,TTFT,quality,memory,power and estimates use separate series. Ranges are preserved;no new sweep points,repeats,medians or statistics were created.

### V009-S01 · Reported generation throughput (concurrency scope unreported unless row states it)

- **Profile(s):** V009-HP-TEST
- **Model / weights / quantization:** Qwen3.6 35BMoE; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Splash1.6.1 per title; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V009-P001; V009-HP-TEST | generation throughput · ~170 tokens/s | headline;contextnotfixed; narrated result;not independently verified | [0:32](https://www.youtube.com/watch?v=8dhcnt-G19M&t=32s) |
| V009-P010; V009-HP-TEST | generation throughput · 93–95 tokens/s | 128Ksetting;codequestion; narrated result;not independently verified | [12:23](https://www.youtube.com/watch?v=8dhcnt-G19M&t=743s) |

### V009-S02 · Reported generation throughput (concurrency scope unreported unless row states it)

- **Profile(s):** V009-HP-TEST
- **Model / weights / quantization:** Qwen3.8 27Bdense; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Splash1.6.1 per title; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V009-P002; V009-HP-TEST | generation throughput · 56–70 tokens/s | headline;thinking/contextvary; narrated result;not independently verified | [0:42](https://www.youtube.com/watch?v=8dhcnt-G19M&t=42s) |

### V009-S03 · Reported generation throughput (concurrency scope unreported unless row states it)

- **Profile(s):** V009-HP-TEST
- **Model / weights / quantization:** selectedMoE,exactartifactnotrestated; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Splash1.6.1 per title; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V009-P003; V009-HP-TEST | generation throughput · 152 tokens/s | firstquestion; narrated result;not independently verified | [4:38](https://www.youtube.com/watch?v=8dhcnt-G19M&t=278s) |

### V009-S04 · Reported generation throughput (concurrency scope unreported unless row states it)

- **Profile(s):** V009-HP-TEST
- **Model / weights / quantization:** sameMoE; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Splash1.6.1 per title; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V009-P004; V009-HP-TEST | generation throughput · 113 tokens/s | secondquestion,morethinking; narrated result;not independently verified | [4:47](https://www.youtube.com/watch?v=8dhcnt-G19M&t=287s) |
| V009-P005; V009-HP-TEST | generation throughput · 117 tokens/s | code-generationrequest; narrated result;not independently verified | [6:01](https://www.youtube.com/watch?v=8dhcnt-G19M&t=361s) |
| V009-P011; V009-HP-TEST | generation throughput · 103–107 tokens/s | repository/toolcalls; narrated result;not independently verified | [12:50](https://www.youtube.com/watch?v=8dhcnt-G19M&t=770s) |

### V009-S05 · Reported generation throughput (concurrency scope unreported unless row states it)

- **Profile(s):** V009-HP-TEST
- **Model / weights / quantization:** Qwen3.8 27B; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Splash1.6.1 per title; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V009-P006; V009-HP-TEST | generation throughput · 33 tokens/s | extra-highthinking; narrated result;not independently verified | [8:35](https://www.youtube.com/watch?v=8dhcnt-G19M&t=515s) |
| V009-P007; V009-HP-TEST | generation throughput · 46 tokens/s | mediumthinking;shortgreeting; narrated result;not independently verified | [8:44](https://www.youtube.com/watch?v=8dhcnt-G19M&t=524s) |
| V009-P008; V009-HP-TEST | generation throughput · 28–30 tokens/s | extra-high;contextnotfixed; narrated result;not independently verified | [10:01](https://www.youtube.com/watch?v=8dhcnt-G19M&t=601s) |
| V009-P009; V009-HP-TEST | generation throughput · 32 tokens/s | reportedaverage; narrated result;not independently verified | [11:24](https://www.youtube.com/watch?v=8dhcnt-G19M&t=684s) |

### V009-S06 · Reported generation throughput (concurrency scope unreported unless row states it)

- **Profile(s):** V009-HP-TEST
- **Model / weights / quantization:** dense27B selection; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Splash1.6.1 per title; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V009-P012; V009-HP-TEST | generation throughput · 34 tokens/s | repositoryanalysis;predicted30notseparatemeasurement; narrated result;not independently verified | [14:10](https://www.youtube.com/watch?v=8dhcnt-G19M&t=850s) |

## Detailed hardware profiles

Minimum fields follow motherboard/CPU/RAMmodules+speed/GPUvariant+count+VRAM/PSU/storage. “Unknown”means not reported,not an invitation to fill from a different owner or manufacturer memory. Costs are quotes/paid/estimates only where identified;no fakeBOMtotal.

### V009-HP-TEST · Apple M6 Mac Mini (caption label; not independently verified)

**Role:** creator demonstration machine; RAM and GPU-core count not stated. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=8dhcnt-G19M&t=26s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 0/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=8dhcnt-G19M&t=26s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=8dhcnt-G19M&t=26s) |
| RAM | — | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=8dhcnt-G19M&t=26s) |
| GPU | — | PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=8dhcnt-G19M&t=26s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=8dhcnt-G19M&t=26s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=8dhcnt-G19M&t=26s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Splash1.6.1 per displayed video title; runtime version not separately certified Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, gpu, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V009-P001 / V009-S01 | Qwen3.6 35BMoE; not stated; Splash1.6.1 per title | generation throughput: ~170 tokens/s | headline;contextnotfixed; narrated result;not independently verified; [0:32](https://www.youtube.com/watch?v=8dhcnt-G19M&t=32s) |
| V009-P002 / V009-S02 | Qwen3.8 27Bdense; not stated; Splash1.6.1 per title | generation throughput: 56–70 tokens/s | headline;thinking/contextvary; narrated result;not independently verified; [0:42](https://www.youtube.com/watch?v=8dhcnt-G19M&t=42s) |
| V009-P003 / V009-S03 | selectedMoE,exactartifactnotrestated; not stated; Splash1.6.1 per title | generation throughput: 152 tokens/s | firstquestion; narrated result;not independently verified; [4:38](https://www.youtube.com/watch?v=8dhcnt-G19M&t=278s) |
| V009-P004 / V009-S04 | sameMoE; not stated; Splash1.6.1 per title | generation throughput: 113 tokens/s | secondquestion,morethinking; narrated result;not independently verified; [4:47](https://www.youtube.com/watch?v=8dhcnt-G19M&t=287s) |
| V009-P005 / V009-S04 | sameMoE; not stated; Splash1.6.1 per title | generation throughput: 117 tokens/s | code-generationrequest; narrated result;not independently verified; [6:01](https://www.youtube.com/watch?v=8dhcnt-G19M&t=361s) |
| V009-P006 / V009-S05 | Qwen3.8 27B; not stated; Splash1.6.1 per title | generation throughput: 33 tokens/s | extra-highthinking; narrated result;not independently verified; [8:35](https://www.youtube.com/watch?v=8dhcnt-G19M&t=515s) |
| V009-P007 / V009-S05 | Qwen3.8 27B; not stated; Splash1.6.1 per title | generation throughput: 46 tokens/s | mediumthinking;shortgreeting; narrated result;not independently verified; [8:44](https://www.youtube.com/watch?v=8dhcnt-G19M&t=524s) |
| V009-P008 / V009-S05 | Qwen3.8 27B; not stated; Splash1.6.1 per title | generation throughput: 28–30 tokens/s | extra-high;contextnotfixed; narrated result;not independently verified; [10:01](https://www.youtube.com/watch?v=8dhcnt-G19M&t=601s) |
| V009-P009 / V009-S05 | Qwen3.8 27B; not stated; Splash1.6.1 per title | generation throughput: 32 tokens/s | reportedaverage; narrated result;not independently verified; [11:24](https://www.youtube.com/watch?v=8dhcnt-G19M&t=684s) |
| V009-P010 / V009-S01 | Qwen3.6 35BMoE; not stated; Splash1.6.1 per title | generation throughput: 93–95 tokens/s | 128Ksetting;codequestion; narrated result;not independently verified; [12:23](https://www.youtube.com/watch?v=8dhcnt-G19M&t=743s) |
| V009-P011 / V009-S04 | sameMoE; not stated; Splash1.6.1 per title | generation throughput: 103–107 tokens/s | repository/toolcalls; narrated result;not independently verified; [12:50](https://www.youtube.com/watch?v=8dhcnt-G19M&t=770s) |
| V009-P012 / V009-S06 | dense27B selection; not stated; Splash1.6.1 per title | generation throughput: 34 tokens/s | repositoryanalysis;predicted30notseparatemeasurement; narrated result;not independently verified; [14:10](https://www.youtube.com/watch?v=8dhcnt-G19M&t=850s) |


## Scope

Caption-only evidence;no chart/video viewing or independent hardware validation. ASR and source contradictions are retained. Full original caption text is not included. Original450claim records and99hardwarefact records are preserved byte-for-byte in their originalCSVs;new profiles/series are a separately typed organization layer.
