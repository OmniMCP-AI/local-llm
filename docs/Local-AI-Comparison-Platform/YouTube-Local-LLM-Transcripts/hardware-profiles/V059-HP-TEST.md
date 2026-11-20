# Hardware profile

### V059-HP-TEST · FourM3Ultra MacStudio cluster /1.5TB aggregate unifiedmemory

**Role:** creator cluster experiment;different network modes must stay distinct. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=44s) · [additional disclosure](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=192s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 1/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=44s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=44s) |
| RAM | unified/shared RAM: 1.5terabytes aggregate explicitly stated;half nodes512GB,other half256gigs as narrated at3:16–3:22 | qty 2nodes×512GB;2nodes×256GB;internal module layout not reported; Modules:2nodes×512GB;2nodes×256GB;internal module layout not reported;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=44s) |
| GPU | — | PerGPUVRAM:Not reported in available captions;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=44s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=44s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=44s) |
| Interconnect | Thunderbolt5/RDMA experiments versus Ethernet/pipeline modes | — | — | [source](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=44s) |

**Selection / tradeoffs:** Pool memory for large local dense/MoE models and test communication scaling. Pipeline and RDMA results differ;dense andMoE scaling/power differ. Model precision changes are not speedups at equal quality.

**Expansion / compatibility:** Unknown / not reported RDMA requires the discussed OS/beta path;an unsuccessful model/RDMA attempt is not a successful benchmark. No reproducible driver/firmware matrix supplied.

**Deployment:** macOS26.2beta;Exo/MLX paths;exact commits not stated Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** Unknown / not reported Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** One/two/four-node modes use different subsets;which512GB/256GBnodes are in each two-node subset is not stated.

**Unknowns:** motherboard, cpu, gpu, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V059-P006 / V059-S02 | sameLlama; not stated; Exo/MLX;modeinconditions | decode: 5 tokens/s | pipeline; narrated result;not independently verified; [6:51](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=411s) |
| V059-P010 / V059-S07 | Llama3.3 70B FP16; not stated; Exo/MLX;modeinconditions | decode: 15.5 tokens/s | RDMA;treatnodecountcontextasqualification; narrated result;not independently verified; [13:16](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=796s) |
| V059-P011 / V059-S03 | sameLlama; not stated; Exo/MLX;modeinconditions | time to first token: justover1 seconds | RDMA; narrated result;not independently verified; [13:13](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=793s) |
| V059-P013 / V059-S09 | sameKimi; not stated; Exo/MLX;modeinconditions | decode: nearly35 tokens/s | distributedconfiguration; narrated result;not independently verified; [13:47](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=827s) |
| V059-P017 / V059-S12 | sameDeepSeek; not stated; Exo/MLX;modeinconditions | decode: 24 tokens/s | scalestopoorlyrelative dense; narrated result;not independently verified; [15:38](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=938s) |
| V059-P018 / V059-S13 | sameDeepSeek; not stated; Exo/MLX;modeinconditions | time to first token: under2 seconds | comparedwith3.5; narrated result;not independently verified; [15:43](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=943s) |
| V059-P019 / V059-S14 | MoE atthispoint;exactmodelnotretied; not stated; Exo/MLX;modeinconditions | power pernode: 115–125 W | longstory; narrated result;not independently verified; [17:29](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=1049s) |
| V059-P020 / V059-S15 | sameMoE; not stated; Exo/MLX;modeinconditions | aggregate power: 480 W | creatorapproximatesnodesum; narrated result;not independently verified; [17:33](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=1053s) |
| V059-P021 / V059-S16 | Llama3.3 70B FP16; not stated; Exo/MLX;modeinconditions | aggregate power: 600 W | denseworkload; narrated result;not independently verified; [18:10](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=1090s) |
| V059-P023 / V059-S18 | sameLlama FP8; not stated; Exo/MLX;modeinconditions | decode: 26 tokens/s | precisionchangedfromFP16; narrated result;not independently verified; [18:32](https://www.youtube.com/watch?v=4l4UWZGxvoc&t=1112s) |


Caption-derived research facts and original notes only;not a transcript.

## llmfit field alignment

Researchpartialprojection;NOT a validcompleteHardwareProfile. Thisdoesnotchangebuildcompleteness. [Pinnedupstreamschema](https://github.com/AlexsJones/llmfit/blob/26450cccaf3a3f14b1822875f2473847a744a718/llmfit-core/data/hardware/schema.json).

FullBOM,role,ownership,prices,compatibility andrunconditions arepreservedoutsidecore in [research/hardware.json](../llmfit/research/hardware.json),record`V059-HP-TEST`. See[mapping](../llmfit/mapping.md);nativeprofiledoesnotcarry discreteVRAM ormotherboard.
