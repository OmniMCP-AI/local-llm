# Hardware profile

### V005-HP-TEST · Developer RTX4090 / i7-13700K /64GB host

**Role:** developer test setup as narrated. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=GW56S3LVb2g&t=98s) · [additional disclosure](https://www.youtube.com/watch?v=GW56S3LVb2g&t=98s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 3/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=GW56S3LVb2g&t=98s) |
| CPU | Intel Core i7-13700K | — | — | [source](https://www.youtube.com/watch?v=GW56S3LVb2g&t=98s) |
| RAM | system/unspecified RAM: 64GB | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=GW56S3LVb2g&t=98s) |
| GPU | RTX4090 | qty one; PerGPUVRAM:24GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=GW56S3LVb2g&t=98s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=GW56S3LVb2g&t=98s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=GW56S3LVb2g&t=98s) |

**Other component disclosures:** setup disclosure spans1:38–1:45

**Selection / tradeoffs:** The video evaluates a fork optimized for older NVIDIA cards,not only Blackwell. Unknown / not reported

**Expansion / compatibility:** Unknown / not reported CUDA13/Linux recommendation later in the video is general guidance,not proof of this host OS. Runtime/driver versions for the actual test remain unknown.

**Deployment:** Adamant/Basalt fork compared with Strata; OS not established for this record Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** 450watts; reported GPU setting; not measured whole-system power;NOT a PSU specification Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Unknown / not reported

**Unknowns:** motherboard, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V005-P001 / V005-S01 | Qwen3.8FlashNext family; not stated; Adamant / Strata | decode prose: 160 vs116 tokens/s | Adamant then Strata;4Kprompt;full262Kcontext enabled;Unsloth4bit; narrated result;not independently verified; [2:02](https://www.youtube.com/watch?v=GW56S3LVb2g&t=122s) |
| V005-P002 / V005-S02 | same family; not stated; Adamant / Strata | decode code: 165 vs133 tokens/s | Adamant then Strata; narrated result;not independently verified; [2:12](https://www.youtube.com/watch?v=GW56S3LVb2g&t=132s) |
| V005-P003 / V005-S03 | same family; not stated; Adamant / Strata | prefill: 2900 vs1700 tokens/s | 4Kprompt;Adamant then Strata; narrated result;not independently verified; [2:21](https://www.youtube.com/watch?v=GW56S3LVb2g&t=141s) |
| V005-P004 / V005-S03 | same family; not stated; Adamant / Strata | prefill: 6150 vs3560 tokens/s | 64Kprompt;Adamant then Strata; narrated result;not independently verified; [2:28](https://www.youtube.com/watch?v=GW56S3LVb2g&t=148s) |
| V005-P005 / V005-S04 | same family; not stated; Adamant / Strata | request-to-completion time: 6.8 to4.6 seconds | short prompt;Strata toAdamant;not TTFT; narrated result;not independently verified; [2:39](https://www.youtube.com/watch?v=GW56S3LVb2g&t=159s) |
| V005-P006 / V005-S04 | same family; not stated; Adamant / Strata | request-to-completion time: 22.5 to14 seconds | long prompt;Strata toAdamant; narrated result;not independently verified; [2:45](https://www.youtube.com/watch?v=GW56S3LVb2g&t=165s) |
| V005-P007 / V005-S02 | same family; not stated; Adamant / Strata | draft-assisted generation: 372 vs169 tokens/s | JSON versus prose;separate run; narrated result;not independently verified; [3:36](https://www.youtube.com/watch?v=GW56S3LVb2g&t=216s) |


Caption-derived research facts and original notes only;not a transcript.

## llmfit field alignment

ExactupstreamHardwareProfileJSONschema-compatibleminimalcore. Thisdoesnotchangebuildcompleteness. [Pinnedupstreamschema](https://github.com/AlexsJones/llmfit/blob/26450cccaf3a3f14b1822875f2473847a744a718/llmfit-core/data/hardware/schema.json).

Nativefile:[profile](../llmfit/native/hardware/v005-hp-test.json). FullBOM,role,ownership,prices,compatibility andrunconditions arepreservedoutsidecore in [research/hardware.json](../llmfit/research/hardware.json),record`V005-HP-TEST`. See[mapping](../llmfit/mapping.md);nativeprofiledoesnotcarry discreteVRAM ormotherboard.
