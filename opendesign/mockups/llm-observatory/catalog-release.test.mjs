import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { writeCatalogRelease } from "./catalog-release-build.mjs";
import { readHardwareCatalog } from "./catalog-hardware-build.mjs";
import { writeLocalCatalogProfiles } from "./catalog-local-build.mjs";
import { importLocalCatalog } from "./catalog-pg.mjs";
import { onRequestGet } from "./functions/catalog/[release]/[[path]].js";
import { onRequestGet as goToFit } from "./functions/fit.js";

const here = dirname(fileURLToPath(import.meta.url));
const host = "https://example.test";

async function buildFixture(t, hardware) {
  const output = await mkdtemp(join(tmpdir(), "fastest-catalog-"));
  t.after(() => rm(output, { recursive: true, force: true }));
  const release = await writeCatalogRelease(here, output, hardware);

  return {
    release,
    read: (name) => readFile(join(output, "catalog", release, name), "utf8"),
    readData: (name) => readFile(join(output, "catalog-data", release, name), "utf8").then(JSON.parse),
    request: (path) => onRequestGet({
      request: new Request(host + "/catalog/" + release + "/" + path),
      params: { release, path: path.split("/") },
      next: () => new Response("Not found", { status: 404 }),
      env: {
        ASSETS: {
          async fetch(request) {
            try {
              const file = new URL(request.url).pathname.slice(1);
              return Response.json(JSON.parse(await readFile(join(output, file), "utf8")));
            } catch (error) {
              if (error.code !== "ENOENT") throw error;
              return new Response(null, { status: 404 });
            }
          },
        },
      },
    }),
  };
}

test("the released card keeps repository, family, revision and artifact identities distinct", async (t) => {
  const { read, request } = await buildFixture(t);
  const coverage = JSON.parse(await read("manifest.json"));
  assert.equal(coverage.coverage.sourceRows, 19_192);
  assert.equal(coverage.coverage.publishedRows, 19_192);
  assert.match(await read("LICENSE.txt"), /Copyright \(c\) 2026 Alex Jones/);

  const card = "models/Corianas/1.3b";
  const html = await request(card + ".html");
  const markdown = await request(card + ".md");
  assert.equal(html.status, 200);
  assert.equal(markdown.status, 200);
  assert.match(html.headers.get("content-type"), /^text\/html/);
  assert.match(markdown.headers.get("content-type"), /^text\/markdown/);

  for (const response of [html, markdown]) {
    const text = await response.text();
    assert.match(text, /Corianas\/1\.3b/);
    assert.match(text, /https:\/\/huggingface\.co\/Corianas\/1\.3b/);
    for (const message of ["Family unavailable", "Revision unavailable", "Exact artifact unavailable", "Model license unavailable"]) {
      assert.ok(text.includes(message), `Missing expected gap: ${message}`);
    }
    assert.doesNotMatch(text, /https:\/\/huggingface\.co\/Corianas\/1\.3b\/tree\/main/);
  }

  assert.equal((await request("models/Corianas/does-not-exist.html")).status, 404);
});

test("reviewed repository and conversion artifacts retain their own revisions and digests", async (t) => {
  const { read, request } = await buildFixture(t);
  const { coverage } = JSON.parse(await read("manifest.json"));
  assert.equal(coverage.withExactArtifacts, 1);
  assert.equal(coverage.exactArtifacts, 3);

  for (const extension of ["html", "md"]) {
    const response = await request("models/Qwen/Qwen2.5-0.5B-Instruct." + extension);
    const text = await response.text();
    assert.equal(response.status, 200);
    assert.match(text, /Qwen2\.5/);
    assert.match(text, /apache-2\.0/);
    assert.match(text, /7ae557604adf67be50417f59c2c2f167def9a775\/model\.safetensors/);
    assert.match(text, /fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe/);
    assert.match(text, /9217f5db79a29953eb74d5343926648285ec7e67\/qwen2\.5-0\.5b-instruct-q4/);
    assert.match(text, /74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db/);
    assert.ok(text.replaceAll("\\", "").includes("Q4_K_M"));
    assert.match(text, /9217f5db79a29953eb74d5343926648285ec7e67\/qwen2\.5-0\.5b-instruct-q8_0\.gguf/);
    assert.match(text, /ca59ca7f13d0e15a8cfa77bd17e65d24f6844b554a7b6c12e07a5f89ff76844e/);
    assert.match(text, /runtimes\/llama\.cpp\.html/);
    assert.match(text, /Tested compatibility.*unavailable/i);
  }
});

