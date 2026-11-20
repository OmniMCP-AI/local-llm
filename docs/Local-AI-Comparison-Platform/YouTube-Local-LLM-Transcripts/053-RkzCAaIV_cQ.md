# 053 · This Shouldn’t Be Able to Run 120B Locally

> Original research summary and factual claim tables — NOT a transcript or authored script.

- Source: [This Shouldn’t Be Able to Run 120B Locally](https://www.youtube.com/watch?v=RkzCAaIV_cQ) · Channel: Alex Ziskind
- Caption language: en; automatic track. Retrieval: 2026-11-20T20:49:39.282488+08:00 (Asia/Shanghai).
- Coverage: returned caption track, not audio-verified; first 0.0 ms, final 732880.0 ms. No visual charts or manufacturer specifications independently checked.

## Original research notes

A compact AI appliance demonstration raises useful questions about integrated local-model products, while leaving quality and broad compatibility far from independently established.

- [0:28](https://www.youtube.com/watch?v=RkzCAaIV_cQ&t=28s): The creator introduces a small dedicated device as an alternative to conventional large AI systems. The positioning is a product demonstration, not evidence that it replaces every workstation use case.
- [2:33](https://www.youtube.com/watch?v=RkzCAaIV_cQ&t=153s): Power and connection arrangements are part of the setup. Practical portability includes the host interface and external-power requirements, not merely the enclosure's physical size.
- [4:25](https://www.youtube.com/watch?v=RkzCAaIV_cQ&t=265s): The model-download workflow is described as belonging to the appliance rather than consuming host storage. That distinction affects installation convenience, data placement and later management questions.
- [6:16](https://www.youtube.com/watch?v=RkzCAaIV_cQ&t=376s): A resource dashboard is presented as useful for estimating usage in development. Instrumentation can support planning, but displayed token counts do not independently establish future provider charges or application quality.
- [8:18](https://www.youtube.com/watch?v=RkzCAaIV_cQ&t=498s): An image-generation attempt initially produces an unexpected result. The demonstration usefully exposes friction instead of supporting a blanket conclusion that all advertised local applications work smoothly.

**Platform implication.** Compare appliances on workflow isolation, model management, power, observability and task success. Treat the headline model-size claim as a lead requiring artifact and performance verification, not proof of a satisfactory interactive experience.

## Hardware profile index

These are partial caption-evidence profiles,not LCZ-equivalent complete builds. No part from an LCZ reference has been inserted into a video configuration.

| Profile / role | Core evidence coverage | Linked observations |
| --- | --- | --- |
| [V053-HP-C001 — MacBookNeo](hardware-profiles/V053-HP-C001.md) | configuration as explicitly narrated;creator/third-party claim,not independently verified;2/6corecategories,notcomplete | 1 |
| [V053-HP-C002 — TinyAIPocketLab](hardware-profiles/V053-HP-C002.md) | configuration as explicitly narrated;creator/third-party claim,not independently verified;2/6corecategories,notcomplete | 1 |
| [V053-HP-G001 — RTX5090](hardware-profiles/V053-HP-G001.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 0 |

## Test series and run conditions

Only source-reported observations follow. Unknown conditions stay unknown;rows are not certified apples-to-apples comparisons. Single-request speed,aggregate throughput,prefill,TTFT,quality,memory,power and estimates use separate series. Ranges are preserved;no new sweep points,repeats,medians or statistics were created.

### V053-S01 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V053-HP-C001
- **Model / weights / quantization:** unnamed4Bmodel; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** not stated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V053-P001; V053-HP-C001 | generation · 9 tokens/s | localdemonstration; narrated result;not independently verified | [1:30](https://www.youtube.com/watch?v=RkzCAaIV_cQ&t=90s) |

### V053-S02 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V053-HP-C002
- **Model / weights / quantization:** GPT-OSS120B; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** TinyCLI;engine notstated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V053-P002; V053-HP-C002 | generation · 18 tokens/s | offlinedemo;notmodelqualityassessment; narrated result;not independently verified | [3:44](https://www.youtube.com/watch?v=RkzCAaIV_cQ&t=224s) |

## Detailed hardware profiles

Minimum fields follow motherboard/CPU/RAMmodules+speed/GPUvariant+count+VRAM/PSU/storage. “Unknown”means not reported,not an invitation to fill from a different owner or manufacturer memory. Costs are quotes/paid/estimates only where identified;no fakeBOMtotal.

### V053-HP-C001 · MacBookNeo

**Role:** configuration as explicitly narrated;creator/third-party claim,not independently verified. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=RkzCAaIV_cQ&t=80s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 2/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=RkzCAaIV_cQ&t=80s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=RkzCAaIV_cQ&t=80s) |
| RAM | system/unspecified RAM: 8GB memory;type not stated | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=RkzCAaIV_cQ&t=80s) |
| GPU | — | PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=RkzCAaIV_cQ&t=80s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=RkzCAaIV_cQ&t=80s) |
| Storage | 256GBSSD at2:09 | — | — | [source](https://www.youtube.com/watch?v=RkzCAaIV_cQ&t=80s) |

**Other component disclosures:** unnamed4Bmodeldemo

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, gpu, psu; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V053-P001 / V053-S01 | unnamed4Bmodel; not stated; not stated | generation: 9 tokens/s | localdemonstration; narrated result;not independently verified; [1:30](https://www.youtube.com/watch?v=RkzCAaIV_cQ&t=90s) |

---

### V053-HP-C002 · TinyAIPocketLab

**Role:** configuration as explicitly narrated;creator/third-party claim,not independently verified. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=RkzCAaIV_cQ&t=140s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 2/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=RkzCAaIV_cQ&t=140s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=RkzCAaIV_cQ&t=140s) |
| RAM | system/unspecified RAM: 80GB memory;type not stated | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=RkzCAaIV_cQ&t=140s) |
| GPU | — | PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=RkzCAaIV_cQ&t=140s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=RkzCAaIV_cQ&t=140s) |
| Storage | 1TBSSD | — | — | [source](https://www.youtube.com/watch?v=RkzCAaIV_cQ&t=140s) |

**Other component disclosures:** TDP/supply rating,notwhole-systemwallmeasurement

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** TinyCLI Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** up to60W;30WTDP; rating/limit unless measurement expressly stated;NOT a PSU specification Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, gpu, psu; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V053-P002 / V053-S02 | GPT-OSS120B; not stated; TinyCLI;engine notstated | generation: 18 tokens/s | offlinedemo;notmodelqualityassessment; narrated result;not independently verified; [3:44](https://www.youtube.com/watch?v=RkzCAaIV_cQ&t=224s) |

---

### V053-HP-G001 · RTX5090

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=RkzCAaIV_cQ&t=74s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | RTX5090 | PerGPUVRAM:32GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=RkzCAaIV_cQ&t=74s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** No performance row can be safely assigned to this exact profile. Product mention/recommendation is not a measured build.


## Scope

Caption-only evidence;no chart/video viewing or independent hardware validation. ASR and source contradictions are retained. Full original caption text is not included. Original450claim records and99hardwarefact records are preserved byte-for-byte in their originalCSVs;new profiles/series are a separately typed organization layer.

## llmfit-aligned machine-readable records

Upstreamcommit`26450cccaf3a3f14b1822875f2473847a744a718`. Thisvideo has3losslessresearchprofiles;0have a minimalcore passingthe actualupstreamHardwareProfileJSONschema. Otherprofilesremain explicitlypartial,not paddedwithdefaults. Modelcatalogmetadata is incomplete;runconditions/prefill/concurrency/BOM/provenance remainnamespacedextensions. See[contract](llmfit/schema.md),[fieldmapping](llmfit/mapping.md),[validation](llmfit/validation-report.json). NativecompatibilityisNOTa completebuild,independentmeasurement or testedimport.
