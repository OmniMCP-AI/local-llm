import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { filterResearch } from "./research-filter.mjs";
import { renderResearchHtml, renderResearchMarkdown } from "./research-release-render.mjs";

const sha256 = (bytes) => createHash("sha256").update(bytes).digest("hex");
const json = (value) => JSON.stringify(value, null, 2) + "\n";

// Reviewed editorial associations for the methods already described in the wiki.
const methodTopics = [
  ["hardware-selection", "model-fit"], ["hardware-selection", "distributed-inference"],
  ["hardware-selection", "ownership-cost"], ["hardware-selection", "ownership-cost"],
  ["ownership-cost", "hardware-selection"], ["model-fit", "runtime-tuning"],
  ["runtime-tuning", "model-fit"], ["runtime-tuning", "interactive-chat"],
  ["interactive-chat", "runtime-tuning"], ["multi-user-serving"],
  ["distributed-inference", "runtime-tuning"], ["distributed-inference"],
  ["runtime-tuning"], ["model-evaluation"], ["retrieval"], ["agent-workflows", "model-evaluation"],
  ["ownership-cost"], ["ownership-cost"], ["ownership-cost"], ["ownership-cost"],
];
const methodGates = [
  [6, "M1–M2", "Confirm device capacity, price scope and market. Use a complete bill of materials for whole-build totals and matched positive gains for cost per performance gained."],
  [10, "M1–M3", "Pin the workload and use eligible solo runs. Require cache, load, concurrency and sample counts for latency and serving curves."],
  [13, "M2–M3", "Identify the physical layout. Publish speedup only with matched hardware or runtime treatments."],
  [16, "M1–M4", "Pin task rubrics and acceptance criteria. Control retrieval depth and attempts. Pin tool, task, quality and deadline boundaries for agent runs."],
  [20, "M2–M4", "Disclose scenario assumptions and rate dates. Meter energy with a stated boundary. Verify delivery capacity, equivalent output and cash flows for team or payback claims."],
];

function readMethods(markdown, vocabulary) {
  const methods = [];
  const pattern = /^- \*\*(\d+)\. (.+?)\.\*\* (.+) \[([^\]]+)\]\((https:\/\/www\.youtube\.com\/watch\?v=[\w-]{11}&t=\d+s)\)$/gm;
  for (const [, number, title, summary, citation, url] of markdown.matchAll(pattern)) {
    const position = Number(number);
    if (position !== methods.length + 1 || !methodTopics[position - 1]?.every((id) => Object.hasOwn(vocabulary.topics, id))) {
      throw new Error("Unexpected research method: " + number);
    }
    const [, milestones, requirement] = methodGates.find(([last]) => position <= last);
    methods.push({ id: "method-" + number.padStart(2, "0"), title, summary, citation, url,
      topics: methodTopics[position - 1], gate: { milestones, requirement } });
  }
  if (methods.length !== methodTopics.length) throw new Error("Incomplete timestamped methods inventory");
  return methods;
}

function selectSources(index, approvals) {
  const selected = [];
  for (const source of index.sources) {
    const decision = approvals[source.id];
    if (source.format !== "video" && source.records.length === 0 && !decision) {
      selected.push({ ...source, publicationScope: "editorial-reference" });
      continue;
    }
    if (!decision || decision.status === "withdrawn") continue;
    if (decision.status !== "approved-metadata" || typeof decision.review !== "string" || !decision.review.trim() ||
        decision.sha256 !== sha256(JSON.stringify(source))) {
      throw new Error("Missing or stale research metadata approval for " + source.id);
    }
    selected.push({ ...source, publicationScope: "approved-metadata" });
  }
  if (Object.keys(approvals).some((id) => !index.sources.some((source) => source.id === id))) {
    throw new Error("Research approval refers to an unknown source ID");
  }
  return filterResearch(selected, { query: "" }, "en", () => "").map(({ source }) => source);
}

function selectGraph(graph, sources, vocabulary) {
  const retained = new Set(sources.flatMap(({ id, records }) => [id, ...records.flatMap((row) => [row.id, row.series])]));
  for (const facet of ["topics", "dimensions", "formats"]) {
    for (const id of Object.keys(vocabulary[facet])) retained.add(facet + "/" + id);
  }
  retained.add("research");
  return {
    directed: true, multigraph: false,
    nodes: graph.nodes.filter(({ id }) => retained.has(id)).map(({ id, label, file_type }) => ({ id, label, file_type })),
    links: graph.links.filter(({ source, target }) => retained.has(source) && retained.has(target))
      .map(({ source, target, relation, confidence, source_location, taxonomy_version, annotation_file }) => ({
        source, target, relation, confidence, source_location, taxonomy_version, annotation_file,
      })),
    hyperedges: [],
  };
}

export async function writeResearchRelease(directory, output, approvals = {}) {
  const wiki = (name) => readFile(join(directory, "wiki", name), "utf8");
  const [sourceText, vocabularyText, graphText, methodsMarkdown, client, filter, renderer, builder] = await Promise.all([
    wiki("research-index.json"), wiki("context-vocabulary.json"), wiki("graphify.json"), wiki("pages/comparison-methods.md"),
    ...["research-release-client.mjs", "research-filter.mjs", "research-release-render.mjs", "research-release-build.mjs"]
      .map((name) => readFile(join(directory, name), "utf8")),
  ]);
  const sourceIndex = JSON.parse(sourceText);
  const vocabulary = JSON.parse(vocabularyText);
  const graph = JSON.parse(graphText);
  if (graph.graph.research_index_sha256 !== sha256(sourceText) ||
      graph.graph.research_inputs["context-vocabulary.json"] !== sha256(vocabularyText)) {
    throw new Error("Research release inputs disagree with Graphify. Rebuild wiki/rebuild_graph.py.");
  }

  const taxonomyVersion = sourceIndex.taxonomyVersion;
  const sources = selectSources(sourceIndex, approvals);
  const methods = readMethods(methodsMarkdown, vocabulary).filter(({ url }) =>
    approvals["youtube/" + new URL(url).searchParams.get("v")]?.status !== "withdrawn");
  const publicGraph = selectGraph(graph, sources, vocabulary);
  const input = { taxonomyVersion, vocabulary, sources, methods };
  const release = "v1-" + sha256(json([input, publicGraph, client, filter, renderer, builder])).slice(0, 16);
  const index = { release, ...input };
  const artifacts = {
    "library.html": renderResearchHtml(index),
    "library.md": renderResearchMarkdown(index),
    "index.json": json(index),
    "graphify.json": json({ ...publicGraph, graph: { release, taxonomy_version: taxonomyVersion } }),
    "library.mjs": client,
    "research-filter.mjs": filter,
  };
  artifacts["manifest.json"] = json({
    release, taxonomyVersion,
    scope: "Research discovery metadata",
    coverage: { sources: sources.length, records: sources.reduce((count, source) => count + source.records.length, 0),
      methods: methods.length },
    artifacts: Object.fromEntries(Object.entries(artifacts).map(([name, artifact]) => [name, sha256(artifact)])),
  });

  const target = join(output, "research", release);
  await mkdir(target, { recursive: true });
  await Promise.all(Object.entries(artifacts).map(([name, value]) => writeFile(join(target, name), value)));
  return index;
}
