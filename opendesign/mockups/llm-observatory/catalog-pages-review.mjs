import { mkdir, rm, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { catalogDocument, escapeHtml, escapeMarkdown, hardwareCard, htmlFields, markdownFields, renderCard } from "./catalog-card.mjs";
import { catalogPath, hardwareDirectoryPath, hardwareIdPattern } from "./catalog-paths.mjs";

const machineSections = [
  ["Complete factory configurations", "Complete factory configuration"],
  ["Partial configurations", "Partial configuration"],
  ["Manufacturer system references", "Manufacturer system reference"],
  ["llmfit example presets", "llmfit example preset"],
  ["Research component references", "Component reference"],
];

function directoryTable(title, kind, rows, href, anchor) {
  return `<section class="profile-section"${anchor ? ` id="${anchor}"` : ""}><h2>${title} (${rows.length})</h2>
<table class="profile-chart-table" aria-label="${title}">
<thead><tr><th scope="col">Profile</th><th scope="col">Catalog detail</th></tr></thead>
<tbody>${rows.map(row => `<tr><th scope="row"><a href="${href(kind, row.id)}">${escapeHtml(row.name)}</a><br>
<code>${row.id}</code></th><td>${escapeHtml(row.detail)}</td></tr>`).join("\n")}</tbody></table>
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
  const fields = [
    ["Hardware snapshot date", manifest.hardware.asOf],
    ["GPU catalog identities", String(profiles.cards.length)],
    ["Unresolved GPU references", String(coverage.unresolvedCardReferences)],
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
<div class="profile-actions"><a href="${mdPath}">Markdown</a></div>${htmlFields(fields)}</div>
${directoryTable("GPU cards", "cards", profiles.cards, href, "cards")}
<div id="machines">${sections.map(([label, rows]) => directoryTable(escapeHtml(label), "machines", rows, href)).join("\n")}</div>`;
  const markdown = [
    "---", `title: ${JSON.stringify(title)}`, `route: ${JSON.stringify(path)}`, `release: ${release}`, `snapshot: ${snapshotId}`, "---",
    "", `# ${title}`, "", summary, "", `[HTML directory](${path}) · [Coverage and source manifest](/catalog/${release}/manifest.json)`, "",
    ...markdownFields(fields),
    ...[["GPU cards", "cards", profiles.cards], ...sections.map(([label, rows]) => [label, "machines", rows])]
      .flatMap(([label, kind, rows]) => [
        "", `## ${escapeMarkdown(label)} (${rows.length})`, "",
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
