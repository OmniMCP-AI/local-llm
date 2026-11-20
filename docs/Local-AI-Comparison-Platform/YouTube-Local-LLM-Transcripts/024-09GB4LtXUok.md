# 024 · Strata Coder tested - Local LLM setup

> Original research summary and factual claim tables — NOT a transcript or authored script.

- Source: [Strata Coder tested - Local LLM setup](https://www.youtube.com/watch?v=09GB4LtXUok) · Channel: Luke's Dev Lab
- Caption language: en; automatic track. Retrieval: 2026-11-20T20:49:39.282488+08:00 (Asia/Shanghai).
- Coverage: returned caption track, not audio-verified; first 680.0 ms, final 1112679.9999999998 ms. No visual charts or manufacturer specifications independently checked.

## Original research notes

A local coding setup is evaluated through practical tasks, revealing a broader quality picture than a single throughput number or one attractive generated page.

- [0:41](https://www.youtube.com/watch?v=09GB4LtXUok&t=41s): The presenter begins with a constrained hardware and model choice. The observations describe that configuration, not the complete runtime's performance across its possible supported machines.
- [3:46](https://www.youtube.com/watch?v=09GB4LtXUok&t=226s): A retrieval-style test places information at multiple positions and repeats attempts. This provides a more concrete context-handling question than merely quoting the maximum accepted context length.
- [6:45](https://www.youtube.com/watch?v=09GB4LtXUok&t=405s): A generated interface needs follow-up corrections to layout and controls. Iterative repair effort is an outcome variable that can be missed by a first-response demonstration.
- [12:34](https://www.youtube.com/watch?v=09GB4LtXUok&t=754s): An interactive example is tested for movement and usability, not just whether code was emitted. Successful generation and satisfactory user experience remain distinct evaluation steps.
- [15:39](https://www.youtube.com/watch?v=09GB4LtXUok&t=939s): The creator reports a mixed overall result that includes troublesome prefill behavior. Separate input latency, reasoning output and application correctness rather than compressing these into one approval score.

**Platform implication.** A useful local-agent comparison should retain task artifacts, retries and human correction time. Treat this as one practical evaluation narrative; reproduce its tests before assigning a general coding-quality or long-context certification to the model.

## Hardware profile index

These are partial caption-evidence profiles,not LCZ-equivalent complete builds. No part from an LCZ reference has been inserted into a video configuration.

| Profile / role | Core evidence coverage | Linked observations |
| --- | --- | --- |
| [V024-HP-C001 — creator workstation / captionRTX2080at2:03/RTX2000later;exactSKUuncertain](hardware-profiles/V024-HP-C001.md) | configuration as explicitly narrated;creator/third-party claim,not independently verified;2/6corecategories,notcomplete | 5 |
| [V024-HP-C002 — secondbenchmarkGPU / RTX5090](hardware-profiles/V024-HP-C002.md) | configuration as explicitly narrated;creator/third-party claim,not independently verified;1/6corecategories,notcomplete | 3 |

## Test series and run conditions

Only source-reported observations follow. Unknown conditions stay unknown;rows are not certified apples-to-apples comparisons. Single-request speed,aggregate throughput,prefill,TTFT,quality,memory,power and estimates use separate series. Ranges are preserved;no new sweep points,repeats,medians or statistics were created.

### V024-S01 · Prefill / input processing

- **Profile(s):** V024-HP-C001, V024-HP-C002
- **Model / weights / quantization:** Qwen3.8FlashNext GSQR Coda as captioned; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Strata; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V024-P001; V024-HP-C001 | uncachedprefill · justover70 tokens/s | 32GBDDR4host; narrated result;not independently verified | [2:37](https://www.youtube.com/watch?v=09GB4LtXUok&t=157s) |
| V024-P002; V024-HP-C001 | cachedprefill · 8K to479K tokens/s | source sayspersecond;notcontextcapacity; narrated result;not independently verified | [2:41](https://www.youtube.com/watch?v=09GB4LtXUok&t=161s) |
| V024-P004; V024-HP-C002 | uncachedprefill · justunder200 tokens/s | sameCodaartifact; narrated result;not independently verified | [3:09](https://www.youtube.com/watch?v=09GB4LtXUok&t=189s) |
| V024-P005; V024-HP-C002 | cachedprefill · 22K toover1M tokens/s | notcontextcapacity; narrated result;not independently verified | [3:15](https://www.youtube.com/watch?v=09GB4LtXUok&t=195s) |

### V024-S02 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V024-HP-C001, V024-HP-C002
- **Model / weights / quantization:** Qwen3.8FlashNext GSQR Coda as captioned; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Strata; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V024-P003; V024-HP-C001 | decode · 42–43 tokens/s | 32GBDDR4host; narrated result;not independently verified | [2:52](https://www.youtube.com/watch?v=09GB4LtXUok&t=172s) |
| V024-P006; V024-HP-C002 | decode · 182 tokens/s | sameCodaartifact; narrated result;not independently verified | [3:23](https://www.youtube.com/watch?v=09GB4LtXUok&t=203s) |

### V024-S03 · Quality / task outcomes (not speed)

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** Qwen3.8FlashNext GSQR Coda as captioned; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Strata; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V024-P007; testGPU notretied (profileunassigned) | context-retrievalsuccess · 15/15 trials | 128Kcontext;5depths,3runseach; narrated result;not independently verified | [3:48](https://www.youtube.com/watch?v=09GB4LtXUok&t=228s) |
| V024-P008; samequalityevaluation (profileunassigned) | reasoningpassrate · 100/100/92/58 percent | easy/medium/hard/expertrespectively; narrated result;not independently verified | [4:48](https://www.youtube.com/watch?v=09GB4LtXUok&t=288s) |
| V024-P009; sameevaluation (profileunassigned) | Pythonchallengepassrate · 99/100 tasks | creatorchallenge-suite,notindependentHumanEval; narrated result;not independently verified | [5:27](https://www.youtube.com/watch?v=09GB4LtXUok&t=327s) |

### V024-S04 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V024-HP-C001
- **Model / weights / quantization:** Coda; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Strata; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V024-P010; V024-HP-C001 | generation · ~40 tokens/s | closingapproximationofsame42–43result;not independentrun; narrated result;not independently verified | [17:29](https://www.youtube.com/watch?v=09GB4LtXUok&t=1049s) |

### V024-S05 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V024-HP-C001
- **Model / weights / quantization:** Coda vs27Bdense; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Strata; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V024-P011; V024-HP-C001 | speedratio · ~4 times | task/modelcomparison;notqualityequivalent; narrated result;not independently verified | [17:56](https://www.youtube.com/watch?v=09GB4LtXUok&t=1076s) |

## Detailed hardware profiles

Minimum fields follow motherboard/CPU/RAMmodules+speed/GPUvariant+count+VRAM/PSU/storage. “Unknown”means not reported,not an invitation to fill from a different owner or manufacturer memory. Costs are quotes/paid/estimates only where identified;no fakeBOMtotal.

### V024-HP-C001 · creator workstation / captionRTX2080at2:03/RTX2000later;exactSKUuncertain

**Role:** configuration as explicitly narrated;creator/third-party claim,not independently verified. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=09GB4LtXUok&t=123s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 2/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=09GB4LtXUok&t=123s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=09GB4LtXUok&t=123s) |
| RAM | system/unspecified RAM: 32GBDDR4 | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=09GB4LtXUok&t=123s) |
| GPU | captionRTX2080at2:03/RTX2000later;exactSKUuncertain | PerGPUVRAM:16GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=09GB4LtXUok&t=123s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=09GB4LtXUok&t=123s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=09GB4LtXUok&t=123s) |

**Other component disclosures:** not automatically identifiedasRTX2000Ada

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Strata/Coda Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** 70Wlimit; rating/limit unless measurement expressly stated;NOT a PSU specification Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V024-P001 / V024-S01 | Qwen3.8FlashNext GSQR Coda as captioned; not stated; Strata | uncachedprefill: justover70 tokens/s | 32GBDDR4host; narrated result;not independently verified; [2:37](https://www.youtube.com/watch?v=09GB4LtXUok&t=157s) |
| V024-P002 / V024-S01 | Qwen3.8FlashNext GSQR Coda as captioned; not stated; Strata | cachedprefill: 8K to479K tokens/s | source sayspersecond;notcontextcapacity; narrated result;not independently verified; [2:41](https://www.youtube.com/watch?v=09GB4LtXUok&t=161s) |
| V024-P003 / V024-S02 | Qwen3.8FlashNext GSQR Coda as captioned; not stated; Strata | decode: 42–43 tokens/s | 32GBDDR4host; narrated result;not independently verified; [2:52](https://www.youtube.com/watch?v=09GB4LtXUok&t=172s) |
| V024-P010 / V024-S04 | Coda; not stated; Strata | generation: ~40 tokens/s | closingapproximationofsame42–43result;not independentrun; narrated result;not independently verified; [17:29](https://www.youtube.com/watch?v=09GB4LtXUok&t=1049s) |
| V024-P011 / V024-S05 | Coda vs27Bdense; not stated; Strata | speedratio: ~4 times | task/modelcomparison;notqualityequivalent; narrated result;not independently verified; [17:56](https://www.youtube.com/watch?v=09GB4LtXUok&t=1076s) |

---

### V024-HP-C002 · secondbenchmarkGPU / RTX5090

**Role:** configuration as explicitly narrated;creator/third-party claim,not independently verified. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=09GB4LtXUok&t=189s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=09GB4LtXUok&t=189s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=09GB4LtXUok&t=189s) |
| RAM | — | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=09GB4LtXUok&t=189s) |
| GPU | RTX5090 | PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=09GB4LtXUok&t=189s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=09GB4LtXUok&t=189s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=09GB4LtXUok&t=189s) |

**Other component disclosures:** do notcarry32GBhostRAMfromseparateworkstation

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V024-P004 / V024-S01 | Qwen3.8FlashNext GSQR Coda as captioned; not stated; Strata | uncachedprefill: justunder200 tokens/s | sameCodaartifact; narrated result;not independently verified; [3:09](https://www.youtube.com/watch?v=09GB4LtXUok&t=189s) |
| V024-P005 / V024-S01 | Qwen3.8FlashNext GSQR Coda as captioned; not stated; Strata | cachedprefill: 22K toover1M tokens/s | notcontextcapacity; narrated result;not independently verified; [3:15](https://www.youtube.com/watch?v=09GB4LtXUok&t=195s) |
| V024-P006 / V024-S02 | Qwen3.8FlashNext GSQR Coda as captioned; not stated; Strata | decode: 182 tokens/s | sameCodaartifact; narrated result;not independently verified; [3:23](https://www.youtube.com/watch?v=09GB4LtXUok&t=203s) |


## Scope

Caption-only evidence;no chart/video viewing or independent hardware validation. ASR and source contradictions are retained. Full original caption text is not included. Original450claim records and99hardwarefact records are preserved byte-for-byte in their originalCSVs;new profiles/series are a separately typed organization layer.

## llmfit-aligned machine-readable records

Upstreamcommit`26450cccaf3a3f14b1822875f2473847a744a718`. Thisvideo has2losslessresearchprofiles;1have a minimalcore passingthe actualupstreamHardwareProfileJSONschema. Otherprofilesremain explicitlypartial,not paddedwithdefaults. Modelcatalogmetadata is incomplete;runconditions/prefill/concurrency/BOM/provenance remainnamespacedextensions. See[contract](llmfit/schema.md),[fieldmapping](llmfit/mapping.md),[validation](llmfit/validation-report.json). NativecompatibilityisNOTa completebuild,independentmeasurement or testedimport.
