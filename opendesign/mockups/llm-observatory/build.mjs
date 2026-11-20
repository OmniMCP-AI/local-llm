import { createHash } from "node:crypto";
import { writeResearchRelease } from "./research-release-build.mjs";
import { mkdir, readFile, readdir, rm, writeFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { readHardwareCatalog } from "./catalog-hardware-build.mjs";
import { writeCatalogRelease } from "./catalog-release-build.mjs";
import { activeHighlights, wikiHtmlRoute, writeWikiRelease } from "./wiki-release.mjs";
import { withdrawnReference } from "./evidence-provenance.mjs";
import { writeEvidenceState } from "./evidence-state.mjs";
import topologyReports from "./catalog-topology.json" with { type: "json" };
import highlights from "./wiki/highlights.json" with { type: "json" };

const here = (name) => new URL(name, import.meta.url);
const require = createRequire(import.meta.url);
const { build } = require("esbuild");
const openccRoot = resolve(dirname(require.resolve("opencc-js")), "../..");
const pages = process.argv.includes("--pages");
const outputArgument = process.argv.indexOf("--output");
if (outputArgument !== -1 && (!pages || !process.argv[outputArgument + 1])) throw new Error("--output requires a Pages directory");
const output = outputArgument === -1 ? fileURLToPath(here("dist/")) : resolve(process.argv[outputArgument + 1]);
const openccNotices = await Promise.all(["LICENSE", "THIRD_PARTY_LICENSES.md", "LICENSES/Apache-2.0.txt"]
  .map((name) => readFile(resolve(openccRoot, name), "utf8")));
const stylesheetNames = ["styles", "knowledge", "goals", "feedback", "catalog", "technology", "methods", "costs", "highlights", "profile-benchmarks", "locale"];
const [stylesheets, image, wikiNames, graph, fullGraph, mediaIndex] = await Promise.all([
  Promise.all(stylesheetNames.map((name) => readFile(here(name + ".css"), "utf8"))),
  readFile(here("hero-gpu.png")),
  readdir(here("wiki/pages/")),
  readFile(here("wiki/graph.json"), "utf8").then(JSON.parse),
  readFile(here("wiki/graphify.json"), "utf8").then(JSON.parse),
  readFile(here("hardware-assets/assets.json"), "utf8").then(JSON.parse),
]);
const contentHash = createHash("sha256");
const documents = Object.fromEntries(await Promise.all(wikiNames.filter((name) => name.endsWith(".md")).sort().map(async (name) => {
  const raw = (await readFile(here("wiki/pages/" + name), "utf8")).replace(/\r\n?/g, "\n");
  const [, frontmatter, body] = raw.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/) ?? [];
  if (!frontmatter) throw new Error("Missing Markdown frontmatter: " + name);
  const fields = Object.fromEntries(frontmatter.split("\n").map((line) => {
    const colon = line.indexOf(":");
    return [line.slice(0, colon), line.slice(colon + 1).trim()];
  }));
  if (!fields.title || !fields.kind || !fields.summary) throw new Error("Incomplete Markdown frontmatter: " + name);
  return [name.replace(/\.md$/, ""), { ...fields, body, raw }];
})));
for (const [slug, doc] of Object.entries(documents)) contentHash.update("pages/" + slug + ".md\0" + doc.raw + "\0");
if (contentHash.digest("hex") !== fullGraph.graph.source_sha256) throw new Error("Wiki index is stale. Rebuild with Graphify using wiki/rebuild_graph.py.");
const researchPayload = await readFile(here("wiki/research-index.json"));
if (createHash("sha256").update(researchPayload).digest("hex") !== fullGraph.graph.research_index_sha256) {
  throw new Error("Research index and Graphify release disagree. Run wiki/rebuild_graph.py.");
}
for (const [name, expected] of Object.entries(fullGraph.graph.research_inputs)) {
  const bytes = await readFile(here("wiki/" + name));
  if (createHash("sha256").update(bytes).digest("hex") !== expected) throw new Error("Research tags are stale: " + name + ". Run wiki/rebuild_graph.py.");
}
let researchIndex;
let approvals = {};
if (pages) {
  const approvalPath = process.env.FASTEST_RESEARCH_METADATA_APPROVALS;
  approvals = approvalPath ? JSON.parse(await readFile(approvalPath, "utf8")) : {};
  researchIndex = await writeResearchRelease(fileURLToPath(here(".")), output, approvals);
}
const media = Object.fromEntries(await Promise.all(Object.entries(mediaIndex).map(async ([id, asset]) => {
  if (!/^[a-z0-9-]+\.jpg$/.test(asset.file)) throw new Error("Invalid hardware photo filename: " + asset.file);
  const jpeg = await readFile(here("hardware-assets/" + asset.file));
  return [id, { ...asset, data: "data:image/jpeg;base64," + jpeg.toString("base64") }];
})));
const catalogDirectory = fileURLToPath(here("."));
const withdrawn = Object.entries(approvals).filter(([, value]) => value.status === "withdrawn").map(([id]) => id);
const isWithdrawn = withdrawnReference(JSON.parse(researchPayload), approvals);
const publicTopologies = topologyReports.filter(({ source, id }) => !isWithdrawn(source) && !isWithdrawn(id));
const publicDocuments = Object.fromEntries(Object.entries(documents)
  .filter(([, { evidence, status }]) => !isWithdrawn(evidence) && status !== "withdrawn")
  .map(([id, doc]) => {
    const clean = (text) => text.split("\n").filter((line) => !isWithdrawn(line)).join("\n");
    return [id, { ...doc, body: clean(doc.body), raw: clean(doc.raw) }];
  }));
