import assert from "node:assert/strict";

const [base, canonical = base] = process.argv.slice(2);
if (!base) throw new Error("Usage: node verify-pages.mjs <served origin> [canonical origin]");
const origin = new URL(canonical).origin;
const get = (path, options = {}) => fetch(new URL(path, base), {
  redirect: "manual", signal: AbortSignal.timeout(15_000), ...options,
});

async function read(path, contentType, alternate) {
  const response = await get(path);
  assert.equal(response.status, 200, path);
  assert.equal(response.headers.get("content-type")?.split(";")[0], contentType, path);
  if (alternate) {
    assert.ok(response.headers.get("link")?.includes("<" + origin + alternate + ">; rel=\"alternate\""), path);
  }
  return response.text();
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

console.log("Verified " + release + ", " + pages.length + " wiki pairs and " + highlights.length + " active highlights at " + base);
