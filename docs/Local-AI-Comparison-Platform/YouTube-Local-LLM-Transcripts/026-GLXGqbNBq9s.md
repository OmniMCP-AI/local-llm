# 026 · Project Maya Deepseek V4.1 Flash 1017 + GLM 5.3 Local Ai Review

> Original research summary and factual claim tables — NOT a transcript or authored script.

- Source: [Project Maya Deepseek V4.1 Flash 1017 + GLM 5.3 Local Ai Review](https://www.youtube.com/watch?v=GLXGqbNBq9s) · Channel: Digital Spaceport
- Caption language: en; automatic track. Retrieval: 2026-11-20T20:49:39.282488+08:00 (Asia/Shanghai).
- Coverage: returned caption track, not audio-verified; first 0.0 ms, final 506400.0 ms. No visual charts or manufacturer specifications independently checked.

## Original research notes

A local-model review combines an older workstation, heavily compressed artifacts and coding demonstrations, making the configuration details essential to interpreting the result.

- [0:19](https://www.youtube.com/watch?v=GLXGqbNBq9s&t=19s): The creator describes an older workstation with multiple consumer GPUs and substantial RAM. The reported generation experience belongs to that full memory hierarchy, not just its graphics cards.
- [1:41](https://www.youtube.com/watch?v=GLXGqbNBq9s&t=101s): Alternative runtime and model-file routes are mentioned with large storage requirements. A claim that a model runs locally does not mean its artifact is small or entirely GPU-resident.
- [2:50](https://www.youtube.com/watch?v=GLXGqbNBq9s&t=170s): An adaptive game is offered as an example application. Its existence demonstrates an output artifact, but does not establish correctness or comparable effort against other models.
- [4:47](https://www.youtube.com/watch?v=GLXGqbNBq9s&t=287s): The creator describes extensive iteration behind a polished result. Development time, repeated attempts and interaction volume should be considered when assessing practical productivity rather than judging the final screen alone.
- [5:58](https://www.youtube.com/watch?v=GLXGqbNBq9s&t=358s): Another model is tried on an animated example. A small number of visually evaluated outputs supplies qualitative evidence, not a comprehensive coding or multimodal quality benchmark.

**Platform implication.** For the existing platform, preserve the complete workstation configuration and the work required to reach an artifact. Do not assign the video's final application quality to a model without recording iteration history, compression and runtime provenance.

## Hardware profile index

These are partial caption-evidence profiles,not LCZ-equivalent complete builds. No part from an LCZ reference has been inserted into a video configuration.

| Profile / role | Core evidence coverage | Linked observations |
| --- | --- | --- |
| [V026-HP-TEST — Dell PrecisionT5810 /E5-2696v4 /dual3060 /256GB](hardware-profiles/V026-HP-TEST.md) | creator demonstration setup;3/6corecategories,notcomplete | 3 |

Only1 grounded profile is available;additional complete machines cannot be invented from this source.

## Test series and run conditions

Only source-reported observations follow. Unknown conditions stay unknown;rows are not certified apples-to-apples comparisons. Single-request speed,aggregate throughput,prefill,TTFT,quality,memory,power and estimates use separate series. Ranges are preserved;no new sweep points,repeats,medians or statistics were created.

### V026-S01 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V026-HP-TEST
- **Model / weights / quantization:** DeepSeekV4.1Flash1017; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** ProjectMaya; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V026-P001; V026-HP-TEST | decode · 11.1 tokens/s | prompt/context/batch not fully stated; narrated result;not independently verified | [0:16](https://www.youtube.com/watch?v=GLXGqbNBq9s&t=16s) |

### V026-S02 · Prefill / input processing

- **Profile(s):** Unassigned:source does not safely bind an exact profile
- **Model / weights / quantization:** modelnotunambiguouslyidentified; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Maya; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V026-P002; hardwareofrecalledrunnotclear (profileunassigned) | prefill · 1100–1500 tokens/s | creatorrecallsdevelopmentthrough1Mcontext;currentUI128Kdifferent; narrated result;not independently verified | [5:17](https://www.youtube.com/watch?v=GLXGqbNBq9s&t=317s) |

### V026-S03 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V026-HP-TEST
- **Model / weights / quantization:** DeepSeekV4.1Flash; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Maya; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V026-P003; V026-HP-TEST | decode · about9 tokens/s | deepercontext;exactlengthnotstated; narrated result;not independently verified | [5:54](https://www.youtube.com/watch?v=GLXGqbNBq9s&t=354s) |

### V026-S04 · Other reported observations / stability (not a comparable speed benchmark)

- **Profile(s):** V026-HP-TEST
- **Model / weights / quantization:** animated-catcodingmodel;identitynotisolated; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** Maya; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V026-P004; V026-HP-TEST | thinkingtime · 4,413 as captioned seconds | ASRmayhavecollapseddecimal;do notcorrectortrustexactvalue; narrated timing;value requires sourcecheck | [7:05](https://www.youtube.com/watch?v=GLXGqbNBq9s&t=425s) |

## Detailed hardware profiles

Minimum fields follow motherboard/CPU/RAMmodules+speed/GPUvariant+count+VRAM/PSU/storage. “Unknown”means not reported,not an invitation to fill from a different owner or manufacturer memory. Costs are quotes/paid/estimates only where identified;no fakeBOMtotal.

### V026-HP-TEST · Dell PrecisionT5810 /E5-2696v4 /dual3060 /256GB

**Role:** creator demonstration setup. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=GLXGqbNBq9s&t=19s) · [additional disclosure](https://www.youtube.com/watch?v=GLXGqbNBq9s&t=19s)

**Use case:** DeepSeekV4.1Flash1017 andGLM5.3 generation demonstrations.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 3/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=GLXGqbNBq9s&t=19s) |
| CPU | E5 2696 V4;22cores44threads as narrated | — | — | [source](https://www.youtube.com/watch?v=GLXGqbNBq9s&t=19s) |
| RAM | 256GB system RAM;modulecount/speed not stated | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=GLXGqbNBq9s&t=19s) |
| GPU | 3060s (as captioned) | qty 2; PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=GLXGqbNBq9s&t=19s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=GLXGqbNBq9s&t=19s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=GLXGqbNBq9s&t=19s) |
| Chassis | DellPrecisionT5810 system;exactchassispart notstated | — | — | [source](https://www.youtube.com/watch?v=GLXGqbNBq9s&t=19s) |

**Other component disclosures:** GPU at0:23;CPU at0:29;RAM at0:35;no per-card VRAM inferred

**Selection / tradeoffs:** Unknown / not reported The captions do not give per-cardVRAM,PSU,storage or motherboard model;T5810 is a chassis/system identity,not a motherboard SKU.

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Project Maya,described as a Strata fork;new release age~5hours is not a stable version number. DeepSeek1017 checkpoint as narrated. Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V026-P001 / V026-S01 | DeepSeekV4.1Flash1017; not stated; ProjectMaya | decode: 11.1 tokens/s | prompt/context/batch not fully stated; narrated result;not independently verified; [0:16](https://www.youtube.com/watch?v=GLXGqbNBq9s&t=16s) |
| V026-P003 / V026-S03 | DeepSeekV4.1Flash; not stated; Maya | decode: about9 tokens/s | deepercontext;exactlengthnotstated; narrated result;not independently verified; [5:54](https://www.youtube.com/watch?v=GLXGqbNBq9s&t=354s) |
| V026-P004 / V026-S04 | animated-catcodingmodel;identitynotisolated; not stated; Maya | thinkingtime: 4,413 as captioned seconds | ASRmayhavecollapseddecimal;do notcorrectortrustexactvalue; narrated timing;value requires sourcecheck; [7:05](https://www.youtube.com/watch?v=GLXGqbNBq9s&t=425s) |


## Scope

Caption-only evidence;no chart/video viewing or independent hardware validation. ASR and source contradictions are retained. Full original caption text is not included. Original450claim records and99hardwarefact records are preserved byte-for-byte in their originalCSVs;new profiles/series are a separately typed organization layer.
