# 025 · 11 GPUs You Should Get for Local AI Before Qwen 4's Release!

> Original research summary and factual claim tables — NOT a transcript or authored script.

- Source: [11 GPUs You Should Get for Local AI Before Qwen 4's Release!](https://www.youtube.com/watch?v=kQKCp7PlVxY) · Channel: Weights & Wonders
- Caption language: en; automatic track. Retrieval: 2026-11-20T20:49:39.282488+08:00 (Asia/Shanghai).
- Coverage: returned caption track, not audio-verified; first 480.0 ms, final 1287144.0 ms. No visual charts or manufacturer specifications independently checked.

## Original research notes

Despite sharing a title with another playlist entry, this is a different video ID and presents its own uncertain assumptions and hardware comparisons.

- [0:50](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=50s): The creator explicitly questions which model variant an early quality claim describes. Recommendations based on a presumed future artifact should remain conditional until its identity is established.
- [4:23](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=263s): A published hardware test is used to discuss realized bandwidth and splitting work across cards. The source attribution and execution method are necessary context for the performance claim.
- [7:45](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=465s): The shopping discussion applies a budget filter before examining remaining options. A shortlist generated under a budget is not the same as an unrestricted performance ranking.
- [10:58](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=658s): A dual-consumer-card route is discussed alongside new-purchase pricing and warranty. Acquisition channel and support risk can affect value even when total memory looks attractive.
- [14:21](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=861s): An Intel example depends on patched software and a named community result. Treat such support as a configuration-specific research lead rather than universal out-of-the-box compatibility.

**Platform implication.** Keep this entry distinct from position21 while avoiding duplicate assumptions in the knowledge base. A comparison record should distinguish official runtime support, community patches and forecasts, and preserve the budget and warranty conditions of each recommendation.

## Hardware profile index

These are partial caption-evidence profiles,not LCZ-equivalent complete builds. No part from an LCZ reference has been inserted into a video configuration.

| Profile / role | Core evidence coverage | Linked observations |
| --- | --- | --- |
| [V025-HP-C001 — modifiedpair / RTX2080Ti](hardware-profiles/V025-HP-C001.md) | configuration as explicitly narrated;creator/third-party claim,not independently verified;1/6corecategories,notcomplete | 1 |
| [V025-HP-C002 — SXM2 benchmarkpair / V100SXM2](hardware-profiles/V025-HP-C002.md) | configuration as explicitly narrated;creator/third-party claim,not independently verified;1/6corecategories,notcomplete | 1 |
| [V025-HP-G001 — RTX2080Ti(original)](hardware-profiles/V025-HP-G001.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 0 |
| [V025-HP-G003 — RX7900XTX](hardware-profiles/V025-HP-G003.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 1 |
| [V025-HP-G004 — RX970 as captioned;exactSKUuncertain](hardware-profiles/V025-HP-G004.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 0 |
| [V025-HP-G005 — ArcProB60](hardware-profiles/V025-HP-G005.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 2 |
| [V025-HP-G006 — TeslaP40](hardware-profiles/V025-HP-G006.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 1 |
| [V025-HP-G007 — TeslaV100](hardware-profiles/V025-HP-G007.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 1 |
| [V025-HP-G008 — TeslaV100](hardware-profiles/V025-HP-G008.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 0 |
| [V025-HP-G009 — AMDMI50](hardware-profiles/V025-HP-G009.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 0 |
| [V025-HP-E01 — Dual3060 comparison](hardware-profiles/V025-HP-E01.md) | Caption-reported partial configuration /comparison;not a full build;1/6corecategories,notcomplete | 1 |
| [V025-HP-E02 — Dual5060Ti16GB comparison](hardware-profiles/V025-HP-E02.md) | Caption-reported partial configuration /comparison;not a full build;1/6corecategories,notcomplete | 1 |
| [V025-HP-E03 — Singlemodified2080Ti22GB](hardware-profiles/V025-HP-E03.md) | Caption-reported partial configuration /comparison;not a full build;1/6corecategories,notcomplete | 1 |
| [V025-HP-E04 — DualP40 community comparison](hardware-profiles/V025-HP-E04.md) | Caption-reported partial configuration /comparison;not a full build;1/6corecategories,notcomplete | 1 |
| [V025-HP-E05 — DualP100 community comparison](hardware-profiles/V025-HP-E05.md) | Caption-reported partial configuration /comparison;not a full build;1/6corecategories,notcomplete | 4 |
| [V025-HP-E06 — DualMI50 16GB community comparison](hardware-profiles/V025-HP-E06.md) | Caption-reported partial configuration /comparison;not a full build;1/6corecategories,notcomplete | 1 |

## Test series and run conditions

Only source-reported observations follow. Unknown conditions stay unknown;rows are not certified apples-to-apples comparisons. Single-request speed,aggregate throughput,prefill,TTFT,quality,memory,power and estimates use separate series. Ranges are preserved;no new sweep points,repeats,medians or statistics were created.

### V025-S01 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V025-HP-C001, V025-HP-C002, V025-HP-E01, V025-HP-E02, V025-HP-E03, V025-HP-E04, V025-HP-E05, V025-HP-E06, V025-HP-G003, V025-HP-G005, V025-HP-G006, V025-HP-G007
- **Model / weights / quantization:** Qwen3.8 27B comparison;some claims about futureQwen4 are not these tests; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** llama.cpp family unless patch specified; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V025-P001; oneRTX3060 (profileunassigned) | decode · 16 tokens/s | 2bit;not4bit; narrated result;not independently verified | [9:17](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=557s) |
| V025-P002; V025-HP-E01 | decode · 57 tokens/s | 32Kprompt;sourceGitHub; narrated result;not independently verified | [9:59](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=599s) |
| V025-P003; samepair (profileunassigned) | decode · 43 tokens/s | 129Kprompt; narrated result;not independently verified | [10:07](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=607s) |
| V025-P006; V025-HP-E02 | decode · 76 tokens/s | tensor split;131Kcontext; narrated result;not independently verified | [11:15](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=675s) |
| V025-P007; samepair (profileunassigned) | decode · 43 tokens/s | slightlylargerfile;layersplit; narrated result;not independently verified | [11:40](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=700s) |
| V025-P008; samepair (profileunassigned) | decode · 66 tokens/s | samefile;tensorsplit; narrated result;not independently verified | [11:47](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=707s) |
| V025-P009; V025-HP-C001 | decode · 60 tokens/s | shortprompt;tensorsplit; narrated result;not independently verified | [12:30](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=750s) |
| V025-P010; V025-HP-E03 | decode · 30 tokens/s | 128Kcontext;8bitKV; narrated result;not independently verified | [13:09](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=789s) |
| V025-P011; V025-HP-G003 | decode · 63 tokens/s | 131Kcontext; narrated result;not independently verified | [13:40](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=820s) |
| V025-P012; twoRX97016GB as captioned;SKUuncertain (profileunassigned) | decode · 42 tokens/s | TomHardwareincommunitytable; narrated result;not independently verified | [14:14](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=854s) |
| V025-P013; V025-HP-G005 | decode · 53 tokens/s | patchedsoftware; narrated result;not independently verified | [14:34](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=874s) |
| V025-P014; V025-HP-G005 | decode · 16 tokens/s | withoutpatches; narrated result;not independently verified | [14:37](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=877s) |
| V025-P015; V025-HP-G006 | decode · 12 tokens/s | Zen test; narrated result;not independently verified | [15:55](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=955s) |
| V025-P016; V025-HP-E04 | decode · 23 tokens/s | separatecommunityresult; narrated result;not independently verified | [16:02](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=962s) |
| V025-P017; V025-HP-E05 | decode · 35 tokens/s | longcode;tensorsplit+MTP;creatortest; narrated result;not independently verified | [16:32](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=992s) |
| V025-P018; V025-HP-E05 | decode · 49 tokens/s | patchedllama.cpp;differentcreator; narrated result;not independently verified | [16:43](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=1003s) |
| V025-P020; V025-HP-E05 | decode · 23 tokens/s | after100Kprompt; narrated result;not independently verified | [17:03](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=1023s) |
| V025-P021; V025-HP-G007 | decode · 48 tokens/s | communitytable; narrated result;not independently verified | [17:30](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=1050s) |
| V025-P022; V025-HP-C002 | decode · 59 tokens/s | MTP;262Kcontext;notPCIeversion; narrated result;not independently verified | [18:12](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=1092s) |
| V025-P023; V025-HP-E06 | decode · 48 tokens/s | patchedsoftware; narrated result;not independently verified | [18:55](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=1135s) |

### V025-S02 · Elapsed workflow / phase time (not TTFT unless explicit)

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** Qwen3.8 27B comparison;some claims about futureQwen4 are not these tests; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** llama.cpp family unless patch specified; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V025-P004; samepair (profileunassigned) | prompt-to-finish time · 4.5 minutes | 129Kprompt;notunambiguouslyTTFT; narrated result;not independently verified | [10:25](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=625s) |

### V025-S03 · TTFT / startup latency

- **Profile(s):** V025-HP-E05
- **Model / weights / quantization:** Qwen3.8 27B comparison;some claims about futureQwen4 are not these tests; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** llama.cpp family unless patch specified; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V025-P005; oneRTX3090 (profileunassigned) | time to first token · under3 minutes | 128Kprompt; narrated result;not independently verified | [10:31](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=631s) |
| V025-P019; V025-HP-E05 | time to first token · 11.5 minutes | 100Kprompt; narrated result;not independently verified | [16:52](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=1012s) |

## Detailed hardware profiles

Minimum fields follow motherboard/CPU/RAMmodules+speed/GPUvariant+count+VRAM/PSU/storage. “Unknown”means not reported,not an invitation to fill from a different owner or manufacturer memory. Costs are quotes/paid/estimates only where identified;no fakeBOMtotal.

### V025-HP-C001 · modifiedpair / RTX2080Ti

**Role:** configuration as explicitly narrated;creator/third-party claim,not independently verified. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=727s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** ~$500each · Source-quoted price/estimate,not verified paid price · Keep literal currency;price date not established. Video publication date is not a purchase date.. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=727s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=727s) |
| RAM | — | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=727s) |
| GPU | RTX2080Ti | qty 2; PerGPUVRAM:22GB claimedpercard;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=727s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=727s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=727s) |
| Interconnect | tensor split runtime | — | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=727s) |

**Other component disclosures:** 44GBaggregateclaimed;notstock11GBcard

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V025-P009 / V025-S01 | Qwen3.8 27B comparison;some claims about futureQwen4 are not these tests; not stated; llama.cpp family unless patch specified | decode: 60 tokens/s | shortprompt;tensorsplit; narrated result;not independently verified; [12:30](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=750s) |

---

### V025-HP-C002 · SXM2 benchmarkpair / V100SXM2

**Role:** configuration as explicitly narrated;creator/third-party claim,not independently verified. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=1064s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=1064s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=1064s) |
| RAM | — | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=1064s) |
| GPU | V100SXM2 | qty 2; PerGPUVRAM:16GB each;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=1064s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=1064s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=1064s) |

**Other component disclosures:** 32GBaggregate;do notattachPCIe$420priceasSXM2price

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V025-P022 / V025-S01 | Qwen3.8 27B comparison;some claims about futureQwen4 are not these tests; not stated; llama.cpp family unless patch specified | decode: 59 tokens/s | MTP;262Kcontext;notPCIeversion; narrated result;not independently verified; [18:12](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=1092s) |

---

### V025-HP-G001 · RTX2080Ti(original)

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=723s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | RTX2080Ti(original) | PerGPUVRAM:11GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=723s) |

**Other component disclosures:** 616GB/s

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** No performance row can be safely assigned to this exact profile. Product mention/recommendation is not a measured build.

---

### V025-HP-G003 · RX7900XTX

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=799s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** ~$1300lastweek · Source-quoted price/estimate,not verified paid price · Keep literal currency;price date not established. Video publication date is not a purchase date.. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | RX7900XTX | PerGPUVRAM:24GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=799s) |

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
| V025-P011 / V025-S01 | Qwen3.8 27B comparison;some claims about futureQwen4 are not these tests; not stated; llama.cpp family unless patch specified | decode: 63 tokens/s | 131Kcontext; narrated result;not independently verified; [13:40](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=820s) |

