# 019 · Budget Builder's Dream! Build Your Own 128GB Local AI Server for Under ¥3000 – Running Qwen3.8-Fl...

> Original research summary and factual claim tables — NOT a transcript or authored script.

- Source: [Budget Builder's Dream! Build Your Own 128GB Local AI Server for Under ¥3000 – Running Qwen3.8-Fl...](https://www.youtube.com/watch?v=mjR-LJmHg_I) · Channel: 阿雷科技
- Caption language: en; automatic track. Retrieval: 2026-11-20T20:49:39.282488+08:00 (Asia/Shanghai).
- Coverage: returned caption track, not audio-verified; first 1835.0 ms, final 336117.0 ms. No visual charts or manufacturer specifications independently checked.

## Original research notes

A budget server demonstration emphasizes local document work and reused components, while its example configuration highlights the need to resolve artifact details carefully.

- [0:10](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=10s): The creator describes expanding an older workstation platform with substantial system memory. Installed capacity is a starting point, but does not alone establish the performance of the model pipeline.
- [1:13](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=73s): The demonstrated WebUI workload names a particular model, context setting and quantization. Those details are more useful for reproducibility than the broader model branding in the displayed title.
- [2:23](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=143s): The presenter gives a low-cost build estimate and warns that graphics-card pricing may have changed. The estimate should remain dated and geographically attributed rather than becoming a default budget.
- [3:10](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=190s): Another configuration is described as only modestly faster in the creator's experience. This is an anecdotal comparison, not proof of equivalence across all models and memory arrangements.
- [4:42](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=282s): Private material on network storage motivates the local workflow. The audience need is keeping document processing under local control, not simply obtaining the highest generation rate.

**Platform implication.** An advisor should distinguish used-component acquisition costs from repeatable performance and operating overhead. Preserve the discrepancy between title-level branding and the actual demonstrated artifact instead of silently normalizing them into one model entry.

## Hardware profile index

These are partial caption-evidence profiles,not LCZ-equivalent complete builds. No part from an LCZ reference has been inserted into a video configuration.

| Profile / role | Core evidence coverage | Linked observations |
| --- | --- | --- |
| [V019-HP-TEST — Creator X99-T8 /128GB DDR3 /singleT10 NAS-analysis server](hardware-profiles/V019-HP-TEST.md) | creator built server;3/6corecategories,notcomplete | 2 |
| [V019-HP-E01 — Separate DD24-labelled /5060Ti comparison host](hardware-profiles/V019-HP-E01.md) | Caption-reported partial configuration /comparison;not a full build;2/6corecategories,notcomplete | 0 |
| [V019-HP-E02 — Suggested V100 alternative,not installed](hardware-profiles/V019-HP-E02.md) | Recommendation only;not tested/owned in this source;1/6corecategories,notcomplete | 0 |

## Test series and run conditions

Only source-reported observations follow. Unknown conditions stay unknown;rows are not certified apples-to-apples comparisons. Single-request speed,aggregate throughput,prefill,TTFT,quality,memory,power and estimates use separate series. Ranges are preserved;no new sweep points,repeats,medians or statistics were created.

### V019-S01 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V019-HP-TEST
- **Model / weights / quantization:** Qwen2.5-7B-Instruct as captioned; Exactrepository/filehash not reported unless source conditions state it; Q3_K_S. KVprecision:row-specific or unknown.
- **Engine / version / execution:** WebUI;engine notgiven; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V019-P001; V019-HP-TEST | generation · ~40;fluctuates30–60 tokens/s | 128Ksetting;Q3_K_S;titlementionsdifferentmodelfamily; narrated result;not independently verified | [1:40](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=100s) |

### V019-S02 · Power / energy (boundary-dependent)

- **Profile(s):** V019-HP-TEST
- **Model / weights / quantization:** notrestated; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** notstated; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V019-P002; V019-HP-TEST | power · about200 W | systemoperation;measurementboundarynotexplicit; narrated result;not independently verified | [5:23](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=323s) |

## Detailed hardware profiles

Minimum fields follow motherboard/CPU/RAMmodules+speed/GPUvariant+count+VRAM/PSU/storage. “Unknown”means not reported,not an invitation to fill from a different owner or manufacturer memory. Costs are quotes/paid/estimates only where identified;no fakeBOMtotal.

### V019-HP-TEST · Creator X99-T8 /128GB DDR3 /singleT10 NAS-analysis server

**Role:** creator built server. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=14s) · [additional disclosure](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=14s)

**Use case:** Private local NAS documents:creator prefers not to send that material to online APIs ([4:21](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=261s)).

**Budget / price basis:** Creator says total<3000;not an independently totaled complete BOM · T10 reportedly bought for a little over1000;RAM~1000;CPU+motherboard bundle<500. No exact itemized total. · Spoken amounts omit currency;video title uses¥. Purchase date not reported.. No complete BOM total has been calculated.

