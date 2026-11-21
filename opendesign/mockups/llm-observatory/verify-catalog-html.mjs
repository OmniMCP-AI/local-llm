import assert from "node:assert/strict";
import { catalogDocument } from "./catalog-card.mjs";
import { standaloneCoordinateScript } from "./coordinate-plot.mjs";

// Derive the trusted controllers from their renderers and verify the exact bytes.
const template = catalogDocument({ title: "Verification", release: "v1-0000000000000000", main: "" });
const trustedScript = template.match(/<script>[\s\S]*?<\/script>/)?.[0];
assert.ok(trustedScript);
const coordinateScript = standaloneCoordinateScript();

export function verifyCatalogScripts(html, path, { chartLinks } = {}) {
  const index = html.indexOf(trustedScript);
  assert.notEqual(index, -1, path);
  let rest = html.slice(0, index) + html.slice(index + trustedScript.length);
  const charts = chartLinks && [...rest.matchAll(/<div data-coordinate-static>/g)].length;
  if (charts) {
    assert.ok(rest.includes(coordinateScript), path);
    rest = rest.replace(coordinateScript, "");
    let dataBlocks = 0;
    rest = rest.replace(/<script type="application\/json" data-coordinate-data>([^<]*)<\/script>/g, (_, data) => {
      const chart = JSON.parse(data);
      assert.ok(chart && [undefined, "scatter", "bar"].includes(chart.kind), path);
      assert.ok(Array.isArray(chart.points) && chart.points.length > 0, path);
      assert.ok(chart.points.every(point => chartLinks.has(point?.href)), path);
      dataBlocks += 1;
      return "";
    });
    assert.equal(dataBlocks, charts, path);
  }
  assert.doesNotMatch(rest, /<script\b/i, path);
}

export const catalogNavigationLinks = [...template.match(/<nav class="profile-nav"[^>]*>([\s\S]*?)<\/nav>/)[1]
  .matchAll(/href="(\/[^\"]*)"/g)].map(([, href]) => href);