---

### V025-HP-G004 · RX970 as captioned;exactSKUuncertain

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=834s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** ~$1500pair · Source-quoted price/estimate,not verified paid price · Keep literal currency;price date not established. Video publication date is not a purchase date.. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | RX970 as captioned;exactSKUuncertain | PerGPUVRAM:16GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=834s) |

**Other component disclosures:** 640GB/s

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** No performance row can be safely assigned to this exact profile. Product mention/recommendation is not a measured build.

---

### V025-HP-G005 · ArcProB60

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=861s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** $1000new · Source-quoted price/estimate,not verified paid price · Keep literal currency;price date not established. Video publication date is not a purchase date.. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | ArcProB60 | PerGPUVRAM:24GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=861s) |

**Other component disclosures:** 456GB/s

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V025-P013 / V025-S01 | Qwen3.8 27B comparison;some claims about futureQwen4 are not these tests; not stated; llama.cpp family unless patch specified | decode: 53 tokens/s | patchedsoftware; narrated result;not independently verified; [14:34](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=874s) |
| V025-P014 / V025-S01 | Qwen3.8 27B comparison;some claims about futureQwen4 are not these tests; not stated; llama.cpp family unless patch specified | decode: 16 tokens/s | withoutpatches; narrated result;not independently verified; [14:37](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=877s) |

