import { catalogPath, topologyRevisionHref } from "./catalog-paths.mjs";
import { cardPosition, cardRatings } from "./catalog-position.mjs";
import { profileStyles } from "./catalog-profile-styles.mjs";

const htmlEntities = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
const escapeHtml = (value) => value.replace(/[&<>"']/g, (char) => htmlEntities[char]);
const escapeMarkdown = (value) => value.replace(/[\n\r]/g, " ").replace(/[\\`*_{}\[\]<>|]/g, "\\$&");
const count = new Intl.NumberFormat("en");

function publisherEvaluationTable(evaluations) {
  if (!evaluations?.length) return null;
  return {
    title: "Publisher-reported benchmark results",
    summary: "These scores describe task quality in the publisher’s evaluation. Local inference performance and machine rankings require separate measurements.",
    headings: ["Benchmark", "Reported score", "Harness", "Execution hardware", "Pinned model-card row"],
    rows: evaluations.map(({ benchmark, version, scorePercent, harness, source, cardUrl, executionHardware }) => [
      [`${benchmark} v${version}`, source], [`${scorePercent}%`], [harness], [executionHardware ?? "Unknown"], ["Model card", cardUrl],
    ]),
  };
}

export function modelCard(row, release, { runtimeRoot = `/catalog/${release}`, discoveryCapture, agentTask } = {}) {
  const { supplemental } = row;
  const { family, familySource, artifacts = [] } = row.identity ?? {};
  const revision = row.identity?.revision ?? supplemental?.revision;
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
    .map(([format, name, id]) => [`Documented ${format} support`, name, `${runtimeRoot}/runtimes/${id}.html`]);
  const { popular, small } = row.discovery ?? {};
  const ranked = popular ?? small;
  return {
    title: row.id,
    kind: "Model repository",
    source: row.source,
    fields: [
      ["Repository", row.id, row.source],
      ["Family", family ?? "Family unavailable", familySource],
      ["Repository revision", revision ?? "Revision unavailable", revision && row.source + "/tree/" + revision],
      ["Exact artifact", artifacts.length ? `${artifacts.length} linked files` : "Exact artifact unavailable"],
      [supplemental ? "Publisher task" : "llmfit snapshot tags", row.detail || "Tags unavailable"],
      supplemental ? ["Model license", supplemental.licenseName, supplemental.licenseUrl]
        : ["Model license tag", row.license || "Model license unavailable"],
      ...runtimeFields,
    ],
    sections: [
      ...(supplemental ? [{
        title: "Reviewed publisher metadata",
        fields: [
          ["Publisher model card", "Pinned README", supplemental.cardUrl],
          ["Upstream revision date", supplemental.revisionDate, supplemental.infoUrl],
          ["Metadata reviewed", supplemental.capturedAt],
          ["Model card SHA-256", supplemental.cardSha256],
          ...(supplemental.licenseSha256 ? [["License file SHA-256", supplemental.licenseSha256]] : []),
          ["Publisher parameter counts", supplemental.parameters, supplemental.cardUrl],
          ["Input modalities", supplemental.inputs.join(", "), supplemental.cardUrl],
          ["Output modalities", supplemental.outputs.join(", "), supplemental.cardUrl],
        ],
      }] : []),
      ...(ranked && discoveryCapture ? [{
        title: "Hugging Face model discovery",
        fields: [
          ...(ranked.family ? [["Hub ranking family", ranked.family]] : []),
          ["Downloads in the Hub snapshot", count.format(ranked.downloads)],
          ["SafeTensors parameters", count.format(ranked.parameters)],
          ["Repository access", ranked.gated ? "Access approval required" : "Open"],
          ...(popular ? [["Popular rank", count.format(popular.rank)]] : []),
          ...(small ? [["Small rank", count.format(small.rank)]] : []),
          ["Ranking snapshot", discoveryCapture.capturedAt, discoveryCapture.source],
        ],
      }] : []),
      ...artifactSections,
      ...(agentTask ? [agentTask] : []),
    ],
    publisherEvaluations: publisherEvaluationTable(supplemental?.publisherEvaluations),
    evidence: agentTask
      ? "Catalog metadata provides discovery. The tool-policy report measures one inventory task under shared CI CPU conditions."
      : "Catalog metadata provides discovery. Tested compatibility, fit estimates and eligible local benchmark results are unavailable in this catalog card.",
  };
}

export function runtimeCard(row, { local = false } = {}) {
  const releaseUrl = row.releaseUrl ?? row.source + "/releases/tag/" + row.tag;
  return {
    title: row.name,
    kind: "Inference runtime",
    source: row.source,
    fields: [
      ["Upstream project", row.name, row.source],
      [row.revisionKind === "commit" ? "Pinned upstream commit" : "Upstream release", row.tag, releaseUrl],
      ["Upstream date", row.published],
      ...(row.category ? [["Project category", row.category]] : []),
      ...(row.latestRelease ? [["Latest verified upstream release", row.latestRelease.tag, row.latestRelease.url]] : []),
      ["Release documentation", "Read the documentation", row.docs],
    ],
    sections: [{
      title: "Upstream documented support",
      fields: [
        ["Workload", row.workload, row.docs],
        ["Artifact format examples", row.formats, row.formatSource],
        ["Backend and platform examples", row.backends, row.backendSource],
        ...(["GGUF", "Safetensors"].includes(row.formats) ? [["Models with this artifact format", "Browse the model catalog",
          (local ? "../../../../fastest-ai.html" : "/") + "#catalog/models?view=all&tag=" + encodeURIComponent(row.formats)]] : []),
      ],
    }, ...(row.references?.length ? [{ title: "Mentioned in video research", fields: row.references.map(
      ({ label, href }) => ["Transcript reference", label, href],
    ) }] : [])],
    evidence: "Tested compatibility: No fastest.ai compatibility test is published in this release. Artifact, hardware, driver and runtime settings need their own test evidence.",
  };
}

export function hardwareCard(row, release, kind, { local = false, peers = [], topologyRevision = row.topologyRevision } = {}) {
  const path = (type, id) => local ? `../${type}/${id}.html` : "/" + catalogPath(release, type, id);
  const common = [["Catalog ID", row.id], ["Pinned source", "Open source record", row.source]];
  const untested = "Untested in this release. No reviewed measurement is published for this identity.";

  if (kind === "cards") {
    const vendor = row.vendorSpec;
    const vendorFields = Object.entries(vendor?.facts ?? {}).map(([label, value]) => [label, value, vendor.source]);
    const memory = vendor?.facts["Memory configuration"] ?? vendor?.facts["Dedicated memory (GB)"];
    const bus = vendor?.facts["Memory bus"] ?? vendor?.facts["Memory bus (bits)"];
    const bandwidth = vendor?.facts["Memory bandwidth"] ?? vendor?.facts["Memory bandwidth (GB/s)"];
    const power = vendor?.facts["Rated graphics power (W)"];
    const maximumTdp = vendor?.facts["Maximum TDP (W)"];
    const boardPower = vendor?.facts["Board power (rated)"];
    const moduleMemory = vendor?.facts["Module memory (aggregate)"];
    const moduleBandwidth = vendor?.facts["Module bandwidth (aggregate)"];
    const withSource = (label, value) => [label, value ?? "Unknown", value && vendor?.source];
    const memoryField = moduleMemory ? withSource("Aggregate module capacity", moduleMemory)
      : memory ? withSource("Capacity / configuration", memory)
      : ["Capacity / configuration", row.memory ?? "Unknown", row.memory && row.source];
    const gallery = vendor?.gallery;
    const ratings = cardRatings(row);
    const peerRatings = peers.map(cardRatings);
    const graphic = (label, metric, unit) => ratings[metric] && {
      label, value: ratings[metric], unit,
      max: Math.max(ratings[metric], ...peerRatings.map(peer => peer[metric] ?? 0)),
    };
    return {
      title: row.name,
      kind: row.kind,
      source: vendor?.source ?? row.source,
      position: cardPosition(row, peers, id => path("cards", id)),
      visuals: [
        { title: "On-board memory", graphic: graphic("Nominal capacity", "capacity", "GB"), fields: [
          memoryField,
          withSource("Memory bus", bus),
          withSource(moduleBandwidth ? "Aggregate module bandwidth" : "Memory bandwidth", moduleBandwidth ?? bandwidth),
        ] },
        { title: "Host and power", graphic: graphic("Rated graphics power", "power", "W"), fields: [
          withSource("Host interface", vendor?.facts["Host interface"]),
          withSource(boardPower ? "Board power (rated)" : maximumTdp ? "Maximum TDP (W)" : "Rated graphics power (W)",
            boardPower ?? maximumTdp ?? power),
          withSource("Interconnect", vendor?.facts["Interconnect"]),
        ] },
      ],
      photos: row.photos ?? [],
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
        {
          title: "Manufacturer specifications",
          fields: vendor
            ? [
              ["Published product designation", vendor.designation, vendor.source],
              ["Specification applies to", vendor.scope ?? "Manufacturer product reference"],
              ...(vendor.locator ? [["Source locator", vendor.locator, vendor.source]] : []),
              ...(vendor.capturedAt ? [["Captured", vendor.capturedAt]] : []),
              ...vendorFields,
            ]
            : [["Source coverage", "No manufacturer specification has been matched to this identity."]],
        },
        ...(gallery ? [{
          title: "Product image source",
          fields: [["Source images", gallery.label, gallery.source], ["Depicted hardware", gallery.scope]],
        }] : []),
        ...(row.variants.length ? [{
          title: "Distinct related variants",
          fields: row.variants.map(({ id, name }) => ["Variant", name, path("cards", id)]),
        }] : []),
        ...(row.relatedMachines?.length ? [{
          title: "Linked machines and configurations",
          fields: row.relatedMachines.map(({ id, name }) => ["Machine or configuration", name, path("machines", id)]),
        }] : []),
        ...(row.relatedProfiles.length ? [{
          title: "Research source records",
          fields: row.relatedProfiles.map(({ id }) => ["Hardware reference", id, path("machines", id)]),
        }] : []),
        { title: "Retail availability", fields: [
          ["Variant-matched retail observations", "No approved observation is available in this catalog snapshot."],
        ] },
      ],
      evidence: untested,
    };
  }

  const factory = row.kind === "Complete factory configuration";
  const topology = topologyRevisionHref(topologyRevision, local ? "../../../../fastest-ai.html" : "/");
  const sections = [{
    title: "Memory",
    fields: [
      ["Installed system memory", row.memory.system ?? "Unknown"],
      ...(factory && !row.cardIds.length ? [
        ["Dedicated VRAM", "None (integrated GPU uses shared memory)"],
        ["Runtime-usable GPU memory", "Unknown"],
      ] : [
        ["Reported nominal VRAM per device", row.memory.perDevice ?? "Unknown"],
        ["Reported aggregate VRAM inventory", row.memory.aggregate ?? "Unknown"],
        ["Reported allocation or limit", row.memory.allocation ?? "Unknown"],
        [factory ? "Runtime-usable GPU memory" : "Runtime-usable memory", "Unknown"],
      ]),
      ...(row.sourceMemory?.length ? [["Memory wording in source notes", row.sourceMemory.join(" · "), row.capture]] : []),
    ],
  }];
  if (row.bom?.length) {
    sections.push({
      title: factory ? "System bill of materials" : "Reported components",
      fields: row.bom.map(({ category, part, quantity, source, locator }) => [
        category, [part ?? "Part unknown", quantity ? `quantity ${quantity}` : "quantity unknown", locator]
          .filter(Boolean).join(" · "), source,
      ]),
    });
  }
  if (row.documentedPower) {
    const { label, value, source, locator } = row.documentedPower;
    sections.push({
      title: "Power",
      fields: [
        [label, value, source],
        ["Source locator", locator, source],
        ["Measured system power", "Unavailable"],
      ],
    });
  }
  return {
    title: row.name,
    kind: row.kind,
    source: row.source,
    fields: [
      ...(factory ? [
        ["Catalog ID", row.id],
        ["Manufacturer configuration", row.configuration, row.source],
        ["Source locator", row.locator, row.source],
      ] : common),
      ...(!local && factory && row.fit ? [
        ["Model fit", "Estimate fit for this configuration", "/fit?machine=" + encodeURIComponent(row.id)],
      ] : []),
      ...(row.capture ? [["Source disclosure", "Open timestamped source", row.capture]] : []),
      ...(topology ? [["Topology revision", "Explore this configuration", topology]] : []),
      ...(row.gallery ? [["Manufacturer product gallery", row.gallery.label, row.gallery.source]] : []),
      ...(row.gpu ? [["Preset lookup label", row.gpu]] : []),
      ...(row.missingCoreFields ? [
        ["Core build fields disclosed", `${row.coreFieldsReported} of ${row.coreFieldsTotal}`],
        ["Missing core build fields", row.missingCoreFields.join(", ") || "None listed"],
      ] : []),
      ...(row.interconnect || row.missingCoreFields ? [["Interconnect", row.interconnect ?? "Unknown"]] : []),
      ...row.cardIds.map((id) => ["Linked card reference", id, path("cards", id)]),
      ...(!factory && !row.cardIds.length ? [["Card identity", "No unambiguous discrete-card link in this snapshot"]] : []),
    ],
    sections,
    evidence: row.associations
      ? `${untested} ${row.associations} creator-reported research associations remain outside reviewed results.`
      : untested,
  };
}

function htmlFields(fields) {
  return `<dl class="profile-fields">${fields.map(([name, value, href]) =>
    `<div><dt>${escapeHtml(name)}</dt><dd>${href ? `<a href="${escapeHtml(href)}">${escapeHtml(value)}</a>` : escapeHtml(value)}</dd></div>`).join("")}</dl>`;
}

function ratingScale({ label, value, max, unit }) {
  return `${label} · ${value} ${unit} on the catalog scale of 0–${max} ${unit}`;
}

function htmlSpecGraphic(graphic) {
  const text = escapeHtml(ratingScale(graphic));
  return `<figure class="profile-spec-graphic"><meter min="0" max="${graphic.max}" value="${graphic.value}" aria-label="${text}"></meter><figcaption>${text}</figcaption></figure>`;
}

function markdownFields(fields) {
  return fields.map(([name, value, href]) =>
    `- **${name}** — ${href ? `[${escapeMarkdown(value)}](<${href}>)` : escapeMarkdown(value)}`);
}

const positionTitle = "GPU position by rated specifications";
const positionBasis = "Manufacturer-rated specifications. Each point is one GPU identity with a single reported capacity and a value on both axes.";
const noPosition = "This GPU has no unambiguous pair of rated specifications for these axes.";

function evaluationsHtml({ title, summary, headings, rows }) {
  const rowHtml = rows.map((row) => {
    const [[label, link], ...other] = row;
    return `<tr><th scope="row"><a href="${escapeHtml(link)}">${escapeHtml(label)}</a></th>${
      other.map(([value, href]) => `<td>${href ? `<a href="${escapeHtml(href)}">${escapeHtml(value)}</a>`
        : escapeHtml(value)}</td>`).join("")}</tr>`;
  }).join("\n");
  return `<section class="profile-section"><h2>${escapeHtml(title)}</h2><p>${escapeHtml(summary)}</p>
<table class="profile-chart-table"><thead><tr>${headings.map(heading => `<th scope="col">${escapeHtml(heading)}</th>`).join("")}</tr></thead>
<tbody>${rowHtml}</tbody></table></section>`;
}

function evaluationsMarkdown({ title, summary, headings, rows }) {
  return [`## ${title}`, "", summary, "", `| ${headings.join(" | ")} |`,
    `| ${headings.map(() => "---").join(" | ")} |`,
    ...rows.map(row => `| ${row.map(([value, href]) => href ? `[${escapeMarkdown(value)}](<${href}>)`
      : escapeMarkdown(value)).join(" | ")} |`), ""];
}

function positionHtml({ label, points, selected }) {
  const max = (values, step) => Math.max(step, Math.ceil(Math.max(...values) / step) * step);
  const x = max(points.map(point => point.capacity), 16);
  const y = max(points.map(point => point.value), 100);
  const aria = point => `${point.name}, ${point.capacity} GB, ${point.value} ${label}`;
  const current = point => point === selected ? ' aria-current="page"' : "";
  return `<section class="profile-section"><h2>${positionTitle}</h2><p>${positionBasis}</p>
<div class="profile-chart"><span class="profile-chart-y">${escapeHtml(label)}</span>
<div class="profile-chart-grid" role="group" aria-label="GPU position map">
<span class="profile-chart-max">${y}</span>
${points.map(point => `<a class="profile-chart-dot" href="${escapeHtml(point.href)}"${current(point)}
  style="left:${point.capacity / x * 100}%;bottom:${point.value / y * 100}%"
  title="${escapeHtml(aria(point))}" aria-label="${escapeHtml(aria(point))}"></a>`).join("")}</div>
<div class="profile-chart-x"><span>0</span><span>Nominal GPU memory (GB)</span><span>${x}</span></div></div>
<div class="profile-chart-legend"><span>${points.length} plotted GPUs</span>${selected
    ? `<strong>◆ ${escapeHtml(selected.name)} · ${selected.capacity} GB · ${selected.value} ${label.match(/\(([^)]+)\)$/)[1]}</strong>`
    : `<span>${noPosition}</span>`}</div>
<details><summary>View chart data</summary><table class="profile-chart-table">
<thead><tr><th scope="col">GPU</th><th scope="col">Memory (GB)</th><th scope="col">${escapeHtml(label)}</th><th scope="col">Source</th></tr></thead><tbody>
${points.map(point => `<tr${current(point)}><th scope="row"><a href="${escapeHtml(point.href)}">${escapeHtml(point.name)}</a></th>
<td>${point.capacity}</td><td>${point.value}</td><td><a href="${escapeHtml(point.source)}">Manufacturer</a></td></tr>`).join("")}
</tbody></table></details></section>`;
}

export function renderCard(card, { release, pathname, markdown, local = false }) {
  const depth = pathname.startsWith("catalog/") ? pathname.split("/").length - 3 : 1;
  const root = local ? Array(depth).fill("..").join("/") : `/catalog/${release}`;
  const linksFrom = local ? pathname.split("/").at(-1) : pathname;
  const htmlLink = linksFrom.replace(/\.(md|html)$/, ".html");
  const mdLink = linksFrom.replace(/\.(md|html)$/, ".md");
  const licenseLink = root + "/LICENSE.txt";
  const manifestLink = root + "/manifest.json";
  const home = local ? root + "/../../../fastest-ai.html" : "/";
  const sections = card.sections ?? [];
  const visuals = card.visuals ?? [];
  const photos = card.photos ?? [];
  const position = card.position;
  const evaluations = card.publisherEvaluations;

  if (markdown) {
    return [
      "---",
      `title: ${JSON.stringify(card.title)}`,
      `kind: ${JSON.stringify(card.kind)}`,
      `route: ${JSON.stringify(pathname.replace(/\.(md|html)$/, ".html"))}`,
      `release: ${release}`,
      "locale: en",
      "---",
      "",
      `# ${escapeMarkdown(card.title)}`,
      "",
      ...visuals.flatMap(({ title, fields, graphic }) => [
        `## ${escapeMarkdown(title)}`, "", ...(graphic ? [ratingScale(graphic), ""] : []), ...markdownFields(fields), "",
      ]),
      ...photos.map(({ alt, source, credit, license, licenseUrl }) =>
        `- [${escapeMarkdown(alt)}](<${source}>) · ${escapeMarkdown(credit)}${licenseUrl ? ` · [${escapeMarkdown(license)}](<${licenseUrl}>)` : ""}`),
      ...(position ? [
        `## ${positionTitle}`, "", positionBasis, "",
        position.selected ? `Selected GPU: ${position.selected.capacity} GB · ${position.label}: ${position.selected.value}` : noPosition,
        "", `| GPU | Memory (GB) | ${position.label} | Source |`, "| --- | ---: | ---: | --- |",
        ...position.points.map(point => `| [${escapeMarkdown(point.name)}](<${point.href}>) | ${point.capacity} | ${point.value} | [Manufacturer](<${point.source}>) |`),
        "",
      ] : []),
      ...markdownFields(card.fields),
      ...sections.flatMap(({ title, fields }) => ["", `## ${escapeMarkdown(title)}`, "", ...markdownFields(fields)]),
      ...(evaluations ? ["", ...evaluationsMarkdown(evaluations)] : []),
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
<style>${profileStyles}</style>
</head>
<body class="profile-document"><div class="profile-shell">
<header><nav class="profile-nav" aria-label="Catalog"><a href="${home}">fastest.ai / localdecode.com</a><a href="${home}#catalog/cards">Cards</a><a href="${home}#catalog/machines">Machines</a><a href="${home}#catalog/models">Models</a><a href="${home}#catalog/runtimes">Runtimes</a></nav></header>
<main>
<div class="profile-hero"><p class="profile-kicker">${escapeHtml(card.kind)}</p><h1>${escapeHtml(card.title)}</h1>
<p class="profile-evidence">${escapeHtml(card.evidence)}</p>
<div class="profile-actions">${card.source ? `<a href="${escapeHtml(card.source)}">Open source</a>` : ""}<a href="${mdLink}">Markdown</a></div></div>
${visuals.length ? `<div class="profile-specs">${visuals.map(({ title, fields, graphic }) =>
  `<section class="profile-section"><h2>${escapeHtml(title)}</h2>${graphic ? htmlSpecGraphic(graphic) : ""}${htmlFields(fields)}</section>`).join("")}</div>` : ""}
${position ? positionHtml(position) : ""}
${photos.length ? `<div class="profile-gallery">${photos.map(({ data, alt, source, credit, license, licenseUrl }) =>
  `<figure><img loading="lazy" src="${escapeHtml(data)}" alt="${escapeHtml(alt)}"><figcaption>
  ${escapeHtml(alt)} · <a href="${escapeHtml(source)}">${escapeHtml(credit)}</a>${licenseUrl ? ` · <a href="${escapeHtml(licenseUrl)}">${escapeHtml(license)}</a>` : ""}
  </figcaption></figure>`).join("")}</div>` : ""}
<section class="profile-section"><h2>Catalog details</h2>${htmlFields(card.fields)}</section>
${sections.map(({ title, fields }) => `<section class="profile-section"><h2>${escapeHtml(title)}</h2>${htmlFields(fields)}</section>`).join("\n")}
${evaluations ? evaluationsHtml(evaluations) : ""}
</main>
<footer class="profile-footer">Release <code>${release}</code> · <a href="${manifestLink}">Coverage and sources</a> · <a href="${licenseLink}">llmfit MIT notice</a></footer></div>
</body>
</html>
`;
}
