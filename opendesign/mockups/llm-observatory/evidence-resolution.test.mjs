import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdir, mkdtemp, readFile, writeFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";
import test from "node:test";
import { withLocalPages } from "./pages-test-server.mjs";
import sourceIndex from "./wiki/research-index.json" with { type: "json" };

const run = promisify(execFile);
const digest = (bytes) => createHash("sha256").update(bytes).digest("hex");
const evidenceId = "youtube/09GB4LtXUok";
const source = sourceIndex.sources.find(({ id }) => id === evidenceId);
const receipt = "16660254-d91d-498d-8c9c-91ec112b211b";

test("a reviewed publisher withdrawal retires each archived catalog carrying that exact source", async (t) => {
  const root = await mkdtemp(join(tmpdir(), "fastest-publisher-policy-"));
  t.after(() => rm(root, { recursive: true, force: true }));
  const request = join(root, "request.json");
  const policy = join(root, "policy.json");
  const source = "https://publisher.test/evaluation/";
  const issue = "https://github.com/OmniMCP-AI/local-llm/issues/24";
  const original = "v1-aabbccddeeff0011";
  const older = "v1-2233445566778899";
  const clean = "v1-0101010101010101";
  const fixtures = [original, older, clean].map((id) => join(root, id));
  for (const [release, directory] of [original, older, clean].map((id, index) => [id, fixtures[index]])) {
    const data = join(directory, "catalog-data", release);
    await mkdir(data, { recursive: true });
    await mkdir(join(directory, "wiki"));
    await writeFile(join(directory, "wiki/manifest.json"), JSON.stringify({ catalogRelease: release }));
    await writeFile(join(data, "ex.json"), JSON.stringify([{
      id: "example/model",
      supplemental: { publisherEvaluations: [{ source: release === clean ? source + "different" : source }] },
    }]));
  }
  await writeFile(join(fixtures[0], "evidence-quarantine.json"), JSON.stringify({ paths: ["/downloads/retired.md"], updates: [] }));
  const stage = (modelId) => writeFile(request, JSON.stringify({ action: "withdraw", modelId, source, issue }))
    .then(() => run(process.execPath, ["withdraw-publisher-evaluation.mjs", request, fixtures[0], policy, ...fixtures.slice(1)]));
  await assert.rejects(stage("example/unknown"), /do not identify a published publisher evaluation/);
  await stage("example/model");
  const state = JSON.parse(await readFile(policy, "utf8"));
  assert.deepEqual(state.paths.slice().sort(), [
    `/catalog-data/${older}/*`, `/catalog-data/${original}/*`, `/catalog/${older}/*`,
    `/catalog/${original}/*`, "/downloads/retired.md",
  ]);
  assert.deepEqual(state.publisherWithdrawals, [{ sourceSha256: digest(source), issue, catalogReleases: [older, original] }]);
  assert.ok(!JSON.stringify(state).includes(source));
  const { onRequestGet: readPage } = await import("./functions/_middleware.js");
  const { onRequestGet: readCatalog } = await import("./functions/api/v1/catalog.js");
  const env = { ASSETS: { fetch: (request) => Response.json(
    new URL(request.url).pathname === "/wiki/manifest.json" ? { catalogRelease: clean } : state,
  ) } };
  for (const path of [`/catalog/${original}/models/example/model`, `/catalog-data/${older}/ex.json`]) {
    const request = new Request("https://example.test" + path, { headers: { "If-None-Match": '"old"' } });
    const reply = await readPage({ request, env, next: () => assert.fail("Stale asset was requested") });
    assert.equal(reply.status, 410);
    assert.equal(reply.headers.get("Cache-Control"), "no-store");
  }
  const api = await readCatalog({ request: new Request(`https://example.test/api/v1/catalog?kind=models&revision=${older}`), env });
  assert.equal(api.status, 410);
});