---

### V025-HP-G006 · TeslaP40

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=943s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** $400 · Source-quoted price/estimate,not verified paid price · Keep literal currency;price date not established. Video publication date is not a purchase date.. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | TeslaP40 | PerGPUVRAM:24GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=943s) |

**Other component disclosures:** 346GB/s

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V025-P015 / V025-S01 | Qwen3.8 27B comparison;some claims about futureQwen4 are not these tests; not stated; llama.cpp family unless patch specified | decode: 12 tokens/s | Zen test; narrated result;not independently verified; [15:55](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=955s) |

---

### V025-HP-G007 · TeslaV100

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=1039s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** $900–1000 · Source-quoted price/estimate,not verified paid price · Keep literal currency;price date not established. Video publication date is not a purchase date.. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | TeslaV100 | PerGPUVRAM:32GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=1039s) |

**Other component disclosures:** 900GB/s

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V025-P021 / V025-S01 | Qwen3.8 27B comparison;some claims about futureQwen4 are not these tests; not stated; llama.cpp family unless patch specified | decode: 48 tokens/s | communitytable; narrated result;not independently verified; [17:30](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=1050s) |

---

### V025-HP-G008 · TeslaV100

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=1064s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** $420PCIe;benchmarkedpairSXM2different · Source-quoted price/estimate,not verified paid price · Keep literal currency;price date not established. Video publication date is not a purchase date.. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | TeslaV100 | PerGPUVRAM:16GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=1064s) |