test("runtime cards cite pinned releases and keep documented support apart from tests", async (t) => {
  const { request } = await buildFixture(t);
  for (const [runtime, tag, repository, format] of [
    ["llama.cpp", "v1.0.0", "ggml-org/llama.cpp", "GGUF"],
    ["sglang", "v0.5.23", "sgl-project/sglang", "Safetensors"],
    ["vllm", "v0.34.0", "vllm-project/vllm", "Safetensors"],
    ["ollama", "v0.40.16", "ollama/ollama", "GGUF"],
    ["mlx-lm", "v0.32.2", "ml-explore/mlx-lm", "MLX"],
    ["strata", "v0.2.17", "Niko1221/Strata", "GGUF"],
    ["project-maya", "v1.1.70", "mw00/project-maya", "GGUF"],
  ]) {
    for (const extension of ["html", "md"]) {
      const response = await request(`runtimes/${runtime}.${extension}`);
      assert.equal(response.status, 200);
      const text = await response.text();
      assert.ok(text.includes(`https://github.com/${repository}/releases/tag/${tag}`));
      assert.ok(text.includes("Upstream documented support"));
      assert.ok(text.includes(format));
      assert.ok(text.includes("No fastest.ai compatibility test is published in this release"));
    }
  }
});

test("the runtime profile links an exact commit and the relevant transcript", async (t) => {
  const { request } = await buildFixture(t);
  const response = await request("runtimes/ninfer.html");
  assert.equal(response.status, 200);
  const html = await response.text();
  assert.match(html, /Neroued\/ninfer\/commit\/ebdc67e584bcd9ebe16ee63af9abeb2118bac6cd/);
  assert.match(html, /MhZABCEOUWY/);
  assert.match(html, /Pinned upstream commit/);
});

test("versioned hardware cards preserve uncertain memory, source links and board variants", async (t) => {
  const { read, request } = await buildFixture(t);
  const { hardware } = JSON.parse(await read("manifest.json"));
  assert.equal(hardware.asOf, "2026-11-21");
  assert.equal(hardware.coverage.cards, 112);
  assert.equal(hardware.coverage.researchProfiles, 116);

  const machine = "machines/V018-HP-C002";
  const card = "cards/nvidia-geforce-rtx-2080-ti-colorful-modified";
  for (const extension of ["html", "md"]) {
    const response = await request(`${machine}.${extension}`);
    assert.equal(response.status, 200);
    const text = await response.text();
    assert.match(text, /Partial configuration/);
    assert.match(text, /20 GB system RAM limit/);
    assert.match(text, /Installed system memory.*Unknown/);
    assert.match(text, /Untested in this release/);
    assert.match(text, /1PJGtLpYGOY/);

    const variant = await request(`${card}.${extension}`);
    assert.equal(variant.status, 200);
    const variantText = await variant.text();
    assert.match(variantText, /Colorful GeForce RTX 2080 Ti/);
    assert.match(variantText, /capacities conflict/);
    assert.match(variantText, /cards\/nvidia-geforce-rtx-2080-ti\.html/);
    assert.match(variantText, /V029-HP-C001/);
  }
  assert.equal((await request("cards/nvidia-rtx-2080-ti-every-board.html")).status, 404);
});