test("an opted-in withdrawal retires prior exports and verifies the reviewed release over Pages HTTP", { timeout: 90_000 }, async (t) => {
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
  const existingPolicy = join(previous, "evidence-quarantine.json");
  const existing = JSON.parse(await readFile(existingPolicy, "utf8"));
  const retiredPublisher = {
    sourceSha256: digest("https://publisher.test/retired/"),
    issue: "https://github.com/OmniMCP-AI/local-llm/issues/24",
    catalogReleases: ["v1-1234123412341234"],
  };
  await writeFile(existingPolicy, JSON.stringify({ ...existing, publisherWithdrawals: [retiredPublisher] }));
  const old = JSON.parse(await readFile(join(previous, "wiki/manifest.json"))).researchRelease;
  const exportPath = "downloads/earlier-library.md";
  const markdown = await readFile(join(previous, "research", old, "library.md"));
  await mkdir(join(previous, "downloads", "earlier-guide"), { recursive: true });
  await writeFile(join(previous, exportPath), markdown);
  await writeFile(join(previous, "downloads/earlier-guide/index.html"), "<h1>Archived export</h1>");
  const internalBytes = "Deployment configuration outside the public evidence routes";
  await writeFile(join(previous, "_internal-fixture"), internalBytes);
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
  assert.deepEqual(policy.publisherWithdrawals, [retiredPublisher]);
  assert.ok(policy.paths.includes("/research/" + old + "/*"));
  assert.ok(policy.paths.includes("/" + exportPath));
  assert.match(await read("wiki/evidence-updates.md"), /Withdrawn/);
  const noticePath = "wiki/evidence-updates.json";
  const notice = JSON.parse(await read(noticePath));
  assert.equal(notice.version, 1);
  assert.equal(notice.notices.length, 1);
  const [entry] = notice.notices;
  assert.deepEqual(Object.keys(entry).sort(), ["action", "affectedSha256", "resolution"]);
  assert.equal(entry.action, "withdraw");
  assert.equal(entry.resolution, report.resolutionPath);
  assert.ok(entry.affectedSha256.includes(digest(markdown)));
  assert.ok(entry.affectedSha256.includes(digest("<h1>Archived export</h1>")));
  assert.ok(!entry.affectedSha256.includes(digest(internalBytes)));
  assert.deepEqual(entry.affectedSha256, [...new Set(entry.affectedSha256)].sort());
  assert.ok(entry.affectedSha256.every((hash) => /^[a-f0-9]{64}$/.test(hash)));
  for (const path of ["wiki/evidence-updates.html", "wiki/evidence-updates.md"]) {
    assert.ok((await read(path)).includes("/" + noticePath));
  }
  const verifier = "verify-evidence-resolution.mjs";
  const plan = await run(process.execPath, [verifier, "--purge-plan", join(candidate, "review.json"), "https://fastest.ai"]);
  const urls = new Set(plan.stdout.trim().split("\n"));
  for (const path of ["/", "/index.html", "/index", "/sitemap.xml", "/" + exportPath,
    "/downloads/earlier-guide/", "/downloads/earlier-guide/index.html", "/research/" + old + "/library"]) {
    assert.ok(urls.has("https://fastest.ai" + path), path);
  }
  assert.doesNotMatch(plan.stdout, /\*|\/_headers|\/_redirects|\/_routes\.json/);

  const pages = join(candidate, "pages");
  await mkdir(join(pages, "downloads"));
  await writeFile(join(pages, exportPath), markdown);
  await withLocalPages(pages, t.signal, async (origin) => {
    const { stdout } = await run(process.execPath, [verifier, join(candidate, "review.json"), origin], { signal: t.signal });
    assert.match(stdout, /Verified withdrawal/);
    const response = await fetch(origin + "/" + noticePath, { signal: t.signal });
    assert.equal(response.status, 200);
    assert.match(response.headers.get("content-type"), /^application\/json/);
    assert.equal(response.headers.get("cache-control"), "no-store");
    assert.deepEqual(await response.json(), notice);
    const stale = join(root, "stale-review.json");
    const sitemap = report.changes.find(({ path }) => path === "/sitemap.xml");
    sitemap.after = sitemap.before;
    for (const { artifacts } of report.history) {
      for (const artifact of artifacts) {
        if (artifact.path === sitemap.path) artifact.after = sitemap.after;
      }
    }
    report.diffSha256 = digest(JSON.stringify(report.changes, null, 2) + "\n");
    await writeFile(stale, JSON.stringify(report));
    await assert.rejects(run(process.execPath, [verifier, stale, origin], { signal: t.signal }),
      /sitemap\.xml differs from reviewed bytes/);
  });
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

test("a reviewed correction preserves its prior pin and links the revised source over Pages HTTP", { timeout: 90_000 }, async (t) => {
  const { readResearchApprovals, writeResearchRelease } = await import("./research-release-build.mjs");
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
    ...await readResearchApprovals(),
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
  const noticePath = "wiki/evidence-updates.json";
  const correctedNotice = await readFile(join(corrected, noticePath), "utf8");
  const [correction] = JSON.parse(correctedNotice).notices;
  assert.equal(correction.action, "correct");
  assert.equal(correction.resolution, report.resolutionPath);
  assert.ok(correction.affectedSha256.includes(digest(pinnedBytes)));
  const filter = await readFile(join(corrected, "research", earlier.release, "research-filter.mjs"));
  assert.deepEqual(filter, await readFile(join(corrected, "research", report.candidate.research, "research-filter.mjs")));
  assert.ok(!correction.affectedSha256.includes(digest(filter)), "unchanged bytes should never match the notice");
  assert.doesNotMatch(correctedNotice, /Earlier wording|09GB4LtXUok|research-filter\.mjs|github\.com/);
  await withLocalPages(corrected, t.signal, async (origin) => {
    const { stdout } = await run(process.execPath, ["verify-evidence-resolution.mjs", join(output, "review.json"), origin], { signal: t.signal });
    assert.match(stdout, /Verified correction/);
    const response = await fetch(origin + correction.resolution, { signal: t.signal });
    assert.equal(response.status, 200);
    assert.ok((await response.text()).includes(`id="${correction.resolution.split("#")[1]}"`));
  });
  const correctedState = join(corrected, "evidence-quarantine.json");
  const rebuilt = join(root, "fresh-build");
  await run(process.execPath, ["build.mjs", "--pages", "--output", rebuilt], { env: {
    ...process.env, FASTEST_RESEARCH_METADATA_APPROVALS: approvals, FASTEST_EVIDENCE_STATE: correctedState,
    FASTEST_RESEARCH_ARCHIVE: corrected,
  } });
  assert.deepEqual(await readFile(join(rebuilt, "research", earlier.release, "library.md")), pinnedBytes);
  assert.equal(await readFile(join(rebuilt, noticePath), "utf8"), correctedNotice);

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
  for (const path of ["wiki/evidence-updates.html", "wiki/evidence-updates.md", "evidence-quarantine.json", noticePath]) {
    assert.doesNotMatch(await readFile(join(retired, path), "utf8"), /09GB4LtXUok|Reviewed source/);
  }
  const replayedNotice = await readFile(join(retired, noticePath), "utf8");
  const [earlierNotice, withdrawal] = JSON.parse(replayedNotice).notices;
  const withdrawnReport = JSON.parse(await readFile(join(withdrawn, "review.json")));
  assert.deepEqual(earlierNotice, correction);
  assert.equal(withdrawal.action, "withdraw");
  assert.equal(withdrawal.resolution, withdrawnReport.resolutionPath);
  assert.ok(withdrawal.affectedSha256.includes(digest(pinnedBytes)));
  assert.ok(!withdrawal.affectedSha256.includes(digest(correctedNotice)));
  const replay = join(root, "replayed");
  await run(process.execPath, ["build.mjs", "--pages", "--output", replay], { env: {
    ...process.env, FASTEST_RESEARCH_METADATA_APPROVALS: join(withdrawn, "approvals.json"),
    FASTEST_EVIDENCE_STATE: join(retired, "evidence-quarantine.json"),
  } });
  assert.equal(await readFile(join(replay, noticePath), "utf8"), replayedNotice);
  assert.doesNotMatch(await readFile(join(replay, "wiki/evidence-updates.html"), "utf8"), /09GB4LtXUok|Reviewed source/);
  const state = JSON.parse(await readFile(join(retired, "evidence-quarantine.json")));
  assert.ok(state.paths.includes("/research/" + earlier.release + "/*"));
  await assert.rejects(readFile(join(retired, "research", earlier.release, "library.md")), { code: "ENOENT" });
});
