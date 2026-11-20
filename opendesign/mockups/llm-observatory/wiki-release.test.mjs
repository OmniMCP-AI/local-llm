import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

test("the Pages release offers readable canonical wiki and Markdown from the approved graph", async (t) => {
  const { writeWikiRelease } = await import("./wiki-release.mjs");
  const output = await mkdtemp(join(tmpdir(), "fastest-wiki-test-"));
  t.after(() => rm(output, { recursive: true, force: true }));
  const render = await writeWikiRelease({
    output, origin: "https://example.test", researchRelease: "v1-b9b9b9b9b9b9b9b9",
    documents: {
      index: { title: "Wiki", summary: "The wiki", status: "published", body: "Visit [the guide](#wiki/method).\n\n[Hidden](#wiki/draft)." },
      method: { title: "Method", summary: "Reviewed method", status: "published", redirects: "methods",
        body: "## Conditions\n\n- Keep **the context** fixed.\n- Escape <script> in notes.\n\n[Source](https://www.youtube.com/watch?v=DEPF8rAprS4&t=64s)",
        entity: "protocol-1", evidence: "source-7" },
      draft: { title: "Private draft", summary: "Do not publish", status: "draft", body: "Private notes." },
      retired: { title: "Withdrawn page", summary: "Do not publish", status: "withdrawn", body: "Withdrawn notes." },
    },
    edges: [{ source: "index", target: "method" }, { source: "draft", target: "method" }],
    highlights: [
      { id: "news", type: "news", title: "Current methods", summary: "Read the method.", page: "method",
        status: "published", starts: "2026-11-20", ends: "2026-12-01", priority: 1 },
      { id: "expired", type: "news", title: "Expired highlight", summary: "Old.", page: "method",
        status: "published", starts: "2026-11-01", ends: "2026-11-20", priority: 2 },
      { id: "waiting", type: "news", title: "Draft highlight", summary: "Pending.", page: "method",
        status: "draft", starts: "2026-11-20", ends: "2026-12-01", priority: 3 },
    ],
    releaseDate: "2026-11-21",
    withdrawn: ["youtube/DEPF8rAprS4"],
  });
  const read = (name) => readFile(join(output, name), "utf8");
  const html = await read("wiki/method/index.html");
  const md = await read("wiki/method.md");
  assert.match(html, /<link rel="canonical" href="https:\/\/example.test\/wiki\/method\/">/);
  assert.match(html, /rel="alternate" type="text\/markdown" href="\/wiki\/method.md"/);
  assert.match(html, /<h1>Method<\/h1>/);
  assert.match(html, /<li>Keep <strong>the context<\/strong> fixed.<\/li>/);
  assert.match(html, /&lt;script&gt;/);
  assert.match(html, /Graphify backlinks[\s\S]*href="\/wiki\/"/);
  assert.doesNotMatch(html, /<script|Private draft|DEPF8rAprS4/);
  assert.match(md, /page: "method"/);
  assert.match(md, /entity: "protocol-1"/);
  assert.match(md, /evidence: "source-7"/);
  const release = md.match(/release: "(wiki-[a-f0-9]+)"/)[1];
  assert.ok(html.includes(release));
  assert.match(md, /\[Wiki\]\(\/wiki\/index.md\)/);
  await assert.rejects(read("wiki/draft/index.html"), { code: "ENOENT" });
  await assert.rejects(read("wiki/retired.md"), { code: "ENOENT" });
  assert.match(await read("_redirects"), /^\/wiki\/methods\/ \/wiki\/method\/ 301$/m);
  assert.match(await read("robots.txt"), /Sitemap: https:\/\/example.test\/sitemap.xml/);
  const sitemap = await read("sitemap.xml");
  assert.match(sitemap, /<loc>https:\/\/example.test\/wiki\/method\/<\/loc>/);
  assert.doesNotMatch(sitemap, /draft|retired|\/wiki\/methods\/|<loc>[^<]*\?|\/api\//);
  const llms = await read("llms.txt");
  assert.match(llms, /https:\/\/example.test\/research\/v1-b9b9b9b9b9b9b9b9\/library.md/);
  assert.match(llms, /\[Method\]\(https:\/\/example.test\/wiki\/method.md\)/);
  assert.doesNotMatch(llms, /draft|withdrawn|\/api\/|OpenAPI/i);
  assert.match(render.homeBody, /Current methods[\s\S]*Read the method/);
  assert.match(await read("index.md"), /Current methods[\s\S]*Read the method/);
  assert.doesNotMatch(render.homeBody, /Expired highlight|Draft highlight/);
  assert.deepEqual(render.highlights.map(({ id }) => id), ["news"]);
});

test("a Pages rebuild removes routes, aliases, and highlights from the previous release after withdrawal", async (t) => {
  const { writeWikiRelease } = await import("./wiki-release.mjs");
  const output = await mkdtemp(join(tmpdir(), "fastest-wiki-test-"));
  t.after(() => rm(output, { recursive: true, force: true }));
  const input = {
    output, origin: "https://example.test", researchRelease: "v1-b9b9b9b9b9b9b9b9", releaseDate: "2026-11-21",
    documents: {
      index: { title: "Wiki", summary: "The wiki", status: "published", body: "Visit [the setup](#wiki/setup)." },
      setup: { title: "Exact setup", summary: "Two cards.", status: "published", body: "Configuration notes.",
        evidence: "youtube/DEPF8rAprS4", redirects: "two-cards" },
    },
    edges: [{ source: "index", target: "setup" }],
    highlights: [{
      id: "configuration", type: "configuration", title: "Compare two cards", summary: "Read the source.", page: "setup",
      status: "published", starts: "2026-11-20", ends: "2026-12-01", priority: 1,
    }],
  };
  const first = await writeWikiRelease(input);
  assert.match(first.homeBody, /href="\/wiki\/setup\/"/);
  assert.match(await readFile(join(output, "_redirects"), "utf8"), /\/wiki\/two-cards\/ \/wiki\/setup\/ 301/);

  const updated = await writeWikiRelease({ ...input, withdrawn: ["youtube/DEPF8rAprS4"] });
  assert.doesNotMatch(updated.homeBody, /Compare two cards|\/wiki\/setup\//);
  await assert.rejects(readFile(join(output, "wiki/setup/index.html")), { code: "ENOENT" });
  await assert.rejects(readFile(join(output, "wiki/setup.md")), { code: "ENOENT" });
  for (const artifact of ["sitemap.xml", "llms.txt", "_redirects", "wiki/manifest.json", "wiki/index.html", "wiki/index.md"]) {
    assert.doesNotMatch(await readFile(join(output, artifact), "utf8"), /wiki\/setup|two-cards|DEPF8rAprS4/);
  }
});
