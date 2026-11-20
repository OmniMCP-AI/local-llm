# 018 · New 145B (6.6B Active) Local AI Runs on 1 GPU & BEATS DeepSeek V4 & Qwen! + Gemini 4 Helix Leaked!

> Original research summary and factual claim tables — NOT a transcript or authored script.

- Source: [New 145B (6.6B Active) Local AI Runs on 1 GPU & BEATS DeepSeek V4 & Qwen! + Gemini 4 Helix Leaked!](https://www.youtube.com/watch?v=1PJGtLpYGOY) · Channel: Shaown Ships AI
- Caption language: en; automatic track. Retrieval: 2026-11-20T20:49:39.282488+08:00 (Asia/Shanghai).
- Coverage: returned caption track, not audio-verified; first 100.0 ms, final 599697.0 ms. No visual charts or manufacturer specifications independently checked.

## Original research notes

A release-oriented AI roundup contains local-model claims, but mixes technical assertions, benchmark comparisons and unrelated industry news that require different evidentiary treatment.

- [0:22](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=22s): The creator contrasts a local model with named alternatives using coding-related benchmark language. Such comparisons need the original evaluation setup before being treated as a quality leaderboard.
- [1:50](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=110s): The video combines a memory-footprint claim with an average across several tests. Hardware fit and a heterogeneous benchmark average answer different questions and should remain separate fields.
- [3:42](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=222s): An expert-routing explanation distinguishes total model size from active computation. This can inform the advisor's data model without establishing the source's exact architectural numbers as verified facts.
- [5:20](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=320s): A constrained-machine example is used to support the accessibility argument. Reproducing its runtime, quantization, context and memory policy would be necessary before generalizing it to user hardware.
- [6:41](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=401s): An agent example involves hardware-design software rather than a simple chat response. End-to-end success and tool interaction matter beyond the generation rate cited elsewhere in the roundup.

**Platform implication.** Treat the video as a discovery lead for models and evaluations, not a primary benchmark dataset. Separate release claims, application demonstrations and later news segments before adding anything to the existing research knowledge base.

## Hardware profile index

These are partial caption-evidence profiles,not LCZ-equivalent complete builds. No part from an LCZ reference has been inserted into a video configuration.

| Profile / role | Core evidence coverage | Linked observations |
| --- | --- | --- |
| [V018-HP-C001 — sourcebenchmarkbuild / RTX5090D as captioned](hardware-profiles/V018-HP-C001.md) | configuration as explicitly narrated;creator/third-party claim,not independently verified;1/6corecategories,notcomplete | 3 |
| [V018-HP-C002 — memory-cappedtest / SKU not stated](hardware-profiles/V018-HP-C002.md) | configuration as explicitly narrated;creator/third-party claim,not independently verified;2/6corecategories,notcomplete | 1 |
| [V018-HP-G002 — RTX4090](hardware-profiles/V018-HP-G002.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 1 |
| [V018-HP-E01 — AppleM2Ultra result](hardware-profiles/V018-HP-E01.md) | Caption-reported partial configuration /comparison;not a full build;1/6corecategories,notcomplete | 1 |

## Test series and run conditions

Only source-reported observations follow. Unknown conditions stay unknown;rows are not certified apples-to-apples comparisons. Single-request speed,aggregate throughput,prefill,TTFT,quality,memory,power and estimates use separate series. Ranges are preserved;no new sweep points,repeats,medians or statistics were created.

### V018-S01 · Memory / fit (not throughput)

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** Qwen3.8FlashNext; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not isolated exceptMetal where indicated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V018-P001; notstated (profileunassigned) | peakmemory · 70 GB | standard4bit; creator cites publishedclaims;not independentlyverified | [1:33](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=93s) |

### V018-S02 · Memory / fit (not throughput)

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** DeepSeekV4Flash; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not isolated exceptMetal where indicated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V018-P002; notstated (profileunassigned) | peakmemory · 87 GB | standard4bit comparison; creator cites publishedclaims;not independentlyverified | [1:42](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=102s) |

### V018-S03 · Memory / fit (not throughput)

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** Edge0 145B; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not isolated exceptMetal where indicated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V018-P003; notstated (profileunassigned) | peakmemory · 29 GB | precision not isolated; creator cites publishedclaims;not independentlyverified | [1:50](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=110s) |

### V018-S04 · Memory / fit (not throughput)

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** Edge0 120B; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not isolated exceptMetal where indicated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V018-P004; notstated (profileunassigned) | peakmemory · 29 GB | precision not isolated; creator cites publishedclaims;not independentlyverified | [2:15](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=135s) |

### V018-S05 · Prefill / input processing

- **Profile(s):** V018-HP-C001
- **Model / weights / quantization:** Edge0 145B; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not isolated exceptMetal where indicated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V018-P005; V018-HP-C001 | prefill · 3554.9 tokens/s | 16Kprefill;NVFP4/Q3Kbuilds,exactmetric-toartifactnotstated; creator cites publishedclaims;not independentlyverified | [4:51](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=291s) |

### V018-S06 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V018-HP-C001, V018-HP-C002, V018-HP-E01, V018-HP-G002
- **Model / weights / quantization:** Edge0 145B; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not isolated exceptMetal where indicated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V018-P006; V018-HP-C001 | chatdecode · 99.7 tokens/s | same attributedsource; creator cites publishedclaims;not independentlyverified | [4:58](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=298s) |
| V018-P007; V018-HP-C001 | agentdecode · 121.2 tokens/s | same attributedsource; creator cites publishedclaims;not independentlyverified | [5:00](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=300s) |
| V018-P008; V018-HP-G002 | agentdecode · 91.7 tokens/s | notproofsamequantas5090D; creator cites publishedclaims;not independentlyverified | [5:06](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=306s) |
| V018-P009; V018-HP-E01 | generation · 60.9 tokens/s | Metal;memorynotstated; creator cites publishedclaims;not independentlyverified | [5:13](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=313s) |
| V018-P010; V018-HP-C002 | generation · nearly45 tokens/s | artificiallimits;zeroswap; creator cites publishedclaims;not independentlyverified | [5:29](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=329s) |

## Detailed hardware profiles

Minimum fields follow motherboard/CPU/RAMmodules+speed/GPUvariant+count+VRAM/PSU/storage. “Unknown”means not reported,not an invitation to fill from a different owner or manufacturer memory. Costs are quotes/paid/estimates only where identified;no fakeBOMtotal.

### V018-HP-C001 · sourcebenchmarkbuild / RTX5090D as captioned

**Role:** configuration as explicitly narrated;creator/third-party claim,not independently verified. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=282s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=282s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=282s) |
| RAM | — | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=282s) |
| GPU | RTX5090D as captioned | qty 1; PerGPUVRAM:24GB as captioned;SKU/capacity pairingunverified;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=282s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=282s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=282s) |

