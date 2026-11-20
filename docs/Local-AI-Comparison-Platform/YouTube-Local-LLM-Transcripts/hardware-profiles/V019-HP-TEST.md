# Hardware profile

### V019-HP-TEST · Creator X99-T8 /128GB DDR3 /singleT10 NAS-analysis server

**Role:** creator built server. **Ownership/evidence:** Creator/third-party caption claim;no independent build verification. [source](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=14s) · [additional disclosure](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=14s)

**Use case:** Private local NAS documents:creator prefers not to send that material to online APIs ([4:21](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=261s)).

**Budget / price basis:** Creator says total<3000;not an independently totaled complete BOM · T10 reportedly bought for a little over1000;RAM~1000;CPU+motherboard bundle<500. No exact itemized total. · Spoken amounts omit currency;video title uses¥. Purchase date not reported.. No complete BOM total has been calculated.

**Evidence completeness:** 3/6 core categories have some reported information;this is NOT a complete/reproducible build. RAM modulecount/speed and GPUvariant/count/capacity may still be unknown.

A dash in the BOM means unreported,not zero or includedfree.

| Component | Part / model | Quantity / specification | Cost / procurement | Evidence |
| --- | --- | --- | --- | --- |
| RAM | DDR3;manufacturer/partnumber not reported | qty 4; 32GB each;128GBinstalled;speed/ECCnotstated | subtotal ~1000 for4sticks;currency notspoken; Installed;creator cost claim; Reported bundlecost,not a per-stickprice | [source](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=14s) |
| GPU | T10 | qty 1; Inferencecard;no videooutputs | subtotal A little over1000;currency notspoken; Creator says bought; Reported paid amount,not receiptverified | [source](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=119s) |
| Boot/displayGPU | Radeon6600XT | qty 1; Temporary display/bootrole;not inferenceVRAM | Creator-owned temporarypart | [source](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=54s) |
| Motherboard | Huananzhi X99-T8 | qty 1; DDR3;4additionalRAMslots described | Installed | [source](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=23s) |
| CPU+board bundle | CPU SKU unknown +X99-T8 | qty 1bundle | subtotal <500;not split betweenCPU/board; Source bundlequote;DO NOTdouble count with motherboardrow | [source](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=138s) |
| CPU | — | — | — | [source](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=14s) |
| PSU | — | — | — | [source](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=14s) |
| Storage | — | — | — | [source](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=14s) |
| Cooling | A blower fan is audible;exact fan/cooling component and model not specified | — | — | [source](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=14s) |

**Other component disclosures:** board at0:26;T10 at0:41;6600XT at0:54;do not combine boot card VRAM with inference VRAM

**Selection / tradeoffs:** Cheap DDR3 capacity and an old inference card;creator accepts slower background processing for private workloads. T10 has no video outputs;this X99 board needs a separate boot/display card. Roughly200W reported operation is not the PSU rating.

**Expansion / compatibility:** Creator says4 more DDR3sticks can fit;second T10 is hypothetical,not tested. No BIOS,PSU orPCIe slot/lane map provided. Windows is mentioned as a usable general-purpose test,not confirmed as current inference OS.

**Deployment:** WebUI integration;Qwen2.5-7B-Instruct Q3_K_S;128Kcontext as narrated. Exact engine/OS/version not established. Driver/firmware/BIOS versions:unknown unless explicitly specified above.

**Thermal / power:** About200W reported duringhostoperation;measurementboundarynotfullyspecified;NOT a PSU rating (5:23) Do not equate reported wall draw,TDP or power limit with an installed PSU model.

**Revisions / alternatives:** Temporary6600XT supports boot/display;do not count it as inferenceVRAM. A V100 is suggested as an alternative,not installed.

**Unknowns:** cpu, psu, storage; any unstatedRAM modulecount/speed,GPUvariant/count/capacity,OS/driver/runparameter remains unknown. Cooling/chassis/procurement can also be unreported.

**Linked run records:** configuration-family links only where indicated;not proof of one controlled physical host.

| Run / test series | Model / precision / runtime | Metric / reported result | Conditions / provenance |
| --- | --- | --- | --- |
| V019-P001 / V019-S01 | Qwen2.5-7B-Instruct as captioned; Q3_K_S; WebUI;engine notgiven | generation: ~40;fluctuates30–60 tokens/s | 128Ksetting;Q3_K_S;titlementionsdifferentmodelfamily; narrated result;not independently verified; [1:40](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=100s) |
| V019-P002 / V019-S02 | notrestated; not stated; notstated | power: about200 W | systemoperation;measurementboundarynotexplicit; narrated result;not independently verified; [5:23](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=323s) |


Caption-derived research facts and original notes only;not a transcript.
