import assert from "node:assert/strict";
import test from "node:test";
import { readHardwareCatalog } from "./catalog-hardware-build.mjs";
import { fileURLToPath } from "node:url";
import reports from "./catalog-topology.json" with { type: "json" };
import hardware from "./catalog-hardware-sources.json" with { type: "json" };
import { cardPhotoExample, draftFitEstimate, draftFitRequest, fitScenario, topologyPresets, topologyView } from "./topology.mjs";
import { renderTopologyReference } from "./wiki-release.mjs";

const { catalog } = await readHardwareCatalog(fileURLToPath(new URL(".", import.meta.url)));
test("released presets switch slots and preserve per-device memory provenance", () => {
  const layouts = topologyPresets.map(({ report }) => topologyView(report, {}));
  assert.deepEqual(layouts.map(({ installedCount }) => installedCount), [1, 2, 4, 2]);
  assert.deepEqual(layouts.map(({ activeCount }) => activeCount), [1, null, null, null]);
  assert.deepEqual(layouts[1].parts.map(({ photo, memory }) => [photo, memory]), [["rtx-3060", "12 GB"], ["rtx-3060", "12 GB"]]);
  assert.deepEqual(layouts[2].parts.map(({ memory }) => memory), Array(4).fill("32 GB"));
  assert.equal(layouts[3].mixed, true);
  assert.deepEqual(layouts[3].parts.map(({ memory }) => memory), [null, null]);
  assert.ok(layouts.every(({ links }) => links.length === 0));
});

test("an existing hardware photo link can open its own labeled component example", () => {
  const example = cardPhotoExample("arc-b580", catalog.cards);
  assert.equal(example.scope, "example");
  assert.equal(topologyView(example).parts[0].photo, "arc-b580");
  assert.equal(topologyView(example).activeCount, null);
});

test("a replacement invalidates affected links and does not inherit original conclusions", () => {
  const report = reports.find(({ id }) => id === "V029-HP-C001");
  const replacement = catalog.cards.find(({ id }) => id === "nvidia-geforce-rtx-3060-12gb");
  const original = topologyView(report, {});
  assert.deepEqual(original.links.map(({ state }) => state), ["optional"]);
  const draft = topologyView(report, { 1: replacement });
  assert.equal(draft.draft, true);
  assert.equal(draft.activeCount, null);
  assert.equal(draft.installedCount, 2);
  assert.equal(draft.links.length, 0);
  assert.equal(draft.connection, null);
  assert.equal(draft.mixed, true);
  assert.equal(draft.parts[0].photo, "rtx-3060");
  assert.equal(draft.parts[1].label, original.parts[1].label);
  assert.equal(draftFitRequest(draft), null);
  assert.equal(topologyView(report, {}).links.length, 1);
});

test("only the pinned example scenario can request native fit after a swap", () => {
  const card = catalog.cards.find(({ id }) => id === "nvidia-geforce-rtx-4090");
  const report = reports.find(({ id }) => id === "V005-HP-TEST");
  assert.equal(draftFitRequest(topologyView(report, { 1: card })), null);
  assert.equal(draftFitRequest(topologyView(fitScenario, {})), null);
  const exact = draftFitRequest(topologyView(fitScenario, { 1: card }));
  assert.equal(exact.machine, "llmfit-nvidia-rtx-4090");
  assert.match(exact.artifact, /^[a-f0-9]{64}$/);
  assert.equal(exact.runtime, "llama.cpp");
  assert.equal(exact.context, "4096");
});

