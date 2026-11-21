import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdtemp, readFile, readdir, rm, stat, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, relative } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";
import { readHardwareCatalog } from "./catalog-hardware-build.mjs";
import { modelShard } from "./catalog-paths.mjs";
import { importLocalCatalog } from "./catalog-pg.mjs";
import { onRequestGet as readPage } from "./functions/_middleware.js";
import { onRequestGet as readCatalogProfile } from "./functions/catalog/[release]/[[path]].js";
import { withLocalPages } from "./pages-test-server.mjs";

const run = promisify(execFile);
const here = fileURLToPath(new URL(".", import.meta.url));
const origin = "https://fastest.ai";

test("a production Pages catalog requires a database and an exact pin before writing output", async (t) => {
  const output = await mkdtemp(join(tmpdir(), "fastest-pages-required-pin-"));
  t.after(() => rm(output, { recursive: true, force: true }));
  await writeFile(join(output, "index.html"), "previous release");
  const env = { ...process.env };
  delete env.FASTEST_CATALOG_DATABASE_URL;
  delete env.FASTEST_CATALOG_SNAPSHOT_ID;
  const build = () => run(process.execPath, ["build.mjs", "--pages", "--catalog-postgres", "--output", output], { cwd: here, env });

  await assert.rejects(build(), /FASTEST_CATALOG_DATABASE_URL is required/);
  env.FASTEST_CATALOG_DATABASE_URL = "invalid until a valid pin is supplied";
  for (const snapshot of ["", "0123456789abcdef", "g".repeat(64)]) {
    env.FASTEST_CATALOG_SNAPSHOT_ID = snapshot;
    await assert.rejects(build(), /FASTEST_CATALOG_SNAPSHOT_ID must be a full SHA-256 digest/);
  }
  assert.deepEqual(await readdir(output), ["index.html"]);
  assert.equal(await readFile(join(output, "index.html"), "utf8"), "previous release");
});

async function releaseDigest(directory) {
  const files = [];
  for (const entry of await readdir(directory, { recursive: true, withFileTypes: true })) {
    if (entry.isFile()) files.push(relative(directory, join(entry.parentPath, entry.name)));
  }
  assert.ok(files.length <= 20_000, "Pages free-tier asset limit");
  const hash = createHash("sha256");
  for (const file of files.sort()) {
    const path = join(directory, file);
    assert.ok((await stat(path)).size <= 25 * 1024 ** 2, `Pages asset limit: ${file}`);
    hash.update(file + "\0");
    hash.update(createHash("sha256").update(await readFile(path)).digest());
  }
  return hash.digest("hex");
}

