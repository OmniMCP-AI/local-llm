import assert from "node:assert/strict";
import { test } from "node:test";
import { catalogDocument } from "./catalog-card.mjs";
import { renderStandaloneCoordinatePlot } from "./coordinate-plot.mjs";
import { verifyCatalogScripts } from "./verify-catalog-html.mjs";

test("catalog review allows its locale controls and rejects injected scripts", () => {
  const page = catalogDocument({ title: "Example", release: "v1-1234567890abcdef", main: "<h1>Example</h1>" });
  assert.doesNotThrow(() => verifyCatalogScripts(page));
  assert.throws(() => verifyCatalogScripts(page.replace("<h1>Example</h1>", "<h1>Example</h1><script>alert(1)</script>")));
  assert.throws(() => verifyCatalogScripts(page.replace("const key =", "alert(1); const key =")));
  assert.throws(() => verifyCatalogScripts(page.replace("<script>", "<script src=\"https://malicious.example/x.js\">")));
});

test("GPU review accepts only the chart controller and data with links to reviewed GPU profiles", () => {
  const release = "v1-1234567890abcdef";
  const href = `/catalog/${release}/cards/example`;
  const main = renderStandaloneCoordinatePlot({
    title: "Memory", xAxis: { label: "GPU" }, yAxis: { label: "GB" },
    points: [{ id: "example", name: "<Example>", href, x: 1, y: 16 }],
  });
  const page = catalogDocument({ title: "Example", release, main });
  const check = html => verifyCatalogScripts(html, href, { chartLinks: new Set([href]) });
  assert.doesNotThrow(() => check(page));
  assert.throws(() => verifyCatalogScripts(page, "/catalog/hardware"));
  assert.throws(() => check(page.replace("let labels = false", "let labels = true")));
  assert.throws(() => check(page.replace('type="application/json" data-coordinate-data', "data-coordinate-data")));
  assert.throws(() => check(page.replace(`"href":"${href}"`, '"href":"/unreviewed"')));
});
