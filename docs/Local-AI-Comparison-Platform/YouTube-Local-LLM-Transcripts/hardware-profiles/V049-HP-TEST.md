# Hardware profile

### V049-HP-TEST · Mac mini M4

**Role:** creator embedding experiment;not an LLM generation benchmark. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=VKEXWXMlVS0&t=21s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=VKEXWXMlVS0&t=21s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=VKEXWXMlVS0&t=21s) |
| RAM | system/unspecified RAM: 16GB;memory type not explicitly stated | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=VKEXWXMlVS0&t=21s) |
| GPU | — | PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=VKEXWXMlVS0&t=21s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=VKEXWXMlVS0&t=21s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=VKEXWXMlVS0&t=21s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** ANE/GPU placement experiment;Core ML discussed;OS not stated Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, gpu, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V049-P001 / V049-S01 | embeddingpipeline,notLLMdecode; not stated; Index/GPUbaseline | pipeline elapsed time: 130 seconds | differentroundfrom127sintro;do notaverage; narrated result;not independently verified; [3:17](https://www.youtube.com/watch?v=VKEXWXMlVS0&t=197s) |
| V049-P002 / V049-S02 | sameembeddingpipeline; not stated; visiononANE | time reduction: 20 seconds | baseline130s;do notsilentlymake20stotaltime; narrated result;not independently verified; [3:21](https://www.youtube.com/watch?v=VKEXWXMlVS0&t=201s) |
| V049-P003 / V049-S03 | sameembeddingpipeline; not stated; vision+some languageonANE | pipeline elapsed time: 70 seconds | notLLMtokenrate; narrated result;not independently verified; [3:23](https://www.youtube.com/watch?v=VKEXWXMlVS0&t=203s) |


Caption-derived research facts and original notes only;not a transcript.