test("draft fit only displays an estimate matching the exact inputs and engine revision", () => {
  const card = catalog.cards.find(({ id }) => id === "nvidia-geforce-rtx-4090");
  const request = draftFitRequest(topologyView(fitScenario, { 1: card }));
  const result = {
    kind: "fit_estimate",
    status: "estimated",
    engine: { revision: hardware.upstream.commit },
    machine: { id: request.machine },
    artifact: { sha256: request.artifact },
    runtime: { id: request.runtime },
    assumptions: { context_tokens: 4096, ram_reserved_gib: 8, vram_reserved_gib: 2 },
    estimate: { fit_level: "Perfect", run_mode: "Gpu", quantization: "Q8_0", memory_required_gib: 1.066, memory_available_gib: 22 },
  };
  assert.equal(draftFitEstimate(result, request), result.estimate);
  assert.equal(draftFitEstimate({ ...result, status: "qualified" }, request), null);
  assert.equal(draftFitEstimate({ ...result, machine: { id: "V005-HP-TEST" } }, request), null);
  assert.equal(draftFitEstimate({ ...result, estimate: { ...result.estimate, quantization: "Q4_K_M" } }, request), null);
});

test("the canonical technology wiki can render a static topology inventory", () => {
  const html = renderTopologyReference("html");
  assert.match(html, /Open interactive topology/);
  assert.match(html, /<th[^>]*>Active cards<\/th>/);
  assert.match(html, /4 cards/);
  assert.match(html, /V007-HP-E01/);
  assert.match(html, /Load the model/);
  assert.match(renderTopologyReference("md"), /V028-HP-E03/);
});

test("static topology surfaces link to a configured scaling reader and report missing coverage by default", () => {
  const href = "https://releases.example/topology/scaling";
  assert.match(renderTopologyReference("html", topologyPresets, href), /href="https:\/\/releases\.example\/topology\/scaling"/);
  assert.ok(renderTopologyReference("md", topologyPresets, href).includes(href));
  assert.match(renderTopologyReference("html"), /No reviewed 1→N GPU pair is available here/);
});

test("the Pages fit route forwards only the bounded estimator query to the configured origin", async (t) => {
  const { onRequestGet } = await import("./functions/fit.json.js");
  const origin = "https://release.fastest.example";
  const estimate = { kind: "fit_estimate", status: "estimated" };
  const observed = [];
  let upstream = Response.json(estimate);
  t.mock.method(globalThis, "fetch", async (url, options) => {
    observed.push(url.href);
    assert.equal(options.redirect, "manual");
    assert.equal(options.cache, "no-store");
    assert.equal(options.headers?.Authorization, undefined);
    return upstream;
  });
  const fit = (suffix, env = { FASTEST_RELEASE_ORIGIN: origin }) => onRequestGet({
    request: new Request("https://fastest.example/fit.json" + suffix, { headers: { Authorization: "private" } }), env,
  });
  const query = "?machine=llmfit-nvidia-rtx-4090&context=4096";
  const response = await fit(query);
  assert.deepEqual(await response.json(), estimate);
  assert.equal(response.headers.get("Cache-Control"), "no-store");
  assert.deepEqual(observed, [origin + "/fit.json" + query]);
  assert.equal((await fit("?machine=one&machine=two")).status, 400);
  assert.equal((await fit("?url=https://example.net")).status, 400);
  assert.equal((await fit(query, {})).status, 404);
  assert.equal(observed.length, 1);

  upstream = Response.redirect("https://elsewhere.example/private-preview");
  const redirect = await fit(query);
  assert.equal(redirect.status, 503);
  assert.equal(redirect.headers.get("Location"), null);
  assert.deepEqual(await redirect.json(), { error: "Fit service unavailable." });
  assert.deepEqual(observed, [origin + "/fit.json" + query, origin + "/fit.json" + query]);
});

test("the Pages navigation keeps standalone hash links and resolves hosted evidence destinations", async () => {
  const { navigationHref } = await import("./release-origin.mjs");
  const origin = "https://release.fastest.example";
  assert.equal(navigationHref("goals", false, origin), "#goals");
  assert.equal(navigationHref("goals", true, null), "#goals");
  for (const [route, expected] of [["explorer", "/profiles"], ["goals", "/goals"], ["advisor", "/advisor"], ["costs", "/costs"],
    ["machines", "/profiles#machines"], ["models", "/profiles#models"]]) {
    assert.equal(navigationHref(route, true, origin), origin + expected);
  }
  assert.equal(navigationHref("prices", true, origin), "/prices");
  assert.equal(navigationHref("methods", true, origin), "/wiki/comparison-methods/");
});
