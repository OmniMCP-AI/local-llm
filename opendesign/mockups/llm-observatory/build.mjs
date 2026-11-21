import { createHash } from "node:crypto";
import { readResearchApprovals, writeResearchRelease } from "./research-release-build.mjs";
import { mkdir, readFile, readdir, rm, writeFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { readHardwareCatalog } from "./catalog-hardware-build.mjs";
import { readCatalogPhotos } from "./catalog-topology-build.mjs";
import { prepareCatalogRelease, readCatalogModelFiles, writeCatalogProjection, writeCatalogRelease } from "./catalog-release-build.mjs";
import { catalogReleasePattern, deniedCatalogPin } from "./catalog-paths.mjs";
import { writeLocalCatalogProfiles } from "./catalog-local-build.mjs";
import { profileStyles } from "./catalog-profile-styles.mjs";
import { activeHighlights, wikiHtmlRoute, writeWikiRelease } from "./wiki-release.mjs";
import { withdrawnReference } from "./evidence-provenance.mjs";
import { emptyEvidenceState, validateEvidenceState, writeEvidenceState } from "./evidence-state.mjs";
import { allowedResearchPin, deniedResearchPin, readResearchPin, researchReleaseId, writeResearchPin } from "./research-released-snapshot.mjs";
import { navigationHref, releaseOrigin } from "./release-origin.mjs";
import { withPreviewResults } from "./research-preview.mjs";
import highlights from "./wiki/highlights.json" with { type: "json" };

const here = (name) => new URL(name, import.meta.url);
const require = createRequire(import.meta.url);
const { build } = require("esbuild");
const openccRoot = resolve(dirname(require.resolve("opencc-js")), "../..");
const pages = process.argv.includes("--pages");
const catalogPostgres = process.argv.includes("--catalog-postgres");
const catalogDatabase = process.env.FASTEST_CATALOG_DATABASE_URL;
const catalogSnapshot = process.env.FASTEST_CATALOG_SNAPSHOT_ID;
if (catalogPostgres) {
  if (!pages) throw new Error("--catalog-postgres requires --pages");
  if (!catalogDatabase?.trim()) throw new Error("FASTEST_CATALOG_DATABASE_URL is required");
  if (!/^[a-f0-9]{64}$/.test(catalogSnapshot ?? "")) {
    throw new Error("FASTEST_CATALOG_SNAPSHOT_ID must be a full SHA-256 digest");
  }
}
const outputArgument = process.argv.indexOf("--output");
if (outputArgument !== -1 && (!pages || !process.argv[outputArgument + 1])) throw new Error("--output requires a Pages directory");
const output = outputArgument === -1 ? fileURLToPath(here("dist/")) : resolve(process.argv[outputArgument + 1]);
const releaseDate = (pages ? process.env.FASTEST_RELEASE_DATE : undefined) ??
  new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Shanghai" }).format(new Date());
if (pages && (!/^\d{4}-\d{2}-\d{2}$/.test(releaseDate) || Number.isNaN(Date.parse(releaseDate)) ||
    new Date(releaseDate).toISOString().slice(0, 10) !== releaseDate)) {
  throw new Error("FASTEST_RELEASE_DATE must be a valid YYYY-MM-DD date");
}
const openccNotices = await Promise.all(["LICENSE", "THIRD_PARTY_LICENSES.md", "LICENSES/Apache-2.0.txt"]
  .map((name) => readFile(resolve(openccRoot, name), "utf8")));
const stylesheetNames = ["styles", "knowledge", "goals", "feedback", "catalog", "technology", "methods", "costs", "highlights", "profile-benchmarks", "locale"];
const [stylesheets, image, wikiNames, graph, fullGraph] = await Promise.all([
  Promise.all(stylesheetNames.map((name) => readFile(here(name + ".css"), "utf8"))),
  readFile(here("hero-gpu.png")),
  readdir(here("wiki/pages/")),
  readFile(here("wiki/graph.json"), "utf8").then(JSON.parse),
  readFile(here("wiki/graphify.json"), "utf8").then(JSON.parse),
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
let evidenceState = emptyEvidenceState;
if (pages) {
  approvals = await readResearchApprovals(process.env.FASTEST_RESEARCH_METADATA_APPROVALS);
  const stateFile = process.env.FASTEST_EVIDENCE_STATE;
  if (stateFile) evidenceState = validateEvidenceState(JSON.parse(await readFile(stateFile, "utf8")));
  const blocked = new Set(Object.keys(approvals).filter((id) => approvals[id].status === "withdrawn")
    .map((id) => createHash("sha256").update(id).digest("hex")));
  if (evidenceState.withdrawnSources?.some((hash) => !blocked.has(hash))) {
    throw new Error("Build approvals would restore a withdrawn research source");
  }
} else {
  researchIndex = await withPreviewResults(JSON.parse(researchPayload));
}
const catalogDirectory = fileURLToPath(here("."));
const withdrawn = Object.entries(approvals).filter(([, value]) => value.status === "withdrawn").map(([id]) => id);
const isWithdrawn = withdrawnReference(JSON.parse(researchPayload), approvals);
const published = catalogPostgres ? (await import("./catalog-pg.mjs")).readPublishedCatalog(catalogDatabase, catalogSnapshot) : null;
const modelFiles = published ?? await readCatalogModelFiles(catalogDirectory);
const projection = published && prepareCatalogRelease(published);
if (projection && ((withdrawn.length && isWithdrawn(JSON.stringify(published))) ||
    deniedCatalogPin(projection.manifest.release, evidenceState.paths))) {
  throw new Error("PostgreSQL catalog snapshot conflicts with active evidence withdrawals: " + catalogSnapshot);
}
if (pages) researchIndex = await writeResearchRelease(catalogDirectory, output, approvals);
const photos = published?.photos ?? await readCatalogPhotos(here("."));
const media = Object.fromEntries(Object.entries(photos).filter(([, asset]) => !isWithdrawn(asset.source)));
const publicDocuments = Object.fromEntries(Object.entries(documents)
  .filter(([, { evidence, status }]) => !isWithdrawn(evidence) && status !== "withdrawn")
  .map(([id, doc]) => {
    const clean = (text) => text.split("\n").filter((line) => !isWithdrawn(line)).join("\n");
    return [id, { ...doc, body: clean(doc.body), raw: clean(doc.raw) }];
  }));
const hardware = published?.hardware ?? await readHardwareCatalog(catalogDirectory, isWithdrawn);
if (!published) {
  const gpuPhotos = {
    "nvidia-geforce-rtx-4090": "rtx-4090",
    "nvidia-geforce-rtx-3090": "rtx-3090",
    "nvidia-geforce-rtx-3060-12gb": "rtx-3060",
    "intel-arc-b580": "arc-b580",
  };
  for (const card of hardware.catalog.cards) {
    const photo = media[gpuPhotos[card.id]];
    if (photo) card.photos = [photo];
  }
  hardware.digest = createHash("sha256").update(JSON.stringify({ catalog: hardware.catalog, manifest: hardware.manifest })).digest("hex");
}
const hardwareDirectory = {
  asOf: hardware.manifest.asOf,
  coverage: hardware.manifest.coverage,
  cards: hardware.catalog.cards.map(({ id, name, detail, aliases, source, memory, vendorSpec }) => ({ id, name, detail, aliases, source, memory, vendorSpec })),
  machines: hardware.catalog.machines.map(({ id, name, detail, kind, source }) => ({ id, name, detail, kind, source })),
};
const runtimes = published?.runtimes ?? JSON.parse(await readFile(here("catalog-runtimes.json"), "utf8")).map(({ references, ...row }) => ({
  ...row,
  references: (references ?? []).filter(({ href }) => !isWithdrawn(href)),
}));
let catalogRelease = "";
if (pages) {
  catalogRelease = projection ? await writeCatalogProjection(output, projection)
    : await writeCatalogRelease(catalogDirectory, output, hardware, runtimes, modelFiles);
}
let localCatalogRelease = "";
let localModelIds = [];
let topologyReports = published?.topologies;
if (!pages) {
  const localOutput = fileURLToPath(here("local-catalog/"));
  const { importLocalCatalog } = await import("./catalog-pg.mjs");
  const imported = await importLocalCatalog(hardware);
  topologyReports = imported.topologies;
  console.log(`Imported local PostgreSQL catalog snapshot ${imported.snapshotId}`);
  localCatalogRelease = await writeLocalCatalogProfiles(localOutput, imported, imported.modelLicenseNotice);
  localModelIds = imported.catalog.models.map(({ id }) => id);
}
topologyReports ??= (await import("./catalog-topology.json", { with: { type: "json" } })).default;
const publicTopologies = topologyReports.filter(({ source, id, links = [] }) =>
  ![source, id, ...links.map(link => link.source)].some(isWithdrawn));
const origin = pages ? releaseOrigin(process.env.FASTEST_RELEASE_ORIGIN) : null;
const scalingUrl = origin && origin + "/topology/scaling";
const wikiRelease = pages ? await writeWikiRelease({
  output,
  origin: process.env.FASTEST_PUBLIC_ORIGIN ?? "https://fastest.ai",
  researchRelease: researchIndex.release,
  catalogRelease,
  catalogApi: catalogPostgres,
  documents: publicDocuments,
  topologies: publicTopologies,
  scalingUrl,
  advisorUrl: origin && navigationHref("advisor", pages, origin),
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
    __FASTEST_CATALOG_POSTGRES__: String(catalogPostgres),
    __FASTEST_RELEASE_ORIGIN__: JSON.stringify(origin),
    __FASTEST_RESEARCH_INDEX__: JSON.stringify(researchIndex),
    __FASTEST_CATALOG_RELEASE__: JSON.stringify(catalogRelease),
    __FASTEST_MODEL_CATALOG__: JSON.stringify(modelFiles.source),
    __FASTEST_SUPPLEMENTAL_MODELS__: JSON.stringify(modelFiles.supplementalModels),
    __FASTEST_MODEL_IDENTITIES__: JSON.stringify(modelFiles.identities),
    __FASTEST_MODEL_DISCOVERY__: JSON.stringify(modelFiles.discovery),
    __FASTEST_RUNTIMES__: JSON.stringify(runtimes),
    __FASTEST_LOCAL_CATALOG_RELEASE__: JSON.stringify(localCatalogRelease),
    __FASTEST_LOCAL_MODEL_IDS__: JSON.stringify(localModelIds),
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
    __FASTEST_SCALING_URL__: JSON.stringify(scalingUrl),
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
<style>${stylesheets.join("\n")}${profileStyles}</style>
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
  const archive = process.env.FASTEST_RESEARCH_ARCHIVE;
  const retained = {};
  for (const [release, expected] of Object.entries(evidenceState.researchPins)) {
    if (release === researchIndex.release || deniedResearchPin(release, evidenceState.paths)) continue;
    if (!archive) throw new Error("FASTEST_RESEARCH_ARCHIVE is required for retained research pins");
    const pin = await readResearchPin(archive, release, expected);
    if (!allowedResearchPin(pin, approvals, evidenceState.paths) ||
      [...pin.files.values()].some((content) => isWithdrawn(content.toString("utf8")))) continue;
    await writeResearchPin(output, pin);
    retained[release] = expected;
  }
  await writeEvidenceState(output, { ...evidenceState, researchPins: retained }, isWithdrawn);
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
    if (name !== researchIndex.release && !Object.hasOwn(retained, name) && researchReleaseId.test(name)) {
      await rm(join(output, "research", name), { recursive: true, force: true });
    }
  }
  if (projection) {
    for (const root of ["catalog", "catalog-data"]) {
      for (const name of await readdir(join(output, root))) {
        if (name !== catalogRelease && catalogReleasePattern.test(name)) {
          await rm(join(output, root, name), { recursive: true, force: true });
        }
      }
    }
  }
} else {
  await writeFile(here("fastest-ai.html"), html);
}
