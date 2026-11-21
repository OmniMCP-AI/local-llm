import { catalogPath, hardwareDirectoryPath, modelCollectionPath, runtimeDirectoryPath, topologyRevisionHref } from "./catalog-paths.mjs";
import { bandwidthAxis, cardPosition, cardRatings, memoryAxis, speedAxis } from "./catalog-position.mjs";
import { axisTitle, renderCoordinatePlot } from "./coordinate-plot.mjs";
import { profileStyles } from "./catalog-profile-styles.mjs";
import { navigationHref, navigationRoutes } from "./release-origin.mjs";
import { languages } from "./locale-settings.mjs";
import { rates, supplementalRates } from "./display-fx.mjs";
import { siteTranslations, eastAsianGermanSiteTranslations } from "./site-translations.js";

const htmlEntities = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
export const escapeHtml = (value) => value.replace(/[&<>"']/g, (char) => htmlEntities[char]);
export const escapeMarkdown = (value) => value.replace(/[\n\r]/g, " ").replace(/[\\`*_{}\[\]<>|]/g, "\\$&");
const count = new Intl.NumberFormat("en");

function publisherEvaluationTable(evaluations) {
  if (!evaluations?.length) return null;
  return {
    title: "Publisher-reported benchmark results",
    summary: "These scores describe task quality in the publisher’s evaluation. Local inference performance and machine rankings require separate measurements.",
    headings: ["Benchmark", "Reported score", "Harness", "Execution hardware", "Benchmark run date", "Publication date", "Model-card revision date", "Ingestion date", "Pinned model-card row"],
    rows: evaluations.map(({ benchmark, version, scorePercent, metric, harness, source, cardUrl, executionHardware, dates }) => [
      [`${benchmark} v${version}`, source], [`${scorePercent}%${metric ? " " + metric : ""}`],
      [harness], [executionHardware ?? "Unknown"],
      ...["origin", "publication", "revision", "ingestion"].map(key => [dates?.[key]?.value ?? "Unknown", dates?.[key]?.source]),
      ["Model card", cardUrl],
    ]),
  };
}

export function modelCard(row, release, { runtimeRoot = `/catalog/${release}`, runtimeHref, discoveryCapture, agentTask } = {}) {
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
    .map(([format, name, id]) => [`Documented ${format} support`, name,
      runtimeHref ? runtimeHref(id) : `${runtimeRoot}/runtimes/${id}.html`]);
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
      ...(supplemental ? [["Publisher task", supplemental.task ?? row.detail]] : []),
      ...(!supplemental || supplemental.inUpstream ? [["llmfit snapshot tags", row.detail || "Tags unavailable"]] : []),
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
          ...(supplemental.licenseNote ? [["License conditions", supplemental.licenseNote, supplemental.licenseUrl]] : []),
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

export function runtimeCard(row, { local = false, observation, review = false } = {}) {
  const releaseUrl = row.releaseUrl ?? row.source + "/releases/tag/" + row.tag;
  return {
    title: row.name,
    kind: "Inference runtime",
    source: row.source,
    fields: [
      ["Upstream project", row.name, row.source],
      ...(review ? [["Runtime ID", row.id]] : []),
      [row.revisionKind === "commit" ? "Pinned upstream commit" : "Upstream release", row.tag, releaseUrl],
      ["Upstream date", row.published],
      ...(row.category ? [["Project category", row.category]] : []),
      ...(row.latestRelease ? [["Latest verified upstream release", row.latestRelease.tag, row.latestRelease.url]] : []),
      ["Release documentation", "Read the documentation", row.docs],
    ],
    sections: [...(observation ? [{
      title: "Runtime release watch",
      fields: [
        ["Last observed stable release", observation.release?.tag ?? "No stable release observed", observation.release?.url],
        ...(observation.release ? [["Release published", observation.release.publishedAt]] : []),
        ["Last successful refresh", observation.refreshedAt],
        ...(observation.stale ? [["Feed status", "The retained release feed is stale."]] : []),
        ...(observation.failed ? [["Latest refresh", "The refresh failed."]] : []),
        ["Official releases", "Publisher release history", observation.feedUrl],
        ["Watch history", "Open the runtime release watch", observation.watchUrl],
      ],
    }] : []), {
      title: "Upstream documented support",
      fields: [
        ["Workload", row.workload, row.docs],
        ["Artifact format examples", row.formats, row.formatSource],
        ["Backend and platform examples", row.backends, row.backendSource],
        ["Tested driver, hardware and settings", "No reviewed matching test in this release"],
        ["Tested context, cache and concurrency", "Not reported in this release"],
        ...(!review && ["GGUF", "Safetensors"].includes(row.formats) ? [["Models with this artifact format", "Browse the model catalog",
          (local ? "../../../../fastest-ai.html" : "/") + "#catalog/models?view=all&tag=" + encodeURIComponent(row.formats)]] : []),
      ],
    }, ...(row.references?.length ? [{ title: "Mentioned in video research", fields: row.references.map(
      ({ label, href }) => ["Transcript reference", label, href],
    ) }] : [])],
    evidence: "Tested compatibility: No fastest.ai compatibility test is published in this release. Artifact, hardware, driver and runtime settings need their own test evidence.",
  };
}

export function hardwareCard(row, release, kind, {
  local = false, peers = [], topologyRevision = row.topologyRevision, reviewProfileHref,
} = {}) {
  const path = reviewProfileHref ?? ((type, id) => local ? `../${type}/${id}.html` : "/" + catalogPath(release, type, id));
  const common = [["Catalog ID", row.id], ["Pinned source", "Open source record", row.source]];
  const untested = "Untested in this release. No reviewed measurement is published for this identity.";

  if (kind === "cards") {
    const vendor = row.vendorSpec;
    const modified = row.modification;
    const firstEvidence = modified?.evidence[0].source;
    const reportedCapacity = modified?.capacityGb != null ? `${modified.capacityGb} GB` : null;
    const bandwidthSource = vendor?.bandwidthSource ?? vendor?.source;
    const vendorFields = Object.entries(vendor?.facts ?? {}).map(([label, value]) =>
      [label, value, label === "Memory bandwidth" ? bandwidthSource : vendor.source]);
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
      : modified ? ["Reported modified capacity", reportedCapacity ?? "Unknown", reportedCapacity && firstEvidence]
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
          moduleBandwidth ? withSource("Aggregate module bandwidth", moduleBandwidth)
            : ["Memory bandwidth", bandwidth ?? "Unknown", bandwidth && bandwidthSource],
        ] },
        { title: "Host and power", graphic: graphic("Rated graphics power", "power", "W"), fields: [
          withSource("Host interface", vendor?.facts["Host interface"]),
          withSource(boardPower ? "Board power (rated)" : maximumTdp ? "Maximum TDP (W)" : "Rated graphics power (W)",
            boardPower ?? maximumTdp ?? power),
          withSource("Interconnect", vendor?.facts["Interconnect"]),
        ] },
      ],
      photos: row.photos ?? [],
      gallery,
      fields: [
        ...common,
        ["Manufacturer", row.manufacturer],
        ["Board or product variant", row.variant],
        ["Source names and lookup aliases", row.aliases.join(" · ") || "Unavailable"],
        ...(!modified ? [["Reported nominal memory per device", row.memory ?? "Unknown"], ["Runtime-usable memory", "Unknown"]] : []),
        ...(row.parent ? [[modified ? "Base GPU identity" : "Related product family or calibration", row.parent, path("cards", row.parent)]] : []),
      ],
      sections: [
        ...(modified ? [{
          title: "Memory modification evidence",
          fields: [
            ["Stock capacity before modification", modified.stockGb != null ? `${modified.stockGb} GB` : "Unknown",
              modified.stockGb != null && firstEvidence],
            ["Modified capacity scope", modified.capacityScope, firstEvidence],
            ...(modified.installedGb != null ? [["Reported installed memory", `${modified.installedGb} GB`, firstEvidence]] : []),
            ...(modified.validatedGb != null ? [["Reported tested framebuffer", `${modified.validatedGb} GB`, firstEvidence]] : []),
            ["Runtime-usable memory", modified.usableGb != null ? `${modified.usableGb} GB` : "Unknown",
              modified.usableGb != null && firstEvidence],
            ...modified.evidence.map(({ kind, source, detail }) => [kind, detail, source]),
          ],
        }] : []),
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
  const creator = row.buildSource;
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
    photos: row.photos,
    video: row.video && { credit: creator?.author, ...row.video },
    fields: [
      ...(factory ? [
        ["Catalog ID", row.id],
        ["Manufacturer configuration", row.configuration, row.source],
        ["Source locator", row.locator, row.source],
      ] : common),
      ...(creator ? [
        ["Builder", creator.author],
        ["Source platform", creator.platform, row.source],
        ["Source locator", creator.locator, row.source],
      ] : []),
      ...(!local && !reviewProfileHref && factory && row.fit ? [
        ["Model fit", "Estimate fit for this configuration", "/fit?machine=" + encodeURIComponent(row.id)],
      ] : []),
      ...(row.capture ? [["Source disclosure", "Open timestamped source", row.capture]] : []),
      ...(topology ? [["Topology revision", reviewProfileHref ? topologyRevision : "Explore this configuration",
        reviewProfileHref ? null : topology]] : []),
      ...(row.gallery ? [[creator ? "Photographs at the source" : "Manufacturer product gallery", row.gallery.label, row.gallery.source]] : []),
      ...(row.gpu ? [["Preset lookup label", row.gpu]] : []),
      ...(row.missingCoreFields ? [
        ["Core build fields disclosed", `${row.coreFieldsReported} of ${row.coreFieldsTotal}`],
        ["Missing core build fields", row.missingCoreFields.join(", ") || "None listed"],
      ] : []),
      ...(row.interconnect || row.missingCoreFields ? [["Interconnect", row.interconnect ?? "Unknown"]] : []),
      ...row.cardIds.map((id) => ["Linked card reference", id, path("cards", id)]),
      ...(!factory && !creator && !row.cardIds.length ? [["Card identity", "No unambiguous discrete-card link in this snapshot"]] : []),
    ],
    sections,
    evidence: creator
      ? "Hardware disclosed by the builder. Reviewed benchmark results are unavailable for this build."
      : row.associations
      ? `${untested} ${row.associations} creator-reported research associations remain outside reviewed results.`
      : untested,
  };
}

export function htmlFields(fields) {
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

export function markdownFields(fields) {
  return fields.map(([name, value, href]) =>
    `- **${name}** — ${href ? `[${escapeMarkdown(value)}](<${href}>)` : escapeMarkdown(value)}`);
}

const positionTitle = "GPU position by rated specifications";
const positionBasis = "Manufacturer-rated specifications. Each point is one GPU identity with a single reported capacity and a value on both axes.";
const speedTitle = "Measured GPU decode speed";
const speedUnavailable = "Measured decode speed unavailable. This release has no matched, reviewed single-GPU cohort for one model, artifact, context and runtime protocol.";
const gpuAxis = { label: "GPU", categorical: true };
const imageSourceTitle = "Product image source";
const imageSourceFields = gallery => [["Source images", gallery.label, gallery.source], ["Depicted hardware", gallery.scope]];

function evaluationsHtml({ title, summary, headings, rows }, heading) {
  const rowHtml = rows.map((row) => {
    const [[label, link], ...other] = row;
    return `<tr><th scope="row"><a href="${escapeHtml(link)}">${escapeHtml(label)}</a></th>${
      other.map(([value, href]) => `<td>${href ? `<a href="${escapeHtml(href)}">${escapeHtml(value)}</a>`
        : escapeHtml(value)}</td>`).join("")}</tr>`;
  }).join("\n");
  return `<section class="profile-section"><${heading}>${escapeHtml(title)}</${heading}><p>${escapeHtml(summary)}</p>
<table class="profile-chart-table"><thead><tr>${headings.map(heading => `<th scope="col">${escapeHtml(heading)}</th>`).join("")}</tr></thead>
<tbody>${rowHtml}</tbody></table></section>`;
}

function evaluationsMarkdown({ title, summary, headings, rows }) {
  return [`## ${title}`, "", summary, "", `| ${headings.join(" | ")} |`,
    `| ${headings.map(() => "---").join(" | ")} |`,
    ...rows.map(row => `| ${row.map(([value, href]) => href ? `[${escapeMarkdown(value)}](<${href}>)`
      : escapeMarkdown(value)).join(" | ")} |`), ""];
}

function positionHtml({ id, name, points, capacityPoints }, heading) {
  const selected = points.find(point => point.id === id);
  const capacity = capacityPoints.find(point => point.id === id);
  const active = point => point.id === id ? ' aria-current="page"' : "";
  const atlas = {
    title: positionTitle, xAxis: memoryAxis, yAxis: bandwidthAxis, points, selectedId: id,
    emptyText: "The release has no comparable manufacturer-rated memory and bandwidth pairs.",
  };
  const gpuLabels = new Map(capacityPoints.map(point => [point.id, point.short]));
  const memory = {
    title: "GPU memory capacity", xAxis: { ...gpuAxis, formatTick: id => gpuLabels.get(id) }, yAxis: memoryAxis, kind: "bar", points: capacityPoints,
    selectedId: id, emptyText: "The release has no comparable manufacturer-rated memory capacities.",
  };
  const speed = { title: speedTitle, xAxis: memoryAxis, yAxis: speedAxis, points: [], emptyText: speedUnavailable };
  return `<section class="profile-section"><${heading}>${positionTitle}</${heading}><p>${positionBasis}</p>
<p class="profile-chart-note">${selected ? `◆ Selected GPU: ${escapeHtml(name)} · ${selected.x} GB · ${selected.y} GB/s`
    : `${escapeHtml(name)} has no unambiguous pair of rated specifications for these axes.`}</p>
${renderCoordinatePlot(atlas)}
<details><summary>View chart data (${points.length} GPUs)</summary><table class="profile-chart-table">
<thead><tr><th scope="col">GPU</th><th scope="col">${axisTitle(memoryAxis)}</th><th scope="col">${axisTitle(bandwidthAxis)}</th><th scope="col">Source</th></tr></thead><tbody>
${points.map(point => `<tr${active(point)}><th scope="row"><a href="${escapeHtml(point.href)}">${escapeHtml(point.name)}</a></th>
<td>${point.x}</td><td>${point.y}</td><td>${point.bandwidthSource !== point.source
    ? `<a href="${escapeHtml(point.source)}">Capacity</a> · <a href="${escapeHtml(point.bandwidthSource)}">Bandwidth</a>`
    : `<a href="${escapeHtml(point.source)}">Manufacturer</a>`}</td></tr>`).join("")}
</tbody></table></details></section>
<section class="profile-section"><${heading}>GPU memory capacity</${heading}>
<p>Manufacturer-rated memory per GPU, ordered by capacity.</p>
<p class="profile-chart-note">${capacity ? `◆ Selected GPU: ${escapeHtml(name)} · ${capacity.y} GB`
    : `${escapeHtml(name)} has no unambiguous manufacturer-rated capacity on this scale.`}</p>
${renderCoordinatePlot(memory)}
<details><summary>View memory data (${capacityPoints.length} GPUs)</summary><table class="profile-chart-table">
<thead><tr><th scope="col">GPU</th><th scope="col">${axisTitle(memoryAxis)}</th><th scope="col">Source</th></tr></thead><tbody>
${capacityPoints.map(point => `<tr${active(point)}><th scope="row"><a href="${escapeHtml(point.href)}">${escapeHtml(point.name)}</a></th>
<td>${point.y}</td><td><a href="${escapeHtml(point.source)}">Manufacturer</a></td></tr>`).join("")}
</tbody></table></details></section>
<section class="profile-section"><${heading}>${speedTitle}</${heading}>${renderCoordinatePlot(speed)}</section>`;
}

function positionMarkdown({ id, name, points, capacityPoints }) {
  const selected = points.find(point => point.id === id);
  const capacity = capacityPoints.find(point => point.id === id);
  const noPair = `${name} has no unambiguous pair of rated specifications for these axes.`;
  const link = point => `[${escapeMarkdown(point.name)}](<${point.href}>)`;
  const source = point => `[Manufacturer](<${point.source}>)`;
  return [
    `## ${positionTitle}`, "", positionBasis, "",
    selected ? `Selected GPU: ${name} · ${selected.x} GB · ${selected.y} GB/s` : noPair,
    "", `| GPU | ${axisTitle(memoryAxis)} | ${axisTitle(bandwidthAxis)} | Source |`, "| --- | ---: | ---: | --- |",
    ...points.map(point => `| ${link(point)} | ${point.x} | ${point.y} | ${point.bandwidthSource !== point.source
      ? `[Capacity](<${point.source}>) · [Bandwidth](<${point.bandwidthSource}>)` : source(point)} |`),
    "", "## GPU memory capacity", "", "Manufacturer-rated memory per GPU, ordered by capacity.", "",
    capacity ? `Selected GPU: ${name} · ${capacity.y} GB` : `${name} has no unambiguous manufacturer-rated capacity on this scale.`,
    "", `| GPU | ${axisTitle(memoryAxis)} | Source |`, "| --- | ---: | --- |",
    ...capacityPoints.map(point => `| ${link(point)} | ${point.y} | ${source(point)} |`),
    "", `## ${speedTitle}`, "", speedUnavailable, "",
  ];
}

export function catalogDocument({ title, home = "/", mdLink, release, review, canonical, main, root = `/catalog/${release}`, local = false, releaseOrigin = null }) {
  const directory = hardwareDirectoryPath(release);
  const translations = {};
  const chinese = { Explorer: "探索", Compare: "目标对比", Battles: "对决", "Guided advisor": "配置顾问", Methods: "评测方法", Costs: "成本", Catalog: "目录", Machines: "整机", Models: "模型", Wiki: "知识库", "Price watch": "价格趋势", "For agents": "智能体" };
  const traditional = { Explorer: "探索", Compare: "目標比較", Battles: "對決", "Guided advisor": "配置顧問", Methods: "評測方法", Costs: "成本", Catalog: "目錄", Machines: "整機", Models: "模型", Wiki: "知識庫", "Price watch": "價格趨勢", "For agents": "智慧體" };
  for (const label of Object.keys(navigationRoutes(releaseOrigin))) {
    const source = local && (label === "Compare" || label === "Costs") ? label + " demo" : label;
    const regional = siteTranslations[source] ?? [];
    const east = eastAsianGermanSiteTranslations[source] ?? [];
    translations[source] = { "zh-Hans": chinese[label], "zh-Hant": traditional[label], hi: regional[0], es: regional[1], ar: regional[2], fr: regional[3], ja: east[0], ko: east[1], de: east[2] };
  }
  const localeData = JSON.stringify({ languages, translations, referenceCodes: [...Object.keys(rates), ...Object.keys(supplementalRates)] }).replace(/</g, "\\u003c");
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${escapeHtml(title)} | fastest.ai catalog</title>
${review ? '<meta name="robots" content="noindex">\n' : ""}\
${canonical ? `<link rel="canonical" href="${escapeHtml(canonical)}">\n` : ""}<link rel="alternate" type="text/markdown" href="${mdLink}">
<style>${profileStyles}</style>
</head>
<body class="profile-document"><div class="profile-shell">
<header class="profile-header"><a class="profile-brand" href="${home}">fastest.ai / localdecode.com</a><nav class="profile-nav" aria-label="Main navigation">${Object.entries(navigationRoutes(releaseOrigin)).map(([label, route]) => {
    const href = navigationHref(route, !local, releaseOrigin, true);
    const destination = href.startsWith("#") ? home + href : href;
    const displayLabel = local && (label === "Compare" || label === "Costs") ? label + " demo" : label;
    return `<a href="${escapeHtml(destination)}"${route === "catalog" ? ' aria-current="page"' : ""}>${escapeHtml(displayLabel)}</a>`;
  }).join("")}</nav><details class="profile-locale"><summary>Language and currency</summary><label>Language <select id="profile-language">${Object.entries(languages).map(([tag, value]) => `<option value="${tag}" lang="${tag}">${value.label}</option>`).join("")}</select></label><label>Display currency <select id="profile-currency"><option value="auto">Follow language</option></select></label><form id="profile-rate" hidden><label>Units per USD <input id="profile-rate-value" type="number" min="0" step="any" required></label><button type="submit">Apply rate</button></form></details><nav class="profile-actions profile-catalog-nav" aria-label="Catalog">${review
    ? `<a href="${directory}">Hardware catalog</a><a href="${directory}#cards">GPU cards</a><a href="${directory}#machines">Machine profiles</a><a href="${modelCollectionPath(release)}">Model catalog</a><a href="${runtimeDirectoryPath(release)}">Runtime catalog</a>`
    : `<a href="${home}#catalog/cards">Cards</a><a href="${home}#catalog/machines">Machines</a><a href="${home}#catalog/models">Models</a><a href="${home}#catalog/runtimes">Runtimes</a>`}</nav></header>
<main>
${main}
</main>
<footer class="profile-footer">Release <code>${release}</code>${review ? ` · PostgreSQL snapshot <code>${review.snapshotId}</code>` : ""
    } · <a href="${root}/manifest.json">Coverage and sources</a> · <a href="${root}/LICENSE.txt">llmfit MIT notice</a></footer></div>
<script>
(() => {
  const data = ${localeData};
  const key = "fastest-locale-v1";
  let choices = {};
  try { choices = JSON.parse(localStorage.getItem(key)) || {}; } catch {}
  const language = document.getElementById("profile-language");
  const currency = document.getElementById("profile-currency");
  const rateForm = document.getElementById("profile-rate");
  const rateValue = document.getElementById("profile-rate-value");
  const links = [...document.querySelectorAll('nav[aria-label="Main navigation"] a')];
  const original = links.map(link => link.textContent);
  const codes = Intl.supportedValuesOf ? Intl.supportedValuesOf("currency") : ["USD", "CNY", "TWD", "EUR", "JPY", "KRW", "INR", "MXN", "SAR"];
  const unsupported = new Set(["XAG", "XAU", "XBA", "XBB", "XBC", "XBD", "XDR", "XPD", "XPT", "XSU", "XTS", "XUA", "XXX"]);
  for (const code of new Set([...data.referenceCodes, ...codes])) if (!unsupported.has(code)) currency.add(new Option(code, code));
  const preferred = navigator.languages?.length ? navigator.languages : [navigator.language];
  const browserLanguage = preferred.map(tag => { try { const locale = new Intl.Locale(tag); return locale.language === "zh" ? (locale.maximize().script === "Hant" ? "zh-Hant" : "zh-Hans") : locale.language; } catch { return "en"; } }).find(tag => data.languages[tag]);
  const visitor = document.documentElement.dataset.visitorLanguage;
  language.value = data.languages[choices.language] ? choices.language : data.languages[visitor] ? visitor : browserLanguage || "en";
  currency.value = choices.currency && [...currency.options].some(option => option.value === choices.currency) ? choices.currency : "auto";
  function update() {
    const selected = language.value;
    const code = currency.value === "auto" ? data.languages[selected].currency : currency.value;
    rateForm.hidden = data.referenceCodes.includes(code);
    rateValue.value = choices.manual?.[code] || "";
    document.documentElement.lang = selected;
    document.documentElement.dir = data.languages[selected].direction || "ltr";
    links.forEach((link, index) => { link.textContent = data.translations[original[index]]?.[selected] || original[index]; });
  }
  function save() {
    choices.language = language.value;
    choices.currency = currency.value;
    try { localStorage.setItem(key, JSON.stringify(choices)); } catch {}
    update();
  }
  language.addEventListener("change", save);
  currency.addEventListener("change", save);
  rateForm.addEventListener("submit", event => {
    event.preventDefault();
    const rate = Number(rateValue.value);
    if (!Number.isFinite(rate) || rate <= 0) return;
    const code = currency.value === "auto" ? data.languages[language.value].currency : currency.value;
    choices.manual = { ...choices.manual, [code]: rate };
    try { localStorage.setItem(key, JSON.stringify(choices)); } catch {}
    update();
  });
  update();
})();
</script>
</body>
</html>
`;
}

export function renderCard(card, { release, pathname, markdown, local = false, review, releaseOrigin = null }) {
  const depth = pathname.startsWith("catalog/") ? pathname.split("/").length - 3 : 1;
  const root = local ? Array(depth).fill("..").join("/") : `/catalog/${release}`;
  const linksFrom = local ? pathname.split("/").at(-1) : pathname;
  const htmlLink = review?.htmlPath ?? linksFrom.replace(/\.(md|html)$/, review ? "" : ".html");
  const mdLink = linksFrom.replace(/\.(md|html)$/, ".md");
  const licenseLink = root + "/LICENSE.txt";
  const manifestLink = root + "/manifest.json";
  const home = local ? root + "/../../../fastest-ai.html" : "/";
  const sections = card.sections ?? [];
  const visuals = card.visuals ?? [];
  const photos = card.photos ?? [];
  const { video, gallery } = card;
  const mediaNotices = photoNotices(photos);
  const position = card.position;
  const evaluations = card.publisherEvaluations;

  if (markdown) {
    return [
      "---",
      `title: ${JSON.stringify(card.title)}`,
      `kind: ${JSON.stringify(card.kind)}`,
      `route: ${JSON.stringify(review ? htmlLink : pathname.replace(/\.(md|html)$/, ".html"))}`,
      `release: ${release}`,
      ...(review ? [`snapshot: ${review.snapshotId}`] : []),
      "locale: en",
      "---",
      "",
      `# ${escapeMarkdown(card.title)}`,
      "",
      ...visuals.flatMap(({ title, fields, graphic }) => [
        `## ${escapeMarkdown(title)}`, "", ...(graphic ? [ratingScale(graphic), ""] : []), ...markdownFields(fields), "",
      ]),
      ...(photos.length || video ? ["## Build and product media", ""] : []),
      ...photos.map(({ alt, source, credit, license, licenseUrl }) =>
        `- [${escapeMarkdown(alt)}](<${source}>) · ${escapeMarkdown(credit)}${licenseUrl ? ` · [${escapeMarkdown(license)}](<${licenseUrl}>)` : ""}`),
      ...(video ? [`- [${escapeMarkdown(video.title)}](<${video.source ?? card.source}>) · [YouTube thumbnail](<${videoThumbnail(video)}>) · ${escapeMarkdown(videoAttribution(video))}`] : []),
      ...(mediaNotices.length ? ["", "### Image license notices", "", ...mediaNotices.flatMap(notice => ["```text", notice, "```", ""])] : []),
      ...(photos.length || video ? [""] : []),
      ...(gallery ? [`## ${imageSourceTitle}`, "", ...markdownFields(imageSourceFields(gallery)), ""] : []),
      ...(position ? positionMarkdown(position) : []),
      ...markdownFields(card.fields),
      ...sections.flatMap(({ title, fields }) => ["", `## ${escapeMarkdown(title)}`, "", ...markdownFields(fields)]),
      ...(evaluations ? ["", ...evaluationsMarkdown(evaluations)] : []),
      "",
      "## Evidence",
      "",
      card.evidence,
      "",
      `${review ? `[${review.directory?.title ?? "Hardware catalog"}](${review.directory?.path ?? hardwareDirectoryPath(release, true)}) · ` : ""
        }[Coverage and source manifest](${manifestLink}) · [llmfit MIT notice](${licenseLink}) · [HTML card](${htmlLink})`,
      "",
    ].join("\n");
  }
  return catalogDocument({
    title: card.title, home, mdLink, release, review, root, local, releaseOrigin,
    canonical: review && review.origin + htmlLink,
    main: renderCardContent(card, { mdLink }),
  });
}

