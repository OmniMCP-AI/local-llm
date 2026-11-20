import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { filterResearch } from "./research-filter.mjs";

const { sources } = JSON.parse(readFileSync(new URL("./wiki/research-index.json", import.meta.url)));
const vocab = JSON.parse(readFileSync(new URL("./wiki/context-vocabulary.json", import.meta.url)));
const find = (filters) => filterResearch(sources, { query: "", ...filters }, "en", (group,id) => vocab[group][id][0]);
const records = (filters) => find(filters).flatMap(match => match.records).map(row => row.id);

test("a mixed source has distinct Python, retrieval and unclassified prefill records", () => {
  const source = "youtube/09GB4LtXUok";
  assert.ok(find({ topic: "coding" }).some(result => result.source.id === source));
  assert.ok(records({ task: "coding", dimension: "quality" }).includes("V024-P009"));
  assert.ok(records({ task: "retrieval", dimension: "quality" }).includes("V024-P007"));
  assert.ok(records({ task: "unspecified", dimension: "prefill" }).includes("V024-P001"));
  assert.ok(!records({ task: "coding" }).includes("V024-P001"));
  assert.ok(!records({ task: "retrieval", query: "Pythonchallengepassrate" }).includes("V024-P007"));
});

test("a guide about code evaluation stays discoverable without issuing a local test claim", () => {
  assert.ok(find({ format:"blog", topic:"coding" }).some(x => x.source.id === "together-evaluation-methods"));
  assert.deepEqual(find({ format:"blog", topic:"coding", task:"coding" }), []);
});

test("estimated and incomplete results preserve their original scope", () => {
  assert.ok(records({ task:"agent-workflows", dimension:"projection" }).includes("V021-P012"));
  assert.ok(!records({ task:"document-processing" }).includes("V027-P001"));
  assert.ok(!records({ task:"image-generation" }).includes("V053-P002"));
});

test("undated sources sort after dated ones and title sorting does not depend on dates", () => {
  const results = find({}).map(({ source }) => source);
  const dates = results.map(x => x.date || "");
  assert.deepEqual(dates,[...dates].sort().reverse());
  assert.equal(find({ sort:"title" }).length,results.length);
  assert.deepEqual(find({ query:"nonexistent-fixture-92873" }),[]);
});

test("every record resolves to its source, series, dimension and approved vocabulary", () => {
  const ids=new Set();
  for(const { source, records: rows } of find({})) {
    assert.ok(Object.hasOwn(vocab.formats,source.format) && Object.keys(source.topics).length);
    for(const id of Object.keys(source.topics)) assert.ok(Object.hasOwn(vocab.topics,id));
    for(const r of rows) {
      assert.ok(!ids.has(r.id) && Object.hasOwn(vocab.dimensions,r.dimension));
      ids.add(r.id);
      assert.ok(r.seriesUrl.startsWith(source.note+"?plain=1#L"));
      assert.ok(r.url.includes(source.id.split("/")[1]) && r.evidence && r.conditions);
      assert.equal(Boolean(r.task), Boolean(r.topics.length));
      for(const id of r.topics) assert.ok(Object.hasOwn(vocab.topics,id));
    }
  }
});
