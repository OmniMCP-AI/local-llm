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

const testDatabase = process.env.FASTEST_TEST_DATABASE_URL;
const testCatalogReader = process.env.FASTEST_TEST_CATALOG_READER_URL;
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
  assert.equal(manifest.supplement.repositories, 3);
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

    const firstModels = await (await get("/api/v1/catalog?kind=models&limit=2")).json();
    assert.deepEqual(firstModels.pagination, { limit: 2, offset: 0, total: 19_195, nextOffset: 2 });
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
