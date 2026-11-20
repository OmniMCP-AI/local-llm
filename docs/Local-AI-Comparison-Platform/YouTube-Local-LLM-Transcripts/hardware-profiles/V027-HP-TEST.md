# Hardware profile

### V027-HP-TEST · Single3060 12GB /E5-2696v4 /64GB Strata host

**Role:** creator single-GPU demonstration setup. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=WOlXMUKJeuI&t=4s) · [additional disclosure](https://www.youtube.com/watch?v=WOlXMUKJeuI&t=74s)

**Use case:** Local LLM inference;see associated run records. This is not a purchase recommendation.

**Budget / price basis:** Unknown / not reported · Unknown / not reported · Unknown / not reported. No complete BOM total has been calculated.

**Evidence completeness:** 3/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| Motherboard | — | — | — | [source](https://www.youtube.com/watch?v=WOlXMUKJeuI&t=4s) |
| CPU | E5 2696 V4 explicitly identified at0:48;2695 discussed only as alternative | — | — | [source](https://www.youtube.com/watch?v=WOlXMUKJeuI&t=4s) |
| RAM | 64GB system RAM | Modules:Not reported in available captions;speed:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=WOlXMUKJeuI&t=4s) |
| GPU | 3060 | qty 1; PerGPUVRAM:12GB;aggregateVRAM:Not reported in available captions | — | [source](https://www.youtube.com/watch?v=WOlXMUKJeuI&t=4s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=WOlXMUKJeuI&t=4s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=WOlXMUKJeuI&t=4s) |

**Selection / tradeoffs:** Tests whether one3060 can run the workflow instead of two. Unknown / not reported

**Expansion / compatibility:** Unknown / not reported The creator highlights sustained all-core/BIOS capability as relevant. No BIOS version or actual turbo setting is supplied.

**Deployment:** Strata;Vision stack enabled;reasoningX-high;exact engine/model build not established Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** About350W peak while running as narrated;boundary not fully specified;NOT a PSU rating Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** E5-2695v4 is an alternative discussed,not the installed CPU. Do not copy256GBRAM orDell model from another video.

**Unknowns:** motherboard, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V027-P001 / V027-S01 | selectedQwen27B discussed; not stated; Strata | decode: about33 tokens/s | Visionenabled; narrated result;not independently verified; [1:03](https://www.youtube.com/watch?v=WOlXMUKJeuI&t=63s) |
| V027-P002 / V027-S02 | same context; not stated; Strata | prefill ceiling expectation: about850 unitnotrepeated | notmeasuredprefill; explicit creator expectation; [1:08](https://www.youtube.com/watch?v=WOlXMUKJeuI&t=68s) |
| V027-P003 / V027-S03 | same task; not stated; Strata | thinkingtime: 617 seconds | page/repositoryanalysis; narrated result;not independently verified; [2:02](https://www.youtube.com/watch?v=WOlXMUKJeuI&t=122s) |
| V027-P004 / V027-S04 | same task; not stated; Strata | displayedaverage throughput: 49.2 unitnotrepeated | do notclassifyasprefill;32Koutputdiscussed; narrated result;not independently verified; [2:13](https://www.youtube.com/watch?v=WOlXMUKJeuI&t=133s) |


Caption-derived research facts and original notes only;not a transcript.
