# 048 · M5、M6 Mac 如何選? Mac 跑本地 AI:模型裝得下,為什麼跑Agent就想退貨?

> Original research summary and factual claim tables — NOT a transcript or authored script.

- Source: [M5、M6 Mac 如何選? Mac 跑本地 AI:模型裝得下,為什麼跑Agent就想退貨?](https://www.youtube.com/watch?v=dnk_lPZ0Y-E) · Channel: 路可
- Caption language: zh-Hant; manual track. Retrieval: 2026-11-20T20:49:39.282488+08:00 (Asia/Shanghai).
- Coverage: returned caption track, not audio-verified; first 0.0 ms, final 1023300.0 ms. No visual charts or manufacturer specifications independently checked.

## Original research notes

This Mac-selection discussion centers on the distinction between accommodating a model and making a local agent feel responsive during realistic input-heavy work.

- [0:36](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=36s): The presenter separates input computation from output generation. A fast visible stream does not ensure that users will avoid a long pause after submitting a substantial request.
- [3:14](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=194s): Unified memory is presented as an advantage for accommodating large models. The purchase specification still needs a practical allocation and background-use allowance before it becomes a reliable fit estimate.
- [6:06](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=366s): A hardware feature shared across several discussed chips is distinguished from a differentiator between purchase options. Features common to the comparison set cannot by themselves justify a premium recommendation.
- [8:50](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=530s): Sparse expert models are introduced as a relevant workload category. Their active computation and total storage demands should be modeled separately rather than ranked solely by headline parameter count.
- [14:09](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=849s): The discussion notes that an application's software path affects the benefit obtained from hardware. A result in one application cannot automatically predict performance through a different framework.

**Platform implication.** Keep task shape, architecture, usable memory and software stack in the advisor's decision model. The note uses the available Traditional Chinese uploaded-caption track, but the video's hardware and performance assertions still require independent verification.

## Hardware profile index

These are partial caption-evidence profiles,not LCZ-equivalent complete builds. No part from an LCZ reference has been inserted into a video configuration.

| Profile / role | Core evidence coverage | Linked observations |
| --- | --- | --- |
| [V048-HP-C001 — sameM5comparison](hardware-profiles/V048-HP-C001.md) | configuration as explicitly narrated;creator/third-party claim,not independently verified;1/6corecategories,notcomplete | 2 |
| [V048-HP-E01 — M3Ultra phase-timing comparison](hardware-profiles/V048-HP-E01.md) | Caption-reported partial configuration /comparison;not a full build;1/6corecategories,notcomplete | 2 |
| [V048-HP-E02 — NVIDIA small-box phase-timing comparison](hardware-profiles/V048-HP-E02.md) | Caption-reported partial configuration /comparison;not a full build;1/6corecategories,notcomplete | 2 |

## Test series and run conditions

Only source-reported observations follow. Unknown conditions stay unknown;rows are not certified apples-to-apples comparisons. Single-request speed,aggregate throughput,prefill,TTFT,quality,memory,power and estimates use separate series. Ranges are preserved;no new sweep points,repeats,medians or statistics were created.

### V048-S01 · TTFT / startup latency

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** modelnotidentified; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** backend/settingsnotfullyspecified; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V048-P001; sameMac,modelunspecified (profileunassigned) | warmcachedTTFT · 2.9 seconds | fullcachehit; citedmeasurement | [2:39](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=159s) |
| V048-P002; sameMac (profileunassigned) | uncachedTTFT · 82 seconds | samemodel;recompute; citedmeasurement | [2:43](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=163s) |

### V048-S02 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V048-HP-C001
- **Model / weights / quantization:** modelnotidentified; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** backend/settingsnotfullyspecified; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V048-P003; M5 versusM4 (profileunassigned) | first-token speedup · 3.3–4 times | Apple researchclaim;modelnotnamed; third-partyclaim | [4:53](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=293s) |
| V048-P005; V048-HP-C001 | decode · 29.6 to31 per-second count;unitimplicit | sameswitch; citedmeasurement | [5:40](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=340s) |
| V048-P008; M5generation versusprevious (profileunassigned) | decode improvement · 19–27 percent | officialnumbersquoted;testdetailsmissing; third-partyclaim | [7:31](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=451s) |

### V048-S03 · Prefill / input processing

- **Profile(s):** V048-HP-C001, V048-HP-E01, V048-HP-E02
- **Model / weights / quantization:** modelnotidentified; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** backend/settingsnotfullyspecified; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V048-P004; V048-HP-C001 | prefill · 247 to636 per-second count;unitnotspelledoutinclause | accelerator switch;tokencontext; citedmeasurement | [5:35](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=335s) |
| V048-P006; V048-HP-E01 | input/prefill latency · 5.57 seconds | sameunnamedmodel/input; citedcomparison | [6:40](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=400s) |
| V048-P007; V048-HP-E02 | input/prefill latency · 1.47 seconds | samecomparison; citedcomparison | [6:45](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=405s) |

### V048-S04 · Elapsed workflow / phase time (not TTFT unless explicit)

- **Profile(s):** V048-HP-E01, V048-HP-E02
- **Model / weights / quantization:** modelnotidentified; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** backend/settingsnotfullyspecified; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V048-P009; V048-HP-E01 | outputphase · 0.85 seconds | sameunnamedrequest; teammeasurementquoted | [15:24](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=924s) |
| V048-P010; V048-HP-E02 | outputphase · 2.87 seconds | sameunnamedrequest; teammeasurementquoted | [15:30](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=930s) |
| V048-P011; hybridMac+NVIDIApipeline (profileunassigned) | combinedtime · 2.32 seconds | selectfastphaseoneach;setupnotfullygiven; quotedprototype/calculation | [15:41](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=941s) |

## Detailed hardware profiles

Minimum fields follow motherboard/CPU/RAMmodules+speed/GPUvariant+count+VRAM/PSU/storage. “Unknown”means not reported,not an invitation to fill from a different owner or manufacturer memory. Costs are quotes/paid/estimates only where identified;no fakeBOMtotal.

### V048-HP-C001 · sameM5comparison

**Role:** configuration as explicitly narrated;creator/third-party claim,not independently verified. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=327s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=327s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=327s) |
| RAM | — | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=327s) |
| GPU | M5 | PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=327s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=327s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=327s) |

