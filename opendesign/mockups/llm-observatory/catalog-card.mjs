import { catalogPath } from "./catalog-paths.mjs";

const htmlEntities = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
const escapeHtml = (value) => value.replace(/[&<>"']/g, (char) => htmlEntities[char]);
const escapeMarkdown = (value) => value.replace(/[\n\r]/g, " ").replace(/[\\`*_{}\[\]<>|]/g, "\\$&");

export function modelCard(row, release) {
  const { family, familySource, revision, artifacts = [] } = row.identity ?? {};
  const artifactSections = artifacts.map((artifact) => {
    const base = `https://huggingface.co/${artifact.repository}`;
    const pinned = base + "/blob/" + artifact.revision;
    return {
      title: artifact.path,
      fields: [
        ["Artifact repository", artifact.repository, base],
        ["Artifact revision", artifact.revision, base + "/tree/" + artifact.revision],
        ["Exact file", artifact.path, pinned + "/" + artifact.path],
        ["SHA-256 (upstream)", artifact.sha256],
        ["Format", artifact.format],
        ["Quantization", artifact.quantization ?? "Quantization unavailable"],
        ["Tokenizer file", artifact.tokenizer ?? "Tokenizer file unavailable", artifact.tokenizer && pinned + "/" + artifact.tokenizer],
        ["Artifact terms", artifact.license, pinned + "/LICENSE"],
      ],
    };
  });
  const runtimeFields = [
    ["GGUF", "llama.cpp", "llama.cpp"],
    ["Safetensors", "SGLang", "sglang"],
    ["Safetensors", "vLLM", "vllm"],
  ].filter(([format]) => artifacts.some((artifact) => artifact.format === format))
    .map(([format, name, id]) => [`Documented ${format} support`, name, "/" + catalogPath(release, "runtimes", id)]);
  return {
    title: row.id,
    kind: "Model repository",
    fields: [
      ["Repository", row.id, row.source],
      ["Family", family ?? "Family unavailable", familySource],
      ["Repository revision", revision ?? "Revision unavailable", revision && row.source + "/tree/" + revision],
      ["Exact artifact", artifacts.length ? `${artifacts.length} linked files` : "Exact artifact unavailable"],
      ["llmfit snapshot tags", row.detail || "Tags unavailable"],
      ["Model license tag", row.license || "Model license unavailable"],
      ...runtimeFields,
    ],
    sections: artifactSections,
    evidence: "Catalog metadata provides discovery. Tested compatibility, fit estimates and eligible benchmark results are unavailable in this catalog card.",
  };
}

export function runtimeCard(row) {
  return {
    title: row.name,
    kind: "Inference runtime",
    fields: [
      ["Project repository", row.name, row.source],
      ["Upstream release", row.tag, row.source + "/releases/tag/" + row.tag],
      ["Upstream release date", row.published],
      ["Release documentation", "Read the documentation", row.docs],
    ],
    sections: [{
      title: "Upstream documented support",
      fields: [
        ["Workload", row.workload, row.docs],
        ["Artifact format examples", row.formats, row.formatSource],
        ["Backend and platform examples", row.backends, row.backendSource],
        ["Models with this artifact format", "Browse the model catalog", "/#catalog/models?tag=" + encodeURIComponent(row.formats)],
      ],
    }],
    evidence: "Tested compatibility: No fastest.ai compatibility test is published in this release. Artifact, hardware, driver and runtime settings need their own test evidence.",
  };
}

export function hardwareCard(row, release, kind) {
  const path = (type, id) => "/" + catalogPath(release, type, id);
  const common = [["Catalog ID", row.id], ["Pinned source", "Open source record", row.source]];
  const untested = "Untested in this release. No reviewed measurement is published for this identity.";

  if (kind === "cards") {
    return {
      title: row.name,
      kind: row.kind,
      fields: [
        ...common,
        ["Manufacturer", row.manufacturer],
        ["Board or product variant", row.variant],
        ["Source names and lookup aliases", row.aliases.join(" · ") || "Unavailable"],
        ["Reported nominal memory per device", row.memory ?? "Unknown"],
        ["Runtime-usable memory", "Unknown"],
        ...(row.parent ? [["Related product family or calibration", row.parent, path("cards", row.parent)]] : []),
      ],
      sections: [
        ...(row.variants.length ? [{
          title: "Distinct related variants",
          fields: row.variants.map(({ id, name }) => ["Variant", name, path("cards", id)]),
        }] : []),
        ...(row.relatedProfiles.length ? [{
          title: "Research source records",
          fields: row.relatedProfiles.map(({ id }) => ["Hardware reference", id, path("machines", id)]),
        }] : []),
      ],
      evidence: untested,
    };
  }

  const sections = [{
    title: "Memory",
    fields: [
      ["Installed system memory", row.memory.system ?? "Unknown"],
      ["Reported nominal VRAM per device", row.memory.perDevice ?? "Unknown"],
      ["Reported aggregate VRAM inventory", row.memory.aggregate ?? "Unknown"],
      ["Reported allocation or limit", row.memory.allocation ?? "Unknown"],
      ["Runtime-usable memory", "Unknown"],
      ...(row.sourceMemory?.length ? [["Memory wording in source notes", row.sourceMemory.join(" · "), row.capture]] : []),
    ],
  }];
  if (row.bom?.length) {
    sections.push({
      title: "Reported components",
      fields: row.bom.map(({ category, part, quantity, source }) => [
        category, [part ?? "Part unknown", quantity ? `quantity ${quantity}` : "quantity unknown"].join(" · "), source,
      ]),
    });
  }
  return {
    title: row.name,
    kind: row.kind,
    fields: [
      ...common,
      ...(row.capture ? [["Source disclosure", "Open timestamped source", row.capture]] : []),
      ...(row.gpu ? [["Preset lookup label", row.gpu]] : []),
      ...(row.missingCoreFields ? [
        ["Core build fields disclosed", `${row.coreFieldsReported} of ${row.coreFieldsTotal}`],
        ["Missing core build fields", row.missingCoreFields.join(", ") || "None listed"],
        ["Interconnect", row.interconnect ?? "Unknown"],
      ] : []),
      ...row.cardIds.map((id) => ["Linked card reference", id, path("cards", id)]),
      ...(row.cardIds.length ? [] : [["Card identity", "No unambiguous discrete-card link in this snapshot"]]),
    ],
    sections,
    evidence: row.associations
      ? `${untested} ${row.associations} creator-reported research associations remain outside reviewed results.`
      : untested,
  };
}

function htmlFields(fields) {
  return `<dl>${fields.map(([name, value, href]) =>
    `<dt>${escapeHtml(name)}</dt><dd>${href ? `<a href="${escapeHtml(href)}">${escapeHtml(value)}</a>` : escapeHtml(value)}</dd>`).join("")}</dl>`;
}

function markdownFields(fields) {
  return fields.map(([name, value, href]) =>
    `- **${name}** — ${href ? `[${escapeMarkdown(value)}](<${href}>)` : escapeMarkdown(value)}`);
}

export function renderCard(card, { release, pathname, markdown }) {
  const root = `/catalog/${release}`;
  const htmlLink = pathname.replace(/\.(md|html)$/, ".html");
  const mdLink = pathname.replace(/\.(md|html)$/, ".md");
  const licenseLink = root + "/LICENSE.txt";
  const manifestLink = root + "/manifest.json";
  const sections = card.sections ?? [];

  if (markdown) {
    return [
      "---",
      `title: ${JSON.stringify(card.title)}`,
      `kind: ${JSON.stringify(card.kind)}`,
      `route: ${JSON.stringify(htmlLink)}`,
      `release: ${release}`,
      "locale: en",
      "---",
      "",
      `# ${escapeMarkdown(card.title)}`,
      "",
      ...markdownFields(card.fields),
      ...sections.flatMap(({ title, fields }) => ["", `## ${escapeMarkdown(title)}`, "", ...markdownFields(fields)]),
      "",
      "## Evidence",
      "",
      card.evidence,
      "",
      `[Coverage and source manifest](${manifestLink}) · [llmfit MIT notice](${licenseLink}) · [HTML card](${htmlLink})`,
      "",
    ].join("\n");
  }
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${escapeHtml(card.title)} | fastest.ai catalog</title>
<link rel="alternate" type="text/markdown" href="${mdLink}">
<style>
body{font:1rem/1.6 system-ui,sans-serif;max-width:50rem;margin:2rem auto;padding:0 1.25rem;color:#192b28;background:#fff}
h1{font-size:clamp(1.5rem,5vw,2.5rem);overflow-wrap:anywhere;line-height:1.2}
a{color:#12655a} dt{font-weight:600} dd{margin:0 0 .75rem;overflow-wrap:anywhere}
nav{display:flex;gap:1rem;flex-wrap:wrap} footer{margin-top:2rem;border-top:1px solid #b8c6c2;padding-top:1rem}
</style>
</head>
<body>
<header><nav aria-label="Catalog"><a href="/#catalog/cards">Cards</a><a href="/#catalog/machines">Machines</a><a href="/#catalog/models">Models</a><a href="/#catalog/runtimes">Runtimes</a><a href="${mdLink}">Markdown</a></nav></header>
<main>
<p>${escapeHtml(card.kind)}</p><h1>${escapeHtml(card.title)}</h1>
${htmlFields(card.fields)}
${sections.map(({ title, fields }) => `<section><h2>${escapeHtml(title)}</h2>${htmlFields(fields)}</section>`).join("\n")}
<h2>Evidence</h2><p>${escapeHtml(card.evidence)}</p>
</main>
<footer>Release <code>${release}</code> · <a href="${manifestLink}">Coverage and sources</a> · <a href="${licenseLink}">llmfit MIT notice</a></footer>
</body>
</html>
`;
}
