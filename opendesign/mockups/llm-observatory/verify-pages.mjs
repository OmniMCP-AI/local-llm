import assert from "node:assert/strict";
import { verifyReviewCatalog } from "./verify-review-catalog.mjs";

const args = process.argv.slice(2);
const review = args.includes("--review");
const [base, canonical = base] = args.filter((arg) => arg !== "--review");
if (!base) throw new Error("Usage: node verify-pages.mjs <served origin> [canonical origin]");
const origin = new URL(canonical).origin;
const get = (path, options = {}) => fetch(new URL(path, base), {
  redirect: "manual", signal: AbortSignal.timeout(15_000), ...options,
});

async function read(path, contentType, alternate) {
  const response = await get(path);
  assert.equal(response.status, 200, path);
  assert.equal(response.headers.get("content-type")?.split(";")[0], contentType, path);
  if (review) assert.equal(response.headers.get("x-robots-tag"), "noindex", path);
  if (alternate) {
    assert.ok(response.headers.get("link")?.includes("<" + origin + alternate + ">; rel=\"alternate\""), path);
  }
  return response.text();
}

async function verifyHardwareDirectory(catalog, reviewCatalog) {
  const { html: directory, markdown: directoryMarkdown } = reviewCatalog.directory;
  const { release, snapshotId, hardware: { asOf, coverage } } = catalog;
  const root = `/catalog/${release}`;
  const [html, markdown] = await Promise.all([
    read(directory, "text/html", directoryMarkdown), read(directoryMarkdown, "text/markdown", directory),
  ]);
  assert.match(html, /<main>\s*<[^>]+><h1>Hardware catalog<\/h1>/);
  assert.doesNotMatch(html, /<script\b/i);
  assert.ok(html.includes(`href="${directoryMarkdown}"`) && markdown.includes(`[HTML directory](${directory})`));
  assert.ok(html.includes(snapshotId) && markdown.includes(`snapshot: ${snapshotId}`));
  for (const [label, value] of [
    ["Hardware snapshot date", asOf],
    ["GPU catalog identities", coverage.cards],
    ["Unresolved GPU references", coverage.unresolvedCardReferences],
    ["Machine profile records", coverage.untestedProfiles + coverage.reviewedMeasuredProfiles],
    ["Reviewed measured profiles", coverage.reviewedMeasuredProfiles],
    ["Untested machine profiles", coverage.untestedProfiles],
  ]) {
    assert.ok(html.includes(`<dt>${label}</dt><dd>${value}</dd>`), label);
    assert.ok(markdown.includes(`**${label}** — ${value}`), label);
  }
  for (const [label, count] of [
    ["Complete factory configurations", coverage.completeBuilds],
    ["Partial configurations", coverage.partialMachines],
    ["Research component references", coverage.researchComponentReferences],
  ]) {
    assert.ok(html.includes(`<h2>${label} (${count})</h2>`), label);
    assert.ok(markdown.includes(`## ${label} (${count})`), label);
  }
  const kinds = ["cards", "machines"];
  const sheets = await Promise.all(kinds.map(async (kind) =>
    JSON.parse(await read(`/catalog-data/${release}/${kind}.json`, "application/json"))));
  const rows = kinds.flatMap((kind, index) => sheets[index].map(row => ({ ...row, path: `${root}/${kind}/${row.id}` })));
  const routes = rows.map(row => row.path).sort();
  const htmlLinks = (body) => [...body.matchAll(/href="(\/[^"]*)"/g)].map(([, href]) => href);
  const markdownLinks = (body) => [...body.matchAll(/\]\(<?(\/[^)>\s]+)>?\)/g)].map(([, href]) => href);
  const isProfile = (href) => href.startsWith(root + "/cards/") || href.startsWith(root + "/machines/");
  assert.deepEqual(htmlLinks(html).filter(isProfile).sort(), routes);
  assert.deepEqual(markdownLinks(markdown).filter(isProfile).sort(), routes.map(path => path + ".md").sort());

  const commonLinks = [directory, directoryMarkdown, root + "/manifest.json", root + "/LICENSE.txt"];
  const htmlRoutes = new Set(["/", directory + "#cards", directory + "#machines",
    reviewCatalog.models.popular.html, reviewCatalog.runtimes.html, ...commonLinks, ...routes]);
  const markdownRoutes = new Set([...commonLinks, ...routes.map(path => path + ".md")]);
  const htmlText = (value) => value.replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[char]);
  async function verifyProfile({ id, path, source, vendorSpec, topologyRevision, parent, cardIds, relatedMachines, variants, relatedProfiles }) {
    const [page, companion] = await Promise.all([read(path, "text/html"), read(path + ".md", "text/markdown")]);
    assert.ok(page.includes(`<dt>Catalog ID</dt><dd>${id}</dd>`) && companion.includes(`**Catalog ID** — ${id}`), path);
    assert.ok(page.includes(snapshotId) && companion.includes(`snapshot: ${snapshotId}`), path);
    assert.ok(page.includes(`rel="canonical" href="${origin + path}"`), path);
    assert.ok(page.includes(`rel="alternate" type="text/markdown" href="${path}.md"`), path);
    assert.ok(companion.includes(`[HTML card](${path})`), path);
    const links = htmlLinks(page);
    const companionLinks = markdownLinks(companion);
    assert.ok(links.includes(directory) && companionLinks.includes(directoryMarkdown), path);
    assert.ok(links.every(link => htmlRoutes.has(link) || link === path + ".md"), path);
    assert.ok(companionLinks.every(link => markdownRoutes.has(link) || link === path), path);
    for (const citation of [source, vendorSpec?.source].filter(Boolean)) {
      assert.ok(page.includes(`href="${htmlText(citation)}"`) && companion.includes(`<${citation}>`), path);
    }
    for (const [kind, ids] of [
      ["cards", [parent, ...(cardIds ?? []), ...(variants ?? []).map(row => row.id)].filter(Boolean)],
      ["machines", [...(relatedMachines ?? []), ...(relatedProfiles ?? [])].map(row => row.id)],
    ]) {
      for (const id of ids) {
        const linked = `${root}/${kind}/${id}`;
        if (htmlRoutes.has(linked)) assert.ok(links.includes(linked) && companionLinks.includes(linked + ".md"), linked);
      }
    }
    assert.doesNotMatch(page, /<script\b/i, path);
    assert.match(page, /<dt>Runtime-usable (?:GPU )?memory<\/dt><dd>Unknown<\/dd>/, path);
    assert.match(companion, /\*\*Runtime-usable (?:GPU )?memory\*\* — Unknown/, path);
    if (topologyRevision) assert.ok(page.includes(topologyRevision) && companion.includes(topologyRevision), path);
    if (id === "msi-geforce-rtx-5090-32g-suprim-liquid-soc") {
      for (const fact of ["G5090-32SLS", "Board-partner SKU", "394 × 121 × 55 mm", "Multiple product views from MSI"]) {
        assert.ok(page.includes(fact) && companion.includes(fact), fact);
      }
    }
  }
  for (let offset = 0; offset < rows.length; offset += 12) {
    await Promise.all(rows.slice(offset, offset + 12).map(verifyProfile));
  }
  return rows.length;
}

