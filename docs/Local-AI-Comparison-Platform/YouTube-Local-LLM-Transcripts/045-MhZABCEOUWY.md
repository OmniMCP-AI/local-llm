# 045 · NInfer + 千问3.8 27b = 1.5倍速@256K上下文(单张4090 24GB)

> Original research summary and factual claim tables — NOT a transcript or authored script.

- Source: [NInfer + 千问3.8 27b = 1.5倍速@256K上下文(单张4090 24GB)](https://www.youtube.com/watch?v=MhZABCEOUWY) · Channel: 云八云
- Caption language: zh; manual track. Retrieval: 2026-11-20T20:49:39.282488+08:00 (Asia/Shanghai).
- Coverage: returned caption track, not audio-verified; first 166.0 ms, final 678244.0 ms. No visual charts or manufacturer specifications independently checked.

## Original research notes

A single-machine runtime comparison is useful for its explicit tradeoff between sustained generation and the wait before the first response arrives.

- [0:24](https://www.youtube.com/watch?v=MhZABCEOUWY&t=24s): The creator describes substantial tuning of the baseline before evaluating another engine. Baseline effort and configuration should be recorded before interpreting any reported improvement as an intrinsic runtime advantage.
- [2:13](https://www.youtube.com/watch?v=MhZABCEOUWY&t=133s): The video contrasts a broadly compatible engine with a more specialized execution path. Compatibility breadth and aggressive optimization can create different maintenance and deployment tradeoffs for users.
- [4:02](https://www.youtube.com/watch?v=MhZABCEOUWY&t=242s): The presenter reports a large-context configuration on one consumer GPU. This is a configuration-specific claim, not proof that every artifact with the same model branding will fit identically.
- [5:54](https://www.youtube.com/watch?v=MhZABCEOUWY&t=354s): The new setup is described as taking longer to begin responding. A faster sustained output rate can therefore coexist with a worse first-response experience for some tasks.
- [7:40](https://www.youtube.com/watch?v=MhZABCEOUWY&t=460s): The summary explicitly acknowledges a cold-prefill disadvantage while discussing memory, context and power. These dimensions should remain separate rather than being combined into a single speedup claim.

**Platform implication.** The platform should display cold and warm behavior, first-token latency, generation speed and whole-system power separately. Seek original configuration files and repeat runs before presenting the creator's observed advantage as a generally reproducible result.

## Hardware profile index

These are partial caption-evidence profiles,not LCZ-equivalent complete builds. No part from an LCZ reference has been inserted into a video configuration.

| Profile / role | Core evidence coverage | Linked observations |
| --- | --- | --- |
| [V045-HP-TEST — 4090 (RTX4090 explicitly named at2:04)](hardware-profiles/V045-HP-TEST.md) | creator local test setup;1/6corecategories,notcomplete | 13 |

Only1 grounded profile is available;additional complete machines cannot be invented from this source.

## Test series and run conditions

Only source-reported observations follow. Unknown conditions stay unknown;rows are not certified apples-to-apples comparisons. Single-request speed,aggregate throughput,prefill,TTFT,quality,memory,power and estimates use separate series. Ranges are preserved;no new sweep points,repeats,medians or statistics were created.

### V045-S01 · Single-request generation / reported speed claim (concurrency may be unknown)

- **Profile(s):** V045-HP-TEST
- **Model / weights / quantization:** 千问3.8 27B unlesshistorical3.6noted; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** NInfer / llama.cpp; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V045-P001; V045-HP-TEST | decode · 七八十 tokens/s | 200K;llama.cpp;approximateChinese; creatorbaseline | [0:30](https://www.youtube.com/watch?v=MhZABCEOUWY&t=30s) |
| V045-P002; V045-HP-TEST | average decode · 一百 tokens/s | 256K;NInfer;approximateChinese; creatorrun | [4:10](https://www.youtube.com/watch?v=MhZABCEOUWY&t=250s) |
| V045-P006; V045-HP-TEST | small-task generation · ~130 tokens/s | NInfer; creatorrun | [6:34](https://www.youtube.com/watch?v=MhZABCEOUWY&t=394s) |
| V045-P007; V045-HP-TEST | long-context decode · 五六十;goodcase七十 tokens/s | llama.cpp+MTP; creatorcomparison | [6:55](https://www.youtube.com/watch?v=MhZABCEOUWY&t=415s) |
| V045-P008; V045-HP-TEST | overall generation ratio · 1.5 times | workloadnotidenticaltoallpriornumbers; creatorapproximation | [7:01](https://www.youtube.com/watch?v=MhZABCEOUWY&t=421s) |
| V045-P013; V045-HP-TEST | historical generation · 40–50 tokens/s | Qwen3.6+MTP;not3.8samemodel; creatorrecollection | [10:58](https://www.youtube.com/watch?v=MhZABCEOUWY&t=658s) |

### V045-S02 · TTFT / startup latency

- **Profile(s):** V045-HP-TEST
- **Model / weights / quantization:** 千问3.8 27B unlesshistorical3.6noted; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** NInfer / llama.cpp; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V045-P003; V045-HP-TEST | time to first token · ~五 seconds | llama.cpp;firstcoldagentrequest; creatorrun | [6:01](https://www.youtube.com/watch?v=MhZABCEOUWY&t=361s) |
| V045-P004; V045-HP-TEST | time to first token · 十二三 seconds | NInfer;coldagentrequest;not12.3s; creatorrun | [6:03](https://www.youtube.com/watch?v=MhZABCEOUWY&t=363s) |

### V045-S03 · Prefill / input processing

- **Profile(s):** V045-HP-TEST
- **Model / weights / quantization:** 千问3.8 27B unlesshistorical3.6noted; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** NInfer / llama.cpp; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V045-P005; V045-HP-TEST | coldprefill speed deficit · 两三成 fraction as spoken | NInferrelativebaseline;rough20–30%,notexact; creatorcomparison | [6:19](https://www.youtube.com/watch?v=MhZABCEOUWY&t=379s) |

### V045-S04 · Power / energy (boundary-dependent)

- **Profile(s):** V045-HP-TEST
- **Model / weights / quantization:** 千问3.8 27B unlesshistorical3.6noted; Exactrepository/filehash not reported unless source conditions state it; not stated. KVprecision:row-specific or unknown.
- **Engine / version / execution:** NInfer / llama.cpp; version unknown unless row states it. TP/layer split/speculation,cachewarm/cold:row-specific or unknown.
- **Workload controls:** input/context/output lengths,batch/concurrency,repeatcount,statistic,temperature:only explicitly stated row conditions apply;otherwise unknown. Kbase is not assumed.
- **Comparability:** Source-narrated observations;NOT certified controlled/sameweights tests. Different hardware/runtime settings remain separate rows.

| Run / hardware profile | Reported metric / value | Run conditions / evidence status | Timestamp |
| --- | --- | --- | --- |
| V045-P009; V045-HP-TEST | whole-system wall power maximum · 五百三四十 W | NInfer+4090decode;colloquialrange; creatormeasured | [7:53](https://www.youtube.com/watch?v=MhZABCEOUWY&t=473s) |
| V045-P010; V045-HP-TEST | cachedprefill wall power · 两三百 W | NInfer;lowerthan decode; creatorapproximation | [7:59](https://www.youtube.com/watch?v=MhZABCEOUWY&t=479s) |
| V045-P011; V045-HP-TEST | daily consumptionbaseline · 六到七千瓦 ascaptioned unitconflict | llama.cpp;sourcecallspowerbutdailyenergy implied;notnormalized; creatorclaim;unitsrequirecheck | [8:22](https://www.youtube.com/watch?v=MhZABCEOUWY&t=502s) |
| V045-P012; V045-HP-TEST | daily consumptionnew · 四点五到五千瓦时 kWh asspoken | NInfer;similar~100Mtokens/dayclaimed; creatorclaim;day-to-daynotcontrolled | [8:28](https://www.youtube.com/watch?v=MhZABCEOUWY&t=508s) |

## Detailed hardware profiles

Minimum fields follow motherboard/CPU/RAMmodules+speed/GPUvariant+count+VRAM/PSU/storage. “Unknown”means not reported,not an invitation to fill from a different owner or manufacturer memory. Costs are quotes/paid/estimates only where identified;no fakeBOMtotal.

### V045-HP-TEST · 4090 (RTX4090 explicitly named at2:04)

**Role:** creator local test setup. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=MhZABCEOUWY&t=242s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=MhZABCEOUWY&t=242s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=MhZABCEOUWY&t=242s) |
| RAM | — | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=MhZABCEOUWY&t=242s) |
| GPU | 4090 (RTX4090 explicitly named at2:04) | qty 一张(single); PerGPUVRAM:24GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=MhZABCEOUWY&t=242s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=MhZABCEOUWY&t=242s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=MhZABCEOUWY&t=242s) |

**Other component disclosures:** model 千问3.8 27B;do not treat context fit as performance for every artifact

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** NInfer4090fork versus llama.cpp;OS not stated Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V045-P001 / V045-S01 | 千问3.8 27B unlesshistorical3.6noted; not stated; NInfer / llama.cpp | decode: 七八十 tokens/s | 200K;llama.cpp;approximateChinese; creatorbaseline; [0:30](https://www.youtube.com/watch?v=MhZABCEOUWY&t=30s) |
| V045-P002 / V045-S01 | 千问3.8 27B unlesshistorical3.6noted; not stated; NInfer / llama.cpp | average decode: 一百 tokens/s | 256K;NInfer;approximateChinese; creatorrun; [4:10](https://www.youtube.com/watch?v=MhZABCEOUWY&t=250s) |
| V045-P003 / V045-S02 | 千问3.8 27B unlesshistorical3.6noted; not stated; NInfer / llama.cpp | time to first token: ~五 seconds | llama.cpp;firstcoldagentrequest; creatorrun; [6:01](https://www.youtube.com/watch?v=MhZABCEOUWY&t=361s) |
| V045-P004 / V045-S02 | 千问3.8 27B unlesshistorical3.6noted; not stated; NInfer / llama.cpp | time to first token: 十二三 seconds | NInfer;coldagentrequest;not12.3s; creatorrun; [6:03](https://www.youtube.com/watch?v=MhZABCEOUWY&t=363s) |
| V045-P005 / V045-S03 | 千问3.8 27B unlesshistorical3.6noted; not stated; NInfer / llama.cpp | coldprefill speed deficit: 两三成 fraction as spoken | NInferrelativebaseline;rough20–30%,notexact; creatorcomparison; [6:19](https://www.youtube.com/watch?v=MhZABCEOUWY&t=379s) |
| V045-P006 / V045-S01 | 千问3.8 27B unlesshistorical3.6noted; not stated; NInfer / llama.cpp | small-task generation: ~130 tokens/s | NInfer; creatorrun; [6:34](https://www.youtube.com/watch?v=MhZABCEOUWY&t=394s) |
| V045-P007 / V045-S01 | 千问3.8 27B unlesshistorical3.6noted; not stated; NInfer / llama.cpp | long-context decode: 五六十;goodcase七十 tokens/s | llama.cpp+MTP; creatorcomparison; [6:55](https://www.youtube.com/watch?v=MhZABCEOUWY&t=415s) |
| V045-P008 / V045-S01 | 千问3.8 27B unlesshistorical3.6noted; not stated; NInfer / llama.cpp | overall generation ratio: 1.5 times | workloadnotidenticaltoallpriornumbers; creatorapproximation; [7:01](https://www.youtube.com/watch?v=MhZABCEOUWY&t=421s) |
| V045-P009 / V045-S04 | 千问3.8 27B unlesshistorical3.6noted; not stated; NInfer / llama.cpp | whole-system wall power maximum: 五百三四十 W | NInfer+4090decode;colloquialrange; creatormeasured; [7:53](https://www.youtube.com/watch?v=MhZABCEOUWY&t=473s) |
| V045-P010 / V045-S04 | 千问3.8 27B unlesshistorical3.6noted; not stated; NInfer / llama.cpp | cachedprefill wall power: 两三百 W | NInfer;lowerthan decode; creatorapproximation; [7:59](https://www.youtube.com/watch?v=MhZABCEOUWY&t=479s) |
| V045-P011 / V045-S04 | 千问3.8 27B unlesshistorical3.6noted; not stated; NInfer / llama.cpp | daily consumptionbaseline: 六到七千瓦 ascaptioned unitconflict | llama.cpp;sourcecallspowerbutdailyenergy implied;notnormalized; creatorclaim;unitsrequirecheck; [8:22](https://www.youtube.com/watch?v=MhZABCEOUWY&t=502s) |
| V045-P012 / V045-S04 | 千问3.8 27B unlesshistorical3.6noted; not stated; NInfer / llama.cpp | daily consumptionnew: 四点五到五千瓦时 kWh asspoken | NInfer;similar~100Mtokens/dayclaimed; creatorclaim;day-to-daynotcontrolled; [8:28](https://www.youtube.com/watch?v=MhZABCEOUWY&t=508s) |
| V045-P013 / V045-S01 | 千问3.8 27B unlesshistorical3.6noted; not stated; NInfer / llama.cpp | historical generation: 40–50 tokens/s | Qwen3.6+MTP;not3.8samemodel; creatorrecollection; [10:58](https://www.youtube.com/watch?v=MhZABCEOUWY&t=658s) |


## Scope

Caption-only evidence;no chart/video viewing or independent hardware validation. ASR and source contradictions are retained. Full original caption text is not included. Original450claim records and99hardwarefact records are preserved byte-for-byte in their originalCSVs;new profiles/series are a separately typed organization layer.

## llmfit-aligned machine-readable records

Upstreamcommit`26450cccaf3a3f14b1822875f2473847a744a718`. Thisvideo has1losslessresearchprofiles;0have a minimalcore passingthe actualupstreamHardwareProfileJSONschema. Otherprofilesremain explicitlypartial,not paddedwithdefaults. Modelcatalogmetadata is incomplete;runconditions/prefill/concurrency/BOM/provenance remainnamespacedextensions. See[contract](llmfit/schema.md),[fieldmapping](llmfit/mapping.md),[validation](llmfit/validation-report.json). NativecompatibilityisNOTa completebuild,independentmeasurement or testedimport.