**Other component disclosures:** 900GB/s

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** No performance row can be safely assigned to this exact profile. Product mention/recommendation is not a measured build.

---

### V025-HP-G009 · AMDMI50

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=1122s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** $310 · Source-quoted price/estimate,not verified paid price · Keep literal currency;price date not established. Video publication date is not a purchase date.. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | AMDMI50 | PerGPUVRAM:16GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=1122s) |

**Other component disclosures:** 1024GB/s

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** No performance row can be safely assigned to this exact profile. Product mention/recommendation is not a measured build.

---

### V025-HP-E01 · Dual3060 comparison

**Role:** Caption-reported partial configuration /comparison;not a full build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=600s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=600s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=600s) |
| RAM | — | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=600s) |
| GPU | RTX3060 | qty 2; PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=600s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=600s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=600s) |

**Selection / tradeoffs:** Unknown / not reported 32K versus129K result rows are separate context cases;do not import RAM orPSU from another video.

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V025-P002 / V025-S01 | Qwen3.8 27B comparison;some claims about futureQwen4 are not these tests; not stated; llama.cpp family unless patch specified | decode: 57 tokens/s | 32Kprompt;sourceGitHub; narrated result;not independently verified; [9:59](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=599s) |

---

### V025-HP-E02 · Dual5060Ti16GB comparison

