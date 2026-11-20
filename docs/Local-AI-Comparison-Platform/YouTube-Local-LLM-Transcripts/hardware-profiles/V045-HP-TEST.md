# Hardware profile

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


Caption-derived research facts and original notes only;not a transcript.
