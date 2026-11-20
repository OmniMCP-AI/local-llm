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