**Other component disclosures:** model,chipvariantandRAMnotstated;acceleration-switchcomparison

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V048-P004 / V048-S03 | modelnotidentified; not stated; backend/settingsnotfullyspecified | prefill: 247 to636 per-second count;unitnotspelledoutinclause | accelerator switch;tokencontext; citedmeasurement; [5:35](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=335s) |
| V048-P005 / V048-S02 | modelnotidentified; not stated; backend/settingsnotfullyspecified | decode: 29.6 to31 per-second count;unitimplicit | sameswitch; citedmeasurement; [5:40](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=340s) |

---

### V048-HP-E01 · M3Ultra phase-timing comparison

**Role:** Caption-reported partial configuration /comparison;not a full build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=400s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=400s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=400s) |
| RAM | — | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=400s) |
| GPU | AppleM3Ultra | PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=400s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=400s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=400s) |

**Selection / tradeoffs:** Unknown / not reported Exact model/RAM/settings unspecified;do not inheritM5setup.

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V048-P006 / V048-S03 | modelnotidentified; not stated; backend/settingsnotfullyspecified | input/prefill latency: 5.57 seconds | sameunnamedmodel/input; citedcomparison; [6:40](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=400s) |
| V048-P009 / V048-S04 | modelnotidentified; not stated; backend/settingsnotfullyspecified | outputphase: 0.85 seconds | sameunnamedrequest; teammeasurementquoted; [15:24](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=924s) |

---

### V048-HP-E02 · NVIDIA small-box phase-timing comparison

**Role:** Caption-reported partial configuration /comparison;not a full build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=405s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=405s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=405s) |
| RAM | — | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=405s) |
| GPU | NVIDIA;machineSKU notstated | PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=405s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=405s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=405s) |

**Selection / tradeoffs:** Unknown / not reported No basis to identify this asDGXSpark from generic wording alone.

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V048-P007 / V048-S03 | modelnotidentified; not stated; backend/settingsnotfullyspecified | input/prefill latency: 1.47 seconds | samecomparison; citedcomparison; [6:45](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=405s) |
| V048-P010 / V048-S04 | modelnotidentified; not stated; backend/settingsnotfullyspecified | outputphase: 2.87 seconds | sameunnamedrequest; teammeasurementquoted; [15:30](https://www.youtube.com/watch?v=dnk_lPZ0Y-E&t=930s) |


## Scope

Caption-only evidence;no chart/video viewing or independent hardware validation. ASR and source contradictions are retained. Full original caption text is not included. Original450claim records and99hardwarefact records are preserved byte-for-byte in their originalCSVs;new profiles/series are a separately typed organization layer.
