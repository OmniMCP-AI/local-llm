import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { writeCatalogRelease } from "./catalog-release-build.mjs";
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
  assert.equal(coverage.exactArtifacts, 2);

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
