# 013 · Reddit Says This Small Qwen Is 98% as Good. I Tested It on My Mac Studio

> Original research summary and factual claim tables — NOT a transcript or authored script.

- Source: [Reddit Says This Small Qwen Is 98% as Good. I Tested It on My Mac Studio](https://www.youtube.com/watch?v=YcosZPh-kcI) · Channel: The Dark Factory
- Caption language: en; manual track. Retrieval: 2026-11-20T20:49:39.282488+08:00 (Asia/Shanghai).
- Coverage: returned caption track, not audio-verified; first 0.0 ms, final 620555.9999999999 ms. No visual charts or manufacturer specifications independently checked.

## Original research notes

The source examines a compact-model marketing claim through several evaluation methods, showing why a retained-quality percentage needs a clearly defined denominator.

- [0:12](https://www.youtube.com/watch?v=YcosZPh-kcI&t=12s): The presenter starts from claims about smaller files and limited-memory hardware. The purchasing implication depends on both answer quality and where the model's remaining data actually resides.
- [1:37](https://www.youtube.com/watch?v=YcosZPh-kcI&t=97s): Several compression approaches are treated as distinct artifacts rather than interchangeable versions of one model. Their common ancestry does not make their error behavior equivalent.
- [3:08](https://www.youtube.com/watch?v=YcosZPh-kcI&t=188s): The creator distinguishes agreement with another model from benchmark performance and task success. The evaluation discussion also acknowledges repeated trials and noise in a small test set.
- [4:48](https://www.youtube.com/watch?v=YcosZPh-kcI&t=288s): Reported results vary across completed tasks, serious errors and unfinished responses. A single aggregate quality label conceals failure modes that may matter differently to individual users.
- [8:14](https://www.youtube.com/watch?v=YcosZPh-kcI&t=494s): The conclusion recommends checking the model on the intended job rather than accepting the strongest promotional percentage. The source remains an attributed evaluation, not an independent certification.

**Platform implication.** For the existing comparison platform, keep artifact identity, evaluation definition and error categories attached to quality claims. Link fit estimates to task-level acceptance criteria instead of equating a smaller download with preserved usefulness.

## Hardware profile index

These are partial caption-evidence profiles,not LCZ-equivalent complete builds. No part from an LCZ reference has been inserted into a video configuration.

| Profile / role | Core evidence coverage | Linked observations |
| --- | --- | --- |
| [V013-HP-C001 — creator PC / RTX5090](hardware-profiles/V013-HP-C001.md) | configuration as explicitly narrated;creator/third-party claim,not independently verified;2/6corecategories,notcomplete | 4 |
| [V013-HP-C002 — creator MacStudio](hardware-profiles/V013-HP-C002.md) | configuration as explicitly narrated;creator/third-party claim,not independently verified;0/6corecategories,notcomplete | 13 |

## Test series and run conditions

Only source-reported observations follow. Unknown conditions stay unknown;rows are not certified apples-to-apples comparisons. Single-request speed,aggregate throughput,prefill,TTFT,quality,memory,power and estimates use separate series. Ranges are preserved;no new sweep points,repeats,medians or statistics were created.

### V013-S01 · Reported generation throughput (concurrency scope unreported unless row states it)

- **Profile(s):** V013-HP-C002
- **Model / weights / quantization:** near-full27B versusBonsai compressed27B; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** runtime not stated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V013-P001; V013-HP-C002 | generation throughput · 33 vs61 tokens/s | creatorintro;exactprecisionnotisolated;Bonsai61tokens/s follows at0:50; narrated result;not independently verified | [0:43](https://www.youtube.com/watch?v=YcosZPh-kcI&t=43s) |

### V013-S02 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V013-HP-C002
- **Model / weights / quantization:** ordinary smaller Qwen rival; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not stated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V013-P002; V013-HP-C002 | decode · 131 tokens/s | differentmodel,not compressed27B; narrated result;not independently verified | [5:45](https://www.youtube.com/watch?v=YcosZPh-kcI&t=345s) |

### V013-S03 · Memory / fit (not throughput)

- **Profile(s):** V013-HP-C001
- **Model / weights / quantization:** FlashNext2bit discussed; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not isolated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V013-P003; V013-HP-C001 | observed VRAM use · under7 GB | offloaded sparsemodel;not fullmodelsize; narrated result;not independently verified | [7:30](https://www.youtube.com/watch?v=YcosZPh-kcI&t=450s) |

### V013-S04 · Memory / fit (not throughput)

- **Profile(s):** V013-HP-C001
- **Model / weights / quantization:** sameFlashNext; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** notisolated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V013-P004; V013-HP-C001 | observed systemRAM use · 67 GB | do notcallGPUVRAM; narrated result;not independently verified | [7:41](https://www.youtube.com/watch?v=YcosZPh-kcI&t=461s) |

### V013-S05 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V013-HP-C001
- **Model / weights / quantization:** sameFlashNext; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** notisolated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V013-P005; V013-HP-C001 | decode · 32 tokens/s | afterstartup; narrated result;not independently verified | [7:55](https://www.youtube.com/watch?v=YcosZPh-kcI&t=475s) |

### V013-S06 · TTFT / startup latency

- **Profile(s):** V013-HP-C001
- **Model / weights / quantization:** sameFlashNext; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** notisolated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V013-P006; V013-HP-C001 | time to first token · 37 seconds | longquestion;lengthnotstated; narrated result;not independently verified | [7:55](https://www.youtube.com/watch?v=YcosZPh-kcI&t=475s) |

### V013-S07 · Quality / task outcomes (not speed)

- **Profile(s):** V013-HP-C002
- **Model / weights / quantization:** modelvariant:ordinary4bitQwen; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** evaluation setup; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V013-P007; V013-HP-C002 | next-token agreement · 89 percent | samebookpage versusfullmodel;notbenchmark intelligence score; creator evaluation | [2:51](https://www.youtube.com/watch?v=YcosZPh-kcI&t=171s) |

### V013-S08 · Quality / task outcomes (not speed)

- **Profile(s):** V013-HP-C002
- **Model / weights / quantization:** modelvariant:UnslothcompressedQwen; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** evaluation setup; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V013-P008; V013-HP-C002 | next-token agreement · 68 percent | samebookpage versusfullmodel;notbenchmark intelligence score; creator evaluation | [2:57](https://www.youtube.com/watch?v=YcosZPh-kcI&t=177s) |

### V013-S09 · Quality / task outcomes (not speed)

- **Profile(s):** V013-HP-C002
- **Model / weights / quantization:** modelvariant:smart-squeezeQwen; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** evaluation setup; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V013-P009; V013-HP-C002 | next-token agreement · 67 percent | samebookpage versusfullmodel;notbenchmark intelligence score; creator evaluation | [2:57](https://www.youtube.com/watch?v=YcosZPh-kcI&t=177s) |

### V013-S10 · Quality / task outcomes (not speed)

- **Profile(s):** V013-HP-C002
- **Model / weights / quantization:** modelvariant:BonsaiQwen; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** evaluation setup; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V013-P010; V013-HP-C002 | next-token agreement · 62 percent | samebookpage versusfullmodel;notbenchmark intelligence score; creator evaluation | [2:57](https://www.youtube.com/watch?v=YcosZPh-kcI&t=177s) |

### V013-S11 · Quality / task outcomes (not speed)

- **Profile(s):** V013-HP-C002
- **Model / weights / quantization:** modelvariant:tinyQwen; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** evaluation setup; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V013-P011; V013-HP-C002 | next-token agreement · 60 percent | samebookpage versusfullmodel;notbenchmark intelligence score; creator evaluation | [2:57](https://www.youtube.com/watch?v=YcosZPh-kcI&t=177s) |

### V013-S12 · Quality / task outcomes (not speed)

- **Profile(s):** V013-HP-C002
- **Model / weights / quantization:** full-sizeQwen; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** creator20-tasktest; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V013-P012; V013-HP-C002 | tasks without fixes · 11–14 of20tasks | 3runseach;blindgrader;small sample; creator evaluation | [4:20](https://www.youtube.com/watch?v=YcosZPh-kcI&t=260s) |

### V013-S13 · Quality / task outcomes (not speed)

- **Profile(s):** V013-HP-C002
- **Model / weights / quantization:** Bonsai; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** creator20-tasktest; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V013-P013; V013-HP-C002 | tasks without fixes · 10 of20tasks | 3runseach;blindgrader;small sample; creator evaluation | [4:32](https://www.youtube.com/watch?v=YcosZPh-kcI&t=272s) |

### V013-S14 · Quality / task outcomes (not speed)

- **Profile(s):** V013-HP-C002
- **Model / weights / quantization:** Unsloth; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** creator20-tasktest; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V013-P014; V013-HP-C002 | tasks without fixes · 12 of20tasks | 3runseach;blindgrader;small sample; creator evaluation | [4:48](https://www.youtube.com/watch?v=YcosZPh-kcI&t=288s) |

### V013-S15 · Quality / task outcomes (not speed)

- **Profile(s):** V013-HP-C002
- **Model / weights / quantization:** trimmed; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** creator20-tasktest; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V013-P015; V013-HP-C002 | tasks without fixes · 7 of20tasks | 3runseach;blindgrader;small sample; creator evaluation | [5:19](https://www.youtube.com/watch?v=YcosZPh-kcI&t=319s) |

### V013-S16 · Quality / task outcomes (not speed)

- **Profile(s):** V013-HP-C002
- **Model / weights / quantization:** tiny; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** creator20-tasktest; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V013-P016; V013-HP-C002 | tasks without fixes · 5 of20tasks | 3runseach;blindgrader;small sample; creator evaluation | [5:26](https://www.youtube.com/watch?v=YcosZPh-kcI&t=326s) |

### V013-S17 · Quality / task outcomes (not speed)

- **Profile(s):** V013-HP-C002
- **Model / weights / quantization:** smallerQwenrival; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** creator20-tasktest; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V013-P017; V013-HP-C002 | tasks without fixes · 8 of20tasks | 3runseach;blindgrader;small sample; creator evaluation | [5:36](https://www.youtube.com/watch?v=YcosZPh-kcI&t=336s) |

## Detailed hardware profiles

Minimum fields follow motherboard/CPU/RAMmodules+speed/GPUvariant+count+VRAM/PSU/storage. “Unknown”means not reported,not an invitation to fill from a different owner or manufacturer memory. Costs are quotes/paid/estimates only where identified;no fakeBOMtotal.

### V013-HP-C001 · creator PC / RTX5090

**Role:** configuration as explicitly narrated;creator/third-party claim,not independently verified. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=YcosZPh-kcI&t=450s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 2/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=YcosZPh-kcI&t=450s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=YcosZPh-kcI&t=450s) |
| RAM | system/unspecified RAM: 94GB as captioned;not silently changedto96 | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=YcosZPh-kcI&t=450s) |
| GPU | RTX5090 | qty 1; PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=YcosZPh-kcI&t=450s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=YcosZPh-kcI&t=450s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=YcosZPh-kcI&t=450s) |

**Other component disclosures:** 67GBRAM andunder7GBVRAMare observeduse,notinstalledcapacity

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V013-P003 / V013-S03 | FlashNext2bit discussed; not stated; not isolated | observed VRAM use: under7 GB | offloaded sparsemodel;not fullmodelsize; narrated result;not independently verified; [7:30](https://www.youtube.com/watch?v=YcosZPh-kcI&t=450s) |
| V013-P004 / V013-S04 | sameFlashNext; not stated; notisolated | observed systemRAM use: 67 GB | do notcallGPUVRAM; narrated result;not independently verified; [7:41](https://www.youtube.com/watch?v=YcosZPh-kcI&t=461s) |
| V013-P005 / V013-S05 | sameFlashNext; not stated; notisolated | decode: 32 tokens/s | afterstartup; narrated result;not independently verified; [7:55](https://www.youtube.com/watch?v=YcosZPh-kcI&t=475s) |
| V013-P006 / V013-S06 | sameFlashNext; not stated; notisolated | time to first token: 37 seconds | longquestion;lengthnotstated; narrated result;not independently verified; [7:55](https://www.youtube.com/watch?v=YcosZPh-kcI&t=475s) |

---

### V013-HP-C002 · creator MacStudio

**Role:** configuration as explicitly narrated;creator/third-party claim,not independently verified. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=YcosZPh-kcI&t=43s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 0/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=YcosZPh-kcI&t=43s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=YcosZPh-kcI&t=43s) |
| RAM | — | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=YcosZPh-kcI&t=43s) |
| GPU | — | PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=YcosZPh-kcI&t=43s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=YcosZPh-kcI&t=43s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=YcosZPh-kcI&t=43s) |

**Other component disclosures:** chip/RAM not stated in comparison

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, gpu, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V013-P001 / V013-S01 | near-full27B versusBonsai compressed27B; not stated; runtime not stated | generation throughput: 33 vs61 tokens/s | creatorintro;exactprecisionnotisolated;Bonsai61tokens/s follows at0:50; narrated result;not independently verified; [0:43](https://www.youtube.com/watch?v=YcosZPh-kcI&t=43s) |
| V013-P002 / V013-S02 | ordinary smaller Qwen rival; not stated; not stated | decode: 131 tokens/s | differentmodel,not compressed27B; narrated result;not independently verified; [5:45](https://www.youtube.com/watch?v=YcosZPh-kcI&t=345s) |
| V013-P007 / V013-S07 | modelvariant:ordinary4bitQwen; not stated; evaluation setup | next-token agreement: 89 percent | samebookpage versusfullmodel;notbenchmark intelligence score; creator evaluation; [2:51](https://www.youtube.com/watch?v=YcosZPh-kcI&t=171s) |
| V013-P008 / V013-S08 | modelvariant:UnslothcompressedQwen; not stated; evaluation setup | next-token agreement: 68 percent | samebookpage versusfullmodel;notbenchmark intelligence score; creator evaluation; [2:57](https://www.youtube.com/watch?v=YcosZPh-kcI&t=177s) |
| V013-P009 / V013-S09 | modelvariant:smart-squeezeQwen; not stated; evaluation setup | next-token agreement: 67 percent | samebookpage versusfullmodel;notbenchmark intelligence score; creator evaluation; [2:57](https://www.youtube.com/watch?v=YcosZPh-kcI&t=177s) |
| V013-P010 / V013-S10 | modelvariant:BonsaiQwen; not stated; evaluation setup | next-token agreement: 62 percent | samebookpage versusfullmodel;notbenchmark intelligence score; creator evaluation; [2:57](https://www.youtube.com/watch?v=YcosZPh-kcI&t=177s) |
| V013-P011 / V013-S11 | modelvariant:tinyQwen; not stated; evaluation setup | next-token agreement: 60 percent | samebookpage versusfullmodel;notbenchmark intelligence score; creator evaluation; [2:57](https://www.youtube.com/watch?v=YcosZPh-kcI&t=177s) |
| V013-P012 / V013-S12 | full-sizeQwen; not stated; creator20-tasktest | tasks without fixes: 11–14 of20tasks | 3runseach;blindgrader;small sample; creator evaluation; [4:20](https://www.youtube.com/watch?v=YcosZPh-kcI&t=260s) |
| V013-P013 / V013-S13 | Bonsai; not stated; creator20-tasktest | tasks without fixes: 10 of20tasks | 3runseach;blindgrader;small sample; creator evaluation; [4:32](https://www.youtube.com/watch?v=YcosZPh-kcI&t=272s) |
| V013-P014 / V013-S14 | Unsloth; not stated; creator20-tasktest | tasks without fixes: 12 of20tasks | 3runseach;blindgrader;small sample; creator evaluation; [4:48](https://www.youtube.com/watch?v=YcosZPh-kcI&t=288s) |
| V013-P015 / V013-S15 | trimmed; not stated; creator20-tasktest | tasks without fixes: 7 of20tasks | 3runseach;blindgrader;small sample; creator evaluation; [5:19](https://www.youtube.com/watch?v=YcosZPh-kcI&t=319s) |
| V013-P016 / V013-S16 | tiny; not stated; creator20-tasktest | tasks without fixes: 5 of20tasks | 3runseach;blindgrader;small sample; creator evaluation; [5:26](https://www.youtube.com/watch?v=YcosZPh-kcI&t=326s) |
| V013-P017 / V013-S17 | smallerQwenrival; not stated; creator20-tasktest | tasks without fixes: 8 of20tasks | 3runseach;blindgrader;small sample; creator evaluation; [5:36](https://www.youtube.com/watch?v=YcosZPh-kcI&t=336s) |


## Scope

Caption-only evidence;no chart/video viewing or independent hardware validation. ASR and source contradictions are retained. Full original caption text is not included. Original450claim records and99hardwarefact records are preserved byte-for-byte in their originalCSVs;new profiles/series are a separately typed organization layer.
