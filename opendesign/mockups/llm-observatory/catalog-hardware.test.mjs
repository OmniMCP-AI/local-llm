import assert from "node:assert/strict";
import { dirname } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { readHardwareCatalog } from "./catalog-hardware-build.mjs";

const here = dirname(fileURLToPath(import.meta.url));

test("the hardware snapshot accounts for all sources and keeps memory limits separate", async () => {
  const { manifest, catalog } = await readHardwareCatalog(here);
  assert.equal(manifest.asOf, "2026-11-21");
  assert.equal(manifest.coverage.llmfitDiscreteMatchers, 72);
  assert.equal(manifest.coverage.researchProfiles, 116);
  assert.equal(manifest.coverage.researchComponentReferences, 46);
  assert.equal(manifest.coverage.partialMachines, 70);
  assert.equal(manifest.coverage.upstreamPresets, 3);
  assert.equal(manifest.coverage.completeBuilds, 4);
  assert.equal(manifest.coverage.reviewedMeasuredProfiles, 0);
  assert.equal(manifest.coverage.creatorReportedAssociations, 293);
  assert.equal(catalog.machines.length, 124);
  assert.equal(manifest.coverage.manufacturerMachines, 5);
  assert.equal(manifest.coverage.cards, 116);
  assert.equal(manifest.coverage.cardsWithVendorSpecs, 109);
  assert.equal(manifest.coverage.cardsWithSpecificVendorSpecs, 87);
  assert.equal(manifest.coverage.cardsWithProductImageLinks, 49);
  assert.equal(manifest.coverage.boardPartnerCards, 8);

  const find = (rows, id) => rows.find((row) => row.id === id);
  assert.equal(find(catalog.machines, "V001-HP-G001").kind, "Component reference");
  assert.equal(find(catalog.machines, "V005-HP-G002").kind, "Partial configuration");
  const capped = find(catalog.machines, "V018-HP-C002");
  assert.deepEqual(capped.memory, {
    system: null, perDevice: null, aggregate: null,
    allocation: "20 GB system RAM limit; 16 GB VRAM limit (creator reported)",
  });
  const reported = find(catalog.machines, "V022-HP-C002");
  assert.equal(reported.memory.system, null);
  assert.match(reported.memory.allocation, /46 GB.*ambiguous/i);
  assert.equal(find(catalog.machines, "llmfit-apple-m3-max-128gb").memory.system, "128 GB unified memory");

  assert.equal(find(catalog.cards, "nvidia-a100").variant, "PCIe 40 GB calibration");
  assert.equal(find(catalog.cards, "nvidia-a100-sxm").variant, "SXM calibration");
  const mi300 = find(catalog.cards, "amd-instinct-mi300");
  assert.equal(mi300.kind, "Unresolved family reference");
  assert.equal(mi300.vendorSpec.facts.Architecture, "CDNA 3");
  assert.equal(mi300.vendorSpec.facts["Memory configuration"], undefined);
  assert.equal(mi300.memory, null);
  assert.ok(find(catalog.cards, "amd-radeon-rx-7600"));
  for (const id of ["amd-radeon-instinct-mi50-16gb", "amd-radeon-instinct-mi50-32gb", "nvidia-tesla-v100-16gb", "nvidia-tesla-v100-32gb", "nvidia-tesla-v100-sxm2", "nvidia-geforce-rtx-2080-ti-colorful-modified"]) {
    assert.ok(find(catalog.cards, id), id);
  }
  assert.equal(find(catalog.machines, "V024-HP-C001").cardIds.length, 0);
  assert.deepEqual(find(catalog.machines, "V019-HP-TEST").cardIds.sort(), ["amd-radeon-rx-6600-xt", "t10-unresolved"].sort());
});