const videoThumbnail = ({ id, thumbnail }) => thumbnail ?? "https://i.ytimg.com/vi/" + id + "/hqdefault.jpg";
const videoPlayer = ({ id, player, start }) => player ??
  ("https://www.youtube-nocookie.com/embed/" + id + (start ? "?start=" + start : ""));
const videoAttribution = ({ credit }) => `Publisher thumbnail${credit ? " by " + credit : ""}. It may depict the video topic.`;

const photoNotices = photos => [...new Set(photos.map(({ licenseNotice }) => licenseNotice).filter(Boolean))];

export function renderCardContent(card, { mdLink, nested = false } = {}) {
  const title = nested ? "h2" : "h1";
  const heading = nested ? "h3" : "h2";
  const { sections = [], visuals = [], photos = [], video, gallery, position, publisherEvaluations } = card;
  const mediaNotices = photoNotices(photos);
  return `<div class="profile-hero"><p class="profile-kicker">${escapeHtml(card.kind)}</p><${title}>${escapeHtml(card.title)}</${title}>
<p class="profile-evidence">${escapeHtml(card.evidence)}</p>
<div class="profile-actions">${card.source ? `<a href="${escapeHtml(card.source)}">Open source</a>` : ""}${mdLink ? `<a href="${mdLink}">Markdown</a>` : ""}</div></div>
${visuals.length ? `<div class="profile-specs">${visuals.map(({ title, fields, graphic }) =>
  `<section class="profile-section"><${heading}>${escapeHtml(title)}</${heading}>${graphic ? htmlSpecGraphic(graphic) : ""}${htmlFields(fields)}</section>`).join("")}</div>` : ""}
${video ? `<figure class="profile-video">
  <a href="${escapeHtml(video.source ?? card.source)}"><img width="480" height="360"
    referrerpolicy="no-referrer" src="${escapeHtml(videoThumbnail(video))}" alt="${escapeHtml(video.title)} thumbnail"></a>
  <figcaption><a href="${escapeHtml(video.source ?? card.source)}">${escapeHtml(video.title)} on YouTube</a> · ${escapeHtml(videoAttribution(video))}</figcaption>
  <details><summary>Watch source video</summary><iframe loading="lazy" title="${escapeHtml(video.title)}"
    src="${escapeHtml(videoPlayer(video))}"
    referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe></details></figure>` : ""}
${photos.length ? `<div class="profile-gallery">${photos.map(({ data, alt, source, credit, license, licenseUrl }) =>
  `<figure><img loading="lazy" src="${escapeHtml(data)}" alt="${escapeHtml(alt)}"><figcaption>
  ${escapeHtml(alt)} · <a href="${escapeHtml(source)}">${escapeHtml(credit)}</a>${licenseUrl ? ` · <a href="${escapeHtml(licenseUrl)}">${escapeHtml(license)}</a>` : ""}
  </figcaption></figure>`).join("")}</div>` : ""}
${mediaNotices.length ? `<details class="profile-photo-notices"><summary>Image license notices</summary>
${mediaNotices.map(notice => `<pre>${escapeHtml(notice)}</pre>`).join("")}</details>` : ""}
${gallery ? `<section class="profile-section"><${heading}>${imageSourceTitle}</${heading}>${htmlFields(imageSourceFields(gallery))}</section>` : ""}
${position ? positionHtml(position, heading) : ""}
<section class="profile-section"><${heading}>Catalog details</${heading}>${htmlFields(card.fields)}</section>
${sections.map(({ title, fields }) => `<section class="profile-section"><${heading}>${escapeHtml(title)}</${heading}>${htmlFields(fields)}</section>`).join("\n")}
${publisherEvaluations ? evaluationsHtml(publisherEvaluations, heading) : ""}`;
}
