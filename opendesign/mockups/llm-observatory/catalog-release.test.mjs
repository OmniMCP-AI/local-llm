import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { writeCatalogRelease } from "./catalog-release-build.mjs";
import { readHardwareCatalog } from "./catalog-hardware-build.mjs";
import { writeLocalHardwareProfiles } from "./catalog-local-build.mjs";
import { onRequestGet } from "./functions/catalog/[release]/[[path]].js";

const here = dirname(fileURLToPath(import.meta.url));
const host = "https://example.test";

async function buildFixture(t) {
  const output = await mkdtemp(join(tmpdir(), "fastest-catalog-"));
  t.after(() => rm(output, { recursive: true, force: true }));
  const release = await writeCatalogRelease(here, output);

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
  assert.equal(hardware.coverage.cards, 104);
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

test("every released hardware row resolves in both formats", async (t) => {
  const { readData, request } = await buildFixture(t);
  for (const [kind, count] of [["cards", 104], ["machines", 120]]) {
    const rows = await readData(kind + ".json");
    assert.equal(rows.length, count);
    for (const { id, source } of rows) {
      const detail = kind + "/" + id;
      for (const format of ["html", "md"]) {
        const response = await request(detail + "." + format);
        assert.equal(response.status, 200, detail + "." + format);
        assert.ok((await response.text()).includes(source), id + " must retain its original source");
      }
    }
  }
});

test("GPU profiles highlight only identities with exact rated values", async (t) => {
  const { request } = await buildFixture(t);
  const html = await (await request("cards/amd-radeon-pro-w7800.html")).text();
  const markdown = await (await request("cards/amd-radeon-pro-w7800.md")).text();
  assert.match(html, /profile-chart-dot" href="[^"]*w7800.html" aria-current="page"/);
  assert.match(html, /32 GB · 576 GB\/s/);
  assert.match(markdown, /Selected GPU: 32 GB · Rated memory bandwidth \(GB\/s\): 576/);
  const ambiguous = await (await request("cards/nvidia-geforce-rtx-3060.html")).text();
  assert.match(ambiguous, /has no unambiguous pair of rated specifications/);
  assert.doesNotMatch(ambiguous, /profile-chart-dot"[^>]*aria-current/);
});

test("the offline catalog generates linked HTML and Markdown for every GPU", async (t) => {
  const output = await mkdtemp(join(tmpdir(), "fastest-local-catalog-"));
  t.after(() => rm(output, { recursive: true, force: true }));
  const hardware = await readHardwareCatalog(here);
  const release = await writeLocalHardwareProfiles(output, hardware, "Test license");
  for (const { id, source } of hardware.catalog.cards) {
    const root = join(output, "catalog", release, "cards", id);
    const [html, markdown] = await Promise.all(["html", "md"].map(ext => readFile(root + "." + ext, "utf8")));
    assert.ok(html.includes(source) && markdown.includes(source), id);
    assert.ok(html.includes(`href="${id}.md"`), id);
    assert.ok(html.includes("../../../../fastest-ai.html#catalog/cards"), id);
    assert.ok(html.includes("On-board memory") && markdown.includes("On-board memory"), id);
  }
});
