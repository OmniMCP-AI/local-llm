import assert from "node:assert/strict";
import { test } from "node:test";
import { hardwareCard, renderCard } from "./catalog-card.mjs";
import { renderCoordinatePlot } from "./coordinate-plot.mjs";

const card = (id, spec) => ({
  id, name: id, source: "https://example.test/" + id, kind: "Component reference", manufacturer: "Example",
  variant: "Board", aliases: [], variants: [], relatedProfiles: [],
  vendorSpec: spec && { source: "https://example.test/spec/" + id, designation: id, facts: spec },
});
const known = card("Known GPU", { "Memory configuration": "32 GB GDDR6", "Memory bandwidth": "576 GB/s" });
const powerOnly = card("GPU with missing bandwidth", { "Memory configuration": "24 GB GDDR6", "Rated graphics power (W)": "260" });
const peers = [known, powerOnly];
const render = (row, markdown) => renderCard(hardwareCard(row, "v1-test", "cards", {
  peers, reviewProfileHref: (_type, id) => "/" + encodeURIComponent(id),
}), { release: "v1-test", pathname: "card.html", markdown });

test("GPU pages retain one rated bandwidth cohort and show a measured speed coverage gap", () => {
  const selected = render(known, false);
  const unavailable = render(powerOnly, false);
  for (const html of [selected, unavailable]) {
    assert.match(html, /GPU position by rated specifications/);
    assert.match(html, /Rated memory bandwidth \(GB\/s\)/);
    assert.match(html, /Show point labels/);
    assert.match(html, /coordinate-popup/);
    assert.match(html, /Nominal GPU memory<\/dt><dd>32 GB/);
    assert.match(html, /Rated memory bandwidth<\/dt><dd>576 GB\/s/);
    assert.match(html, /Measured decode speed unavailable/);
    assert.doesNotMatch(html, /Original schematic|Conceptual GPU and memory layout/);
    assert.doesNotMatch(html, /GPU position by rated graphics power/);
  }
  assert.match(selected, /href="\/Known%20GPU" aria-current="page"/);
  assert.equal((selected.match(/class="coordinate-point coordinate-selected"/g) ?? []).length, 2);
  assert.match(selected, /Selected GPU: Known GPU · 32 GB · 576 GB\/s/);
  assert.doesNotMatch(unavailable, /href="\/Known%20GPU" aria-current="page"/);
  assert.match(unavailable, /GPU with missing bandwidth has no unambiguous pair of rated specifications/);
  const markdown = render(known, true);
  assert.match(markdown, /Selected GPU: Known GPU · 32 GB · 576 GB\/s/);
  assert.match(markdown, /Measured decode speed unavailable/);
  assert.doesNotMatch(markdown, /Original schematic|Conceptual GPU and memory layout/);
});

test("NVIDIA product and architecture sources cover distinct RTX 3090 and RTX 4090 bandwidth values", async () => {
  const { fileURLToPath } = await import("node:url");
  const { readHardwareCatalog } = await import("./catalog-hardware-build.mjs");
  const here = fileURLToPath(new URL(".", import.meta.url));
  const { catalog } = await readHardwareCatalog(here);
  for (const [id, bandwidth, locator] of [
    ["nvidia-geforce-rtx-3090", "936", "GA102-GPU-Architecture-Whitepaper-V1.pdf"],
    ["nvidia-geforce-rtx-3090-ti", "1008", "nvidia-ada-gpu-architecture.pdf"],
    ["nvidia-geforce-rtx-4090", "1008", "rtx-5090/#specs"],
  ]) {
    const gpu = catalog.cards.find(card => card.id === id);
    const output = renderCard(hardwareCard(gpu, "v1-test", "cards", { peers: catalog.cards }), {
      release: "v1-test", pathname: "card.md", markdown: true,
    });
    assert.ok(output.includes(`· ${bandwidth} GB/s`), id);
    assert.ok(output.includes(locator), id);
    assert.ok(output.includes("Product images on NVIDIA"), id);
  }
  const { catalog: withoutWhitepaper } = await readHardwareCatalog(here, value => value?.includes("GA102-GPU-Architecture-Whitepaper-V1.pdf"));
  const rtx3090 = withoutWhitepaper.cards.find(card => card.id === "nvidia-geforce-rtx-3090");
  assert.equal(rtx3090.vendorSpec.facts["Memory bandwidth"], undefined);
  assert.equal(rtx3090.vendorSpec.facts["Memory configuration"], "24 GB GDDR6X");
  assert.equal(rtx3090.vendorSpec.gallery.label, "Product images on NVIDIA");
});


