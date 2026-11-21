import assert from "node:assert/strict";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { readHardwareCatalog } from "./catalog-hardware-build.mjs";
import { battleMarkdown, battlePair, battleRecords, battleSuggestions } from "./battle.mjs";
import { cardRatings } from "./catalog-position.mjs";

const here = fileURLToPath(new URL(".", import.meta.url));
const seller = "https://www.bim-computing.com/products/";
const rtx4090 = "nvidia-geforce-rtx-4090";
const mod4090 = rtx4090 + "-modified-48gb";

test("the hardware catalog publishes aftermarket VRAM as a distinct sourced identity", async () => {
  const { catalog, manifest } = await readHardwareCatalog(here);
  const cards = new Map(catalog.cards.map(card => [card.id, card]));
  const stock = cards.get(rtx4090);
  const modified = cards.get(mod4090);
  assert.ok(modified);
  assert.equal(stock.vendorSpec.facts["Memory configuration"], "24 GB GDDR6X");
  assert.ok(stock.variants.some(({ id }) => id === mod4090));
  assert.equal(modified.parent, rtx4090);
  assert.equal(modified.vendorSpec, null);
  assert.equal(modified.modification.stockGb, 24);
  assert.equal(modified.modification.capacityGb, 48);
  assert.equal(modified.modification.usableGb, undefined);
  assert.equal(modified.modification.evidence[0].kind, "Seller listing");
  assert.equal(modified.source, seller + "retrofitted-rtx-4090-48gb");
  assert.deepEqual(cardRatings(modified), { capacity: null, bandwidth: null, power: null });
  assert.equal(manifest.coverage.memoryModifiedCards, catalog.cards.filter(card => card.modification).length);
  assert.equal(manifest.coverage.memoryModifiedWithSellerEvidence, 8);
});

test("the CMP variants keep separate capacity evidence and scope", async () => {
  const { catalog } = await readHardwareCatalog(here);
  const cards = new Map(catalog.cards.map(card => [card.id, card]));
  for (const [variant, stockGb, capacityGb, evidence] of [
    ["hynix", 8, 64, "Creator report"],
    ["samsung", 10, 40, "Creator report"],
    ["modified-80gb", 8, 80, "Lab demonstration"],
  ]) {
    const card = cards.get("nvidia-cmp-170hx-" + variant);
    assert.equal(card.parent, "nvidia-cmp-170hx");
    assert.equal(card.modification.stockGb, stockGb);
    assert.equal(card.modification.capacityGb, capacityGb);
    assert.equal(card.modification.evidence[0].kind, evidence);
    assert.equal(card.modification.usableGb, undefined);
  }
  const lab = cards.get("nvidia-cmp-170hx-modified-80gb").modification;
  assert.equal(lab.installedGb, 80);
  assert.equal(lab.validatedGb, 80);
  assert.ok(!cards.has("nvidia-cmp-130-modified-80gb"));
});

test("withdrawing the listing removes the source and its dependent aftermarket identity", async () => {
  const source = seller + "retrofitted-rtx-4090-48gb";
  const { catalog } = await readHardwareCatalog(here, value => value === source);
  assert.ok(!catalog.cards.some(({ id }) => id === mod4090));
  assert.ok(!catalog.cards.find(({ id }) => id === rtx4090).variants.some(({ id }) => id === mod4090));
  assert.ok(!JSON.stringify(catalog).includes(source));
});

test("Battles compares aftermarket VRAM with stock and workstation alternatives without rated deltas", async () => {
  const { catalog } = await readHardwareCatalog(here);
  const records = battleRecords(catalog);
  const suggestions = battleSuggestions(records, "cards");
  for (const left of [rtx4090, "nvidia-rtx-a6000"]) {
    const pair = battlePair(records, "cards", left, mod4090);
    assert.ok(pair);
    assert.ok(suggestions.some(item => new Set([item.left.id, item.right.id]).has(left) &&
      new Set([item.left.id, item.right.id]).has(mod4090)));
    const markdown = battleMarkdown(pair, { release: "v1-test", prefix: "/", origin: "https://example.test" });
    assert.match(markdown, /Nominal VRAM \| (?:24 GB GDDR6X|48 GB GDDR6 with ECC) \| Unavailable/);
    assert.match(markdown, /Reported modified capacity \| Unavailable \| 48 GB/);
    assert.match(markdown, /Runtime-usable VRAM \| Unavailable \| Unavailable/);
    assert.ok(markdown.includes(seller + "retrofitted-rtx-4090-48gb"));
    assert.doesNotMatch(markdown, /more nominal VRAM/);
    assert.match(markdown, /Matched performance, price and measured energy data are unavailable/);
  }
});