**Role:** Caption-reported partial configuration /comparison;not a full build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=675s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=675s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=675s) |
| RAM | — | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=675s) |
| GPU | RTX5060Ti | qty 2; PerGPUVRAM:16GB each;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=675s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=675s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=675s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Tensor split versuslayer split discussed Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V025-P006 / V025-S01 | Qwen3.8 27B comparison;some claims about futureQwen4 are not these tests; not stated; llama.cpp family unless patch specified | decode: 76 tokens/s | tensor split;131Kcontext; narrated result;not independently verified; [11:15](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=675s) |

---

### V025-HP-E03 · Singlemodified2080Ti22GB

**Role:** Caption-reported partial configuration /comparison;not a full build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=789s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=789s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=789s) |
| RAM | — | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=789s) |
| GPU | RTX2080Ti modified | qty 1; PerGPUVRAM:22GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=789s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=789s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=789s) |

**Selection / tradeoffs:** Unknown / not reported Not the same memory capacity or power as a two-card build.

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** 128Kcontext,8bitKV as narrated Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V025-P010 / V025-S01 | Qwen3.8 27B comparison;some claims about futureQwen4 are not these tests; not stated; llama.cpp family unless patch specified | decode: 30 tokens/s | 128Kcontext;8bitKV; narrated result;not independently verified; [13:09](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=789s) |

---

### V025-HP-E04 · DualP40 community comparison

**Role:** Caption-reported partial configuration /comparison;not a full build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=962s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=962s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=962s) |
| RAM | — | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=962s) |
| GPU | TeslaP40 | qty 2; PerGPUVRAM:24GBeach as product specification in samechapter;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=962s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=962s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=962s) |

**Selection / tradeoffs:** Unknown / not reported Not a complete testedhostBOM;singlecard reference is separate.

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V025-P016 / V025-S01 | Qwen3.8 27B comparison;some claims about futureQwen4 are not these tests; not stated; llama.cpp family unless patch specified | decode: 23 tokens/s | separatecommunityresult; narrated result;not independently verified; [16:02](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=962s) |

---

### V025-HP-E05 · DualP100 community comparison

**Role:** Caption-reported partial configuration /comparison;not a full build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=992s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=992s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=992s) |
| RAM | — | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=992s) |
| GPU | P100 | qty 2; PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=992s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=992s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=992s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Tensor split+MTP;community patchedbuilds are separate runs Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V025-P017 / V025-S01 | Qwen3.8 27B comparison;some claims about futureQwen4 are not these tests; not stated; llama.cpp family unless patch specified | decode: 35 tokens/s | longcode;tensorsplit+MTP;creatortest; narrated result;not independently verified; [16:32](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=992s) |
| V025-P018 / V025-S01 | Qwen3.8 27B comparison;some claims about futureQwen4 are not these tests; not stated; llama.cpp family unless patch specified | decode: 49 tokens/s | patchedllama.cpp;differentcreator; narrated result;not independently verified; [16:43](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=1003s) |
| V025-P019 / V025-S03 | Qwen3.8 27B comparison;some claims about futureQwen4 are not these tests; not stated; llama.cpp family unless patch specified | time to first token: 11.5 minutes | 100Kprompt; narrated result;not independently verified; [16:52](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=1012s) |
| V025-P020 / V025-S01 | Qwen3.8 27B comparison;some claims about futureQwen4 are not these tests; not stated; llama.cpp family unless patch specified | decode: 23 tokens/s | after100Kprompt; narrated result;not independently verified; [17:03](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=1023s) |

---

### V025-HP-E06 · DualMI50 16GB community comparison

**Role:** Caption-reported partial configuration /comparison;not a full build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=1135s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=1135s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=1135s) |
| RAM | — | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=1135s) |
| GPU | AMDMI50 | qty 2; PerGPUVRAM:16GB each;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=1135s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=1135s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=1135s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Patchedruntime;versionnotstated Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V025-P023 / V025-S01 | Qwen3.8 27B comparison;some claims about futureQwen4 are not these tests; not stated; llama.cpp family unless patch specified | decode: 48 tokens/s | patchedsoftware; narrated result;not independently verified; [18:55](https://www.youtube.com/watch?v=kQKCp7PlVxY&t=1135s) |


## Scope

Caption-only evidence;no chart/video viewing or independent hardware validation. ASR and source contradictions are retained. Full original caption text is not included. Original450claim records and99hardwarefact records are preserved byte-for-byte in their originalCSVs;new profiles/series are a separately typed organization layer.
