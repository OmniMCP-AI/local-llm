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
  assert.equal(manifest.coverage.completeBuilds, 0);
  assert.equal(manifest.coverage.reviewedMeasuredProfiles, 0);
  assert.equal(manifest.coverage.creatorReportedAssociations, 293);
  assert.equal(catalog.machines.length, 120);
  assert.equal(manifest.coverage.manufacturerMachines, 1);
  assert.equal(manifest.coverage.cards, 104);
  assert.ok(manifest.coverage.cardsWithVendorSpecs >= 39);

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
  assert.equal(find(catalog.cards, "amd-instinct-mi300").kind, "Unresolved family reference");
  assert.ok(find(catalog.cards, "amd-radeon-rx-7600"));
  for (const id of ["amd-radeon-instinct-mi50-16gb", "amd-radeon-instinct-mi50-32gb", "nvidia-tesla-v100-16gb", "nvidia-tesla-v100-32gb", "nvidia-tesla-v100-sxm2", "nvidia-geforce-rtx-2080-ti-colorful-modified"]) {
    assert.ok(find(catalog.cards, id), id);
  }
  assert.equal(find(catalog.machines, "V024-HP-C001").cardIds.length, 0);
  assert.deepEqual(find(catalog.machines, "V019-HP-TEST").cardIds.sort(), ["amd-radeon-rx-6600-xt", "t10-unresolved"].sort());
});
