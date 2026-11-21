import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { copyFile, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { readCatalogModelFiles, writeCatalogRelease } from "./catalog-release-build.mjs";
import { withdrawnPublisherSource } from "./evidence-state.mjs";
import { readHardwareCatalog } from "./catalog-hardware-build.mjs";
import { writeLocalCatalogProfiles } from "./catalog-local-build.mjs";
import { importLocalCatalog, readPublishedCatalog } from "./catalog-pg.mjs";
import { renderTopologyReference } from "./wiki-release.mjs";
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

const recentModels = [
  ["thinkingmachines/Inkling-2-Mini", "ed40e7da625f594fc9c4990f5f66be24873c22d7", "26.4B total", "5.4B effective", "https://www.apache.org/licenses/LICENSE-2.0"],
  ["thinkingmachines/Inkling-2-Small", "885d78bfca61a7e9a498e33cfa7ad35850533b8c", "594B total", "17B active", "https://www.apache.org/licenses/LICENSE-2.0"],
  ["moonshotai/Kimi-K3.1-Pro", "d9e99b0792a5e93b78ea9bea62a68167e36ddd9e", "2.8T total", "104B activated",
    "https://huggingface.co/moonshotai/Kimi-K3.1-Pro/blob/d9e99b0792a5e93b78ea9bea62a68167e36ddd9e/LICENSE"],
  ["ibm-granite/granite-4.2-3b", "4e9c275e232f10211ec88644d106a1f6a1b60e06", "3B dense", "3.7B parameters",
    "https://www.apache.org/licenses/LICENSE-2.0", "Text"],
  ["mistralai/Mistral-Large-4-1T-A52B", "f12dabdc0c1e99e7f7924461a6f308859b05af4d", "1T total", "49B active per token",
    "https://huggingface.co/mistralai/Mistral-Large-4-1T-A52B/blob/f12dabdc0c1e99e7f7924461a6f308859b05af4d/LICENSE",
    "Text, image", ["52B including embeddings and output layers", "Mistral Ecosystem Open-Weight License",
      "Model-as-a-Service businesses need a separate commercial license",
      "d242ebedb53ffd7e26c220e3305665ca47e4e5267fa62ff4cdeb3953b8353c78"]],
];

const gemmaAndAreteProfiles = [
  {
    id: "google/gemma-4-E2B-it",
    revision: "4adf15748de9e1a0097b6274cee9c15836c41c37",
    digest: "3e0608a6be80e3eb040a5aa6c76707809503deb85be6360184a118fb6156526c",
    parameters: "2.3B effective parameters and 5.1B total",
    inputs: "Text, image, audio",
    benchmark: "LiveCodeBench v6",
    score: "44%",
    heading: "benchmark-results",
    line: 92,
  },
  {
    id: "google/gemma-4-E4B-it",
    revision: "4ecc2ba63bcac23ba4a767fc87025b1450f84c9c",
    digest: "b21e4f69614ccd77baa2f3797d05311040dee07b989cb9f0d25111aa4b605b2c",
    parameters: "4.5B effective parameters and 8B total",
    inputs: "Text, image, audio",
    benchmark: "LiveCodeBench v6",
    score: "52%",
    heading: "benchmark-results",
    line: 92,
  },
  {
    id: "NousResearch/Arete-27B",
    revision: "108f0afbdcfaa1ceeda4a635004304dfff6d4da2",
    digest: "c22421177d0e1f47bc0d9428b672c78b0635778025350ef694f113b2bfb7fef1",
    parameters: "27B parameter scale",
    inputs: "Text",
    benchmark: "Terminal-Bench v2.1",
    score: "70%",
    heading: "general-and-agentic-capabilities",
    line: 155,
  },
];

function assertGemmaOrAreteProfile(body, { id, revision, digest, parameters, inputs, benchmark, score, heading, line }) {
  const card = `https://huggingface.co/${id}/blob/${revision}/README.md`;
  for (const value of [id, card, digest, parameters, "Apache License 2.0", "https://www.apache.org/licenses/LICENSE-2.0",
    "Input modalities", inputs, "Output modalities", "Publisher-reported benchmark results", benchmark, score,
    "Unreported in model card", "Execution hardware", "Unknown", `${card}#${heading}`, `${card}#L${line}`]) {
    assert.ok(body.includes(value), `${id} lacks ${value}`);
  }
  assert.doesNotMatch(body, /Small rank|[\d.]+B active/);
}

function assertReviewedModel(body, [id, revision, total, active, license, inputs = "Text, image", extra = []]) {
  for (const value of [id, `https://huggingface.co/${id}/blob/${revision}/README.md`, total, active, license,
    "Input modalities", inputs, "Output modalities", "2026-11-21", ...extra]) {
    assert.ok(body.includes(value), `${id} lacks ${value}`);
  }
  assert.doesNotMatch(body, /Popular rank|Small rank|Downloads in the Hub snapshot|\/blob\/main\//);
}

const publisherScores = new Map([
  ["thinkingmachines/Inkling-2-Mini", ["48.2%", "inkling-2-mini"]],
  ["thinkingmachines/Inkling-2-Small", ["72.1%", "inkling-2-small"]],
]);

function assertPublisherScore(body, [id, revision]) {
  assert.doesNotMatch(body, /Artificial Analysis|Terminal.Bench|BrowseComp/);
  if (id === "ibm-granite/granite-4.2-3b") {
    for (const value of ["Publisher-reported benchmark results", "LiveCodeBench v6", "69.71% pass@1",
      "NeMo Evaluator SDK", "Unknown", "8f22ddce440f0c15ecb58fc9f8501b882baf5f2b7ab0d13872fe77d88c1ad792",
      "https://huggingface.co/blog/ibm-granite/granite-4-2#results",
      `https://huggingface.co/${id}/blob/${revision}/README.md#L279`]) {
      assert.ok(body.includes(value), `${id} lacks ${value}`);
    }
    return;
  }
  if (!publisherScores.has(id)) {
    assert.doesNotMatch(body, /Publisher-reported benchmark results/);
    return;
  }
  const [score, slug] = publisherScores.get(id);
  for (const value of ["Publisher-reported benchmark results", "DeepSWE v1.1", score,
    "mini-swe-agent v2.4.6", "Execution hardware", "Unknown",
    `https://thinkingmachines.ai/news/${slug}/`,
    `https://huggingface.co/${id}/blob/${revision}/README.md#L124`]) {
    assert.ok(body.includes(value), `${id} lacks ${value}`);
  }
}

test("reviewed model cards retain pinned sources and llmfit counts", async (t) => {
  const { read, request } = await buildFixture(t);
  const manifest = JSON.parse(await read("manifest.json"));
  assert.equal(manifest.coverage.publishedRows, 19_192);
  for (const model of recentModels) {
    for (const ext of ["html", "md"]) {
      const response = await request("models/" + model[0] + "." + ext);
      assert.equal(response.status, 200);
      const body = await response.text();
      assertReviewedModel(body, model);
      assertPublisherScore(body, model);
    }
  }
  assert.equal(manifest.supplement.repositories, 8);
  assert.equal(manifest.supplement.publisherResults, 6);
  assert.match(manifest.supplement.sha256, /^[a-f0-9]{64}$/);
});

test("compact Gemma and Arete cards publish selected scores from their own pinned model cards", async (t) => {
  const { request } = await buildFixture(t);
  for (const model of gemmaAndAreteProfiles) {
    for (const ext of ["html", "md"]) {
      const response = await request(`models/${model.id}.${ext}`);
      assert.equal(response.status, 200);
      assertGemmaOrAreteProfile(await response.text(), model);
    }
  }
});

test("rebuilding a withdrawn publisher evaluation changes the catalog pin and preserves other model metadata", async (t) => {
  const output = await mkdtemp(join(tmpdir(), "fastest-publisher-fixture-"));
  t.after(() => rm(output, { recursive: true, force: true }));
  for (const name of ["catalog-models.json", "catalog-identities.json", "model-discovery.json"]) {
    await copyFile(join(here, name), join(output, name));
  }
  const source = "https://publisher.test/withdrawn/";
  const retainedSource = "https://publisher.test/retained/";
  const original = JSON.parse(await readFile(join(here, "catalog-model-supplements.json"), "utf8"));
  const example = original.models[0];
  example.id = "example/fixture-model";
  example.publisherEvaluations = [
    { ...example.publisherEvaluations[0], source, scorePercent: 61.1 },
    { ...example.publisherEvaluations[0], source: retainedSource, scorePercent: 62.2 },
  ];
  await writeFile(join(output, "catalog-model-supplements.json"), JSON.stringify(original));
  const before = await readCatalogModelFiles(output);
  const after = await readCatalogModelFiles(output, withdrawnPublisherSource({
    publisherWithdrawals: [{ sourceSha256: createHash("sha256").update(source).digest("hex") }],
  }));
  const release = (models) => writeCatalogRelease(here, output, undefined, undefined, models);
  const beforePin = await release(before);
  const afterPin = await release(after);
  assert.notEqual(beforePin, afterPin);
  const shard = JSON.parse(await readFile(join(output, "catalog-data", afterPin, "ex.json"), "utf8"));
  const { supplemental, ...metadata } = shard.find(({ id }) => id === example.id);
  const { publisherEvaluations, ...details } = supplemental;
  assert.match(metadata.source, /huggingface\.co\/example\/fixture-model/);
  assert.equal(details.revision, example.revision);
  assert.deepEqual(publisherEvaluations.map(({ source, scorePercent }) => [source, scorePercent]), [[retainedSource, 62.2]]);
});

test("a publisher score pinned to a different model-card revision cannot enter the catalog", async (t) => {
  const output = await mkdtemp(join(tmpdir(), "fastest-catalog-stale-score-"));
  t.after(() => rm(output, { recursive: true, force: true }));
  const seed = "catalog-model-supplements.json";
  const supplement = JSON.parse(await readFile(join(here, seed), "utf8"));
  const [mini] = supplement.models;
  mini.revision = "b".repeat(40);
  await Promise.all([
    ...["catalog-models.json", "catalog-identities.json", "model-discovery.json"].map((name) =>
      copyFile(join(here, name), join(output, name))),
    writeFile(join(output, seed), JSON.stringify(supplement)),
  ]);
  await assert.rejects(readCatalogModelFiles(output), /Publisher evaluation .*does not match.*Inkling-2-Mini/);
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
  const { readData, request } = await buildFixture(t);
  const directory = await readData("runtimes.json");
  for (const [id, releaseUrl] of [
    ["mlx-lm", "https://github.com/ml-explore/mlx-lm/releases/tag/v0.32.2"],
    ["openvino", "https://github.com/openvinotoolkit/openvino.genai/releases/tag/2026.4.1.0"],
    ["aiter", "https://github.com/ROCm/aiter/releases/tag/v0.1.29.post1"],
  ]) {
    assert.equal(directory.find((row) => row.id === id)?.releaseUrl, releaseUrl);
  }
  for (const [runtime, tag, repository, format] of [
    ["llama.cpp", "v1.0.0", "ggml-org/llama.cpp", "GGUF"],
    ["sglang", "v0.5.23", "sgl-project/sglang", "Safetensors"],
    ["vllm", "v0.34.0", "vllm-project/vllm", "Safetensors"],
    ["ollama", "v0.40.16", "ollama/ollama", "GGUF"],
    ["mlx-lm", "v0.32.2", "ml-explore/mlx-lm", "MLX"],
    ["openvino", "2026.4.1.0", "openvinotoolkit/openvino.genai", "OpenVINO"],
    ["strata", "v0.2.17", "Niko1221/Strata", "GGUF"],
    ["project-maya", "v1.1.70", "mw00/project-maya", "GGUF"],
    ["mnn", "3.6.2", "alibaba/MNN", "MNN"],
    ["mlx-swift-lm", "3.33.0", "ml-explore/mlx-swift-lm", "MLX"],
    ["ctranslate2", "v4.9.0", "OpenNMT/CTranslate2", "CTranslate2"],
    ["whisper.cpp", "v1.9.5", "ggml-org/whisper.cpp", "ggml"],
    ["open-webui", "v0.13.4", "open-webui/open-webui", "OpenAI-compatible"],
    ["aiter", "v0.1.29.post1", "ROCm/aiter", "Framework-managed"],
    ["exo", "v1.0.71", "exo-explore/exo", "MLX"],
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
  assert.equal(hardware.asOf, "2026-11-22");
  assert.equal(hardware.coverage.memoryModifiedCards, 16);
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
  for (const [, fields] of html.matchAll(/<dl class="profile-fields">([^]*?)<\/dl>/g)) {
    for (const [, label, href, text] of fields.matchAll(/<dt>(.*?)<\/dt><dd>(?:<a href="([^"]*)">)?([^<]*)(?:<\/a>)?<\/dd>/g)) {
      const value = unescape(text);
      const expected = href ? `[${value}](<${unescape(href)}>)` : value;
      assert.ok(plainMarkdown.includes(`**${unescape(label)}** — ${expected}\n`), `${id}: ${unescape(label)}`);
    }
  }
}

test("the Radeon RX 9060 XT 8 GB reference and ASUS board retain separate evidence", async (t) => {
  const { request } = await buildFixture(t);
  const referenceId = "amd-radeon-rx-9060-xt-8gb";
  const boardId = "asus-dual-rx9060xt-8g";
  for (const [id, expected] of [
    [referenceId, ["8 GB GDDR6", "Up to 320 GB/s", "AMD artist render", "amd-radeon-rx-9060xt-8gb.html"]],
    [boardId, ["8 GB GDDR6", "202 × 120 × 49 mm", "DUAL-RX9060XT-8G", "Board-partner SKU", "Product images on ASUS"]],
  ]) {
    const [html, markdown] = await Promise.all(["html", "md"].map(async (extension) => {
      const response = await request(`cards/${id}.${extension}`);
      assert.equal(response.status, 200, id);
      return response.text();
    }));
    assertProfileFieldsAgree(html, markdown, id);
    for (const body of [html, markdown]) {
      for (const fact of expected) assert.ok(body.includes(fact), `${id} lacks ${fact}`);
      assert.match(body, /Runtime-usable memory.*Unknown/);
      assert.match(body, /Untested in this release/);
    }
    if (id === boardId) {
      assert.match(html, /<dt>Rated graphics power \(W\)<\/dt><dd>Unknown<\/dd>/);
      assert.ok(html.includes(`cards/${referenceId}.html`));
    } else {
      assert.match(html, /<dt>Rated graphics power \(W\)<\/dt><dd><a href="[^"]+">150<\/a><\/dd>/);
    }
  }
});

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

const exact5060TiBoards = [
  {
    id: "colorful-igame-rtx5060ti-mini-w-oc-8gb",
    designation: "iGame GeForce RTX 5060 Ti Mini W OC 8GB",
    source: "https://www.colorful.cn/home/new?id=09e8d6a3-f28d-419e-bc68-2b25cbe99968",
    galleryLabel: "White Mini series images on Colorful",
    facts: ["8 GB", "Single fan", "White Mini series"],
  },
  {
    id: "asus-t1-rtx5060ti-o8g-gaming",
    designation: "T1-RTX5060TI-O8G-GAMING",
    source: "https://www.asus.com/ca-en/motherboards-components/graphics-cards/asus/t1-rtx5060ti-o8g-gaming/techspec/",
    galleryLabel: "T1 product images on ASUS",
    facts: ["8 GB GDDR7", "269 × 120 × 50 mm", "2662 MHz", "1 × 8-pin"],
  },
  {
    id: "pny-vcg5060t8dfxpb1-o",
    designation: "VCG5060T8DFXPB1-O",
    source: "https://www.pny.com/File%20Library/Company/Support/Product%20Brochures/GeForce%20Graphics/English/rtx-5060-ti-8gb-dual-fan-oc-brochure.pdf",
    gallerySource: "https://www.pny.com/geforce-rtx-5060-ti-8gb-models?sku=VCG5060T8DFXPB1-O",
    galleryLabel: "Product gallery on PNY",
    facts: ["8 GB GDDR7", "2692 MHz", "751492795652", "245 × 120 × 39.9 mm", "1 × 8-pin", "448 GB/s"],
    power: "180",
  },
  {
    id: "pny-vcg5060t16dfxpb1-o",
    designation: "VCG5060T16DFXPB1-O",
    source: "https://www.pny.com/File%20Library/Company/Support/Product%20Brochures/GeForce%20Graphics/English/rtx-5060-ti-16gb-dual-fan-oc-brochure.pdf",
    gallerySource: "https://www.pny.com/geforce-rtx-5060-ti-16gb-models?sku=VCG5060T16DFXPB1-O",
    galleryLabel: "Product gallery on PNY",
    facts: ["16 GB GDDR7", "2692 MHz", "751492795072", "245 × 120 × 39.9 mm", "1 × 8-pin", "448 GB/s"],
    parent: "nvidia-geforce-rtx-5060-ti-16gb",
    power: "180",
  },
];

function assertExact5060TiBoard(html, markdown, {
  id, designation, source, gallerySource, galleryLabel, facts,
  parent = "nvidia-geforce-rtx-5060-ti", power = "Unknown",
}) {
  for (const body of [html, markdown]) {
    for (const value of [designation, source, gallerySource, galleryLabel, "Board-partner SKU", ...facts].filter(Boolean)) {
      assert.ok(body.includes(value), `${id} lacks ${value}`);
    }
    assert.ok(body.includes(`cards/${parent}.html`));
    if (parent.endsWith("-16gb")) assert.doesNotMatch(body, /8 GB GDDR7|VCG5060T8DFXPB1-O/);
    else assert.doesNotMatch(body, /16 GB GDDR7|DUAL-RTX5060TI-16G|VCG5060T16DFXPB1-O/);
    assert.match(body, /Runtime-usable memory.*Unknown/);
    assert.match(body, /Untested in this release/);
    assert.match(body, /No approved observation is available in this catalog snapshot/);
  }
  assert.match(html, new RegExp(String.raw`<dt>Rated graphics power \(W\)</dt><dd>(?:<a href="[^"]*">)?${power}(?:</a>)?</dd>`));
  assertProfileFieldsAgree(html, markdown, id);
}

test("released RTX 5060 Ti boards use exact manufacturer sources and stay distinct", async (t) => {
  const { request } = await buildFixture(t);
  for (const board of exact5060TiBoards) {
    const [html, markdown] = await Promise.all(["html", "md"].map(async (format) => {
      const response = await request(`cards/${board.id}.${format}`);
      assert.equal(response.status, 200, board.id);
      return response.text();
    }));
    assertExact5060TiBoard(html, markdown, board);
  }
  for (const { id, parent = "nvidia-geforce-rtx-5060-ti" } of exact5060TiBoards) {
    const family = await request(`cards/${parent}.html`).then(response => response.text());
    assert.ok(family.includes(`cards/${id}.html`));
  }
  const family = await request("cards/nvidia-geforce-rtx-5060-ti.html").then(response => response.text());
  assert.ok(family.includes("cards/nvidia-geforce-rtx-5060-ti-16gb.html"));
});

test("withdrawing the PNY 8 GB brochure removes its exact board from the replacement release", async (t) => {
  const { id, source } = exact5060TiBoards.find(board => board.id === "pny-vcg5060t8dfxpb1-o");
  const hardware = await readHardwareCatalog(here, value => value === source);
  const { readData, request } = await buildFixture(t, hardware);
  const rows = await readData("cards.json");
  assert.ok(!rows.some(row => row.id === id));
  for (const ext of ["html", "md"]) {
    assert.equal((await request(`cards/${id}.${ext}`)).status, 404);
    assert.equal((await request(`cards/pny-vcg5060t16dfxpb1-o.${ext}`)).status, 200);
    const family = await request(`cards/nvidia-geforce-rtx-5060-ti.${ext}`).then(response => response.text());
    assert.ok(!family.includes(`cards/${id}.html`));
  }
});

const tinyboxId = "tinybox-red-4x-mi300x-batch-2";
const tinyboxSource = "https://tinycorp.myshopify.com/products/tinybox-red-4xmi300x";

function assertTinyboxProfile(html, markdown) {
  assertProfileFieldsAgree(html, markdown, tinyboxId);
  for (const body of [html, markdown]) {
    for (const fact of [tinyboxSource, "Batch 2", "192 GB DDR5", "768 GB aggregate installed", "AMD Genoa",
      "refurbished AMD Instinct MI300X", "custom tiny corp carrier", "PCIe 5.0 x16", "No xGMI", "Untested in this release"]) {
      assert.ok(body.includes(fact), fact);
    }
    assert.match(body, /Runtime-usable GPU memory.*Unknown/);
    assert.match(body, /Measured system power.*Unavailable/);
    assert.match(body, /Manufacturer product gallery/);
    assert.doesNotMatch(body, /None \(integrated GPU|89,000|60,000/);
  }
}

test("the released tinybox profile separates installed GPU memory and documented connections from measured evidence", async (t) => {
  const { request } = await buildFixture(t);
  const [html, markdown] = await Promise.all(["html", "md"].map(async ext => {
    const response = await request(`machines/${tinyboxId}.${ext}`);
    assert.equal(response.status, 200);
    return response.text();
  }));
  assertTinyboxProfile(html, markdown);
  const gpu = await request("cards/amd-instinct-mi300x.html").then(response => response.text());
  assert.ok(gpu.includes(`machines/${tinyboxId}.html`));

  const withdrawn = await readHardwareCatalog(here, value => value === tinyboxSource);
  const filtered = await buildFixture(t, withdrawn);
  assert.equal((await filtered.request(`machines/${tinyboxId}.html`)).status, 404);
  const filteredGpu = await filtered.request("cards/amd-instinct-mi300x.html").then(response => response.text());
  assert.ok(!filteredGpu.includes(tinyboxId));
});

test("every released hardware row resolves in both formats", async (t) => {
  const { read, readData, request } = await buildFixture(t);
  const { hardware: { coverage } } = JSON.parse(await read("manifest.json"));
  for (const [kind, count] of [["cards", coverage.cards], ["machines", 125 + coverage.creatorBuilds]]) {
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

test("released modified GPU profiles expose seller and lab evidence in both formats", async (t) => {
  const { request } = await buildFixture(t);
  for (const [id, fields] of [
    ["nvidia-geforce-rtx-4090-modified-48gb", ["48 GB", "Seller listing", "Seller service", "Advertised board capacity"]],
    ["nvidia-cmp-170hx-modified-80gb", ["80 GB", "Lab demonstration", "Reported tested framebuffer", "Synthetic memory reads and writes"]],
  ]) {
    const [html, markdown] = await Promise.all(["html", "md"].map(async extension => {
      const response = await request(`cards/${id}.${extension}`);
      assert.equal(response.status, 200);
      return response.text();
    }));
    for (const body of [html, markdown]) {
      for (const field of fields) assert.ok(body.includes(field), field);
      assert.match(body, /Runtime-usable memory[^\n]*Unknown/);
      assert.match(body, /GPU position by rated specifications/);
      assert.match(body, /has no unambiguous pair of rated specifications/);
      assert.doesNotMatch(body, /Selected GPU:|<tr\b[^>]*aria-current="page"|class="coordinate-mark"[^>]*aria-current="page"/);
    }
    assertProfileFieldsAgree(html, markdown, id);
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
  assert.equal(JSON.parse(await read("manifest.json")).hardware.coverage.completeBuilds, 4);
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
  assert.equal(JSON.parse(await read("manifest.json")).hardware.coverage.completeBuilds, 3);
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
    assert.doesNotMatch(family, /Selected GPU:|<tr\b[^>]*aria-current="page"|class="coordinate-mark"[^>]*aria-current="page"/);
  }
});

test("GPU profiles highlight only identities with exact rated values", async (t) => {
  const { request } = await buildFixture(t);
  const html = await (await request("cards/amd-radeon-pro-w7800.html")).text();
  const markdown = await (await request("cards/amd-radeon-pro-w7800.md")).text();
  assert.match(html, /coordinate-mark" href="[^"]*w7800.html" aria-current="page"/);
  assert.match(html, /32 GB · 576 GB\/s/);
  assert.match(html, /<meter[^>]+aria-label="Nominal capacity · 32 GB/);
  assert.match(html, /<meter[^>]+aria-label="Rated graphics power · 260 W/);
  assert.match(markdown, /Nominal capacity · 32 GB on the catalog scale/);
  assert.match(markdown, /Rated graphics power · 260 W on the catalog scale/);
  assert.match(markdown, /Selected GPU: AMD Radeon PRO W7800 · 32 GB · 576 GB\/s/);
  const ambiguous = await (await request("cards/nvidia-geforce-rtx-3060.html")).text();
  assert.match(ambiguous, /has no unambiguous pair of rated specifications/);
  assert.doesNotMatch(ambiguous, /coordinate-mark"[^>]*aria-current/);
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

test("offline machine profiles link to the exact topology revision in the standalone app", async (t) => {
  const temporary = await mkdtemp(join(tmpdir(), "fastest-local-topology-"));
  t.after(() => rm(temporary, { recursive: true, force: true }));
  const output = join(temporary, "local-catalog");
  const hardware = await readHardwareCatalog(here);
  const id = "V021-HP-C001";
  const revision = "topology-" + "a".repeat(64);
  const release = await writeLocalCatalogProfiles(output, {
    ...hardware, topologies: [{ id, revision }],
  }, "Test license");
  const machines = join(output, "catalog", release, "machines");
  const href = "../../../../fastest-ai.html#wiki/gpu-topology/" + revision;
  const [html, markdown] = await Promise.all(["html", "md"].map(ext => readFile(join(machines, id + "." + ext), "utf8")));
  assert.ok(html.includes(`href="${href}"`));
  assert.ok(markdown.includes(`[Explore this configuration](<${href}>)`));
  assertProfileFieldsAgree(html, markdown, id);
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
  const mnn = await readFile(join(root, "runtimes/mnn.md"), "utf8");
  assert.match(mnn, /https:\/\/github\.com\/alibaba\/MNN\/releases\/tag\/3\.6\.2/);
  assert.equal(manifest.hardware.coverage.completeBuilds, 4);
  assert.equal(manifest.hardware.coverage.cardsWithSpecificVendorSpecs, 127);
  for (const [id, source, fact, parent] of [
    ["nvidia-h200-nvl", "https://www.nvidia.com/en-us/data-center/h200/", "Up to 600 W (configurable)", "nvidia-h200"],
    ["intel-arc-a770-8gb", "intel-arc-a770-graphics-8gb/specifications.html", "512 GB/s", "intel-arc-a770"],
    ["asrock-b60-ct-24g", "Intel%20Arc%20Pro%20B60%20Creator%2024GB/index.asp", "B60 CT 24G", "intel-arc-pro-b60"],
    ["sparkle-sbp60w-24g", "sparkle.com.tw/files/20251230103738615.pdf", "SBP60W-24G", "intel-arc-pro-b60"],
    ["asus-dual-rx9060xt-8g", "dual-rx9060xt-8g/techspec/", "202 × 120 × 49 mm", "amd-radeon-rx-9060-xt-8gb"],
  ]) {
    const [html, markdown] = await Promise.all(["html", "md"].map(ext =>
      readFile(join(root, "cards", id + "." + ext), "utf8")));
    assertProfileFieldsAgree(html, markdown, id);
    for (const body of [html, markdown]) {
      assert.ok(body.includes(source) && body.includes(fact) && body.includes(`cards/${parent}.html`), id);
    }
  }
  for (const profile of factoryProfiles) {
    const [html, markdown] = await Promise.all(["html", "md"].map(ext =>
      readFile(join(root, "machines", profile[0] + "." + ext), "utf8")));
    assertFactoryProfile(html, markdown, profile);
  }
  for (const board of exact5060TiBoards) {
    const [html, markdown] = await Promise.all(["html", "md"].map(ext =>
      readFile(join(root, "cards", board.id + "." + ext), "utf8")));
    assertExact5060TiBoard(html, markdown, board);
  }
  assert.equal(manifest.models.inventory, 19_192);
  assert.equal(manifest.models.profiles, 308);
  assert.equal(manifest.models.supplement.repositories, 8);
  assert.equal(manifest.models.popular, 300);
  assert.equal(manifest.models.small, 75);
  assert.equal(manifest.models.discovery.capturedAt, "2026-11-20T21:34:32+00:00");
  assert.match(await readFile(join(root, "LICENSE.txt"), "utf8"), /Copyright \(c\) 2026 Alex Jones/);
  const published = readPublishedCatalog(testDatabase, imported.snapshotId);
  const photoCard = hardware.catalog.cards.find(({ id }) => id === "nvidia-geforce-rtx-5090");
  assert.deepEqual(published.hardware.catalog.cards.find(({ id }) => id === photoCard.id).photos, photoCard.photos);
  const [photoHtml, photoMarkdown] = await Promise.all(["html", "md"].map(ext =>
    readFile(join(root, "cards", photoCard.id + "." + ext), "utf8")));
  for (const { source, licenseUrl, alt } of photoCard.photos) {
    assert.ok(photoHtml.includes(source) && photoHtml.includes(licenseUrl) && photoHtml.includes(alt));
    assert.ok(photoMarkdown.includes(source) && photoMarkdown.includes(licenseUrl) && photoMarkdown.includes(alt));
  }
  assert.equal((photoHtml.match(/data:image\/jpeg;base64,/g) ?? []).length, photoCard.photos.length);
  const modified = published.hardware.catalog.cards.find(({ id }) => id === "nvidia-geforce-rtx-4090-modified-48gb");
  assert.equal(modified.parent, "nvidia-geforce-rtx-4090");
  assert.equal(modified.modification.capacityGb, 48);
  assert.equal(modified.modification.evidence[0].kind, "Seller listing");
  assert.equal(modified.vendorSpec, null);
  const topology = published.topologies.find(({ id }) => id === tinyboxId);
  assert.match(topology?.revision ?? "", /^topology-[a-f0-9]{64}$/);
  assert.deepEqual(topology.devices.map(({ slot, card }) => [slot, card]), [1, 2, 3, 4].map(slot => [slot, "amd-instinct-mi300x"]));
  assert.deepEqual(topology.hosts.map(({ slot }) => slot), [5]);
  assert.deepEqual(topology.links.map(({ slots, label, source }) => [slots, label, source]),
    [1, 2, 3, 4].map(slot => [[5, slot], "PCIe 5.0 x16", tinyboxSource]));
  assert.equal(topology.activeCount, undefined);
  for (const format of ["html", "md"]) {
    const staticTopology = renderTopologyReference(format, [{ label: "tinybox", report: topology }]);
    for (const slot of [1, 2, 3, 4]) {
      assert.ok(staticTopology.includes(`PCIe 5.0 x16 (Host system ↔ Card ${slot})`));
    }
    assert.ok(staticTopology.includes("#wiki/gpu-topology/" + topology.revision));
  }
  const tinyboxPair = await Promise.all(["html", "md"].map(ext =>
    readFile(join(root, "machines", tinyboxId + "." + ext), "utf8")));
  assertTinyboxProfile(...tinyboxPair);
  for (const body of tinyboxPair) {
    assert.ok(body.includes("../../../../fastest-ai.html#wiki/gpu-topology/" + topology.revision));
  }
  const filteredHardware = await readHardwareCatalog(here, value => value === tinyboxSource);
  const filtered = await importLocalCatalog(filteredHardware, testDatabase);
  assert.ok(!filtered.topologies.some(({ id }) => id === tinyboxId));
  assert.ok(!filtered.catalog.machines.some(({ id }) => id === tinyboxId));
  for (const { id, designation, source, parent = "nvidia-geforce-rtx-5060-ti" } of exact5060TiBoards) {
    const board = published.hardware.catalog.cards.find(row => row.id === id);
    assert.equal(board?.parent, parent);
    assert.equal(board.variant, designation);
    assert.equal(board.vendorSpec.designation, designation);
    assert.equal(board.vendorSpec.source, source);
  }
  assert.equal(published.source.models.length, 19_192);
  assert.deepEqual(published.source.models.find(({ id }) => id === "ibm-granite/granite-4.2-3b"),
    JSON.parse(await readFile(join(here, "catalog-models.json"), "utf8")).models
      .find(({ id }) => id === "ibm-granite/granite-4.2-3b"));
  assert.deepEqual(published.supplementalModels.map(({ id }) => id).sort(),
    [...recentModels.map(([id]) => id), ...gemmaAndAreteProfiles.map(({ id }) => id)].sort());
  for (const model of recentModels) {
    const [html, markdown] = await Promise.all(["html", "md"].map(ext =>
      readFile(join(root, "models", model[0] + "." + ext), "utf8")));
    assertReviewedModel(html, model);
    assertReviewedModel(markdown, model);
    assertPublisherScore(html, model);
    assertPublisherScore(markdown, model);
    assertProfileFieldsAgree(html, markdown, model[0]);
  }
  for (const profile of gemmaAndAreteProfiles) {
    const [html, markdown] = await Promise.all(["html", "md"].map(ext =>
      readFile(join(root, "models", profile.id + "." + ext), "utf8")));
    assertGemmaOrAreteProfile(html, profile);
    assertGemmaOrAreteProfile(markdown, profile);
    assertProfileFieldsAgree(html, markdown, profile.id);
  }
  for (const ext of ["html", "md"]) {
    const body = await readFile(join(root, "models/Qwen/Qwen2.5-0.5B-Instruct." + ext), "utf8");
    assert.match(body, /Popular rank.*11/);
    assert.match(body, /Small rank.*4/);
    assert.match(body, /7ae557604adf67be50417f59c2c2f167def9a775/);
    assert.match(body, /74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db/);
    await assert.rejects(readFile(join(root, "models/Corianas/1.3b." + ext), "utf8"), { code: "ENOENT" });
  }
});