const hardware = await readHardwareCatalog(catalogDirectory, isWithdrawn);
const hardwareDirectory = {
  asOf: hardware.manifest.asOf,
  coverage: hardware.manifest.coverage,
  cards: hardware.catalog.cards.map(({ id, name, detail, aliases, source, memory }) => ({ id, name, detail, aliases, source, memory })),
  machines: hardware.catalog.machines.map(({ id, name, detail, kind, source }) => ({ id, name, detail, kind, source })),
};
const catalogRelease = pages ? await writeCatalogRelease(catalogDirectory, output, hardware) : "";
const releaseDate = new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Shanghai" }).format(new Date());
const wikiRelease = pages ? await writeWikiRelease({
  output: output,
  origin: process.env.FASTEST_PUBLIC_ORIGIN ?? "https://fastest.ai",
  researchRelease: researchIndex.release,
  catalogRelease,
  documents: publicDocuments,
  topologies: publicTopologies,
  edges: graph.edges,
  highlights: highlights.filter(({ source }) => !isWithdrawn(source)),
  releaseDate,
  withdrawn,
}) : null;
const wikiDocuments = wikiRelease
  ? { ...wikiRelease.publicPages, ...Object.fromEntries(Object.entries(publicDocuments).filter(([, doc]) => doc.status === "preview")) }
  : documents;
const releaseHighlights = wikiRelease?.highlights ?? activeHighlights(highlights, documents, releaseDate);
const result = await build({
  entryPoints: ["app", ...(pages ? ["price-entry"] : [])].map((name) => fileURLToPath(here(name + ".jsx"))),
  outdir: output,
  nodePaths: [dirname(dirname(require.resolve("esbuild/package.json")))],
  bundle: true,
  minify: true,
  write: false,
  charset: "utf8",
  banner: { js: "/*! opencc-js and OpenCC dictionaries\n" + openccNotices.join("\n").replaceAll("*/", "* /") + "\n*/" },
  target: ["es2022"],
  define: {
    "process.env.NODE_ENV": '"production"',
    __FASTEST_PAGES__: String(pages),
    __FASTEST_RESEARCH_INDEX__: JSON.stringify(researchIndex ?? null),
    __FASTEST_CATALOG_RELEASE__: JSON.stringify(catalogRelease),
    __FASTEST_HARDWARE_DIRECTORY__: JSON.stringify(hardwareDirectory),
    __FASTEST_WIKI_DOCUMENTS__: JSON.stringify(wikiDocuments),
    __FASTEST_WIKI_PUBLIC_ROUTES__: JSON.stringify(Object.fromEntries(Object.keys(wikiRelease?.publicPages ?? {})
      .map((id) => [id, wikiHtmlRoute(id)]))),
    __FASTEST_WIKI_HIGHLIGHTS__: JSON.stringify(releaseHighlights.map((entry) => ({
      ...entry, href: pages ? entry.href : entry.previewHref,
    }))),
    __FASTEST_WIKI_GRAPH__: JSON.stringify(pages ? {
      nodes: graph.nodes.filter(({ id }) => Object.hasOwn(wikiDocuments, id)),
      edges: graph.edges.filter(({ source, target }) =>
        Object.hasOwn(wikiDocuments, source) && Object.hasOwn(wikiDocuments, target)),
    } : graph),
    __FASTEST_TOPOLOGY_REPORTS__: JSON.stringify(publicTopologies),
    __FASTEST_HARDWARE_ASSETS__: JSON.stringify(media),
    __FASTEST_HERO_IMAGE__: JSON.stringify("data:image/png;base64," + image.toString("base64")),
  },
  legalComments: "inline",
});
const scriptFor = (name) => result.outputFiles.find(({ path }) => path.endsWith("/" + name + ".js"))
  .text.replace(/<\/script/gi, "<\\/script");
const previewHead = '<meta name="description" content="Interactive prototype for comparing local AI hardware, performance, and cost.">\n'
  + "<title>fastest.ai | Local AI benchmark explorer</title>";
const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
${wikiRelease?.homeHead ?? previewHead}
<style>${stylesheets.join("\n")}</style>
</head>
<body>
<div id="root"></div>
${wikiRelease?.homeBody ?? "<noscript>This prototype requires JavaScript. Open this file in a browser with JavaScript enabled.</noscript>"}
<script>${scriptFor("app")}</script>
</body>
</html>
`;
if (pages) {
  await mkdir(output, { recursive: true });
  await writeFile(join(output, "index.html"), html);
  const stateFile = process.env.FASTEST_EVIDENCE_STATE;
  await writeEvidenceState(output, stateFile ? JSON.parse(await readFile(stateFile, "utf8")) : undefined);
  const priceStyles = await Promise.all(["styles", "locale", "price-comparison"].map((name) => readFile(here(name + ".css"), "utf8")));
  await writeFile(join(output, "prices.html"), `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Dated regional prices with original quotes and independent display currency.">
<title>Regional price comparison · fastest.ai</title>
<style>${priceStyles.join("\n")}</style>
</head>
<body>
<div id="root"></div>
<noscript><main><h1>Regional price comparison</h1><p><a href="/api/price-comparison">Read the exact price data</a>.</p></main></noscript>
<script>${scriptFor("price-entry")}</script>
</body>
</html>
`);
  for (const name of await readdir(join(output, "research"))) {
    if (name !== researchIndex.release && /^v1-[a-f0-9]{16}$/.test(name)) {
      await rm(join(output, "research", name), { recursive: true, force: true });
    }
  }
} else {
  await writeFile(here("fastest-ai.html"), html);
}
