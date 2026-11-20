# 052 · Want to Run AI Agents Locally? Here is The Bare Minimum Setup/Build

> Original research summary and factual claim tables — NOT a transcript or authored script.

- Source: [Want to Run AI Agents Locally? Here is The Bare Minimum Setup/Build](https://www.youtube.com/watch?v=P-Fmo_CCIbY) · Channel: Daniel Jindoo 
- Caption language: en; automatic track. Retrieval: 2026-11-20T20:49:39.282488+08:00 (Asia/Shanghai).
- Coverage: returned caption track, not audio-verified; first 0.0 ms, final 977800.0 ms. No visual charts or manufacturer specifications independently checked.

## Original research notes

An introductory local-agent guide is useful for identifying user constraints and expectation-setting, rather than supplying a rigorously comparable hardware benchmark dataset.

- [0:33](https://www.youtube.com/watch?v=P-Fmo_CCIbY&t=33s): The presenter explains the roles of system components through an accessible analogy. This helps frame requirements, but the analogy should not replace measured behavior when recommending a purchase.
- [3:13](https://www.youtube.com/watch?v=P-Fmo_CCIbY&t=193s): Graphics-memory capacity is presented as a primary constraint on the local experience. A fit advisor should pair that capacity with context, compression and the intended operating margin.
- [5:46](https://www.youtube.com/watch?v=P-Fmo_CCIbY&t=346s): An entry-level Apple configuration is discussed as usable with limitations. The distinction between technically usable and comfortable daily operation should be explicit in any recommendation language.
- [11:15](https://www.youtube.com/watch?v=P-Fmo_CCIbY&t=675s): The Raspberry Pi discussion limits expectations for routine local AI use. Edge-device experimentation and a practical daily agent are different product goals with different acceptance criteria.
- [13:48](https://www.youtube.com/watch?v=P-Fmo_CCIbY&t=828s): The creator warns against treating local agents as interchangeable with leading cloud systems. Privacy, controllability, quality and waiting time can pull the user's decision in different directions.

**Platform implication.** Use this source to develop a requirements questionnaire, not to set universal minimum specifications. Ask about task difficulty, concurrency and acceptable delay before attaching a ready-for-agents label to any proposed build.

## Hardware profile index

These are partial caption-evidence profiles,not LCZ-equivalent complete builds. No part from an LCZ reference has been inserted into a video configuration.

| Profile / role | Core evidence coverage | Linked observations |
| --- | --- | --- |
| [V052-HP-C001 — recommendedLinuxbuild](hardware-profiles/V052-HP-C001.md) | recommended configuration,not tested measurement;3/6corecategories,notcomplete | 0 |
| [V052-HP-C002 — MacminiM4Pro](hardware-profiles/V052-HP-C002.md) | configuration recommendation/experience,not controlledtest;1/6corecategories,notcomplete | 1 |
| [V052-HP-C003 — MacStudioM3Ultra](hardware-profiles/V052-HP-C003.md) | configuration as explicitly narrated;creator/third-party claim,not independently verified;1/6corecategories,notcomplete | 1 |

## Test series and run conditions

Only source-reported observations follow. Unknown conditions stay unknown;rows are not certified apples-to-apples comparisons. Single-request speed,aggregate throughput,prefill,TTFT,quality,memory,power and estimates use separate series. Ranges are preserved;no new sweep points,repeats,medians or statistics were created.

### V052-S01 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V052-HP-C002
- **Model / weights / quantization:** 32Bmodel;artifactnotnamed; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not stated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V052-P001; V052-HP-C002 | generation · 10–12 words/s,then speaker equates to tokens/s | unitsconflated;notnormalized; creatorguidance,notcontrolledtest | [8:35](https://www.youtube.com/watch?v=P-Fmo_CCIbY&t=515s) |

### V052-S02 · Power / energy (boundary-dependent)

- **Profile(s):** V052-HP-C003
- **Model / weights / quantization:** multipleloadedmodels; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not stated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V052-P002; V052-HP-C003 | idle power · under100 W | idle,notLLMinferenceload; creatorclaim | [10:31](https://www.youtube.com/watch?v=P-Fmo_CCIbY&t=631s) |

### V052-S03 · Power / energy (boundary-dependent)

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** unspecified; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not stated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V052-P003; RTX4090desktop (profileunassigned) | load-versus-other-machine-idle power ratio · 5–10 times | differentloadstates;notfairenergybenchmark; creatorcomparison | [10:34](https://www.youtube.com/watch?v=P-Fmo_CCIbY&t=634s) |

## Detailed hardware profiles

Minimum fields follow motherboard/CPU/RAMmodules+speed/GPUvariant+count+VRAM/PSU/storage. “Unknown”means not reported,not an invitation to fill from a different owner or manufacturer memory. Costs are quotes/paid/estimates only where identified;no fakeBOMtotal.

### V052-HP-C001 · recommendedLinuxbuild

**Role:** recommended configuration,not tested measurement. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=P-Fmo_CCIbY&t=490s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 3/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=P-Fmo_CCIbY&t=490s) |
| CPU | Ryzen7;SKU not stated | — | — | [source](https://www.youtube.com/watch?v=P-Fmo_CCIbY&t=490s) |
| RAM | system/unspecified RAM: 64GB | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=P-Fmo_CCIbY&t=490s) |
| GPU | — | PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=P-Fmo_CCIbY&t=490s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=P-Fmo_CCIbY&t=490s) |
| Storage | 2TBSSD | — | — | [source](https://www.youtube.com/watch?v=P-Fmo_CCIbY&t=490s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, gpu, psu; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** No performance row can be safely assigned to this exact profile. Product mention/recommendation is not a measured build.

---

### V052-HP-C002 · MacminiM4Pro

**Role:** configuration recommendation/experience,not controlledtest. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=P-Fmo_CCIbY&t=495s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=P-Fmo_CCIbY&t=495s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=P-Fmo_CCIbY&t=495s) |
| RAM | unified/shared RAM: 64GB | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=P-Fmo_CCIbY&t=495s) |
| GPU | — | PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=P-Fmo_CCIbY&t=495s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=P-Fmo_CCIbY&t=495s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=P-Fmo_CCIbY&t=495s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, gpu, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V052-P001 / V052-S01 | 32Bmodel;artifactnotnamed; not stated; not stated | generation: 10–12 words/s,then speaker equates to tokens/s | unitsconflated;notnormalized; creatorguidance,notcontrolledtest; [8:35](https://www.youtube.com/watch?v=P-Fmo_CCIbY&t=515s) |

---

### V052-HP-C003 · MacStudioM3Ultra

**Role:** configuration as explicitly narrated;creator/third-party claim,not independently verified. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=P-Fmo_CCIbY&t=614s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=P-Fmo_CCIbY&t=614s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=P-Fmo_CCIbY&t=614s) |
| RAM | unified/shared RAM: 96GB | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=P-Fmo_CCIbY&t=614s) |
| GPU | — | PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=P-Fmo_CCIbY&t=614s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=P-Fmo_CCIbY&t=614s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=P-Fmo_CCIbY&t=614s) |

**Other component disclosures:** under100W isidle,notload

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, gpu, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V052-P002 / V052-S02 | multipleloadedmodels; not stated; not stated | idle power: under100 W | idle,notLLMinferenceload; creatorclaim; [10:31](https://www.youtube.com/watch?v=P-Fmo_CCIbY&t=631s) |


## Scope

Caption-only evidence;no chart/video viewing or independent hardware validation. ASR and source contradictions are retained. Full original caption text is not included. Original450claim records and99hardwarefact records are preserved byte-for-byte in their originalCSVs;new profiles/series are a separately typed organization layer.