const head = await get("/", { method: "HEAD" });
assert.equal(head.status, 200, "HEAD /");
assert.match(head.headers.get("cache-control"), /no-store/);

const { release, pages, researchRelease, highlights } = JSON.parse(await read("/wiki/manifest.json", "application/json"));
assert.match(release, /^wiki-[a-f0-9]{16}$/);
assert.match(researchRelease, /^v1-[a-f0-9]{16}$/);
assert.ok(pages.some(({ html }) => html === "/wiki/"));
assert.ok(pages.some(({ html }) => html === "/wiki/benchmark-method/"));

const home = (await read("/", "text/html", "/index.md")).replace(/<script[s\S]*?<\/script>/gi, "");
const homeMarkdown = await read("/index.md", "text/markdown", "/");
assert.match(home, /<main\b[^>]*>[\s\S]*<h1>fastest\.ai<\/h1>/i);
assert.ok(home.includes("Also known as localdecode.com."));
assert.ok(homeMarkdown.includes("Also known as localdecode.com."));
assert.ok(home.includes('href="/wiki/"'));
assert.ok(home.includes('rel="canonical" href="' + origin + '/"'));
assert.ok(homeMarkdown.includes(release));

for (const { id, html, markdown } of pages) {
  const article = await read(html, "text/html", markdown);
  const source = await read(markdown, "text/markdown", html);
  assert.match(article, /<main\b[\s\S]*<h1>[^<]+<\/h1>/, html);
  assert.doesNotMatch(article, /<script\b/i, html);
  assert.ok(article.includes('rel="canonical" href="' + origin + html + '"'), html);
  assert.ok(article.includes('rel="alternate" type="text/markdown" href="' + markdown + '"'), html);
  assert.ok(article.includes(release) && source.includes(release), id);
  assert.ok(source.includes('page: "' + id + '"'), markdown);
  if (id === "benchmark-method") {
    assert.match(article, /Graphify backlinks/);
    assert.match(source, /## Graphify backlinks/);
  }
}

for (const { href, markdown } of highlights) {
  assert.ok(home.includes('href="' + href + '"'), href);
  assert.ok(homeMarkdown.includes("](" + markdown + ")"), markdown);
}

for (const [from, to] of [
  ["/wiki", "/wiki/"],
  ["/wiki/methods", "/wiki/comparison-methods/"],
  ["/wiki/methods/", "/wiki/comparison-methods/"],
  ["/wiki/methods.md", "/wiki/comparison-methods.md"],
]) {
  const response = await get(from);
  assert.ok([301, 308].includes(response.status), from + " returned " + response.status);
  assert.equal(new URL(response.headers.get("location"), base).pathname, to, from);
}

const robots = await read("/robots.txt", "text/plain");
assert.ok(robots.includes("Sitemap: " + origin + "/sitemap.xml"));
const sitemap = await read("/sitemap.xml", "application/xml");
const llms = await read("/llms.txt", "text/plain");
assert.ok(sitemap.includes("<loc>" + origin + "/</loc>"));
assert.match(llms, /^# fastest\.ai/m);
for (const { html, markdown } of pages) {
  assert.ok(sitemap.includes("<loc>" + origin + html + "</loc>"), html);
  assert.ok(llms.includes("](" + origin + markdown + ")"), markdown);
}
const research = "/research/" + researchRelease + "/library";
assert.ok(sitemap.includes("<loc>" + origin + research + "</loc>"));
assert.ok(llms.includes("](" + origin + research + ".md)"));
assert.match(await read(research, "text/html", research + ".md"), /<h1>Research library<\/h1>/);
assert.match(await read(research + ".md", "text/markdown", research), /^# Research library/m);
assert.doesNotMatch(sitemap + llms, /\/wiki\/agents(?:[./]|<)|\/wiki\/methods(?:[./]|<)|\/api\/|\/openapi\.json|\/\.well-known\/api-catalog|\/mcp\b|<loc>[^<]*\?/i);
for (const path of ["/wiki/agents/", "/wiki/agents.md", "/.well-known/api-catalog"]) {
  const response = await get(path);
  assert.ok([404, 410].includes(response.status), path + " returned " + response.status);
}

let hardwareCount = 0;
let catalogCounts;
if (review) {
  assert.ok(home.includes("Non-production review"), "Review homepage labels the preview");
  assert.match(homeMarkdown, /Non-production review/);
  assert.equal(head.headers.get("x-robots-tag"), "noindex");
  assert.match(robots, /^Disallow: \/$/m);
  assert.doesNotMatch(sitemap, /<loc>[^<]+\/prices<\/loc>/);
  const { catalogRelease, catalogApi } = JSON.parse(await read("/wiki/manifest.json", "application/json"));
  assert.equal(catalogApi, undefined);
  const manifest = JSON.parse(await read("/review-manifest.json", "application/json"));
  assert.equal(manifest.status, "non-production-review");
  assert.equal(manifest.canonicalOrigin, origin);
  assert.match(manifest.head, /^[a-f0-9]{40}$/);
  assert.equal(manifest.wiki.release, release);
  assert.equal(manifest.research.release, researchRelease);
  assert.equal(manifest.catalog.release, catalogRelease);
  const catalog = JSON.parse(await read(manifest.catalog.manifest, "application/json"));
  assert.match(catalog.snapshotId, /^[a-f0-9]{64}$/);
  assert.equal(manifest.catalog.snapshotId, catalog.snapshotId);
  assert.equal(catalog.release, catalogRelease);
  const { html: directory, markdown: directoryMarkdown } = manifest.catalog.directory;
  assert.ok(home.includes(`href="${directory}"`));
  assert.ok(homeMarkdown.includes(`[Hardware catalog](${directoryMarkdown})`));
  assert.ok(!sitemap.includes(directory) && !llms.includes(directory));
  for (const [label, { html, markdown }] of [
    ["Model catalog", manifest.catalog.models.popular], ["Runtime catalog", manifest.catalog.runtimes],
  ]) {
    assert.ok(home.includes(`href="${html}"`) && homeMarkdown.includes(`[${label}](${markdown})`), label);
    assert.ok(!sitemap.includes(html) && !llms.includes(html), label);
  }
  hardwareCount = await verifyHardwareDirectory(catalog, manifest.catalog);
  catalogCounts = await verifyReviewCatalog(catalog, manifest.catalog, { read, origin });
  const machines = JSON.parse(await read(`/catalog-data/${catalogRelease}/machines.json`, "application/json"));
  assert.ok(machines.some(({ topologyRevision }) => topologyRevision));
  const researchManifest = JSON.parse(await read(manifest.research.manifest, "application/json"));
  assert.equal(researchManifest.release, researchRelease);
  assert.doesNotMatch(await read("/wiki/agent-discovery/", "text/html"), /OpenAPI|\/api\//i);
  for (const path of [`/catalog/${catalogRelease}/openapi.json`, "/api/v1/catalog", "/api/feedback", "/api/runtime-releases", "/prices"]) {
    assert.equal((await get(path)).status, 404, path);
  }
}

console.log("Verified " + release + ", " + pages.length + " wiki pairs and " + highlights.length + " active highlights at " + base);
if (review) {
  console.log(`Verified PostgreSQL-pinned catalogs with ${hardwareCount} hardware, ${catalogCounts.modelProfiles} model and ${catalogCounts.runtimes} runtime profile pairs`);
  console.log(`Verified ${catalogCounts.inventory} distinct model repositories in the exact lookup shards`);
}
