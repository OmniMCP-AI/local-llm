import assert from "node:assert/strict";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { hardwareCard, renderCard } from "./catalog-card.mjs";
import { readHardwareCatalog } from "./catalog-hardware-build.mjs";

const here = fileURLToPath(new URL(".", import.meta.url));
const originalId = "nvidia-geforce-rtx-5090-d-32gb";
const originalSource = "https://www.nvidia.cn/geforce/news/rtx-50-series-graphics-cards-gpu-laptop-announcements/";

function profilePair(card) {
  const release = "v1-test";
  const profile = hardwareCard(card, release, "cards");
  return ["html", "md"].map(format => renderCard(profile, {
    release, pathname: `catalog/${release}/cards/${card.id}.${format}`, markdown: format === "md",
  }));
}

test("the original RTX 5090 D profile cites its dated China launch with exact memory and compute specifications", async () => {
  const { catalog } = await readHardwareCatalog(here);
  const original = catalog.cards.find(({ id }) => id === originalId);
  for (const body of profilePair(original)) {
    for (const value of [originalSource, "China launch date", "2025-01-30", "32 GB GDDR7", "1792 GB/s", "21760"]) {
      assert.ok(body.includes(value), value);
    }
    assert.match(body, /Rated graphics power \(W\).*Unknown/);
    assert.match(body, /Memory bus.*Unknown/);
    assert.doesNotMatch(body, /1344 GB\/s|24 GB GDDR7|384-bit/);
  }
});

const mi200 = "https://www.amd.com/en/products/accelerators/instinct/mi200.html#meet-the-series";
const v100 = "https://images.nvidia.com/content/technologies/volta/pdf/tesla-volta-v100-datasheet-letter-fnl-web.pdf#page=1";
const gallerySources = [
  ["amd-instinct-mi100", "https://www.amd.com/content/dam/amd/en/documents/instinct-business-docs/product-briefs/instinct-mi100-brochure.pdf#page=1", "MI100 PCIe"],
  ["amd-instinct-mi210", "https://www.amd.com/content/dam/amd/en/documents/instinct-business-docs/product-briefs/instinct-mi210-brochure.pdf#page=1", "MI210 PCIe"],
  ["amd-instinct-mi250", mi200, "MI250 OAM"],
  ["amd-instinct-mi250x", mi200, "MI250X OAM"],
  ["nvidia-a10", "https://www.nvidia.com/content/dam/en-zz/Solutions/Data-Center/a10/pdf/A10-Product-Brief.pdf#page=6", "A10 PCIe · Figure 1 line drawing"],
  ["nvidia-l4", "https://www.nvidia.com/content/dam/en-zz/Solutions/Data-Center/l4/PB-11316-001_v01.pdf#page=5", "L4 PCIe · Figure 1"],
  ["nvidia-l40", "https://images.nvidia.com/content/Solutions/data-center/vgpu-L40-datasheet.pdf#page=1", "L40 PCIe"],
  ["nvidia-l40s", "https://www.nvidia.com/en-us/data-center/products/ovx/", "L40S PCIe · 3D rendering"],
  ["nvidia-tesla-p100-sxm2-16gb", "https://images.nvidia.com/content/tesla/pdf/nvidia-tesla-p100-datasheet.pdf#page=1", "P100 SXM2 16 GB"],
  ["nvidia-tesla-t4", "https://www.nvidia.com/content/dam/en-zz/Solutions/Data-Center/tesla-t4/t4-tensor-core-datasheet-951643.pdf#page=1", "T4 PCIe"],
  ["nvidia-tesla-v100-pcie-16gb", v100, "V100 PCIe form factor · pictured capacity unspecified"],
  ["nvidia-tesla-v100-pcie-32gb", v100, "V100 PCIe form factor · pictured capacity unspecified"],
  ["nvidia-tesla-v100-sxm2-32gb", v100, "V100 SXM2 form factor · pictured capacity unspecified"],
];

test("accelerator profiles link to manufacturer visuals with the pictured hardware labeled", async () => {
  const { catalog } = await readHardwareCatalog(here);
  const cards = new Map(catalog.cards.map(card => [card.id, card]));
  for (const [id, source, pictured] of gallerySources) {
    for (const body of profilePair(cards.get(id))) {
      assert.ok(body.includes(source), id + " image source");
      assert.ok(body.includes(pictured), id + " pictured hardware");
      assert.doesNotMatch(body, /<img\b/);
    }
  }
});

test("withdrawing the MI200 image source preserves covered technical specifications", async () => {
  const { catalog } = await readHardwareCatalog(here, source => source === mi200);
  const cards = new Map(catalog.cards.map(card => [card.id, card]));
  for (const [id, computeUnits] of [["amd-instinct-mi250", "208"], ["amd-instinct-mi250x", "220"]]) {
    for (const body of profilePair(cards.get(id))) {
      assert.match(body, /Compute units/);
      assert.ok(body.includes(computeUnits));
      assert.doesNotMatch(body, /Product image source/);
      assert.ok(!body.includes(mi200));
    }
  }
  for (const body of profilePair(cards.get("amd-instinct-mi210"))) {
    assert.match(body, /MI210 PCIe/);
  }
});