**Other component disclosures:** do not repair naming/capacity from externalmemory

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** NVFP4/Q3K builds Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V018-P005 / V018-S05 | Edge0 145B; not stated; not isolated exceptMetal where indicated | prefill: 3554.9 tokens/s | 16Kprefill;NVFP4/Q3Kbuilds,exactmetric-toartifactnotstated; creator cites publishedclaims;not independentlyverified; [4:51](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=291s) |
| V018-P006 / V018-S06 | Edge0 145B; not stated; not isolated exceptMetal where indicated | chatdecode: 99.7 tokens/s | same attributedsource; creator cites publishedclaims;not independentlyverified; [4:58](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=298s) |
| V018-P007 / V018-S06 | Edge0 145B; not stated; not isolated exceptMetal where indicated | agentdecode: 121.2 tokens/s | same attributedsource; creator cites publishedclaims;not independentlyverified; [5:00](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=300s) |

---

### V018-HP-C002 · memory-cappedtest / SKU not stated

**Role:** configuration as explicitly narrated;creator/third-party claim,not independently verified. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=318s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 2/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=318s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=318s) |
| RAM | system/unspecified RAM: 20GB limit | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=318s) |
| GPU | SKU not stated | PerGPUVRAM:16GB limit;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=318s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=318s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=318s) |

**Other component disclosures:** zero swap;limits not physicalinstalledcapacities

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V018-P010 / V018-S06 | Edge0 145B; not stated; not isolated exceptMetal where indicated | generation: nearly45 tokens/s | artificiallimits;zeroswap; creator cites publishedclaims;not independentlyverified; [5:29](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=329s) |

---

### V018-HP-G002 · RTX4090

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=306s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | RTX4090 | PerGPUVRAM:24GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=306s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V018-P008 / V018-S06 | Edge0 145B; not stated; not isolated exceptMetal where indicated | agentdecode: 91.7 tokens/s | notproofsamequantas5090D; creator cites publishedclaims;not independentlyverified; [5:06](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=306s) |

---

### V018-HP-E01 · AppleM2Ultra result

**Role:** Caption-reported partial configuration /comparison;not a full build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=311s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=311s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=311s) |
| RAM | — | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=311s) |
| GPU | AppleM2Ultra | PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=311s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=311s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=311s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Metal;runtimeversion not stated Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V018-P009 / V018-S06 | Edge0 145B; not stated; not isolated exceptMetal where indicated | generation: 60.9 tokens/s | Metal;memorynotstated; creator cites publishedclaims;not independentlyverified; [5:13](https://www.youtube.com/watch?v=1PJGtLpYGOY&t=313s) |


## Scope

Caption-only evidence;no chart/video viewing or independent hardware validation. ASR and source contradictions are retained. Full original caption text is not included. Original450claim records and99hardwarefact records are preserved byte-for-byte in their originalCSVs;new profiles/series are a separately typed organization layer.
