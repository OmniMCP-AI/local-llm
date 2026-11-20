# 027 · Testing Strata Local AI on $769 Budget AI Rig

> Original research summary and factual claim tables — NOT a transcript or authored script.

- Source: [Testing Strata Local AI on $769 Budget AI Rig](https://www.youtube.com/watch?v=WOlXMUKJeuI) · Channel: Digital Spaceport
- Caption language: en; automatic track. Retrieval: 2026-11-20T20:49:39.282488+08:00 (Asia/Shanghai).
- Coverage: returned caption track, not audio-verified; first 0.0 ms, final 608640.0 ms. No visual charts or manufacturer specifications independently checked.

## Original research notes

A budget-machine trial is relevant to agent usability because it reports resource constraints alongside document recognition and application-building tasks.

- [0:23](https://www.youtube.com/watch?v=WOlXMUKJeuI&t=23s): The presenter starts from limited graphics memory and an enabled vision path. Hardware-fit advice must identify the intended modality and offloading arrangement, not only the language-model size.
- [2:02](https://www.youtube.com/watch?v=WOlXMUKJeuI&t=122s): A task consumes a long reasoning interval and substantial output despite a high displayed rate. Generation throughput alone does not describe the time a person waits for completion.
- [3:38](https://www.youtube.com/watch?v=WOlXMUKJeuI&t=218s): A handwriting example tests whether the model notices a corrected number. Such detail-sensitive tasks can be more informative for document workflows than a generic successful image description.
- [5:18](https://www.youtube.com/watch?v=WOlXMUKJeuI&t=318s): The creator describes restrictions on parallel sub-agents under the selected batch and memory setup. Single-session success is therefore not evidence of comfortable team or concurrent-agent operation.
- [6:46](https://www.youtube.com/watch?v=WOlXMUKJeuI&t=406s): The demonstration expands into deploying a codebase. End-to-end workflow success is a separate dimension from the earlier isolated recognition and throughput observations on the same machine.

**Platform implication.** Represent concurrency, modality, reasoning time and completion outcome alongside hardware cost. The platform should avoid calling a budget build agent-ready without specifying whether that means one slow interactive session or several simultaneous workers.

## Hardware profile index

These are partial caption-evidence profiles,not LCZ-equivalent complete builds. No part from an LCZ reference has been inserted into a video configuration.

| Profile / role | Core evidence coverage | Linked observations |
| --- | --- | --- |
| [V027-HP-TEST — Single3060 12GB /E5-2696v4 /64GB Strata host](hardware-profiles/V027-HP-TEST.md) | creator single-GPU demonstration setup;3/6corecategories,notcomplete | 4 |

Only1 grounded profile is available;additional complete machines cannot be invented from this source.

## Test series and run conditions

Only source-reported observations follow. Unknown conditions stay unknown;rows are not certified apples-to-apples comparisons. Single-request speed,aggregate throughput,prefill,TTFT,quality,memory,power and estimates use separate series. Ranges are preserved;no new sweep points,repeats,medians or statistics were created.

### V027-S01 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V027-HP-TEST
- **Model / weights / quantization:** selectedQwen27B discussed; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Strata; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V027-P001; V027-HP-TEST | decode · about33 tokens/s | Visionenabled; narrated result;not independently verified | [1:03](https://www.youtube.com/watch?v=WOlXMUKJeuI&t=63s) |

### V027-S02 · Derived estimates / theoretical / ROI (not measured benchmarks)

- **Profile(s):** V027-HP-TEST
- **Model / weights / quantization:** same context; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Strata; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V027-P002; V027-HP-TEST | prefill ceiling expectation · about850 unitnotrepeated | notmeasuredprefill; explicit creator expectation | [1:08](https://www.youtube.com/watch?v=WOlXMUKJeuI&t=68s) |

### V027-S03 · Other reported observations / stability (not a comparable speed benchmark)

- **Profile(s):** V027-HP-TEST
- **Model / weights / quantization:** same task; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Strata; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V027-P003; V027-HP-TEST | thinkingtime · 617 seconds | page/repositoryanalysis; narrated result;not independently verified | [2:02](https://www.youtube.com/watch?v=WOlXMUKJeuI&t=122s) |

### V027-S04 · Reported generation throughput (concurrency scope unreported unless row states it)

- **Profile(s):** V027-HP-TEST
- **Model / weights / quantization:** same task; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Strata; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V027-P004; V027-HP-TEST | displayedaverage throughput · 49.2 unitnotrepeated | do notclassifyasprefill;32Koutputdiscussed; narrated result;not independently verified | [2:13](https://www.youtube.com/watch?v=WOlXMUKJeuI&t=133s) |

## Detailed hardware profiles

Minimum fields follow motherboard/CPU/RAMmodules+speed/GPUvariant+count+VRAM/PSU/storage. “Unknown”means not reported,not an invitation to fill from a different owner or manufacturer memory. Costs are quotes/paid/estimates only where identified;no fakeBOMtotal.

### V027-HP-TEST · Single3060 12GB /E5-2696v4 /64GB Strata host

**Role:** creator single-GPU demonstration setup. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=WOlXMUKJeuI&t=4s) · [additional disclosure](https://www.youtube.com/watch?v=WOlXMUKJeuI&t=74s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 3/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=WOlXMUKJeuI&t=4s) |
| CPU | E5 2696 V4 explicitly identified at0:48;2695 discussed only as alternative | — | — | [source](https://www.youtube.com/watch?v=WOlXMUKJeuI&t=4s) |
| RAM | 64GB system RAM | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=WOlXMUKJeuI&t=4s) |
| GPU | 3060 | qty 1; PerGPUVRAM:12GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=WOlXMUKJeuI&t=4s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=WOlXMUKJeuI&t=4s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=WOlXMUKJeuI&t=4s) |

**Selection / tradeoffs:** Tests whether one3060 can run the workflow instead of two. Unknown / not reported

**Expansion / compatibility:** Unknown / not reported The creator highlights sustained all-core/BIOS capability as relevant. No BIOS version or actual turbo setting is supplied.

**Deployment:** Strata;Vision stack enabled;reasoningX-high;exact engine/model build not established Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** About350W peak while running as narrated;boundary not fully specified;NOT a PSU rating Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** E5-2695v4 is an alternative discussed,not the installed CPU. Do not copy256GBRAM orDell model from another video.

**Unknowns:** motherboard, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V027-P001 / V027-S01 | selectedQwen27B discussed; not stated; Strata | decode: about33 tokens/s | Visionenabled; narrated result;not independently verified; [1:03](https://www.youtube.com/watch?v=WOlXMUKJeuI&t=63s) |
| V027-P002 / V027-S02 | same context; not stated; Strata | prefill ceiling expectation: about850 unitnotrepeated | notmeasuredprefill; explicit creator expectation; [1:08](https://www.youtube.com/watch?v=WOlXMUKJeuI&t=68s) |
| V027-P003 / V027-S03 | same task; not stated; Strata | thinkingtime: 617 seconds | page/repositoryanalysis; narrated result;not independently verified; [2:02](https://www.youtube.com/watch?v=WOlXMUKJeuI&t=122s) |
| V027-P004 / V027-S04 | same task; not stated; Strata | displayedaverage throughput: 49.2 unitnotrepeated | do notclassifyasprefill;32Koutputdiscussed; narrated result;not independently verified; [2:13](https://www.youtube.com/watch?v=WOlXMUKJeuI&t=133s) |


## Scope

Caption-only evidence;no chart/video viewing or independent hardware validation. ASR and source contradictions are retained. Full original caption text is not included. Original450claim records and99hardwarefact records are preserved byte-for-byte in their originalCSVs;new profiles/series are a separately typed organization layer.
