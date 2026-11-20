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
