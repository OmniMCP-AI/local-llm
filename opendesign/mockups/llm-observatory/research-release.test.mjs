import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const directory = fileURLToPath(new URL(".", import.meta.url));
const fixture = "youtube/09GB4LtXUok";
const blog = "together-evaluation-methods";
const digest = (value) => createHash("sha256").update(value).digest("hex");

async function buildRelease(t, approvals = {}) {
  const output = await mkdtemp(join(tmpdir(), "fastest-research-test-"));
  t.after(() => rm(output, { recursive: true, force: true }));
  const { writeResearchRelease } = await import("./research-release-build.mjs");
  const index = await writeResearchRelease(directory, output, approvals);
  const read = (name) => readFile(join(output, "research", index.release, name), "utf8");
  return { index, read };
}

test("a public library emits the editorial references and excludes private video records by default", async (t) => {
  const { index, read } = await buildRelease(t);
  assert.equal(index.sources.find((source) => source.id === blog).records.length, 0);
  assert.ok(!index.sources.some((source) => source.id === fixture));
  for (const artifact of ["library.html", "library.md", "index.json", "graphify.json"]) {
    const content = await read(artifact);
    assert.match(content, /together-evaluation-methods/);
    assert.doesNotMatch(content, /V024-P009|performance-series-observations\.csv/);
  }
  const manifest = JSON.parse(await read("manifest.json"));
  assert.equal(manifest.release, index.release);
  for (const [name, sha256] of Object.entries(manifest.artifacts)) {
    assert.equal(digest(await read(name)), sha256);
  }
});

test("an explicitly reviewed note preserves the three case scopes in its pinned share links", async (t) => {
  const sourceIndex = JSON.parse(await readFile(join(directory, "wiki/research-index.json"), "utf8"));
  const source = sourceIndex.sources.find((entry) => entry.id === fixture);
  const approval = { status: "approved-metadata", review: "TEST-ONLY", sha256: digest(JSON.stringify(source)) };
  const { index, read } = await buildRelease(t, { [fixture]: approval });
  const { researchReleaseUrl, readResearchFilters, filterResearch } = await import("./research-filter.mjs");
  const published = JSON.parse(await read("index.json"));
  const filter = (filters) => {
    const url = new URL(researchReleaseUrl(index.release, filters), "https://fastest.ai");
    assert.equal(url.pathname, "/research/" + index.release + "/library.html");
    const parsed = readResearchFilters(url.searchParams, published.vocabulary);
    return filterResearch(published.sources, parsed, "en", (facet, id) => id)
      .flatMap(({ records }) => records.map(({ id }) => id));
  };
  assert.ok(filter({ task: "coding", dimension: "quality" }).includes("V024-P009"));
  assert.deepEqual(filter({ task: "retrieval", dimension: "quality" }), ["V024-P007"]);
  assert.ok(filter({ task: "unspecified", dimension: "prefill" }).includes("V024-P001"));
  assert.deepEqual(filter({ task: "coding", dimension: "prefill" }), []);
  assert.deepEqual(filter({ format: "blog", topic: "coding", task: "coding" }), []);
  assert.equal(published.sources.find((entry) => entry.id === fixture).language, "en");
  assert.equal(published.sources.at(-1).date, null);
  assert.deepEqual(published.sources.filter((entry) => entry.date).map((entry) => entry.date),
    ["2026-10-27", "2026-06-16", "2025-11-04"]);
  const graph = JSON.parse(await read("graphify.json"));
  assert.ok(graph.links.some((edge) => edge.source === "V024-P007" && edge.target === "topics/retrieval" &&
    edge.relation === "describes_task" && edge.taxonomy_version === 1 && edge.source_location.endsWith("&t=228s")));
  assert.ok(!graph.links.some((edge) => edge.source === "V024-P001" && edge.relation === "describes_task"));
  for (const artifact of ["library.html", "library.md"]) {
    const content = await read(artifact);
    assert.match(content, /V024-P001/);
    assert.match(content, /Retrieve information at five depths in a 128K context/);
    assert.match(content, /Solve the creator’s Python coding challenges/);
    assert.match(content, /V024-S03/);
  }
});

test("an approval for a different source revision cannot publish changed metadata", async (t) => {
  await assert.rejects(buildRelease(t, {
    [fixture]: { status: "approved-metadata", review: "TEST-ONLY", sha256: "0".repeat(64) },
  }), /stale research metadata approval/);
});

test("the 20 method entries link reviewed topics, release gates, and video timestamps", async (t) => {
  const { index, read } = await buildRelease(t);
  assert.equal(index.methods.length, 20);
  const method = index.methods.find(({ id }) => id === "method-15");
  assert.deepEqual(method.topics, ["retrieval"]);
  assert.equal(method.url, "https://www.youtube.com/watch?v=09GB4LtXUok&t=226s");
  assert.match(method.gate.requirement, /retrieval depth and attempts/);
  for (const name of ["library.html", "library.md"]) {
    const body = await read(name);
    assert.match(body, /Retrieval across context/);
    assert.match(body, /\?topic=retrieval/);
    assert.match(body, /M1–M4 release gates/);
  }
});