**Evidence completeness:** 3/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| RAM | DDR3;manufacturer/partnumber not reported | qty 4; 32GB each;128GBinstalled;speed/ECCnotstated | subtotal ~1000 for4sticks;currency notspoken; Installed;creator cost claim; Reported bundlecost,not a per-stickprice | [source](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=14s) |
| GPU | T10 | qty 1; Inferencecard;no videooutputs | subtotal A little over1000;currency notspoken; Creator says bought; Reported paid amount,not receiptverified | [source](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=119s) |
| Boot/displayGPU | Radeon6600XT | qty 1; Temporary display/bootrole;not inferenceVRAM | Creator-owned temporarypart | [source](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=54s) |
| Motherboard | Huananzhi X99-T8 | qty 1; DDR3;4additionalRAMslots described | Installed | [source](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=23s) |
| CPU+board bundle | CPU SKU unknown +X99-T8 | qty 1bundle | subtotal <500;not split betweenCPU/board; Source bundlequote;DO NOTdouble count with motherboardrow | [source](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=138s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=14s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=14s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=14s) |
| Cooling | A blower fan is audible;exact fan/cooling component and model not specified | — | — | [source](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=14s) |

**Other component disclosures:** board at0:26;T10 at0:41;6600XT at0:54;do not combine boot card VRAM with inference VRAM

**Selection / tradeoffs:** Cheap DDR3 capacity and an old inference card;creator accepts slower background processing for private workloads. T10 has no video outputs;this X99 board needs a separate boot/display card. Roughly200W reported operation is not the PSU rating.

**Expansion / compatibility:** Creator says4 more DDR3sticks can fit;second T10 is hypothetical,not tested. No BIOS,PSU orPCIe slot/lane map provided. Windows is mentioned as a usable general-purpose test,not confirmed as current inference OS.

**Deployment:** WebUI integration;Qwen2.5-7B-Instruct Q3_K_S;128Kcontext as narrated. Exact engine/OS/version not established. Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** About200W reported duringhostoperation;measurementboundarynotfullyspecified;NOT a PSU rating (5:23) Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Temporary6600XT supports boot/display;do not count it as inferenceVRAM. A V100 is suggested as an alternative,not installed.

**Unknowns:** cpu, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V019-P001 / V019-S01 | Qwen2.5-7B-Instruct as captioned; Q3_K_S; WebUI;engine notgiven | generation: ~40;fluctuates30–60 tokens/s | 128Ksetting;Q3_K_S;titlementionsdifferentmodelfamily; narrated result;not independently verified; [1:40](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=100s) |
| V019-P002 / V019-S02 | notrestated; not stated; notstated | power: about200 W | systemoperation;measurementboundarynotexplicit; narrated result;not independently verified; [5:23](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=323s) |

---

### V019-HP-E01 · Separate DD24-labelled /5060Ti comparison host

**Role:** Caption-reported partial configuration /comparison;not a full build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=184s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 2/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=184s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=184s) |
| RAM | 64GB | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=184s) |
| GPU | RTX5060Ti | PerGPUVRAM:16GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=184s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=184s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=184s) |

**Selection / tradeoffs:** Unknown / not reported DD24 label is uncertain;no motherboard/CPU binding. Qualitatively slightly faster;not theT10 NAS host.

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** No performance row can be safely assigned to this exact profile. Product mention/recommendation is not a measured build.

---

### V019-HP-E02 · Suggested V100 alternative,not installed

**Role:** Recommendation only;not tested/owned in this source. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=154s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=154s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=154s) |
| RAM | — | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=154s) |
| GPU | V100;variant not stated | PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=154s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=154s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=154s) |

**Selection / tradeoffs:** Unknown / not reported Do not transferT10 cost,VRAM or server measurements to this alternative.

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** No performance row can be safely assigned to this exact profile. Product mention/recommendation is not a measured build.


## Scope

Caption-only evidence;no chart/video viewing or independent hardware validation. ASR and source contradictions are retained. Full original caption text is not included. Original450claim records and99hardwarefact records are preserved byte-for-byte in their originalCSVs;new profiles/series are a separately typed organization layer.

## llmfit-aligned machine-readable records

Upstreamcommit`26450cccaf3a3f14b1822875f2473847a744a718`. Thisvideo has3losslessresearchprofiles;1have a minimalcore passingthe actualupstreamHardwareProfileJSONschema. Otherprofilesremain explicitlypartial,not paddedwithdefaults. Modelcatalogmetadata is incomplete;runconditions/prefill/concurrency/BOM/provenance remainnamespacedextensions. See[contract](llmfit/schema.md),[fieldmapping](llmfit/mapping.md),[validation](llmfit/validation-report.json). NativecompatibilityisNOTa completebuild,independentmeasurement or testedimport.
