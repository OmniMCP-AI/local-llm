import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdir, mkdtemp, readFile, writeFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";
import test from "node:test";
import sourceIndex from "./wiki/research-index.json" with { type: "json" };

const run = promisify(execFile);
const digest = (bytes) => createHash("sha256").update(bytes).digest("hex");
const evidenceId = "youtube/09GB4LtXUok";
const source = sourceIndex.sources.find(({ id }) => id === evidenceId);
const receipt = "16660254-d91d-498d-8c9c-91ec112b211b";

test("an opted-in report stages withdrawal of a released source with exact export and discovery hashes", async (t) => {
  const root = await mkdtemp(join(tmpdir(), "fastest-evidence-test-"));
  t.after(() => rm(root, { recursive: true, force: true }));
  const previous = join(root, "previous");
  const candidate = join(root, "candidate");
  const approvals = join(root, "approvals.json");
  const requestPath = join(root, "request.json");
  await writeFile(approvals, JSON.stringify({
    [evidenceId]: { status: "approved-metadata", review: "fixture", sha256: digest(JSON.stringify(source)) },
  }));
  await run(process.execPath, ["build.mjs", "--pages", "--output", previous], {
    env: { ...process.env, FASTEST_RESEARCH_METADATA_APPROVALS: approvals },
  });
  const old = JSON.parse(await readFile(join(previous, "wiki/manifest.json"))).researchRelease;
  const exportPath = "downloads/earlier-library.md";
  const markdown = await readFile(join(previous, "research", old, "library.md"));
  await mkdir(join(previous, "downloads"));
  await writeFile(join(previous, exportPath), markdown);
  await writeFile(requestPath, JSON.stringify({
    action: "withdraw",
    evidenceId,
    sourceId: evidenceId,
    sourceLocator: source.url,
    intake: { id: receipt, category: "correction", status: "queued", message: "private contribution",
      context_json: JSON.stringify({ page: "/wiki/research/", release: old }) },
  }));

  await run(process.execPath, ["resolve-evidence.mjs", requestPath, previous, candidate, approvals]);

  const report = JSON.parse(await readFile(join(candidate, "review.json")));
  const read = (name) => readFile(join(candidate, "pages", name), "utf8");
  const manifest = JSON.parse(await read("wiki/manifest.json"));
  const now = manifest.researchRelease;
  assert.notEqual(now, old);
  const updated = JSON.parse(await read(`research/${now}/index.json`));
  assert.ok(updated.sources.some(({ id }) => id === "together-evaluation-methods"));
  assert.ok(!updated.sources.some(({ id }) => id === evidenceId));
  for (const path of [`research/${now}/graphify.json`, `research/${now}/library.md`,
    "wiki/comparison-methods.md", "wiki/comparison-methods/index.html", "index.html", "llms.txt", "sitemap.xml"]) {
    assert.doesNotMatch(await read(path), /09GB4LtXUok|V024-P007|private contribution|16660254-d91d/);
  }
  await assert.rejects(read(`research/${old}/library.md`), { code: "ENOENT" });
  await assert.rejects(read(exportPath), { code: "ENOENT" });
  assert.deepEqual(await readFile(join(previous, exportPath)), markdown);
  assert.deepEqual(report.changes.find(({ path }) => path === "/" + exportPath), {
    path: "/" + exportPath, before: digest(markdown), after: null,
  });
  assert.equal(report.changes.find(({ path }) => path === "/sitemap.xml").after, digest(await read("sitemap.xml")));
  assert.ok(report.notificationDraft.includes(digest(markdown)));
  assert.match(report.receiptUpdate, /UPDATE|INSERT/);
  assert.ok(report.receiptUpdate.includes(receipt));
  assert.ok(report.receiptUpdate.includes(report.resolutionPath));
  const policy = JSON.parse(await read("evidence-quarantine.json"));
  assert.ok(policy.paths.includes("/research/" + old + "/*"));
  assert.ok(policy.paths.includes("/" + exportPath));
  assert.match(await read("wiki/evidence-updates.md"), /Withdrawn/);
});

test("Pages denies stale conditional reads before cache or asset lookup", async () => {
  const { onRequestGet } = await import("./functions/_middleware.js");
  const old = "/research/v1-aaaaaaaaaaaaaaaa";
  const policy = { paths: [old + "/*", "/downloads/earlier.csv"] };
  const asset = (input) => {
    const request = new Request(input);
    if (new URL(request.url).pathname === "/evidence-quarantine.json") return Response.json(policy);
    return new Response("old content", { headers: { ETag: '"old"' } });
  };
  for (const path of [old + "/chart.json", old + "%2flibrary.md?old=1", "/downloads/earlier.csv"]) {
    const result = await onRequestGet({
      request: new Request("https://example.test" + path, { headers: { "If-None-Match": '"old"' } }),
      env: { ASSETS: { fetch: asset } },
      next: () => new Response("stale candidate", { status: 200 }),
    });
    assert.equal(result.status, 410, path);
    assert.equal(result.headers.get("Cache-Control"), "no-store");
    assert.doesNotMatch(await result.text(), /stale candidate/);
  }
  const result = await onRequestGet({
    request: new Request("https://example.test/wiki/research.md", { headers: { "If-None-Match": '"old"' } }),
    env: { ASSETS: { fetch: asset } },
    next: (request) => request?.headers.has("If-None-Match")
      ? new Response(null, { status: 304 }) : new Response("fresh", { headers: { ETag: '"new"' } }),
  });
  assert.equal(await result.text(), "fresh");
  assert.equal(result.headers.get("Cache-Control"), "no-store");
  assert.equal(result.headers.get("ETag"), null);
});