test("a date-pinned Pages build is reproducible and serves crawler discovery through Wrangler", { timeout: 60_000 }, async (t) => {
  const scratch = await mkdtemp(join(tmpdir(), "fastest-pages-"));
  const output = join(scratch, "pages");
  t.after(() => rm(scratch, { recursive: true, force: true }));

  const env = {
    ...process.env,
    FASTEST_PUBLIC_ORIGIN: origin,
    FASTEST_RELEASE_DATE: "2026-12-21",
  };
  for (const name of ["FASTEST_RELEASE_ORIGIN", "FASTEST_RESEARCH_METADATA_APPROVALS",
    "FASTEST_EVIDENCE_STATE", "FASTEST_RESEARCH_ARCHIVE"]) delete env[name];
  const build = (directory) => run(process.execPath, ["build.mjs", "--pages", "--output", directory], {
    cwd: here, env, signal: t.signal,
  });
  const rebuilt = join(scratch, "rebuilt");
  await build(output);
  await build(rebuilt);
  assert.equal(await releaseDigest(output), await releaseDigest(rebuilt));
  const manifest = JSON.parse(await readFile(join(output, "wiki/manifest.json"), "utf8"));
  assert.deepEqual(manifest.highlights.map(({ id }) => id), ["dual-rtx-2080-ti-nvlink", "open-benchmark-requests"]);
  const home = await readFile(join(output, "index.html"), "utf8");
  const homeMarkdown = await readFile(join(output, "index.md"), "utf8");
  assert.match(home, /<section data-home-highlights><h2>Research highlights<\/h2>/);
  assert.doesNotMatch(home + homeMarkdown, /Observed inventory tool-policy benchmark|\/agent-task\//);
  const community = await readFile(join(output, "wiki/community/index.html"), "utf8");
  const issues = "https://github.com/OmniMCP-AI/local-llm/issues/new?template=";
  for (const template of ["benchmark-request.yml", "result-correction.yml"]) {
    assert.ok(community.includes('href="' + issues + template + '"'));
  }
  const research = JSON.parse(await readFile(join(output, "research", manifest.researchRelease, "index.json"), "utf8"));
  const example = research.sources.find(({ id }) => id === "llama-bench-jsonl-example");
  assert.deepEqual(example?.records.map(({ dimension }) => dimension), ["prefill", "generation"]);
  assert.ok(!research.sources.some(({ format }) => format === "video"));

  await withLocalPages(output, t.signal, async (origin) => {
    const { stdout } = await run(process.execPath, ["verify-pages.mjs", origin, env.FASTEST_PUBLIC_ORIGIN], {
      cwd: here, signal: t.signal,
    });
    t.diagnostic(stdout.trim());
    const directory = await fetch(origin + "/api/runtime-releases", { signal: t.signal });
    assert.equal(directory.status, 200);
    assert.equal(directory.headers.get("Cache-Control"), "no-store");
    assert.ok(Array.isArray((await directory.json()).runtimes));
  });
});

test("PostgreSQL Pages visitors enter the released catalog and can explicitly open an unconfigured preview example", async () => {
  const { catalogHome, navigationHref } = await import("./release-origin.mjs");
  const origin = "https://release.fastest.example";
  const home = catalogHome("explorer", true, null);
  assert.deepEqual(home, { catalog: "#catalog", prices: "/prices", benchmarks: null, demo: "#explorer-demo" });
  assert.equal(catalogHome(home.demo.slice(1), true, null), null);
  const production = { catalog: "#catalog", prices: "/prices", benchmarks: origin + "/profiles", demo: null };
  assert.deepEqual(catalogHome("explorer", true, origin), production);
  assert.deepEqual(catalogHome("explorer-demo", true, origin), production);
  assert.equal(catalogHome("explorer", false, null), null);
  assert.equal(navigationHref("machines", true, null, true), "#catalog/machines");
  assert.equal(navigationHref("models", true, null, true), "#catalog/models");
  assert.equal(navigationHref("machines", true, origin, true), origin + "/profiles#machines");
  assert.equal(navigationHref("machines", true, null), "#machines");
});

test("the official Qwen model profile links the observed GGUF inventory benchmark in HTML and Markdown", async (t) => {
  const origin = "https://release.example.test";
  const pin = "f".repeat(64);
  const reportUrl = `${origin}/agent-task/${pin}/agent-task`;
  const model = "Qwen/Qwen2.5-7B-Instruct";
  const label = "Observed inventory tool-policy benchmark";
  const { artifact } = JSON.parse(await readFile(new URL("../../../production/fastest_text/plan.json", import.meta.url)));
  const catalog = JSON.parse(await readFile(new URL("catalog-models.json", import.meta.url)));
  const env = {
    FASTEST_RELEASE_ORIGIN: origin,
    FASTEST_AGENT_TASK_RELEASE: pin,
    ASSETS: { fetch: () => Response.json(catalog.models.filter(row => row.id.includes("/Qwen2.5-7B-Instruct"))) },
  };
  async function profile(extension, { id = model, bindings = env } = {}) {
    const release = "v1-" + "a".repeat(16);
    const path = `models/${id}.${extension}`;
    const response = await readCatalogProfile({
      request: new Request(`https://fastest.ai/catalog/${release}/${path}`),
      params: { release, path: path.split("/") },
      env: bindings,
    });
    assert.equal(response.status, 200);
    const body = await response.text();
    if (body.includes(label)) assert.equal(response.headers.get("cache-control"), "no-store");
    return body;
  }
  const report = {
    schema_version: 1,
    kind: "measured",
    conditions: { protocol_id: "inventory-agent-comparison-shared-ci-cpu@1", artifact },
    environment: { backend: "CPU" },
    contexts: ["bundle", "split"].map(id => ({ id, review: { decision: "allow" }, attempts: [{}] })),
  };
  let getReport = () => Response.json(report);
  const upstream = t.mock.method(globalThis, "fetch", async (url, options) => {
    assert.equal(String(url), reportUrl + ".json");
    assert.equal(options.redirect, "manual");
    assert.equal(options.cache, "no-store");
    return getReport();
  });
  const html = await profile("html");
  const markdown = await profile("md");
  assert.ok(html.includes(`href="${reportUrl}.html">${label}</a>`));
  assert.ok(markdown.includes(`[${label}](<${reportUrl}.html>)`));
  for (const body of [html, markdown]) {
    assert.match(body, /Shared CI CPU/);
    assert.ok(body.includes(artifact.repository));
    assert.ok(body.includes(artifact.revision));
    assert.doesNotMatch(body, /Publisher-reported benchmark results/);
  }
  assert.equal(upstream.mock.callCount(), 2);

  for (const bindings of [
    { ...env, FASTEST_RELEASE_ORIGIN: undefined },
    { ...env, FASTEST_RELEASE_ORIGIN: origin + "/not-an-origin" },
    { ...env, FASTEST_RELEASE_ORIGIN: "http://release.example.test" },
    { ...env, FASTEST_AGENT_TASK_RELEASE: undefined },
    { ...env, FASTEST_AGENT_TASK_RELEASE: "f".repeat(63) },
  ]) {
    assert.doesNotMatch(await profile("html", { bindings }), /agent-task|tool-policy benchmark/);
  }
  for (const id of [model + "-AWQ", model + "-GPTQ-Int4", model + "-1M", "unsloth/Qwen2.5-7B-Instruct"]) {
    assert.doesNotMatch(await profile("md", { id }), /agent-task|tool-policy benchmark/);
  }
  assert.equal(upstream.mock.callCount(), 2);

  for (const status of [302, 404, 410, 503]) {
    getReport = () => new Response(null, { status, headers: { Location: reportUrl + ".json" } });
    assert.doesNotMatch(await profile("html"), /agent-task|tool-policy benchmark/);
  }
  for (const invalid of [
    { ...report, kind: "synthetic" },
    { ...report, environment: { backend: "Metal" } },
    { ...report, contexts: [{ ...report.contexts[0], attempts: [] }, report.contexts[1]] },
    { ...report, conditions: { ...report.conditions, artifact: { ...artifact, revision: "0".repeat(40) } } },
    { ...report, conditions: { ...report.conditions, artifact: { ...artifact, quantization: "Q5_K_M" } } },
    { ...report, conditions: { ...report.conditions, artifact: { ...artifact, shards: artifact.shards.slice(0, 1) } } },
  ]) {
    getReport = () => Response.json(invalid);
    assert.doesNotMatch(await profile("md"), /agent-task|tool-policy benchmark/);
  }
});

test("runtime profile pairs link the official observed release and exact watch section", async (t) => {
  const releaseOrigin = "https://release.example.test";
  const repository = "ggml-org/llama.cpp";
  const tag = "test-observed-release";
  const refreshedAt = "2026-11-21T01:00:00Z";
  const catalog = JSON.parse(await readFile(new URL("catalog-runtimes.json", import.meta.url)));
  const report = {
    schema: "fastest.ai/runtime-release-watch/v1",
    sources: {
      "llama.cpp": {
        repository, mode: "live", last_successful_refresh: refreshedAt,
        stale: false, last_error: null,
      },
    },
    releases: [
      { runtime_id: "llama.cpp", status: "prerelease", tag: "ignore-prerelease", prerelease: true },
      { runtime_id: "llama.cpp", status: "current", tag, prerelease: false, published_at: refreshedAt,
        source_url: `https://github.com/${repository}/releases/tag/${tag}` },
    ],
  };
  let upstream = () => Response.json(report);
  t.mock.method(globalThis, "fetch", async (url, options) => {
    assert.equal(String(url), releaseOrigin + "/runtime-releases.json");
    assert.equal(options.redirect, "manual");
    assert.equal(options.cache, "no-store");
    return upstream();
  });
  async function profile(id, extension, origin = releaseOrigin) {
    const release = "v1-" + "a".repeat(16);
    const path = `runtimes/${id}.${extension}`;
    const response = await readCatalogProfile({
      request: new Request(`https://fastest.ai/catalog/${release}/${path}`),
      params: { release, path: path.split("/") },
      env: { FASTEST_RELEASE_ORIGIN: origin, ASSETS: { fetch: () => Response.json(catalog) } },
    });
    assert.equal(response.status, 200);
    assert.equal(response.headers.get("cache-control"), "no-store");
    return response.text();
  }
  const watchUrl = releaseOrigin + "/runtime-releases#runtime-llama.cpp";
  const upstreamUrl = `https://github.com/${repository}/releases/tag/${tag}`;
  const pinnedUrl = `https://github.com/${repository}/releases/tag/v1.0.0`;
  const html = await profile("llama.cpp", "html");
  const markdown = await profile("llama.cpp", "md");
  assert.ok(html.includes(`href="${watchUrl}"`));
  assert.ok(html.includes(`href="${upstreamUrl}"`));
  assert.ok(markdown.includes(`(<${watchUrl}>)`));
  assert.ok(markdown.includes(`(<${upstreamUrl}>)`));
  for (const page of [html, markdown]) {
    assert.ok(page.includes(pinnedUrl));
    assert.ok(page.includes(refreshedAt));
    assert.doesNotMatch(page, /ignore-prerelease/);
  }
  assert.doesNotMatch(await profile("mlx-lm", "html"), /runtime-releases/);
  assert.doesNotMatch(await profile("llama.cpp", "md", null), /runtime-releases/);
  report.sources["llama.cpp"].stale = true;
  report.sources["llama.cpp"].last_error = "Upstream service unavailable";
  const retained = await profile("llama.cpp", "md");
  assert.ok(retained.includes(upstreamUrl));
  assert.match(retained, /feed is stale/i);
  assert.match(retained, /refresh failed/i);
  for (const status of [302, 404, 410, 503]) {
    upstream = () => new Response(null, { status });
    const unavailable = await profile("llama.cpp", "md");
    assert.doesNotMatch(unavailable, /runtime-releases|test-observed-release/);
    assert.ok(unavailable.includes(pinnedUrl));
  }
});

test("the Runtimes directory data exposes official captures without implying freshness", async (t) => {
  const { onRequestGet } = await import("./functions/api/runtime-releases.js");
  const releaseOrigin = "https://release.example.test";
  const refreshedAt = "2026-11-21T01:00:00Z";
  const official = {
    "llama.cpp": "ggml-org/llama.cpp", sglang: "sgl-project/sglang",
    vllm: "vllm-project/vllm", ollama: "ollama/ollama",
  };
  const sources = Object.fromEntries(Object.entries(official).map(([id, repository]) => [id, {
    repository, mode: "live", last_successful_refresh: refreshedAt,
    stale: id === "vllm", last_error: id === "vllm" ? "Source unavailable" : null,
  }]));
  const report = {
    schema: "fastest.ai/runtime-release-watch/v1",
    sources: {
      ...sources,
      "mlx-lm": { ...sources.vllm, repository: "third-party/mlx-lm" },
    },
    releases: [{
      runtime_id: "vllm", status: "current", prerelease: false, tag: "v-test",
      published_at: refreshedAt, source_url: "https://github.com/vllm-project/vllm/releases/tag/v-test",
    }],
  };
  let upstream = () => Response.json(report);
  const mock = t.mock.method(globalThis, "fetch", async (url) => {
    assert.equal(String(url), releaseOrigin + "/runtime-releases.json");
    return upstream();
  });
  async function directory(origin) {
    const response = await onRequestGet({ env: { FASTEST_RELEASE_ORIGIN: origin } });
    assert.equal(response.headers.get("Cache-Control"), "no-store");
    return response.json();
  }
  const data = await directory(releaseOrigin);
  assert.equal(data.html, releaseOrigin + "/runtime-releases");
  assert.deepEqual(data.runtimes.map(({ id }) => id), ["llama.cpp", "sglang", "vllm", "ollama"]);
  const vllm = data.runtimes.find(({ id }) => id === "vllm");
  assert.equal(vllm.refreshedAt, refreshedAt);
  assert.equal(vllm.stale, true);
  assert.equal(vllm.failed, true);
  assert.equal(vllm.release.tag, "v-test");
  assert.equal(vllm.watchUrl, releaseOrigin + "/runtime-releases#runtime-vllm");
  assert.equal(vllm.feedUrl, "https://github.com/vllm-project/vllm/releases");
  assert.deepEqual(await directory("http://release.example.test"), { runtimes: [] });
  assert.equal(mock.mock.callCount(), 1);

  upstream = () => Response.json({ ...report, sources: { ...sources, ollama: { mode: "fixture" } } });
  assert.deepEqual(await directory(releaseOrigin), { runtimes: [] });
  upstream = () => Response.json({ ...report, sources: { ollama: { ...sources.ollama, last_successful_refresh: null } } });
  assert.deepEqual(await directory(releaseOrigin), { runtimes: [] });
  upstream = () => new Response(null, { status: 410 });
  assert.deepEqual(await directory(releaseOrigin), { runtimes: [] });
});

test("the published runtime wiki Markdown discovers the watch while the origin is available", async (t) => {
  const releaseOrigin = "https://release.example.test";
  const report = {
    schema: "fastest.ai/runtime-release-watch/v1",
    sources: {
      ollama: {
        repository: "ollama/ollama", mode: "live", last_successful_refresh: "2026-11-21T01:00:00Z",
        stale: false, last_error: null,
      },
    },
    releases: [],
  };
  let upstream = () => Response.json(report);
  t.mock.method(globalThis, "fetch", async () => upstream());
  const article = "# Inference runtimes and tuning\n";
  async function wiki(path) {
    const response = await readPage({
      request: new Request(origin + path),
      env: { FASTEST_RELEASE_ORIGIN: releaseOrigin, ASSETS: { fetch: () => Response.json({ paths: [] }) } },
      next: () => new Response(article, { headers: { "Content-Type": "text/markdown", "Content-Length": article.length } }),
    });
    assert.equal(response.status, 200);
    assert.equal(response.headers.get("Cache-Control"), "no-store");
    return response.text();
  }
  const linked = await wiki("/wiki/runtimes.md");
  assert.ok(linked.startsWith(article));
  assert.ok(linked.includes(`[Runtime release watch](<${releaseOrigin}/runtime-releases.md>)`));
  assert.equal(await wiki("/wiki/catalog.md"), article);
  upstream = () => new Response(null, { status: 503 });
  assert.equal(await wiki("/wiki/runtimes.md"), article);
});

test("homepage discovery links the pinned inventory report while its public review is live", async (t) => {
  const pin = "b".repeat(64);
  const releaseOrigin = "https://release.example.test";
  const reportUrl = releaseOrigin + "/agent-task/" + pin + "/agent-task";
  const label = "Observed inventory tool-policy benchmark";
  const heading = "## Research highlights";
  const staticEntry = "- [Open research request](/wiki/community.md)\n";
  const staticMarkdown = "# fastest.ai\n\n" + heading + "\n\n" + staticEntry;
  const staticManifest = { release: "wiki-static", highlights: [{ id: "open-benchmark-requests", priority: 10 }] };
  const env = {
    FASTEST_RELEASE_ORIGIN: releaseOrigin,
    FASTEST_AGENT_TASK_RELEASE: pin,
    ASSETS: { fetch: () => Response.json({ paths: [] }) },
  };
  let markdown = staticMarkdown;
  async function home(path, bindings = env, method = "GET") {
    const response = await readPage({
      request: new Request(origin + path, { method }),
      env: bindings,
      next: () => path === "/index.md"
        ? new Response(markdown, { headers: { "Content-Type": "text/markdown", "Content-Length": String(markdown.length) } })
        : Response.json(staticManifest),
    });
    assert.equal(response.status, 200);
    assert.equal(response.headers.get("Cache-Control"), "no-store");
    return response;
  }
  const { artifact } = JSON.parse(await readFile(new URL("../../../production/fastest_text/plan.json", import.meta.url)));
  const report = {
    schema_version: 1,
    kind: "measured",
    conditions: { protocol_id: "inventory-agent-comparison-shared-ci-cpu@1", artifact },
    environment: { backend: "CPU" },
    contexts: ["bundle", "split"].map(id => ({ id, review: { decision: "allow" }, attempts: [{}] })),
  };
  let status = 200;
  const upstream = t.mock.method(globalThis, "fetch", async (url, options) => {
    assert.equal(String(url), reportUrl + ".json");
    assert.equal(options.cache, "no-store");
    assert.equal(options.redirect, "manual");
    return Response.json(report, { status });
  });

  const discovery = await home("/index.md");
  assert.equal(discovery.headers.get("Content-Length"), null);
  const body = await discovery.text();
  assert.ok(body.includes(`[${label}](${reportUrl}.md)`));
  assert.match(body, /shared CI CPU/);
  assert.ok(body.indexOf(label) < body.indexOf(staticEntry));
  const manifest = await (await home("/wiki/manifest.json")).json();
  assert.equal(manifest.release, staticManifest.release);
  assert.equal(manifest.highlights[0].href, reportUrl + ".html");
  assert.equal(manifest.highlights[0].markdown, reportUrl + ".md");
  assert.deepEqual(manifest.highlights.slice(1), staticManifest.highlights);

  markdown = "# fastest.ai\n";
  assert.ok((await (await home("/index.md")).text()).includes(heading + "\n\n- [" + label));
  markdown = staticMarkdown;
  assert.equal(await (await home("/index.md", { ...env, FASTEST_AGENT_TASK_RELEASE: undefined })).text(), staticMarkdown);
  assert.equal((await home("/index.md", env, "HEAD")).body, null);
  assert.equal(upstream.mock.callCount(), 3);

  for (const inactive of [404, 410, 503]) {
    status = inactive;
    assert.equal(await (await home("/index.md")).text(), staticMarkdown);
    assert.deepEqual(await (await home("/wiki/manifest.json")).json(), staticManifest);
  }
  report.contexts[1].review.decision = "deny";
  status = 200;
  assert.equal(await (await home("/index.md")).text(), staticMarkdown);
});

const testDatabase = process.env.FASTEST_TEST_DATABASE_URL;
const testCatalogReader = process.env.FASTEST_TEST_CATALOG_READER_URL;
test("the static Pages review links to exact hardware profiles from its pinned PostgreSQL snapshot", {
  skip: !testDatabase || !testCatalogReader, timeout: 60_000,
}, async (t) => {
  const scratch = await mkdtemp(join(tmpdir(), "fastest-pages-hardware-"));
  t.after(() => rm(scratch, { recursive: true, force: true }));
  const output = join(scratch, "pages");
  const hardware = await readHardwareCatalog(here);
  const id = "apple-mac-mini-m4-24gb-512gb";
  const name = "Mac mini M4 from the Pages review snapshot";
  hardware.catalog.machines.find((row) => row.id === id).name = name;
  const { snapshotId } = await importLocalCatalog(hardware, testDatabase);
  const env = Object.fromEntries(Object.entries(process.env).filter(([key]) => !key.startsWith("FASTEST_")));
  Object.assign(env, {
    FASTEST_PUBLIC_ORIGIN: origin, FASTEST_CATALOG_DATABASE_URL: testCatalogReader, FASTEST_CATALOG_SNAPSHOT_ID: snapshotId,
  });
  await run(process.execPath, ["build.mjs", "--pages", "--catalog-postgres", "--review", "--output", output], {
    cwd: here, env, signal: t.signal,
  });
  const root = "/catalog/v1-" + snapshotId.slice(0, 16);
  await withLocalPages(output, t.signal, async (address) => {
    const get = (route) => fetch(address + route, { redirect: "manual", signal: t.signal });
    const home = await (await get("/")).text();
    assert.ok(home.includes(`href="${root}/hardware"`));
    assert.ok(home.includes(`href="${root}/models">Model catalog</a>`));
    const models = await (await get(root + "/models")).text();
    assert.match(models, /<h1>Popular models<\/h1>/);
    assert.ok(models.includes(`href="${root}/models/openai-community/gpt2"`));
    const model = await get(root + "/models/openai-community/gpt2");
    assert.equal(model.status, 200);
    assert.match(await model.text(), /<dt>Popular rank<\/dt><dd>1<\/dd>/);
    const companion = await get(root + "/models/openai-community/gpt2.md");
    assert.match(companion.headers.get("content-type"), /^text\/markdown/);
    assert.match(await companion.text(), /\*\*Popular rank\*\* — 1/);
    assert.ok(models.includes(`href="${root}/model-lookup"`));
    const lookup = await (await get(root + "/model-lookup?q=Qwen%2FQwen2.5-7B-Instruct-1M")).text();
    assert.match(lookup, /<label for="repository">Exact repository ID<\/label>/);
    const script = lookup.match(/<script src="(\/[^"]+)" defer><\/script>/)?.[1];
    assert.ok(script);
    assert.equal((await get(script)).status, 200);
    const directory = await (await get(root + "/hardware")).text();
    const profile = `${root}/machines/${id}`;
    assert.ok(directory.includes(`href="${profile}">${name}</a>`));
    const html = await get(profile);
    assert.equal(html.status, 200);
    assert.match(html.headers.get("content-type"), /^text\/html/);
    assert.ok((await html.text()).includes(`<h1>${name}</h1>`));
    const markdown = await get(profile + ".md");
    assert.equal(markdown.status, 200);
    assert.match(markdown.headers.get("content-type"), /^text\/markdown/);
    assert.ok((await markdown.text()).includes(`snapshot: ${snapshotId}`));
  }, { staticOnly: true });
  await run(process.execPath, ["build.mjs", "--pages", "--catalog-postgres", "--output", output], {
    cwd: here, env, signal: t.signal,
  });
  await withLocalPages(output, t.signal, async (address) => {
    const directory = await fetch(address + root + "/hardware", { signal: t.signal });
    assert.equal(directory.status, 404);
  });
});

