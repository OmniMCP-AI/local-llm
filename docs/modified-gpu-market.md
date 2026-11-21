# Memory-modified GPUs

Reviewed November 22, 2026. This survey covers public seller catalogs, publicly indexed marketplace listings, repair-shop reports, and first-hand demonstrations. Coverage includes China-linked exporters, the United States, Canada, and Japan. Stock and checkout availability can vary by destination and date. Private marketplaces and unindexed listings leave gaps in coverage.

Track the original chip, original memory configuration, modified capacity, and what the source actually demonstrated. A seller’s listed capacity identifies the offered configuration. Usable capacity under load requires separate evidence for the exact board and driver. A modified board has its own catalog identity and retains a link to the original model where the stock identity is known. Usable VRAM, stable clocks, warranty, runtime support, power, and cooling can vary between boards with the same advertised capacity.

## Seller listings and retrofit services

| Modified card | Stock → modified | Market evidence |
| --- | --- | --- |
| GeForce RTX 2070 | 8 → 16 GB | Exporter product listing. [BIM Computing](https://www.bim-computing.com/products/modded-rtx-2070-16gb) |
| GeForce RTX 2080 Ti | 11 → 22 GB | Exporter product listing and China retrofit service. [BIM Computing](https://www.bim-computing.com/products/retrofitted-rtx-2080-ti-22gb) · [HCIT service](https://www.hcit.com.cn/services/gpu-mod-repair/) |
| GeForce RTX 3080 10 GB | 10 → 20 GB | Exporter product listing and China retrofit service. [BIM Computing](https://www.bim-computing.com/products/modded-rtx-3080-20gb) · [HCIT service](https://www.hcit.com.cn/services/gpu-mod-repair/) |
| GeForce RTX 4080 | 16 → 32 GB | Exporter product listing. [BIM Computing](https://www.bim-computing.com/products/retrofitted-rtx-4080-32gb) |
| GeForce RTX 4080 SUPER | 16 → 32 GB | Japanese repair provider reported completing three retrofits and beginning tests. [Provider’s post](https://x.com/xingyao74043/status/2088846397579948505) |
| GeForce RTX 4090 | 24 → 48 GB | Exporter product listing, US retrofit service, and a documented workshop build. [BIM Computing](https://www.bim-computing.com/products/retrofitted-rtx-4090-48gb) · [GPU Lab](https://gpulab.net/) · [Gamers Nexus and Brother Zhang](https://www.youtube.com/watch?v=TcRGBeOENLg) |
| GeForce RTX 4090 D | 24 → 48 GB | Indexed supplier listing for the D-specific custom board. The title identifies 48 GB. Shipping, stock, and usable capacity remain unverified. [Supplier listing on Alibaba](https://www.alibaba.com/pla/OEM-RTX-4090D-TURBO-48GB-GDDR6X_1601871852514.html) |
| CMP 170HX 8 GB | 8 GB exposed → 64 GB advertised | Exporter product listing. Board and HBM lot still matter for applying individual technical reports. [BIM Computing](https://www.bim-computing.com/products/retrofitted-cmp-170hx-64gb) |
| Radeon RX 580 2048SP | 8 → 16 GB | Kinology board listed by a Canadian retailer and examined by a first-hand reviewer. The 2048SP chip identity is specific to this configuration. [Merlin Computer Solutions](https://www.merlincomputersolutions.ca/product-page/new-kinology-rx-580-16gb-2048sp-graphics-card) · [Dawid Does Tech Stuff](https://www.youtube.com/watch?v=WDz1c59NDvU) |

## Demonstrations and lab reports

| Card | Stock → reported | Evidence and status |
| --- | --- | --- |
| GeForce RTX 3070 | 8 → 16 GB | First-hand modification demonstration. No separate seller inventory verified in this review. [Paulo Gomes](https://www.youtube.com/watch?v=W6uaUHBNFOU) |
| GeForce RTX 5080 | 16 → 32 GB | A repair technician reported a 32 GB conversion. The source page could not be fetched directly during the review, and no exact available seller listing was verified. [智强显卡工作室](https://www.bilibili.com/video/BV1QyBhBTEXF/) |
| CMP 170HX 8 GB | 8 GB exposed → up to 80 GB reported | Kate Land identified the card as a CMP 170HX and reported up to 80 GB on the specific tested hardware. Outcomes differed by specimen. No sale of a working 80 GB unit was verified in this review. [Researcher’s report](https://blog.kate.land/posts/using-voltage-glitching-to-unlock-the-a100/) |
| CMP 170HX 10 GB | 10 GB exposed → 40 GB reported stable | The research seed records a Samsung-memory specimen separately. A framebuffer size reported by a driver can exceed the amount that passes a full memory test on that board. [Creator review](https://www.youtube.com/watch?v=J58FXpo3L4U) · [Community test records](https://github.com/Consensus-Protocol/cmp170hx/blob/main/docs/index.md) |
| GeForce RTX 2080 SUPER | 8 → 16 GB | First-hand workshop demonstration. Seller availability remains unverified. [Paulo Gomes](https://www.youtube.com/watch?v=alam8TRoC4I) |
| Radeon RX 5600 XT | 6 → 16 GB | First-hand workshop build with a changed memory bus. Seller availability remains unverified. [Paulo Gomes](https://www.youtube.com/watch?v=vR9IwDug5T0) |

## Leads requiring confirmation

| Lead | Open question |
| --- | --- |
| GeForce RTX 3090 48 GB | A marketplace taxonomy lists the variant without offers, and an open acceptance test suite describes the expected configuration. Neither source documents a passing test for a specific retail board. [Marketplace record](https://3090-48gb-modified.gpu.ooo/) · [Acceptance test project](https://github.com/Danial-Dirar/3090-48gb-vram-mod-validator) |
| GeForce RTX 5090 64 GB and 96 GB | Treat as unverified leads until an identified board demonstrates usable capacity and a seller can substantiate the exact product. The public 96 GB listing claims and associated reports lack that evidence. [Report and source links](https://www.tweaktown.com/news/114444/rtx-5090-with-64gb-and-96gb-vram-confirmed-by-us-gpu-repair-tech/index.html) |
| RTX A2000 6 → 12 GB | NVIDIA released a factory 12 GB model. Any advertised conversion needs proof that the donor board was the factory 6 GB version. [NVIDIA datasheet](https://www.nvidia.com/content/dam/en-zz/Solutions/products/workstations/nvidia-rtx-a2000-12gb-datasheet.pdf) |
| GeForce RTX 3080 Ti 20 GB | An owner documents an unreleased engineering sample. This separate chip and board identity needs independent verification for any offer using the same name. [Owner teardown](https://www.reddit.com/r/nvidia/comments/1r00759/i_got_a_20gb_3080_ti_that_never_launched_teardown/) |
