import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { test } from "node:test";
import { modelCollections, queryModelCatalog } from "./catalog-search.mjs";
import { readCatalogModelFiles } from "./catalog-release-build.mjs";

const rows = JSON.parse(await readFile(new URL("catalog-models.json", import.meta.url))).models;
const identities = JSON.parse(await readFile(new URL("catalog-identities.json", import.meta.url)));

test("search and source tags apply before stable model pagination", () => {
  const filters = { query: "QWEN/QWEN2.5-0.5B", pageSize: 1 };
  const first = queryModelCatalog(rows, identities, filters);
  const second = queryModelCatalog(rows, identities, { ...filters, page: 2 });
  assert.equal(first.total, 5);
  assert.equal(first.rows[0].id, "Qwen/Qwen2.5-0.5B");
  assert.equal(second.rows[0].id, "Qwen/Qwen2.5-0.5B-Instruct");

  const exactFormat = queryModelCatalog(rows, identities, { ...filters, tag: "GGUF", license: "apache-2.0" });
  assert.deepEqual(exactFormat.rows.map(({ id }) => id), ["Qwen/Qwen2.5-0.5B-Instruct"]);
  assert.equal(queryModelCatalog(rows, identities, { ...filters, tag: "Text to speech" }).total, 0);
  assert.equal(queryModelCatalog(rows, identities, { ...filters, license: "__missing" }).total, 0);
});

test("small and popular shelves preserve dated Hub ranks and resolvable repository IDs", async () => {
  const snapshot = JSON.parse(await readFile(new URL("model-discovery.json", import.meta.url)));
  const byId = new Map(rows.map(row => [row.id, row]));
  assert.equal(snapshot.popular.length, 300);
  assert.equal(snapshot.small.length, 75);
  assert.ok(snapshot.small.every(row => row.parameters <= snapshot.smallLimit));
  for (const shelf of [snapshot.popular, snapshot.small]) {
    assert.ok(shelf.every(row => byId.has(row.id)));
    assert.equal(new Set(shelf.map(row => row.family)).size, shelf.length);
    const page = queryModelCatalog(shelf.map(row => byId.get(row.id)), identities, { ranked: true, pageSize: 3 });
    assert.deepEqual(page.rows.map(row => row.id), shelf.slice(0, 3).map(row => row.id));
  }
});

test("recent publisher records supplement existing repositories without duplicating search or changing ranks", async () => {
  const { source, discovery, supplementalModels } = await readCatalogModelFiles(fileURLToPath(new URL(".", import.meta.url)));
  const { all, recent, popular, small } = modelCollections(source.models, discovery, supplementalModels);
  assert.equal(all.length, 19_196);
  assert.deepEqual(recent.map(({ id }) => id), [
    "thinkingmachines/Inkling-2-Mini", "thinkingmachines/Inkling-2-Small", "moonshotai/Kimi-K3.1-Pro",
    "mistralai/Mistral-Large-4-1T-A52B", "ibm-granite/granite-4.2-3b",
  ]);
  const graniteId = "ibm-granite/granite-4.2-3b";
  const graniteMatches = queryModelCatalog(all, identities, { query: graniteId, tag: "3.7B parameters" });
  const granite = graniteMatches.rows.filter(({ id }) => id === graniteId);
  assert.equal(granite.length, 1);
  assert.equal(granite[0].supplemental.revision, "4e9c275e232f10211ec88644d106a1f6a1b60e06");
  assert.deepEqual(popular.map(({ id }) => id), discovery.popular.map(({ id }) => id));
  assert.deepEqual(small.map(({ id }) => id), discovery.small.map(({ id }) => id));
  assert.deepEqual(queryModelCatalog(all, identities, {
    query: "MOONSHOTAI/KIMI-K3.1-PRO", license: "kimi-k3.1-pro", tag: "Image and text to text",
  }).rows.map(({ id }) => id), ["moonshotai/Kimi-K3.1-Pro"]);
});