test("the highlighted budget region covers the best performance side of the target", () => {
  for (const [reverse, expectedHeight] of [[false, "60.00000%"], [true, "40.00000%"]]) {
    const chart = renderCoordinatePlot({
      title: "Tradeoffs",
      xAxis: { label: "Build price", unit: "USD", domain: [0, 100] },
      yAxis: { label: "Performance", domain: [0, 100], reverse },
      points: [{ id: "gpu", name: "GPU", x: 20, y: 60 }],
      targetArea: { x: 45, y: 40 },
    });
    assert.ok(chart.includes(`--area-width:45.00000%;--area-height:${expectedHeight};top:0`));
  }
});

test("dense point labels are readable in a separate list with exact values", () => {
  const chart = renderCoordinatePlot({
    title: "Costs", kind: "line", showLabels: true,
    xAxis: { label: "Month" }, yAxis: { label: "Cost", unit: "USD" },
    points: [
      { id: "local", name: "Local", x: 1, y: 1000, short: "$1,000" },
      { id: "cloud", name: "Cloud", x: 1, y: 1001, short: "$1,001" },
    ],
  });
  const list = chart.match(/<ul class="coordinate-label-list"[\s\S]*?<\/ul>/)?.[0];
  assert.ok(list, "point labels have their own space outside the plot");
  assert.match(list, /Local[\s\S]*Month: 1[\s\S]*Cost: 1,000 USD/);
  assert.match(list, /Cloud[\s\S]*Month: 1[\s\S]*Cost: 1,001 USD/);
  assert.match(chart, /class="coordinate-viewport"/);
});

test("zoom shows an inspectable categorical subset while retaining the full exact-value list and selection", () => {
  const chart = renderCoordinatePlot({
    title: "Ranks", kind: "bar", interactiveZoom: true, zoom: { start: 0.25, end: 0.75 },
    xAxis: { label: "GPU", categorical: true }, yAxis: { label: "Speed", unit: "tok/s" },
    points: ["A", "B", "C", "D"].map((name, i) => ({ id: name, name, x: name, y: i + 1 })),
    selectedId: "A", showLabels: true,
  });
  assert.match(chart, /Zoom in/);
  assert.match(chart, /Reset zoom/);
  assert.doesNotMatch(chart, /data-point-id="A"/);
  assert.match(chart, /data-point-id="B"/);
  assert.match(chart, /data-point-id="C"/);
  assert.doesNotMatch(chart, /data-point-id="D"/);
  assert.match(chart, /A · GPU: A · Speed: 1 tok\/s/);
  assert.match(chart, /coordinate-selection/);
  assert.match(chart, /type="checkbox" checked/);
});

test("continuous zoom rescales the horizontal domain and preserves exact units", () => {
  const chart = renderCoordinatePlot({
    title: "Prices", interactiveZoom: true, zoom: { start: 0.25, end: 0.75 },
    xAxis: { label: "Price", unit: "USD", domain: [0, 100] },
    yAxis: { label: "Speed", unit: "tok/s", domain: [0, 100] },
    points: [
      { id: "low", name: "Low", x: 10, y: 30 },
      { id: "middle", name: "Middle", x: 50, y: 60 },
      { id: "high", name: "High", x: 90, y: 80 },
    ],
  });
  assert.doesNotMatch(chart, /data-point-id="low"/);
  assert.match(chart, /data-point-id="middle"[^>]*--column:50\.00000%/);
  assert.doesNotMatch(chart, /data-point-id="high"/);
  assert.match(chart, /Price 50 USD, Speed 60 tok\/s/);
  assert.match(chart, /Price \(USD\)/);
});

test("zoom retains a line crossing the visible range even when its endpoints are outside it", () => {
  const chart = renderCoordinatePlot({
    title: "Costs", kind: "line", interactiveZoom: true, zoom: { start: 0.25, end: 0.75 },
    xAxis: { label: "Month", domain: [0, 100] }, yAxis: { label: "Cost", domain: [0, 100] },
    points: [{ id: "a", name: "Start", x: 0, y: 0 }, { id: "b", name: "End", x: 100, y: 100 }],
  });
  assert.match(chart, /<polyline[^>]+points="-500\.000,1000\.000 1500\.000,0\.000"/);
});