test("a reviewed correction preserves its prior pin and links the revised source from the wiki", async (t) => {
  const { writeResearchRelease } = await import("./research-release-build.mjs");
  const { writeWikiRelease } = await import("./wiki-release.mjs");
  const root = await mkdtemp(join(tmpdir(), "fastest-correction-test-"));
  t.after(() => rm(root, { recursive: true, force: true }));
  const fixture = join(root, "fixture");
  await mkdir(join(fixture, "wiki", "pages"), { recursive: true });
  for (const name of ["research-release-client.mjs", "research-filter.mjs", "research-release-render.mjs",
    "research-release-build.mjs", "wiki/context-vocabulary.json", "wiki/pages/comparison-methods.md"]) {
    await writeFile(join(fixture, name), await readFile(name));
  }
  const earlierIndex = structuredClone(sourceIndex);
  const earlierSource = earlierIndex.sources.find(({ id }) => id === evidenceId);
  earlierSource.context = "Earlier wording in the reviewed source.";
  const earlierBytes = JSON.stringify(earlierIndex);
  const earlierGraph = JSON.parse(await readFile("wiki/graphify.json"));
  earlierGraph.graph.research_index_sha256 = digest(earlierBytes);
  await writeFile(join(fixture, "wiki/research-index.json"), earlierBytes);
  await writeFile(join(fixture, "wiki/graphify.json"), JSON.stringify(earlierGraph));
  const previous = join(root, "previous");
  const earlier = await writeResearchRelease(fixture, previous, {
    [evidenceId]: { status: "approved-metadata", review: "earlier fixture", sha256: digest(JSON.stringify(earlierSource)) },
  });
  await writeWikiRelease({
    output: previous, origin: "https://fastest.ai", researchRelease: earlier.release, releaseDate: "2026-11-21",
    documents: { research: { title: "Research", summary: "Research", status: "published", body: "Read evidence." } },
    edges: [], highlights: [],
  });
  const approvals = join(root, "approved.json");
  await writeFile(approvals, JSON.stringify({
    [evidenceId]: { status: "approved-metadata", review: "new fixture", sha256: digest(JSON.stringify(source)) },
  }));
  const request = join(root, "request.json");
  await writeFile(request, JSON.stringify({
    action: "correct", evidenceId, sourceId: evidenceId, sourceLocator: source.url,
    intake: { issue: "https://github.com/OmniMCP-AI/local-llm/issues/24" },
  }));
  const output = join(root, "output");
  await run(process.execPath, ["resolve-evidence.mjs", request, previous, output, approvals]);
  const report = JSON.parse(await readFile(join(output, "review.json")));
  assert.notEqual(report.candidate.research, earlier.release);
  assert.equal(report.receiptUpdate, null);
  assert.match(await readFile(join(output, "pages/wiki/evidence-updates.md"), "utf8"), /\[Reviewed source\]\(https:\/\/www\.youtube\.com\/watch\?v=09GB4LtXUok\)/);
  const pinned = join(output, "pages/research", earlier.release, "library.md");
  assert.match(await readFile(pinned, "utf8"), /Earlier wording in the reviewed source/);
  const pinnedBytes = await readFile(pinned);
  assert.ok(report.notificationDraft.includes(digest(pinnedBytes)));

  const corrected = join(output, "pages");
  const correctedState = join(corrected, "evidence-quarantine.json");
  const rebuilt = join(root, "fresh-build");
  await run(process.execPath, ["build.mjs", "--pages", "--output", rebuilt], { env: {
    ...process.env, FASTEST_RESEARCH_METADATA_APPROVALS: approvals, FASTEST_EVIDENCE_STATE: correctedState,
    FASTEST_RESEARCH_ARCHIVE: corrected,
  } });
  assert.deepEqual(await readFile(join(rebuilt, "research", earlier.release, "library.md")), pinnedBytes);

  await writeFile(pinned, "tampered archive");
  await assert.rejects(run(process.execPath, ["build.mjs", "--pages", "--output", join(root, "tampered-build")], {
    env: { ...process.env, FASTEST_RESEARCH_METADATA_APPROVALS: approvals, FASTEST_EVIDENCE_STATE: correctedState,
      FASTEST_RESEARCH_ARCHIVE: corrected },
  }), /release manifest disagree/);

  await writeFile(request, JSON.stringify({
    action: "withdraw", evidenceId, sourceId: evidenceId, sourceLocator: source.url,
    intake: { issue: "https://github.com/OmniMCP-AI/local-llm/issues/25" },
  }));
  const withdrawn = join(root, "withdrawn");
  await run(process.execPath, ["resolve-evidence.mjs", request, rebuilt, withdrawn, approvals]);
  const retired = join(withdrawn, "pages");
  for (const path of ["wiki/evidence-updates.html", "wiki/evidence-updates.md", "evidence-quarantine.json"]) {
    assert.doesNotMatch(await readFile(join(retired, path), "utf8"), /09GB4LtXUok|Reviewed source/);
  }
  const state = JSON.parse(await readFile(join(retired, "evidence-quarantine.json")));
  assert.ok(state.paths.includes("/research/" + earlier.release + "/*"));
  await assert.rejects(readFile(join(retired, "research", earlier.release, "library.md")), { code: "ENOENT" });
});
