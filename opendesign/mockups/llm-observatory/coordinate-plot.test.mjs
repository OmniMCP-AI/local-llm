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
