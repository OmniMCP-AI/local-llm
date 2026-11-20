# Hardware profile

### V009-HP-TEST · Apple M6 Mac Mini (caption label; not independently verified)

**Role:** creator demonstration machine; RAM and GPU-core count not stated. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=8dhcnt-G19M&t=26s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 0/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=8dhcnt-G19M&t=26s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=8dhcnt-G19M&t=26s) |
| RAM | — | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=8dhcnt-G19M&t=26s) |
| GPU | — | PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=8dhcnt-G19M&t=26s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=8dhcnt-G19M&t=26s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=8dhcnt-G19M&t=26s) |

**Selection / tradeoffs:** Unknown / not reported Unknown / not reported

**Expansion / compatibility:** Unknown / not reported Unknown / not reported

**Deployment:** Splash1.6.1 per displayed video title; runtime version not separately certified Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, cpu, ram, gpu, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V009-P001 / V009-S01 | Qwen3.6 35BMoE; not stated; Splash1.6.1 per title | generation throughput: ~170 tokens/s | headline;contextnotfixed; narrated result;not independently verified; [0:32](https://www.youtube.com/watch?v=8dhcnt-G19M&t=32s) |
| V009-P002 / V009-S02 | Qwen3.8 27Bdense; not stated; Splash1.6.1 per title | generation throughput: 56–70 tokens/s | headline;thinking/contextvary; narrated result;not independently verified; [0:42](https://www.youtube.com/watch?v=8dhcnt-G19M&t=42s) |
| V009-P003 / V009-S03 | selectedMoE,exactartifactnotrestated; not stated; Splash1.6.1 per title | generation throughput: 152 tokens/s | firstquestion; narrated result;not independently verified; [4:38](https://www.youtube.com/watch?v=8dhcnt-G19M&t=278s) |
| V009-P004 / V009-S04 | sameMoE; not stated; Splash1.6.1 per title | generation throughput: 113 tokens/s | secondquestion,morethinking; narrated result;not independently verified; [4:47](https://www.youtube.com/watch?v=8dhcnt-G19M&t=287s) |
| V009-P005 / V009-S04 | sameMoE; not stated; Splash1.6.1 per title | generation throughput: 117 tokens/s | code-generationrequest; narrated result;not independently verified; [6:01](https://www.youtube.com/watch?v=8dhcnt-G19M&t=361s) |
| V009-P006 / V009-S05 | Qwen3.8 27B; not stated; Splash1.6.1 per title | generation throughput: 33 tokens/s | extra-highthinking; narrated result;not independently verified; [8:35](https://www.youtube.com/watch?v=8dhcnt-G19M&t=515s) |
| V009-P007 / V009-S05 | Qwen3.8 27B; not stated; Splash1.6.1 per title | generation throughput: 46 tokens/s | mediumthinking;shortgreeting; narrated result;not independently verified; [8:44](https://www.youtube.com/watch?v=8dhcnt-G19M&t=524s) |
| V009-P008 / V009-S05 | Qwen3.8 27B; not stated; Splash1.6.1 per title | generation throughput: 28–30 tokens/s | extra-high;contextnotfixed; narrated result;not independently verified; [10:01](https://www.youtube.com/watch?v=8dhcnt-G19M&t=601s) |
| V009-P009 / V009-S05 | Qwen3.8 27B; not stated; Splash1.6.1 per title | generation throughput: 32 tokens/s | reportedaverage; narrated result;not independently verified; [11:24](https://www.youtube.com/watch?v=8dhcnt-G19M&t=684s) |
| V009-P010 / V009-S01 | Qwen3.6 35BMoE; not stated; Splash1.6.1 per title | generation throughput: 93–95 tokens/s | 128Ksetting;codequestion; narrated result;not independently verified; [12:23](https://www.youtube.com/watch?v=8dhcnt-G19M&t=743s) |
| V009-P011 / V009-S04 | sameMoE; not stated; Splash1.6.1 per title | generation throughput: 103–107 tokens/s | repository/toolcalls; narrated result;not independently verified; [12:50](https://www.youtube.com/watch?v=8dhcnt-G19M&t=770s) |
| V009-P012 / V009-S06 | dense27B selection; not stated; Splash1.6.1 per title | generation throughput: 34 tokens/s | repositoryanalysis;predicted30notseparatemeasurement; narrated result;not independently verified; [14:10](https://www.youtube.com/watch?v=8dhcnt-G19M&t=850s) |


Caption-derived research facts and original notes only;not a transcript.

## llmfit field alignment

Researchpartialprojection;NOT a validcompleteHardwareProfile. Thisdoesnotchangebuildcompleteness. [Pinnedupstreamschema](https://github.com/AlexsJones/llmfit/blob/26450cccaf3a3f14b1822875f2473847a744a718/llmfit-core/data/hardware/schema.json).

FullBOM,role,ownership,prices,compatibility andrunconditions arepreservedoutsidecore in [research/hardware.json](../llmfit/research/hardware.json),record`V009-HP-TEST`. See[mapping](../llmfit/mapping.md);nativeprofiledoesnotcarry discreteVRAM ormotherboard.
