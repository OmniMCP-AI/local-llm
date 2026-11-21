import assert from "node:assert/strict";
import { test } from "node:test";
import { hardwareCard, renderCard } from "./catalog-card.mjs";

const card = (id, spec) => ({
  id, name: id, source: "https://example.test/" + id, kind: "Component reference", manufacturer: "Example",
  variant: "Board", aliases: [], variants: [], relatedProfiles: [],
  vendorSpec: spec && { source: "https://example.test/spec/" + id, designation: id, facts: spec },
});
const known = card("Known GPU", { "Memory configuration": "32 GB GDDR6", "Memory bandwidth": "576 GB/s" });
const powerOnly = card("GPU with missing bandwidth", { "Memory configuration": "24 GB GDDR6", "Rated graphics power (W)": "260" });
const peers = [known, powerOnly];
const render = (row, markdown) => renderCard(hardwareCard(row, "v1-test", "cards", {
  peers, reviewProfileHref: (_type, id) => "/" + encodeURIComponent(id),
}), { release: "v1-test", pathname: "card.html", markdown });

test("GPU pages retain one rated bandwidth cohort and show a measured speed coverage gap", () => {
  const selected = render(known, false);
  const unavailable = render(powerOnly, false);
  for (const html of [selected, unavailable]) {
    assert.match(html, /GPU position by rated specifications/);
    assert.match(html, /Rated memory bandwidth \(GB\/s\)/);
    assert.match(html, /Show point labels/);
    assert.match(html, /coordinate-popup/);
    assert.match(html, /Nominal GPU memory<\/dt><dd>32 GB/);
    assert.match(html, /Rated memory bandwidth<\/dt><dd>576 GB\/s/);
    assert.match(html, /Measured decode speed unavailable/);
    assert.match(html, /Original schematic/);
    assert.doesNotMatch(html, /GPU position by rated graphics power/);
  }
  assert.match(selected, /href="\/Known%20GPU" aria-current="page"/);
  assert.doesNotMatch(unavailable, /href="\/Known%20GPU" aria-current="page"/);
  assert.match(unavailable, /GPU with missing bandwidth has no unambiguous pair of rated specifications/);
  const markdown = render(known, true);
  assert.match(markdown, /Selected GPU: Known GPU · 32 GB · 576 GB\/s/);
  assert.match(markdown, /Measured decode speed unavailable/);
  assert.match(markdown, /Original schematic/);
});

test("NVIDIA product and architecture sources cover distinct RTX 3090 and RTX 4090 bandwidth values", async () => {
  const { fileURLToPath } = await import("node:url");
  const { readHardwareCatalog } = await import("./catalog-hardware-build.mjs");
  const here = fileURLToPath(new URL(".", import.meta.url));
  const { catalog } = await readHardwareCatalog(here);
  for (const [id, bandwidth, locator] of [
    ["nvidia-geforce-rtx-3090", "936", "GA102-GPU-Architecture-Whitepaper-V1.pdf"],
    ["nvidia-geforce-rtx-3090-ti", "1008", "nvidia-ada-gpu-architecture.pdf"],
    ["nvidia-geforce-rtx-4090", "1008", "rtx-5090/#specs"],
  ]) {
    const gpu = catalog.cards.find(card => card.id === id);
    const output = renderCard(hardwareCard(gpu, "v1-test", "cards", { peers: catalog.cards }), {
      release: "v1-test", pathname: "card.md", markdown: true,
    });
    assert.ok(output.includes(`· ${bandwidth} GB/s`), id);
    assert.ok(output.includes(locator), id);
    assert.ok(output.includes("Product images on NVIDIA"), id);
  }
  const { catalog: withoutWhitepaper } = await readHardwareCatalog(here, value => value?.includes("GA102-GPU-Architecture-Whitepaper-V1.pdf"));
  const rtx3090 = withoutWhitepaper.cards.find(card => card.id === "nvidia-geforce-rtx-3090");
  assert.equal(rtx3090.vendorSpec.facts["Memory bandwidth"], undefined);
  assert.equal(rtx3090.vendorSpec.facts["Memory configuration"], "24 GB GDDR6X");
  assert.equal(rtx3090.vendorSpec.gallery.label, "Product images on NVIDIA");
});
