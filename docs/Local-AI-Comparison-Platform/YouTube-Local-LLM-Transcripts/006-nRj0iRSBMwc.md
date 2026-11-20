# 006 · How Modders Unlocked a $5,000 Chip Inside Normal Nvidia GPUs

> Original research summary and factual claim tables — NOT a transcript or authored script.

- Source: [How Modders Unlocked a $5,000 Chip Inside Normal Nvidia GPUs](https://www.youtube.com/watch?v=nRj0iRSBMwc) · Channel: InRecord
- Caption language: en; automatic track. Retrieval: 2026-11-20T20:49:39.282488+08:00 (Asia/Shanghai).
- Coverage: returned caption track, not audio-verified; first 0.0 ms, final 498017.0 ms. No visual charts or manufacturer specifications independently checked.

## Original research notes

This source is relevant to local inference because it connects low-level GPU configuration claims to prompt-processing and fine-tuning workloads, not just image generation.

- [0:17](https://www.youtube.com/watch?v=nRj0iRSBMwc&t=17s): The creator frames consumer and workstation differences as a software-enforced performance restriction. This is the video's explanation; the note does not independently confirm the underlying hardware policy.
- [1:35](https://www.youtube.com/watch?v=nRj0iRSBMwc&t=95s): Tensor-oriented computation is presented as the link between the hardware discussion and local AI tasks. The claimed relevance is workload-specific rather than a promise of uniform application acceleration.
- [2:50](https://www.youtube.com/watch?v=nRj0iRSBMwc&t=170s): The narrative describes unsuccessful modification approaches and maintenance problems. This supplies a risk theme for research, not instructions or a recommendation to alter firmware or drivers.
- [5:26](https://www.youtube.com/watch?v=nRj0iRSBMwc&t=326s): The video extends its claimed benefits across several AI workloads and operating-system approaches. Such cross-workload assertions require separate measurement evidence rather than reuse of one percentage everywhere.
- [6:57](https://www.youtube.com/watch?v=nRj0iRSBMwc&t=417s): Power-state behavior is discussed as a limitation on persistence. Operational reliability and whether a change survives normal device use matter alongside any initial speed measurement.

**Platform implication.** Record this as an unverified optimization claim with safety and repeatability questions. A hardware advisor should not recommend low-level modifications from a promotional video or assume that the reported effect applies to every GPU generation.

## Hardware profile index

These are partial caption-evidence profiles,not LCZ-equivalent complete builds. No part from an LCZ reference has been inserted into a video configuration.

| Profile / role | Core evidence coverage | Linked observations |
| --- | --- | --- |
| [V006-HP-G001 — RTX3090Ti](hardware-profiles/V006-HP-G001.md) | GPU product/configuration reference;not a complete tested build;1/6corecategories,notcomplete | 2 |
| [V006-HP-E01 — RTX4090 GPUUnlocker tensor-rate report](hardware-profiles/V006-HP-E01.md) | Reported GPU compute experiment,not complete LLM build;1/6corecategories,notcomplete | 1 |

## Test series and run conditions

Only source-reported observations follow. Unknown conditions stay unknown;rows are not certified apples-to-apples comparisons. Single-request speed,aggregate throughput,prefill,TTFT,quality,memory,power and estimates use separate series. Ranges are preserved;no new sweep points,repeats,medians or statistics were created.

### V006-S01 · Auxiliary transport / compute / embedding (not LLM decode)

- **Profile(s):** V006-HP-E01, V006-HP-G001
- **Model / weights / quantization:** not specified; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** GPUUnlock claim; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V006-P001; V006-HP-G001 | BF16 matrix throughput · 87.5 to157.4 TFLOP/s | 450Wstocklimit;microbenchmark,notLLMdecode; creator cites third-party claims;unverified | [4:53](https://www.youtube.com/watch?v=nRj0iRSBMwc&t=293s) |
| V006-P002; V006-HP-G001 | TF32 matrix throughput increase · 94 percent | notLLMthroughput; creator cites third-party claims;unverified | [5:06](https://www.youtube.com/watch?v=nRj0iRSBMwc&t=306s) |
| V006-P005; V006-HP-E01 | heavy matrix-workload speedup · 12–34 percent | not a specificLLMresult; creator cites third-party claims;unverified | [6:14](https://www.youtube.com/watch?v=nRj0iRSBMwc&t=374s) |

### V006-S02 · Other reported observations / stability (not a comparable speed benchmark)

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** not specified; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** GPUUnlock claim; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V006-P003; GPU series not isolated for workload claim (profileunassigned) | LLM prompt-processing increase · 33–55 percent | models/context/precision missing; creator cites third-party claims;unverified | [5:14](https://www.youtube.com/watch?v=nRj0iRSBMwc&t=314s) |
| V006-P004; GPU series not isolated (profileunassigned) | fine-tuning increase · up to50 percent | training,notgeneration; creator cites third-party claims;unverified | [5:21](https://www.youtube.com/watch?v=nRj0iRSBMwc&t=321s) |

## Detailed hardware profiles

Minimum fields follow motherboard/CPU/RAMmodules+speed/GPUvariant+count+VRAM/PSU/storage. “Unknown”means not reported,not an invitation to fill from a different owner or manufacturer memory. Costs are quotes/paid/estimates only where identified;no fakeBOMtotal.

### V006-HP-G001 · RTX3090Ti

**Role:** GPU product/configuration reference;not a complete tested build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=nRj0iRSBMwc&t=285s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| GPU | RTX3090Ti | PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=nRj0iRSBMwc&t=285s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Unknown / not reported Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** 450Wstocklimit; reported product rating/recommendation;not whole-system measurement;NOT a PSU specification Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V006-P001 / V006-S01 | not specified; not stated; GPUUnlock claim | BF16 matrix throughput: 87.5 to157.4 TFLOP/s | 450Wstocklimit;microbenchmark,notLLMdecode; creator cites third-party claims;unverified; [4:53](https://www.youtube.com/watch?v=nRj0iRSBMwc&t=293s) |
| V006-P002 / V006-S01 | not specified; not stated; GPUUnlock claim | TF32 matrix throughput increase: 94 percent | notLLMthroughput; creator cites third-party claims;unverified; [5:06](https://www.youtube.com/watch?v=nRj0iRSBMwc&t=306s) |

---

### V006-HP-E01 · RTX4090 GPUUnlocker tensor-rate report

**Role:** Reported GPU compute experiment,not complete LLM build. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=nRj0iRSBMwc&t=42s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=nRj0iRSBMwc&t=42s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=nRj0iRSBMwc&t=42s) |
| RAM | — | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=nRj0iRSBMwc&t=42s) |
| GPU | RTX4090 | PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=nRj0iRSBMwc&t=42s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=nRj0iRSBMwc&t=42s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=nRj0iRSBMwc&t=42s) |

**Selection / tradeoffs:** Unknown / not reported RawFP16 tensor throughput is not LLMdecode throughput;hostCPU/RAM not supplied.

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** GPUUnlocker experimental40-series branch as narrated Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V006-P005 / V006-S01 | not specified; not stated; GPUUnlock claim | heavy matrix-workload speedup: 12–34 percent | not a specificLLMresult; creator cites third-party claims;unverified; [6:14](https://www.youtube.com/watch?v=nRj0iRSBMwc&t=374s) |


## Scope

Caption-only evidence;no chart/video viewing or independent hardware validation. ASR and source contradictions are retained. Full original caption text is not included. Original450claim records and99hardwarefact records are preserved byte-for-byte in their originalCSVs;new profiles/series are a separately typed organization layer.

## llmfit-aligned machine-readable records

Upstreamcommit`26450cccaf3a3f14b1822875f2473847a744a718`. Thisvideo has2losslessresearchprofiles;0have a minimalcore passingthe actualupstreamHardwareProfileJSONschema. Otherprofilesremain explicitlypartial,not paddedwithdefaults. Modelcatalogmetadata is incomplete;runconditions/prefill/concurrency/BOM/provenance remainnamespacedextensions. See[contract](llmfit/schema.md),[fieldmapping](llmfit/mapping.md),[validation](llmfit/validation-report.json). NativecompatibilityisNOTa completebuild,independentmeasurement or testedimport.
