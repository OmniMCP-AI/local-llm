import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { estimateBattleTitles } from "./battle-title-signals.mjs";

test("reviewed title mentions rank exact catalog pairs and keep source links", async () => {
  const sample = JSON.parse(await readFile(new URL("./battle-title-sample.json", import.meta.url), "utf8"));
  const catalog = {
    cards: ["amd-radeon-rx-7900-xtx", ...[3090, 4090, 5080, 5090].map((model) => `nvidia-geforce-rtx-${model}`)]
      .map(id => ({ id })),
    machines: [{ id: "apple-mac-mini-m4-24gb-512gb" }, { id: "nvidia-dgx-spark-128gb-4tb" }],
  };
  const { sampleSize, pairs } = estimateBattleTitles(sample, catalog);
  assert.equal(sampleSize, 6);
  assert.equal(pairs.cards.length, 6);
  assert.deepEqual(pairs.cards[0], {
    left: "nvidia-geforce-rtx-3090", right: "nvidia-geforce-rtx-4090", count: 3,
    sources: ["https://www.youtube.com/watch?v=3vdM73WV7BI", "https://www.youtube.com/watch?v=H7Wa-WxPiAY",
      "https://www.youtube.com/watch?v=xzwb94eJ-EE"],
  });
  assert.equal(pairs.cards.find(({ left, right }) => left.endsWith("3090") && right.endsWith("5090")).count, 1);
  assert.deepEqual(pairs.machines, []);
});