function assertProfileFieldsAgree(html, markdown, id) {
  const unescape = (value) => value.replaceAll("&amp;", "&").replaceAll("&lt;", "<").replaceAll("&gt;", ">")
    .replaceAll("&quot;", '"').replaceAll("&#39;", "'");
  const plainMarkdown = markdown.replace(/\\([\\`*_{}\[\]<>|])/g, "$1");
  for (const [, label, href, text] of html.matchAll(/<dt>(.*?)<\/dt><dd>(?:<a href="([^"]*)">)?([^<]*)(?:<\/a>)?<\/dd>/g)) {
    const value = unescape(text);
    const expected = href ? `[${value}](<${unescape(href)}>)` : value;
    assert.ok(plainMarkdown.includes(`**${unescape(label)}** — ${expected}\n`), `${id}: ${unescape(label)}`);
  }
}

test("released RTX 5090 D variants preserve separate evidence and product views", async (t) => {
  const { request } = await buildFixture(t);
  for (const format of ["html", "md"]) {
    const unresolved = await request(`cards/nvidia-geforce-rtx-5090-d.${format}`).then(response => response.text());
    assert.match(unresolved, /revision and capacity unresolved/);
    assert.match(unresolved, /No manufacturer specification has been matched to this identity/);

    const original = await request(`cards/nvidia-geforce-rtx-5090-d-32gb.${format}`).then(response => response.text());
    assert.match(original, /32 GB GDDR7/);
    assert.match(original, /ASUS ROG Astral GeForce RTX 5090 D 32 GB OC/);
    assert.match(original, /MSI VANGUARD OC board/);

    const later = await request(`cards/nvidia-geforce-rtx-5090-d-v2.${format}`).then(response => response.text());
    assert.match(later, /24 GB GDDR7/);
    assert.match(later, /384-bit/);

    const asus = await request(`cards/asus-rog-astral-rtx5090d-o32g-gaming.${format}`);
    assert.equal(asus.status, 200);
    const board = await asus.text();
    assert.match(board, /ROG-ASTRAL-RTX5090D-O32G-GAMING/);
    assert.match(board, /512-bit/);
    assert.match(board, /357\.6 × 149\.3 × 76 mm/);
    assert.match(board, /Product image source/);
    assert.match(board, /cards\/nvidia-geforce-rtx-5090-d-32gb\.html/);
  }
});

test("every released hardware row resolves in both formats", async (t) => {
  const { readData, request } = await buildFixture(t);
  for (const [kind, count] of [["cards", 112], ["machines", 123]]) {
    const rows = await readData(kind + ".json");
    assert.equal(rows.length, count);
    for (const { id, source } of rows) {
      const detail = kind + "/" + id;
      const [html, markdown] = await Promise.all(["html", "md"].map(async (format) => {
        const response = await request(detail + "." + format);
        assert.equal(response.status, 200, detail + "." + format);
        const body = await response.text();
        assert.ok(body.includes(source), id + " must retain its original source");
        return body;
      }));
      assertProfileFieldsAgree(html, markdown, id);
    }
  }
});

const factoryProfiles = [
  ["apple-mac-mini-m4-24gb-512gb", "MCYT4LL/A", "April 1, 2026", "Maximum continuous system power", "155 W", "Active cooling fan"],
  ["apple-mac-mini-m6-24gb-512gb", "MHQM4LL/A", "September 2026", "Maximum continuous system power", "155 W", "Active cooling fan"],
  ["nvidia-dgx-spark-128gb-4tb", "128 GB unified memory / 4 TB SSD", "NVIDIA Marketplace U.S.", "External power supply rating", "240 W", "Integrated thermal management system"],
];

function assertFactoryProfile(html, markdown, [id, configuration, locator, powerLabel, powerValue, cooling]) {
  assertProfileFieldsAgree(html, markdown, id);
  for (const body of [html, markdown]) {
    assert.match(body, /Complete factory configuration/);
    assert.ok(body.includes(configuration), id);
    assert.ok(body.includes(locator), id);
    assert.match(body, /System bill of materials/);
    assert.ok(body.includes(cooling), id);
    assert.match(body, /Runtime-usable GPU memory.*Unknown/);
    assert.match(body, /Measured system power.*Unavailable/);
    assert.ok(body.includes(powerLabel) && body.includes(powerValue), id);
    assert.match(body, /Untested in this release/);
  }
}

test("released factory profiles show sourced parts and documented power in both formats", async (t) => {
  const { read, request } = await buildFixture(t);
  assert.equal(JSON.parse(await read("manifest.json")).hardware.coverage.completeBuilds, 3);
  for (const profile of factoryProfiles) {
    const [html, markdown] = await Promise.all(["html", "md"].map(async ext => {
      const response = await request(`machines/${profile[0]}.${ext}`);
      assert.equal(response.status, 200);
      return response.text();
    }));
    assertFactoryProfile(html, markdown, profile);
    const fitPath = "/fit?machine=" + profile[0];
    if (profile[0] === "apple-mac-mini-m4-24gb-512gb") {
      assert.ok(html.includes('href="' + fitPath + '"'));
      assert.ok(markdown.includes("](<" + fitPath + ">)"));
      const request = new Request(host + fitPath);
      const env = { FASTEST_RELEASE_ORIGIN: "https://release.example.test" };
      const selection = goToFit({ request, env });
      assert.equal(selection.status, 307);
      assert.equal(selection.headers.get("location"), env.FASTEST_RELEASE_ORIGIN + fitPath);
      assert.equal(goToFit({ request, env: {} }).status, 404);
    } else {
      assert.ok(!html.includes(fitPath));
      assert.ok(!markdown.includes(fitPath));
    }
  }
});

test("a replacement release omits profiles whose required factory evidence was withdrawn", async (t) => {
  const source = "https://docs.nvidia.com/dgx/dgx-spark/hardware.html";
  const hardware = await readHardwareCatalog(here, value => value === source);
  const { read, readData, request } = await buildFixture(t, hardware);
  assert.equal(JSON.parse(await read("manifest.json")).hardware.coverage.completeBuilds, 2);
  const machines = await readData("machines.json");
  assert.ok(!JSON.stringify(machines).includes(source));
  for (const ext of ["html", "md"]) {
    assert.equal((await request("machines/nvidia-dgx-spark-128gb-4tb." + ext)).status, 404);
    const family = await request("machines/nvidia-dgx-spark." + ext);
    assert.equal(family.status, 200);
    assert.match(await family.text(), /64 GB or 128 GB/);
  }
});

test("source-backed GPU profiles distinguish a documented board from its GPU family", async (t) => {
  const { request } = await buildFixture(t);
  const board = "cards/asus-dual-rx9060xt-16g";
  const variant = "cards/amd-radeon-rx-9060-xt-16gb";
  for (const extension of ["html", "md"]) {
    const response = await request(`${board}.${extension}`);
    assert.equal(response.status, 200);
    const body = await response.text();
    assert.ok(body.includes("DUAL-RX9060XT-16G"));
    assert.ok(body.includes("16 GB GDDR6"));
    assert.ok(body.includes("Product images on ASUS"));
    assert.ok(body.includes("dual-rx9060xt-16g/techspec/"));
    assert.ok(body.includes(`${variant}.html`));

    const product = await (await request(`${variant}.${extension}`)).text();
    assert.ok(product.includes(`${board}.html`));
    assert.ok(product.includes("320 GB/s"));
    assert.match(product, /Exact memory variant/);

    const family = await (await request(`cards/amd-radeon-rx-9060-xt.${extension}`)).text();
    assert.match(family, /Multiple manufacturer configurations/);
    assert.doesNotMatch(family, /Selected GPU:|aria-current="page"/);
  }
});

test("GPU profiles highlight only identities with exact rated values", async (t) => {
  const { request } = await buildFixture(t);
  const html = await (await request("cards/amd-radeon-pro-w7800.html")).text();
  const markdown = await (await request("cards/amd-radeon-pro-w7800.md")).text();
  assert.match(html, /profile-chart-dot" href="[^"]*w7800.html" aria-current="page"/);
  assert.match(html, /32 GB · 576 GB\/s/);
  assert.match(html, /<meter[^>]+aria-label="Nominal capacity · 32 GB/);
  assert.match(html, /<meter[^>]+aria-label="Rated graphics power · 260 W/);
  assert.match(markdown, /Nominal capacity · 32 GB on the catalog scale/);
  assert.match(markdown, /Rated graphics power · 260 W on the catalog scale/);
  assert.match(markdown, /Selected GPU: 32 GB · Rated memory bandwidth \(GB\/s\): 576/);
  const ambiguous = await (await request("cards/nvidia-geforce-rtx-3060.html")).text();
  assert.match(ambiguous, /has no unambiguous pair of rated specifications/);
  assert.doesNotMatch(ambiguous, /profile-chart-dot"[^>]*aria-current/);
});

test("the offline catalog generates linked HTML and Markdown for every GPU", async (t) => {
  const output = await mkdtemp(join(tmpdir(), "fastest-local-catalog-"));
  t.after(() => rm(output, { recursive: true, force: true }));
  const hardware = await readHardwareCatalog(here);
  const release = await writeLocalCatalogProfiles(output, hardware, "Test license");
  for (const { id, source } of hardware.catalog.cards) {
    const root = join(output, "catalog", release, "cards", id);
    const [html, markdown] = await Promise.all(["html", "md"].map(ext => readFile(root + "." + ext, "utf8")));
    assert.ok(html.includes(source) && markdown.includes(source), id);
    assert.ok(html.includes(`href="${id}.md"`), id);
    assert.ok(html.includes("../../../../fastest-ai.html#catalog/cards"), id);
    assert.ok(html.includes("On-board memory") && markdown.includes("On-board memory"), id);
    assert.ok(html.includes("No approved observation is available") &&
      markdown.includes("No approved observation is available"), id);
    assertProfileFieldsAgree(html, markdown, id);
  }
});

test("the offline catalog writes ranked model pairs with relative companion and runtime links", async (t) => {
  const temporary = await mkdtemp(join(tmpdir(), "fastest-local-model-"));
  t.after(() => rm(temporary, { recursive: true, force: true }));
  const output = join(temporary, "local-catalog");
  const id = "Owner/Model.1";
  const release = await writeLocalCatalogProfiles(output, {
    snapshotId: "a".repeat(64),
    catalog: {
      models: [{
        id,
        source: "https://huggingface.co/" + id,
        detail: "<draft> & text",
        identity: { revision: "resolved", artifacts: [{
          repository: id, revision: "resolved", path: "Q4_K_M.gguf", sha256: "digest", format: "GGUF", license: "MIT",
        }] },
        discovery: { popular: { rank: 11, downloads: 900, parameters: 500_000_000, gated: true }, small: { rank: 4 } },
      }],
    },
    manifest: {},
    modelManifest: {
      inventory: 2, popular: 1, small: 1,
      discovery: { source: "https://huggingface.co/api/models", capturedAt: "2026-11-20T21:34:32+00:00" },
    },
    runtimes: [{ id: "llama.cpp", name: "llama.cpp", source: "https://example.test/llama.cpp", tag: "v1", published: "2026-11-20", workload: "Text", formats: "GGUF", backends: "CPU" }],
  }, "Test license");
  const root = join(output, "catalog", release);
  const files = ["html", "md"].map(ext => join(root, "models", id + "." + ext));
  const [html, markdown] = await Promise.all(files.map(file => readFile(file, "utf8")));
  assertProfileFieldsAgree(html, markdown, id);
  assert.match(html, /&lt;draft&gt; &amp; text/);
  assert.match(markdown, /\\<draft\\> & text/);
  assert.match(html, /<a href="Model\.1\.md">Markdown<\/a>/);
  assert.match(markdown, /\[HTML card\]\(Model\.1\.html\)/);
  assert.match(html, /<a href="\.\.\/\.\.\/\.\.\/\.\.\/\.\.\/fastest-ai\.html#catalog\/models">Models<\/a>/);
  assert.match(html, /<a href="\.\.\/\.\.\/runtimes\/llama\.cpp\.html">llama\.cpp<\/a>/);
  for (const link of ["../../manifest.json", "../../LICENSE.txt", "../../runtimes/llama.cpp.html"]) {
    assert.ok(html.includes(link) && markdown.includes(link), link);
    assert.ok(await readFile(join(dirname(files[0]), link), "utf8"));
  }
  for (const body of [html, markdown]) {
    assert.match(body, /Popular rank.*11/);
    assert.match(body, /Small rank.*4/);
    assert.match(body, /500,000,000/);
    assert.match(body, /Access approval/);
    assert.match(body, /https:\/\/huggingface\.co\/api\/models/);
  }
  const { models } = JSON.parse(await readFile(join(root, "manifest.json"), "utf8"));
  assert.deepEqual([models.inventory, models.profiles, models.popular, models.small], [2, 1, 1, 1]);
});

test("the offline catalog rejects repository IDs that escape the release layout", async (t) => {
  const output = await mkdtemp(join(tmpdir(), "fastest-local-model-path-"));
  t.after(() => rm(output, { recursive: true, force: true }));
  await assert.rejects(writeLocalCatalogProfiles(output, {
    snapshotId: "a".repeat(64), catalog: { models: [{ id: "Owner/../escape" }] },
  }, "Test license"), /Invalid local model identity/);
});

const testDatabase = process.env.FASTEST_TEST_DATABASE_URL;
test("the local PostgreSQL snapshot exports ranked repositories and complete factory profiles", { skip: !testDatabase }, async (t) => {
  const output = await mkdtemp(join(tmpdir(), "fastest-local-model-pg-"));
  t.after(() => rm(output, { recursive: true, force: true }));
  const hardware = await readHardwareCatalog(here);
  const imported = await importLocalCatalog(hardware, testDatabase);
  const replayed = await importLocalCatalog(hardware, testDatabase);
  assert.deepEqual(replayed, imported);
  const release = await writeLocalCatalogProfiles(output, replayed, replayed.modelLicenseNotice);
  const root = join(output, "catalog", release);
  const manifest = JSON.parse(await readFile(join(root, "manifest.json"), "utf8"));
  assert.equal(manifest.snapshotId, imported.snapshotId);
  assert.equal(manifest.hardware.coverage.completeBuilds, 3);
  for (const profile of factoryProfiles) {
    const [html, markdown] = await Promise.all(["html", "md"].map(ext =>
      readFile(join(root, "machines", profile[0] + "." + ext), "utf8")));
    assertFactoryProfile(html, markdown, profile);
  }
  assert.equal(manifest.models.inventory, 19_192);
  assert.equal(manifest.models.profiles, 300);
  assert.equal(manifest.models.popular, 300);
  assert.equal(manifest.models.small, 75);
  assert.equal(manifest.models.discovery.capturedAt, "2026-11-20T21:34:32+00:00");
  assert.match(await readFile(join(root, "LICENSE.txt"), "utf8"), /Copyright \(c\) 2026 Alex Jones/);
  for (const ext of ["html", "md"]) {
    const body = await readFile(join(root, "models/Qwen/Qwen2.5-0.5B-Instruct." + ext), "utf8");
    assert.match(body, /Popular rank.*11/);
    assert.match(body, /Small rank.*4/);
    assert.match(body, /7ae557604adf67be50417f59c2c2f167def9a775/);
    assert.match(body, /74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db/);
    await assert.rejects(readFile(join(root, "models/Corianas/1.3b." + ext), "utf8"), { code: "ENOENT" });
  }
});