test("exact factory configurations carry a sourced system bill of materials", async () => {
  const { catalog } = await readHardwareCatalog(here);
  const builds = catalog.machines.filter(({ kind, cardIds }) => kind === "Complete factory configuration" && !cardIds.length);
  assert.deepEqual(builds.map(({ configuration, memory, documentedPower }) =>
    [configuration, memory.system, documentedPower.label, documentedPower.value]), [
    ["MCYT4LL/A", "24 GB unified memory", "Maximum continuous system power", "155 W"],
    ["MHQM4LL/A", "24 GB unified memory", "Maximum continuous system power", "155 W"],
    ["128 GB unified memory / 4 TB SSD", "128 GB LPDDR5X unified system memory", "External power supply rating", "240 W"],
  ]);
  for (const build of builds) {
    assert.deepEqual(build.cardIds, []);
    assert.equal(build.memory.perDevice, null);
    assert.equal(build.memory.aggregate, null);
    assert.equal(build.memory.allocation, null);
    assert.deepEqual(build.bom.map(({ category }) => category), [
      "CPU", "GPU", "Memory", "Storage", "Platform", "Power supply", "Cooling",
    ]);
    assert.ok(build.locator && build.documentedPower.locator);
    assert.ok(build.bom.every(({ part, quantity, source, locator }) =>
      part && quantity && new URL(source).protocol === "https:" && locator));
  }
  const family = catalog.machines.find(({ id }) => id === "nvidia-dgx-spark");
  assert.equal(family.kind, "Manufacturer system reference");
  assert.match(family.memory.system, /64 GB or 128 GB/);
  assert.equal(family.bom, undefined);
});

test("withdrawing a factory BOM source removes dependent builds and updates coverage", async () => {
  const withdrawn = "https://docs.nvidia.com/dgx/dgx-spark/hardware.html";
  const { catalog, manifest } = await readHardwareCatalog(here, value => value === withdrawn);
  assert.equal(manifest.coverage.completeBuilds, 3);
  assert.ok(catalog.machines.some(({ id }) => id === "nvidia-dgx-spark"));
  assert.ok(!catalog.machines.some(({ id }) => id === "nvidia-dgx-spark-128gb-4tb"));
  assert.ok(!JSON.stringify(catalog).includes(withdrawn));
});

test("an image source withdrawal preserves its separately sourced board specification", async () => {
  const { catalog } = await readHardwareCatalog(here, value => value?.includes("pg.asrock.com"));
  const board = catalog.cards.find(({ id }) => id === "asrock-a770-pg-16go");
  assert.equal(board.vendorSpec.designation, "A770 PG 16GO");
  assert.equal(board.vendorSpec.gallery, undefined);
  assert.ok(catalog.cards.find(({ id }) => id === "intel-arc-a770-16gb").variants.some(({ id }) => id === board.id));
});

test("a source withdrawal removes boards whose parent identity disappears", async () => {
  const { catalog } = await readHardwareCatalog(here, value => value?.endsWith("/hardware-profiles/V001-HP-G013.md"));
  assert.ok(catalog.cards.some(({ id }) => id === "amd-radeon-rx-9070-xt"));
  assert.ok(!catalog.cards.some(({ id }) => id === "amd-radeon-rx-9060-xt-16gb"));
  assert.ok(!catalog.cards.some(({ id }) => id === "asus-dual-rx9060xt-16g"));
});

test("a manufacturer source withdrawal removes independently sourced boards under that release", async () => {
  const withdrawn = "https://www.nvidia.cn/geforce/news/rtx-50-series-graphics-cards-gpu-laptop-announcements/";
  const { catalog } = await readHardwareCatalog(here, value => value === withdrawn);
  const ids = catalog.cards.map(({ id }) => id);
  assert.ok(ids.includes("nvidia-geforce-rtx-5090-d"));
  assert.ok(ids.includes("nvidia-geforce-rtx-5090-d-v2"));
  assert.ok(!ids.includes("nvidia-geforce-rtx-5090-d-32gb"));
  assert.ok(!ids.includes("asus-rog-astral-rtx5090d-o32g-gaming"));
});

test("withdrawing the Colorful launch announcement removes just its sourced RTX 5060 Ti board", async () => {
  const source = "https://www.colorful.cn/home/new?id=09e8d6a3-f28d-419e-bc68-2b25cbe99968";
  const { catalog, manifest } = await readHardwareCatalog(here, value => value === source);
  const family = catalog.cards.find(({ id }) => id === "nvidia-geforce-rtx-5060-ti");
  assert.deepEqual(family.variants.map(({ id }) => id).sort(), [
    "asus-t1-rtx5060ti-o8g-gaming", "nvidia-geforce-rtx-5060-ti-16gb", "pny-vcg5060t8dfxpb1-o",
  ]);
  assert.equal(manifest.coverage.boardPartnerCards, 7);
  assert.ok(!JSON.stringify(catalog).includes(source));
});
