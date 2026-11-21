import assert from "node:assert/strict";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { battleHref, battleMarkdown, battlePair, battleRecords } from "./battle.mjs";
import { readHardwareCatalog } from "./catalog-hardware-build.mjs";

const { catalog } = await readHardwareCatalog(fileURLToPath(new URL(".", import.meta.url)));
const records = battleRecords(catalog);
const pin = "v1-0a1b2c3d4e5f6789";
const urls = { release: pin, origin: "https://fastest.example", prefix: "/" };

test("a shareable GPU matchup names the exact rated deltas and keeps missing ratings visible", () => {
  const left = "nvidia-geforce-rtx-5090";
  const right = "nvidia-geforce-rtx-4090";
  const pair = battlePair(records, "cards", left, right);
  assert.equal(battleHref("cards", pair), "#battle/cards?left=" + left + "&right=" + right);
  assert.equal(battleHref("cards", pair, pin), battleHref("cards", pair) + "&release=" + pin);
  const markdown = battleMarkdown(pair, urls);
  assert.match(markdown, /RTX 5090 vs\. NVIDIA GeForce RTX 4090/);
  assert.match(markdown, /8 GB more nominal VRAM/);
  assert.match(markdown, /125 W higher rated graphics power/);
  assert.match(markdown, /Rated memory bandwidth \| 1792 GB\/sec \| Unavailable/);
  assert.match(markdown, new RegExp("/catalog/" + pin + "/cards/" + right + "\\.html"));
  assert.match(markdown, /Matched performance, price and measured energy data are unavailable/);
  assert.equal(battlePair(records, "cards", left, left), null);
  assert.equal(battlePair(records, "machines", left, right), null);
});

test("factory machine comparison separates shared memory from rated power scopes", () => {
  const pair = battlePair(records, "machines", "apple-mac-mini-m4-24gb-512gb", "nvidia-dgx-spark-128gb-4tb");
  const markdown = battleMarkdown(pair, urls);
  assert.match(markdown, /104 GB more installed unified memory/);
  assert.match(markdown, /Documented power rating \(Different specification scopes\) \| 155 W · Maximum continuous system power \| 240 W · External power supply rating/);
  assert.match(markdown, /Installed storage \| 512 GB SSD \| 4 TB self-encrypting NVMe M\.2 SSD/);
  assert.doesNotMatch(markdown, /85 W higher/);
});

test("the released comparison archive publishes linked exact pairings and attributed video mentions", async () => {
  const { renderBattleArchive } = await import("./battle-archive.mjs");
  const left = "nvidia-geforce-rtx-4090", right = "nvidia-geforce-rtx-3090";
  const { html, markdown } = renderBattleArchive(records, urls, {
    sampleSize: 26, observedOn: "2026-11-21", pairs: {
      cards: [{ left, right, count: 2, sources: ["https://www.youtube.com/watch?v=4Y4-ad8m_yM"] }], machines: [],
    },
  });
  assert.match(html, /<table>/);
  assert.match(html, /YouTube title mentions/);
  assert.match(html, /sample of 26 video titles/);
  assert.match(html, /https:\/\/www\.youtube\.com\/watch\?v=4Y4-ad8m_yM/);
  assert.match(markdown, /NVIDIA GeForce RTX 4090 vs\. NVIDIA GeForce RTX 3090/);
  assert.match(markdown, /2 video titles/);
  assert.match(markdown, /104 GB more installed unified memory/);
  assert.doesNotMatch(html + markdown, /Most compared/);
});

test("suggested GPU matchups cover Radeon, older GeForce, workstation and mining alternatives", async () => {
  const { battleSuggestions } = await import("./battle.mjs");
  const cards = battleSuggestions(records, "cards");
  assert.ok(cards.length >= 10);
  assert.ok(battleSuggestions(records, "machines").length >= 2);
  const categories = new Set(cards.map(({ reason }) => reason[0]));
  assert.ok(categories.has("Older GeForce vs. current GeForce"));
  assert.ok(categories.has("Used workstation vs. new GeForce"));
  assert.ok(categories.has("Mining card vs. new GeForce"));
  assert.ok(cards.filter(({ left, right }) => [left.id, right.id].some(id => id.startsWith("amd-"))).length >= 3);
  const mining = cards.find(({ reason }) => reason[0] === "Mining card vs. new GeForce");
  const markdown = battleMarkdown(mining, urls);
  assert.match(markdown, /Nominal VRAM \| Unavailable \| 16 GB GDDR7/);
  assert.match(markdown, /Memory reported by source \| 8 GB stock; up to 64 GB after modification \(creator reported\)/);
  assert.doesNotMatch(markdown, /48 GB more nominal VRAM/);
});
