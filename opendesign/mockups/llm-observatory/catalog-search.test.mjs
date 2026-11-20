import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";
import { queryModelCatalog } from "./catalog-search.mjs";

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
