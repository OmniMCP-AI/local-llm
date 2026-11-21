import { runtimeOverview } from "./runtime-overview.mjs";
import { mkdir, rm, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { build } from "esbuild";
import { catalogDocument, escapeHtml, escapeMarkdown, hardwareCard, htmlFields, markdownFields, modelCard, renderCard, runtimeCard } from "./catalog-card.mjs";
import { catalogPath, hardwareDirectoryPath, hardwareIdPattern, modelCollectionPath, modelLookupPath, runtimeDirectoryPath, runtimeIdPattern } from "./catalog-paths.mjs";
import { recentModels } from "./catalog-search.mjs";

const machineSections = [
  ["Creator-reported builds", "Creator-reported build"],
  ["Complete factory configurations", "Complete factory configuration"],
  ["Partial configurations", "Partial configuration"],
  ["Manufacturer system references", "Manufacturer system reference"],
  ["llmfit example presets", "llmfit example preset"],
  ["Research component references", "Component reference"],
];

function directoryTable(title, rows, href, anchor) {
  return `<section class="profile-section"${anchor ? ` id="${anchor}"` : ""}><h2>${title} (${rows.length})</h2>
<table class="profile-chart-table profile-directory-table" aria-label="${title}">
<thead><tr><th scope="col">Profile</th><th scope="col">Catalog detail</th></tr></thead>
<tbody>${rows.map(row => `<tr><th scope="row"><a href="${href(row)}">${escapeHtml(row.name)}</a>${
    row.name === row.id ? "" : `<br>\n<code>${row.id}</code>`}</th><td>${escapeHtml(row.detail)}</td></tr>`).join("\n")}</tbody></table>
</section>`;
}

export async function writeHardwareDirectory(output, { manifest, hardware }, origin) {
  const { release, snapshotId } = manifest;
  const review = { snapshotId, origin };
  const profiles = hardware.catalog;
  const kinds = ["cards", "machines"];
  const ids = Object.fromEntries(kinds.map(kind => {
    const keys = new Set(profiles[kind].map(row => row.id));
    if (keys.size !== profiles[kind].length || [...keys].some(id => !hardwareIdPattern.test(id))) {
      throw new Error("Invalid or duplicate hardware identity in the Pages review: " + kind);
    }
    return [kind, keys];
  }));
  const href = (kind, id, markdown = false) => ids[kind].has(id)
    ? "/" + catalogPath(release, kind, id, markdown ? "md" : "html").replace(/\.html$/, "") : null;
  const path = hardwareDirectoryPath(release);
  const mdPath = hardwareDirectoryPath(release, true);
  const title = "Hardware catalog";
  const summary = "Browse exact GPU identities and hardware profiles from this catalog snapshot.";
  const coverage = manifest.hardware.coverage;
  const modifiedCards = profiles.cards.filter(row => row.modification);
  const cardSections = [
    ["GPU cards", profiles.cards.filter(row => !row.modification)],
    ...(modifiedCards.length ? [["Memory-modified GPUs", modifiedCards, "memory-modified"]] : []),
  ];
  const fields = [
    ["Hardware snapshot date", manifest.hardware.asOf],
    ["GPU catalog identities", String(profiles.cards.length)],
    ["Unresolved GPU references", String(coverage.unresolvedCardReferences)],
    ...(modifiedCards.length ? [["Memory-modified GPU references", String(modifiedCards.length)]] : []),
    ["Machine profile records", String(profiles.machines.length)],
    ["Reviewed measured profiles", String(coverage.reviewedMeasuredProfiles)],
    ["Untested machine profiles", String(coverage.untestedProfiles)],
  ];
  const machines = Object.groupBy(profiles.machines, row => row.kind);
  const sections = machineSections.flatMap(([label, kind]) => machines[kind] ? [[label, machines[kind]]] : []);
  const knownKinds = new Set(machineSections.map(([, kind]) => kind));
  for (const [kind, rows] of Object.entries(machines)) {
    if (!knownKinds.has(kind)) sections.push([kind, rows]);
  }
  const main = `<div class="profile-hero"><h1>${title}</h1><p class="profile-evidence">${summary}</p>
<div class="profile-actions"><a href="${mdPath}">Markdown</a>${modifiedCards.length
    ? '<a href="#memory-modified">Memory-modified GPUs</a>' : ""}</div>${htmlFields(fields)}</div>
<div id="cards">${cardSections.map(([label, rows, anchor]) => directoryTable(label, rows, row => href("cards", row.id), anchor)).join("\n")}</div>
<div id="machines">${sections.map(([label, rows]) => directoryTable(escapeHtml(label), rows, row => href("machines", row.id))).join("\n")}</div>`;
  const markdown = [
    "---", `title: ${JSON.stringify(title)}`, `route: ${JSON.stringify(path)}`, `release: ${release}`, `snapshot: ${snapshotId}`, "---",
    "", `# ${title}`, "", summary, "", `[HTML directory](${path}) · [Coverage and source manifest](/catalog/${release}/manifest.json)`, "",
    ...(modifiedCards.length ? ["[Memory-modified GPUs](#memory-modified)", ""] : []),
    ...markdownFields(fields),
    ...[...cardSections.map(([label, rows, anchor]) => [label, "cards", rows, anchor]), ...sections.map(([label, rows]) => [label, "machines", rows])]
      .flatMap(([label, kind, rows, anchor]) => [
        "", ...(anchor ? [`<a id="${anchor}"></a>`, ""] : []), `## ${escapeMarkdown(label)} (${rows.length})`, "",
        ...rows.map(row => `- [${escapeMarkdown(row.name)}](${href(kind, row.id, true)}) · \`${row.id}\` · ${escapeMarkdown(row.detail)}`),
      ]),
    "",
  ].join("\n");

  await Promise.all(kinds.map(kind => mkdir(join(output, "catalog", release, kind), { recursive: true })));
  await Promise.all([
    writeFile(join(output, path + ".html"), catalogDocument({
      title, mdLink: mdPath, release, review, canonical: origin + path, main,
    })),
    writeFile(join(output, mdPath), markdown),
    ...kinds.flatMap(kind => profiles[kind].flatMap(row => ["html", "md"].map(extension => {
      const markdown = extension === "md";
      const file = catalogPath(release, kind, row.id, extension);
      const card = hardwareCard(row, release, kind, {
        peers: kind === "cards" ? profiles.cards : [],
        reviewProfileHref: (type, id) => href(type, id, markdown),
      });
      return writeFile(join(output, file), renderCard(card, { release, pathname: "/" + file, markdown, review }));
    }))),
  ]);
}

export async function removeHardwareDirectory(output, release) {
  const path = hardwareDirectoryPath(release);
  await Promise.all([
    rm(join(output, path + ".html"), { force: true }),
    rm(join(output, path + ".md"), { force: true }),
    ...["cards", "machines"].map(kind => rm(join(output, "catalog", release, kind), { recursive: true, force: true })),
  ]);
}

const modelPageSize = 30;
const number = new Intl.NumberFormat("en");
const collectionTitles = { popular: "Popular models", small: "Small models (≤4B parameters)", recent: "Recent releases" };

async function writePair(output, htmlPath, html, markdown) {
  await mkdir(dirname(join(output, htmlPath)), { recursive: true });
  await Promise.all([
    writeFile(join(output, htmlPath + ".html"), html),
    writeFile(join(output, htmlPath + ".md"), markdown),
  ]);
}

async function writeCatalogIndex(output, { title, path, release, review, summary, fields, nav = [], pagination = [], rows, overview }) {
  const navHtml = (label, links) => links.length ? `<nav class="profile-actions" aria-label="${label}">${links.map(([name, url]) =>
    `<a href="${url}"${url === path ? ' aria-current="page"' : ""}>${escapeHtml(name)}</a>`).join("")}</nav>` : "";
  const navMd = (links) => links.map(([name, url]) => `[${escapeMarkdown(name)}](${url}.md)`).join(" · ");
  const sourceHtml = (value, source) => source ? `<a href="${escapeHtml(source)}">${escapeHtml(value ?? "Unknown")}</a>` : escapeHtml(value ?? "Unknown");
  const sourceMd = (value, source) => source ? `[${escapeMarkdown(value ?? "Unknown")}](<${source}>)` : escapeMarkdown(value ?? "Unknown");
  const overviewHtml = overview ? `<section class="profile-section"><h2>Runtime overview</h2>
<p>${escapeHtml(overview.selection.method)} Review v${overview.selection.version} · ${overview.selection.reviewedAt}.</p>
<p>Performance slice: ${escapeHtml(overview.workload.description)}. ${escapeHtml(overview.workload.metric)} (${escapeHtml(overview.workload.unit)}), higher is better. Missing measurements are not ranked.</p>
<table><thead><tr><th>Runtime and version</th><th>Backend</th><th>Formats</th><th>Workload</th><th>Performance</th></tr></thead><tbody>${overview.rows.map(row => `<tr><th>${sourceHtml(`${row.name} ${row.tag ?? "Version unknown"}`, row.releaseUrl ?? (row.source && row.tag && `${row.source}/releases/tag/${row.tag}`))} · ${escapeHtml(row.published ?? "Date unknown")}</th><td>${sourceHtml(row.backends, row.backendSource)}</td><td>${sourceHtml(row.formats, row.formatSource)}</td><td>${sourceHtml(row.workload, row.docs)}</td><td>${row.result ? `#${row.rank} · ${row.result.score} ${escapeHtml(overview.workload.unit)} · <a href="${escapeHtml(row.result.source)}">Run evidence</a> · ${escapeHtml(row.result.runDate)}` : "No eligible measurement"}</td></tr>`).join("")}</tbody></table></section>` : "";
  const overviewMarkdown = overview ? ["## Runtime overview", "", overview.selection.method + ` Review v${overview.selection.version} · ${overview.selection.reviewedAt}.`, "", `Performance slice: ${overview.workload.description}. ${overview.workload.metric} (${overview.workload.unit}), higher is better. Missing measurements are not ranked.`, "", ...overview.rows.map(row => `- ${sourceMd(`${row.name} ${row.tag ?? "Version unknown"}`, row.releaseUrl ?? (row.source && row.tag && `${row.source}/releases/tag/${row.tag}`))} · ${row.published ?? "Date unknown"} · Backend: ${sourceMd(row.backends, row.backendSource)} · Formats: ${sourceMd(row.formats, row.formatSource)} · Workload: ${sourceMd(row.workload, row.docs)} · ${row.result ? `#${row.rank} · ${row.result.score} ${overview.workload.unit} · [Run evidence](<${row.result.source}>) · ${row.result.runDate}` : "No eligible measurement"}`), ""] : [];
  const main = `<div class="profile-hero"><h1>${escapeHtml(title)}</h1><p class="profile-evidence">${escapeHtml(summary)}</p>
<div class="profile-actions"><a href="${path}.md">Markdown</a></div>
${navHtml("Model collections", nav)}${htmlFields(fields)}</div>
${overviewHtml}
${directoryTable(escapeHtml(title), rows, row => row.path)}
${navHtml("Collection pages", pagination)}`;
  const markdown = [
    "---", `title: ${JSON.stringify(title)}`, `route: ${JSON.stringify(path)}`,
    `release: ${release}`, `snapshot: ${review.snapshotId}`, "---", "",
    `# ${escapeMarkdown(title)}`, "", summary, "",
    `[HTML directory](${path}) · [Coverage and source manifest](/catalog/${release}/manifest.json)`, "",
    navMd(nav), "", ...markdownFields(fields), "",
    ...overviewMarkdown,
    ...rows.map(row => `- [${escapeMarkdown(row.name)}](${row.path}.md)${row.name === row.id ? "" : ` · \`${row.id}\``} · ${escapeMarkdown(row.detail)}`),
    "", navMd(pagination), "",
  ].join("\n");
  await writePair(output, path, catalogDocument({
    title, mdLink: path + ".md", release, review, canonical: review.origin + path, main,
  }), markdown);
}

export async function writeModelRuntimeDirectories(output, { manifest, shards, runtimes }, origin) {
  const { release, snapshotId, discovery, supplement } = manifest;
  const review = { snapshotId, origin };
  const modelPath = (id) => "/" + catalogPath(release, "models", id).slice(0, -5);
  const runtimePath = (id) => "/" + catalogPath(release, "runtimes", id).slice(0, -5);
  const allModels = [...shards.values()].flat();
  const collections = Object.fromEntries(["popular", "small"].map(collection => [collection,
    allModels.filter(row => row.discovery?.[collection]).sort((a, b) => a.discovery[collection].rank - b.discovery[collection].rank),
  ]));
  collections.recent = recentModels(allModels);
  const models = new Map(Object.values(collections).flat().map(row => [row.id, row]));
  const runtimeIds = new Set(runtimes.map(row => row.id));
  if (runtimeIds.size !== runtimes.length || [...runtimeIds].some(id => !runtimeIdPattern.test(id))) {
    throw new Error("Invalid or duplicate runtime identity in the Pages review");
  }

  const nav = Object.entries(collectionTitles).map(([collection, title]) =>
    [`${title} (${collections[collection].length})`, modelCollectionPath(release, collection)]);
  nav.push(["Exact model lookup", modelLookupPath(release)]);
  const modelPages = Object.entries(collections).flatMap(([collection, rows]) => {
    const title = collectionTitles[collection];
    const pages = Math.max(1, Math.ceil(rows.length / modelPageSize));
    const summary = collection === "recent"
      ? "Reviewed publisher records ordered by repository revision date, newest first."
      : "One eligible text-generation repository per family, ranked by Hugging Face Hub downloads. Parameter counts are from SafeTensors metadata.";
    const fields = [
      ["Models in this collection", number.format(rows.length)],
      ["Repositories in the full snapshot", number.format(allModels.length)],
      ...(collection === "recent" ? [["Publisher metadata reviewed", supplement?.capturedAt ?? "Unavailable"]]
        : [["Hugging Face Hub ranking snapshot", discovery.capturedAt, discovery.source]]),
    ];
    return Array.from({ length: pages }, (_, index) => {
      const page = index + 1;
      const offset = index * modelPageSize;
      const path = modelCollectionPath(release, collection, page);
      return writeCatalogIndex(output, {
        title, path, release, review, summary, nav, fields: [...fields, ["Collection page", `${page} of ${pages}`]],
        pagination: pages > 1 ? Array.from({ length: pages }, (_, i) =>
          [`Page ${i + 1}`, modelCollectionPath(release, collection, i + 1)]) : [],
        rows: rows.slice(offset, offset + modelPageSize).map(row => {
          const rank = row.discovery?.[collection];
          const detail = rank
            ? `Rank ${rank.rank} · ${number.format(rank.downloads)} downloads · ${number.format(rank.parameters)} parameters${rank.gated ? " · Access approval required" : ""}`
            : row.supplemental.revisionDate;
          return { id: row.id, name: row.id, detail, path: modelPath(row.id) };
        }),
      });
    });
  });
  const runtimeDirectory = runtimeDirectoryPath(release);
  await Promise.all([
    ...modelPages,
    writeModelLookup(output, release, review, runtimeIds, allModels.length),
    writeCatalogIndex(output, {
      title: "Runtime catalog", path: runtimeDirectory, release, review,
      summary: "Browse upstream releases, pinned commits and documented support from this catalog snapshot.",
      fields: [["Runtime projects", number.format(runtimes.length)]],
      overview: runtimeOverview(runtimes),
      rows: runtimes.map(row => ({ id: row.id, name: row.name,
        detail: [row.tag, row.published, row.category].filter(Boolean).join(" · "), path: runtimePath(row.id) })),
    }),
    ...Array.from(models.values(), row => {
      const directory = { title: "Model catalog", path: modelCollectionPath(release) + ".md" };
      const path = modelPath(row.id);
      const render = (markdown) => {
        const card = modelCard(row, release, {
          discoveryCapture: row.discoveryCapture,
          runtimeHref: id => runtimeIds.has(id) ? runtimePath(id) + (markdown ? ".md" : "") : null,
        });
        return renderCard(card, { release, pathname: path + (markdown ? ".md" : ".html"), markdown, review: { ...review, directory } });
      };
      return writePair(output, path, render(false), render(true));
    }),
    ...runtimes.map(row => {
      const path = runtimePath(row.id);
      const directory = { title: "Runtime catalog", path: runtimeDirectory + ".md" };
      const card = runtimeCard(row, { review: true });
      const render = (markdown) => renderCard(card, {
        release, pathname: path + (markdown ? ".md" : ".html"), markdown, review: { ...review, directory },
      });
      return writePair(output, path, render(false), render(true));
    }),
  ]);
}

async function writeModelLookup(output, release, review, runtimeIds, inventory) {
  const path = modelLookupPath(release);
  const title = "Exact model lookup";
  const summary = `Find a model by its case-sensitive owner/repository ID in the ${number.format(inventory)} repositories in this snapshot.`;
  const main = `<div class="profile-hero" data-model-lookup data-release="${release}" data-snapshot="${review.snapshotId}" data-runtimes="${[...runtimeIds].join(" ")}">
<h1>${title}</h1><p class="profile-evidence">${summary}</p>
<form class="profile-lookup" action="${path}" method="get">
<label for="repository">Exact repository ID</label>
<input id="repository" name="q" type="search" required spellcheck="false" autocapitalize="none" placeholder="owner/repository">
<button type="submit">Find model</button>
</form>
<p role="status" id="lookup-status"></p>
<noscript><p>JavaScript reads the local catalog files for this lookup. <a href="${modelCollectionPath(release)}">Browse the model collections</a>.</p></noscript>
</div>
<div id="lookup-result"></div>
<script src="${path}.js" defer></script>`;
  await Promise.all([
    writePair(output, path, catalogDocument({ title, mdLink: path + ".md", release, review, canonical: review.origin + path, main }),
      `---\ntitle: "${title}"\nroute: "${path}"\nrelease: ${release}\nsnapshot: ${review.snapshotId}\n---\n\n# ${title}\n\n${summary}\n\n[Open the browser lookup](${path}) · [Model catalog](${modelCollectionPath(release)}.md)\n`),
    build({
      entryPoints: [fileURLToPath(new URL("./catalog-review-lookup.mjs", import.meta.url))],
      bundle: true, minify: true, outfile: join(output, path + ".js"),
    }),
  ]);
}

export async function removeModelRuntimeDirectories(output, release) {
  const root = join(output, "catalog", release);
  await Promise.all(["models.html", "models.md", "runtimes.html", "runtimes.md", "model-lookup.html", "model-lookup.md", "model-lookup.js",
    "model-collections", "models", "runtimes"]
    .map(path => rm(join(root, path), { recursive: true, force: true })));
}