test("production Pages serves the selected PostgreSQL snapshot through the catalog list and profile pairs", {
  skip: !testDatabase || !testCatalogReader, timeout: 90_000,
}, async (t) => {
  const scratch = await mkdtemp(join(tmpdir(), "fastest-pages-postgres-"));
  t.after(() => rm(scratch, { recursive: true, force: true }));
  const output = join(scratch, "pages");
  const hardware = await readHardwareCatalog(here);
  const machineId = "apple-mac-mini-m4-24gb-512gb";
  const machine = hardware.catalog.machines.find(({ id }) => id === machineId);
  machine.name = "Mac mini M4 from the pinned database snapshot";
  const { snapshotId } = await importLocalCatalog(hardware, testDatabase);
  machine.name = "Mac mini M4 from the newer database snapshot";
  const newer = await importLocalCatalog(hardware, testDatabase);
  assert.notEqual(snapshotId, newer.snapshotId);

  const env = { ...process.env, FASTEST_CATALOG_DATABASE_URL: testCatalogReader, FASTEST_CATALOG_SNAPSHOT_ID: snapshotId };
  for (const name of ["FASTEST_RELEASE_ORIGIN", "FASTEST_RESEARCH_METADATA_APPROVALS", "FASTEST_EVIDENCE_STATE", "FASTEST_RESEARCH_ARCHIVE"]) delete env[name];
  const build = () => run(process.execPath, ["build.mjs", "--pages", "--catalog-postgres", "--output", output], {
    cwd: here, env, signal: t.signal,
  });
  await build();
  const wiki = JSON.parse(await readFile(join(output, "wiki/manifest.json"), "utf8"));
  const release = wiki.catalogRelease;
  const manifest = JSON.parse(await readFile(join(output, "catalog", release, "manifest.json"), "utf8"));
  assert.equal(manifest.snapshotId, snapshotId);
  assert.equal(manifest.coverage.publishedRows, 19_192);
  assert.equal(manifest.supplement.repositories, 8);
  assert.equal(manifest.supplement.publisherResults, 6);
  assert.equal(manifest.discovery.popular, 300);
  assert.equal(manifest.discovery.small, 75);
  assert.equal(manifest.hardware.coverage.completeBuilds, 4);
  assert.equal(manifest.coverage.topologyRevisions, 39);

  const releaseHash = await releaseDigest(output);
  env.FASTEST_CATALOG_SNAPSHOT_ID = "0".repeat(64);
  await assert.rejects(build(), /PostgreSQL catalog snapshot was not found/);
  assert.equal(await releaseDigest(output), releaseHash);

  await run("psql", ["-X", "-w", "--dbname", testDatabase, "--set=ON_ERROR_STOP=1", "--command", `
    UPDATE fastest_catalog.machine SET document = document || '{"name":"Unexpected replacement"}'::jsonb
    WHERE snapshot_id = '${newer.snapshotId}' AND id = '${machineId}'`]);
  env.FASTEST_CATALOG_SNAPSHOT_ID = newer.snapshotId;
  await assert.rejects(build(), /PostgreSQL catalog snapshot content does not match its publication digest/);
  assert.equal(await releaseDigest(output), releaseHash);

  await run("psql", ["-X", "-w", "--dbname", testDatabase, "--set=ON_ERROR_STOP=1", "--command", `
    UPDATE fastest_catalog.topology_node SET document = document || '{"label":"Unexpected card"}'::jsonb
    WHERE snapshot_id = '${snapshotId}' AND machine_id = 'V021-HP-C001' AND slot = 1`]);
  env.FASTEST_CATALOG_SNAPSHOT_ID = snapshotId;
  await assert.rejects(build(), /PostgreSQL catalog snapshot content does not match its publication digest/);
  assert.equal(await releaseDigest(output), releaseHash);
  await run("psql", ["-X", "-w", "--dbname", testDatabase, "--set=ON_ERROR_STOP=1", "--command", `
    UPDATE fastest_catalog.topology_node SET document = original.document
    FROM fastest_catalog.topology_node original
    WHERE topology_node.snapshot_id = '${snapshotId}' AND original.snapshot_id = '${newer.snapshotId}'
      AND topology_node.machine_id = 'V021-HP-C001' AND original.machine_id = topology_node.machine_id
      AND topology_node.slot = 1 AND original.slot = topology_node.slot`]);

  env.FASTEST_CATALOG_SNAPSHOT_ID = snapshotId;
  const approvals = join(scratch, "approvals.json");
  await writeFile(approvals, JSON.stringify({ "youtube/09GB4LtXUok": { status: "withdrawn" } }));
  env.FASTEST_RESEARCH_METADATA_APPROVALS = approvals;
  await assert.rejects(build(), /PostgreSQL catalog snapshot conflicts with active evidence withdrawals/);
  assert.equal(await releaseDigest(output), releaseHash);

  delete env.FASTEST_RESEARCH_METADATA_APPROVALS;
  const quarantine = join(scratch, "quarantine.json");
  await writeFile(quarantine, JSON.stringify({ paths: [`/catalog-data/${release}/*`], updates: [] }));
  env.FASTEST_EVIDENCE_STATE = quarantine;
  await assert.rejects(build(), /PostgreSQL catalog snapshot conflicts with active evidence withdrawals/);
  assert.equal(await releaseDigest(output), releaseHash);

  await withLocalPages(output, t.signal, async (address) => {
    const get = async (path) => {
      const response = await fetch(address + path, { signal: t.signal });
      assert.equal(response.status, 200, path);
      return response;
    };
    const home = await (await get("/")).text();
    assert.match(home, /Mac mini M4 from the pinned database snapshot/);
    assert.doesNotMatch(home, /Mac mini M4 from the newer database snapshot/);
    assert.match(home, /Recent releases/);
    assert.match(home, /thinkingmachines\/Inkling-2-Mini/);
    const machines = await (await get(`/catalog-data/${release}/machines.json`)).json();
    assert.match(machines.find(({ id }) => id === machineId).name, /pinned database snapshot/);
    const response = await get("/api/v1/catalog?kind=machines&q=pinned%20database%20snapshot");
    assert.equal(response.headers.get("cache-control"), "no-store");
    const results = await response.json();
    assert.equal(results.revision, release);
    assert.equal(results.snapshotId, snapshotId);
    assert.equal(results.kind, "machines");
    assert.equal(results.pagination.total, 1);
    assert.equal(results.results[0].id, machineId);
    assert.equal(results.results[0].name, "Mac mini M4 from the pinned database snapshot");
    assert.equal(results.results[0].html, `/catalog/${release}/machines/${machineId}.html`);
    assert.equal(results.results[0].markdown, `/catalog/${release}/machines/${machineId}.md`);
    assert.equal(machines.find(({ id }) => id === machineId).topologyRevision, undefined);
    const { topologyRevision } = machines.find(({ id }) => id === "V021-HP-C001");
    assert.match(topologyRevision, /^topology-[a-f0-9]{64}$/);
    assert.ok(home.includes(topologyRevision));
    const topologyWiki = await (await get("/wiki/gpu-topology/")).text();
    assert.ok(topologyWiki.includes(`/#wiki/gpu-topology/${topologyRevision}`));

    const modelId = "Qwen/Qwen2.5-0.5B-Instruct";
    const models = await (await get(`/catalog-data/${release}/${modelShard(modelId)}.json`)).json();
    const row = models.find(({ id }) => id === modelId);
    assert.equal(row.discovery.popular.rank, 11);
    assert.equal(row.discovery.small.rank, 4);

    const modelSearch = await (await get("/api/v1/catalog?kind=models&q=qwen%2Fqwen2.5-0.5b-instruct")).json();
    assert.equal(modelSearch.pagination.total, 1);
    assert.equal(modelSearch.results[0].id, modelId);
    assert.equal(modelSearch.results[0].source, "https://huggingface.co/" + modelId);
    assert.equal(modelSearch.results[0].markdown, `/catalog/${release}/models/${modelId}.md`);

    const areteId = "NousResearch/Arete-27B";
    const areteSearch = await (await get("/api/v1/catalog?kind=models&q=" + encodeURIComponent(areteId))).json();
    assert.equal(areteSearch.pagination.total, 1);
    assert.equal(areteSearch.results[0].id, areteId);
    assert.equal(areteSearch.results[0].markdown, `/catalog/${release}/models/${areteId}.md`);

    const firstModels = await (await get("/api/v1/catalog?kind=models&limit=2")).json();
    assert.deepEqual(firstModels.pagination, { limit: 2, offset: 0, total: 19_197, nextOffset: 2 });
    const nextModels = await (await get(`/api/v1/catalog?kind=models&revision=${firstModels.revision}&limit=2&offset=2`)).json();
    assert.equal(nextModels.results.length, 2);
    assert.ok(nextModels.results.every(next => firstModels.results.every(first => next.id !== first.id)));

    const [firstShard, secondShard] = Object.keys(manifest.modelShardCounts).sort();
    const previousShard = await (await get(`/catalog-data/${release}/${firstShard}.json`)).json();
    const followingShard = await (await get(`/catalog-data/${release}/${secondShard}.json`)).json();
    const boundaryOffset = previousShard.length - 1;
    const joined = await (await get(`/api/v1/catalog?kind=models&revision=${release}&limit=2&offset=${boundaryOffset}`)).json();
    assert.deepEqual(joined.results.map(({ id }) => id), [previousShard.at(-1).id, followingShard[0].id]);

    const cardSearch = await (await get("/api/v1/catalog?kind=cards&q=nvidia-geforce-rtx-5090")).json();
    assert.ok(cardSearch.results.some(({ id }) => id === "nvidia-geforce-rtx-5090"));
    const runtimeSearch = await (await get("/api/v1/catalog?kind=runtimes&q=llama.cpp")).json();
    assert.equal(runtimeSearch.results.find(({ id }) => id === "llama.cpp").source, "https://github.com/ggml-org/llama.cpp");

    const openapi = await (await get(`/catalog/${release}/openapi.json`)).json();
    const catalogOperation = openapi.paths["/api/v1/catalog"]?.get;
    assert.ok(catalogOperation);
    assert.deepEqual(catalogOperation.parameters.find(({ name }) => name === "kind").schema.enum,
      ["cards", "machines", "models", "runtimes"]);
    assert.ok((await (await get("/llms.txt")).text()).includes(`/catalog/${release}/openapi.json`));

    for (const path of ["/wiki/agent-discovery/", "/wiki/agent-discovery.md"]) {
      assert.ok((await (await get(path)).text()).includes(`/catalog/${release}/openapi.json`));
    }
    assert.equal((await fetch(address + `/api/v1/catalog?kind=cards&revision=v1-${"0".repeat(16)}`,
      { signal: t.signal })).status, 404);

    for (const query of ["kind=models&q=Qwen", "kind=models&offset=2", "kind=models&limit=26", "kind=machines&kind=cards"]) {
      assert.equal((await fetch(address + "/api/v1/catalog?" + query, { signal: t.signal })).status, 400, query);
    }
    for (const [path, expected] of [
      [`machines/${machineId}`, /Mac mini M4 from the pinned database snapshot/],
      [`models/${modelId}`, /Popular rank[^\n]{0,20}11/],
      ["models/moonshotai/Kimi-K3.1-Pro", /d9e99b0792a5e93b78ea9bea62a68167e36ddd9e\/LICENSE/],
      ["models/thinkingmachines/Inkling-2-Mini", /48\.2%/],
      ["models/thinkingmachines/Inkling-2-Small", /72\.1%/],
      ["models/ibm-granite/granite-4.2-3b", /69\.71% pass@1/],
      ["models/mistralai/Mistral-Large-4-1T-A52B", /1T total, 49B active per token/],
      ["models/google/gemma-4-E2B-it", /44%/],
      ["models/google/gemma-4-E4B-it", /52%/],
      [`models/${areteId}`, /70%/],
      ["models/Corianas/1.3b", /Family unavailable/],
      ["runtimes/llama.cpp", /No fastest\.ai compatibility test is published in this release/],
    ]) {
      for (const [extension, type] of [["html", "text/html"], ["md", "text/markdown"]]) {
        const response = await get(`/catalog/${release}/${path}.${extension}`);
        assert.ok(response.headers.get("content-type").startsWith(type));
        assert.match(await response.text(), expected);
      }
    }
    for (const extension of ["html", "md"]) {
      const response = await get(`/catalog/${release}/machines/V021-HP-C001.${extension}`);
      assert.ok((await response.text()).includes(`/#wiki/gpu-topology/${topologyRevision}`));
    }
  });

  const policyFile = join(output, "evidence-quarantine.json");
  const originalPolicy = await readFile(policyFile, "utf8");
  const policy = JSON.parse(originalPolicy);
  try {
    policy.paths.push(`/catalog-data/${release}/qw.json`);
    await writeFile(policyFile, JSON.stringify(policy));
    await withLocalPages(output, t.signal, async (address) => {
      const withdrawn = await fetch(address + `/api/v1/catalog?kind=models&revision=${release}&q=Qwen%2FQwen2.5-0.5B-Instruct`, {
        headers: { "If-None-Match": '"old-catalog"' }, signal: t.signal,
      });
      assert.equal(withdrawn.status, 410);
      assert.equal(withdrawn.headers.get("cache-control"), "no-store");
      assert.doesNotMatch(await withdrawn.text(), /Qwen2\.5/);
    });
  } finally {
    await writeFile(policyFile, originalPolicy);
  }

  await run("psql", ["-X", "-w", "--dbname", testDatabase, "--set=ON_ERROR_STOP=1", "--command", `
    UPDATE fastest_catalog.model_repository
    SET document = jsonb_set(document, '{supplemental,publisherEvaluations,0,scorePercent}', '48.3')
    WHERE snapshot_id = '${snapshotId}' AND id = 'thinkingmachines/Inkling-2-Mini'`]);
  delete env.FASTEST_EVIDENCE_STATE;
  await assert.rejects(build(), /PostgreSQL catalog snapshot content does not match its publication digest/);
  assert.equal(await releaseDigest(output), releaseHash);
});
