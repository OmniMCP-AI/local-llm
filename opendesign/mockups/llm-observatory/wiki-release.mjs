import { createHash } from "node:crypto";
import { battleArchiveMarkdown, battleArchivePath, renderBattleArchive } from "./battle-archive.mjs";
import { mkdir, rm, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { markdownBlocks, markdownInline } from "./wiki-markdown.mjs";
import { inferenceStages, scalingUnavailable, selectTopologyPresets, topologyLinkEndpoints, topologyView } from "./topology.mjs";
import { catalogApiPath } from "./catalog-api.mjs";
import { hardwareDirectoryPath, modelCollectionPath, modelLookupPath, runtimeDirectoryPath, topologyRevisionHref } from "./catalog-paths.mjs";

const escape = (value) => String(value).replace(/[&<>"']/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
})[char]);
const markdown = (text) => text.replace(/[\\`*_{}\[\]<>]/g, "\\$&");
const slugPattern = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
export const wikiHtmlRoute = (id) => id === "index" ? "/wiki/" : "/wiki/" + id + "/";
const mdRoute = (id) => "/wiki/" + id + ".md";

function linkedPage(hash) {
  if (hash === "#wiki") return "index";
  if (hash === "#costs" || hash === "#methods") return "comparison-methods";
  return hash.match(/^#(?:(?:wiki|machines|models|catalog)\/)?([a-z0-9-]+)$/)?.[1];
}

function linkDestination(target, pages, research, withdrawn, format) {
  if (target.startsWith("#")) {
    const page = linkedPage(target);
    if (!Object.hasOwn(pages, page)) return null;
    if (page === "research") return research[format];
    return format === "html" ? wikiHtmlRoute(page) : mdRoute(page);
  }
  if (!target.startsWith("https://")) return null;
  const url = new URL(target);
  if (url.hostname === "www.youtube.com" && withdrawn.has("youtube/" + url.searchParams.get("v"))) return null;
  return target;
}

function renderBody(body, resolveLink, format) {
  const inline = (line) => markdownInline(line).map(({ type, text, href }) => {
    const safe = format === "html" ? escape(text) : markdown(text);
    if (type === "link") {
      const url = resolveLink(href);
      if (!url) return safe;
      return format === "html" ? `<a href="${escape(url)}">${safe}</a>` : `[${safe}](${url})`;
    }
    if (type === "strong") return format === "html" ? `<strong>${safe}</strong>` : `**${safe}**`;
    if (type === "code") return format === "html" ? `<code>${safe}</code>` : "\x60" + text + "\x60";
    return safe;
  }).join("");
  return markdownBlocks(body).map(({ type, text, items }) => {
    if (type === "list") return format === "html"
      ? "<ul>\n" + items.map((item) => `<li>${inline(item)}</li>`).join("\n") + "\n</ul>"
      : items.map((item) => "- " + inline(item)).join("\n");
    if (type === "heading") return format === "html" ? `<h2>${inline(text)}</h2>` : "## " + inline(text);
    return format === "html" ? `<p>${inline(text)}</p>` : inline(text);
  }).join("\n\n");
}

export function renderTopologyReference(format, presets, scalingUrl = null, interactive = true) {
  const topologyExplorer = "/#wiki/technology";
  const rows = presets.map(({ label, report }) => {
    const view = topologyView(report);
    return {
      label, report, topology: interactive && topologyRevisionHref(report.revision),
      summary: `${view.installedCount} ${view.installedCount === 1 ? "card" : "cards"}`,
      active: view.activeCount ?? "Unknown",
      inventory: view.parts.map(({ slot, label: name, memory }) => `${slot}. ${name} · ${memory ?? "VRAM unknown"}`).join(" / "),
      links: [
        view.links.map(({ label: name, slots }) => `${name} (${topologyLinkEndpoints(view, slots)})`).join(" / ") ||
          (view.installedCount === 1 ? "Single-card layout" : "Unknown"),
        report.note,
      ].filter(Boolean).join(" · "),
    };
  });
  if (format === "md") return `## Topology reference

${interactive ? `[Open interactive topology](${topologyExplorer})\n\n` : ""}${scalingUrl ? `[Open the 1→N GPU scaling report](${scalingUrl})` : scalingUnavailable}

${rows.map(({ label, report, summary, active, inventory, links, topology }) =>
  `- [${label} · ${report.id}](${report.source})${topology ? ` · [Explore this configuration](${topology})` : ""} · ${summary} · Active cards ${active} · ${markdown(inventory)} · Documented links ${markdown(links)}`).join("\n")}

## Conceptual inference stages

${inferenceStages.map(({ title, note }, index) => `${index + 1}. **${title}.** ${note}`).join("\n")}
`;
  return `<section><h2>Topology reference</h2>
${interactive ? `<p><a href="${topologyExplorer}">Open interactive topology</a></p>\n` : ""}<p>${scalingUrl ? `<a href="${escape(scalingUrl)}">Open the 1→N GPU scaling report</a>` : scalingUnavailable}</p>
<div style="overflow-x:auto"><table><caption>Source-reported layouts</caption>
<thead><tr><th scope="col">Layout</th><th scope="col">Installed</th><th scope="col">Active cards</th><th scope="col">Inventory by slot</th><th scope="col">Documented links</th></tr></thead>
<tbody>${rows.map(({ label, report, summary, active, inventory, links, topology }) =>
  `<tr><th scope="row"><a href="${escape(report.source)}">${escape(label)} · ${escape(report.id)}</a>${topology ? `<br><a href="${topology}">Explore this configuration</a>` : ""}</th><td>${summary}</td><td>${active}</td><td>${escape(inventory)}</td><td>${escape(links)}</td></tr>`).join("\n")}</tbody></table></div>
<h2>Conceptual inference stages</h2><ol>${inferenceStages.map(({ title, note }) =>
  `<li><strong>${escape(title)}.</strong> ${escape(note)}</li>`).join("")}</ol></section>`;
}

function frontmatter(fields) {
  return ["---", ...Object.entries(fields).filter(([, value]) => value !== undefined).map(([key, value]) => `${key}: ${JSON.stringify(value)}`), "---", ""].join("\n");
}

const styles = `<style>
.wiki-release{max-width:52rem;margin:auto;padding:1.5rem 1rem 3rem;color:#17212b;font:1rem/1.58 system-ui,sans-serif}
.wiki-release a{color:#174e82;text-decoration:underline;text-underline-offset:.18em}
.wiki-release nav{display:flex;flex-wrap:wrap;gap:.5rem 1rem}
.wiki-release h1,.wiki-release h2{line-height:1.2;margin:1.25rem 0 .5rem}
.wiki-release h1{font-size:clamp(1.8rem,6vw,2.5rem)}
.wiki-release li+li{margin-top:.35rem}
.wiki-release-ids{color:#4b5864;overflow-wrap:anywhere}
#root:not(:empty)+.release-fallback{display:none}
</style>`;

function pageHead({ origin, route, alternate, title, summary, release }) {
  return `<meta name="description" content="${escape(summary)}">
<meta name="wiki-release" content="${release}">
<link rel="canonical" href="${escape(origin + route)}">
<link rel="alternate" type="text/markdown" href="${alternate}" title="Markdown">
<title>${escape(title)}</title>
${styles}`;
}

export function activeHighlights(highlights, pages, releaseDate) {
  return highlights
    .filter(({ status, starts, ends, page }) =>
      status === "published" && starts <= releaseDate && releaseDate < ends && Object.hasOwn(pages, page))
    .sort((a, b) => b.priority - a.priority || a.id.localeCompare(b.id))
    .map(({ page, destination, ...entry }) => ({
      ...entry, href: destination ?? wikiHtmlRoute(page), markdown: destination ?? mdRoute(page),
    }));
}

export async function writeWikiRelease({
  output, origin, researchRelease, catalogRelease, documents, edges, highlights, releaseDate, withdrawn = [],
  topologies = [], scalingUrl, advisorUrl, catalogApi = false, review = false, battle = null,
}) {
  const originUrl = new URL(origin);
  if (originUrl.origin !== origin || !["https:", "http:"].includes(originUrl.protocol)) {
    throw new Error("FASTEST_PUBLIC_ORIGIN must be an origin without a trailing slash");
  }
  const catalogOpenApi = catalogApi ? `/catalog/${catalogRelease}/openapi.json` : null;
  const directories = review ? [
    ["Hardware catalog", hardwareDirectoryPath(catalogRelease)],
    ["Model catalog", modelCollectionPath(catalogRelease)],
    ["Runtime catalog", runtimeDirectoryPath(catalogRelease)],
  ] : [];
  const excluded = new Set(withdrawn);
  const pages = Object.fromEntries(Object.entries(documents).filter(([, doc]) =>
    doc.status === "published" && !excluded.has(doc.evidence)));
  const researchRoot = "/research/" + researchRelease + "/";
  const research = { html: researchRoot + "library", md: researchRoot + "library.md" };
  const redirects = new Map();
  const availableHighlights = activeHighlights(highlights, pages, releaseDate);

  const entries = Object.entries(pages).map(([id, doc]) => {
    if (!slugPattern.test(id)) throw new Error("Invalid wiki page ID: " + id);
    const aliases = doc.redirects?.split(",").map((slug) => slug.trim()) ?? [];
    for (const old of aliases) {
      if (!slugPattern.test(old) || Object.hasOwn(documents, old) || redirects.has(old)) {
        throw new Error("Wiki redirect conflicts with a page or another redirect: " + old);
      }
      redirects.set(old, id);
    }
    const neighbors = [...new Set(edges.flatMap(({ source, target }) =>
      source === id ? [target] : target === id ? [source] : []))]
      .filter((target) => target !== id && Object.hasOwn(pages, target)).sort();
    const catalogAccess = id === "agent-discovery" && catalogOpenApi;
    const body = (format) => renderBody(doc.body, (link) => {
      if (link === "#catalog/runtimes" && catalogRelease) {
        return review ? runtimeDirectoryPath(catalogRelease) + (format === "md" ? ".md" : "") : "/#catalog/runtimes";
      }
      return linkDestination(link, pages, research, excluded, format);
    }, format)
      + (id === "technology" || id === "gpu-topology" ? "\n\n" + renderTopologyReference(format, selectTopologyPresets(topologies), scalingUrl, !review) : "")
      + (catalogAccess ? format === "html"
        ? `\n<p><a href="${catalogOpenApi}">Catalog API (OpenAPI)</a> · <a href="${catalogApiPath}?kind=cards">Browse released card metadata</a></p>`
        : `\n\n[Catalog API (OpenAPI)](${catalogOpenApi}) · [Browse released card metadata](${catalogApiPath}?kind=cards)`
        : "");
    const { title, kind, summary, entity, evidence, methods, media } = doc;
    return { id, source: "wiki/pages/" + id + ".md", title, kind, summary, entity, evidence, methods, media,
      aliases, neighbors, html: body("html"), md: body("md") };
  });
  const alternateName = "localdecode.com";
  const release = "wiki-" + createHash("sha256")
    .update(JSON.stringify([entries, availableHighlights, researchRelease, catalogRelease, alternateName, catalogOpenApi,
      ...directories.map(([, path]) => path), ...(battle ? [battleArchivePath] : [])]))
    .digest("hex").slice(0, 16);
  const headers = [
    ...(review ? [
      "/*\n  X-Robots-Tag: noindex\n  Cache-Control: no-store",
      ...[...directories.map(([, path]) => path), modelLookupPath(catalogRelease)].flatMap(path => [
        `${path}\n  Link: <${origin + path}.md>; rel="alternate"; type="text/markdown"`,
        `${path}.md\n  Content-Type: text/markdown; charset=utf-8\n  Link: <${origin + path}>; rel="alternate"; type="text/html"`,
      ]),
      ...["cards/:id", "machines/:id", "models/:owner/:id", "runtimes/:id", "model-collections/:page"].map(route =>
        `/catalog/${catalogRelease}/${route}.md\n  Content-Type: text/markdown; charset=utf-8`),
    ] : []),
    "/research/*\n  Cache-Control: no-store\n  X-Content-Type-Options: nosniff",
    "/wiki/*\n  Cache-Control: no-store\n  X-Content-Type-Options: nosniff",
    `${research.html}\n  Link: <${origin + research.md}>; rel="alternate"; type="text/markdown"`,
    `${research.md}\n  Content-Type: text/markdown; charset=utf-8\n  Link: <${origin + research.html}>; rel="alternate"; type="text/html"`,
    `/index.md\n  Cache-Control: no-store\n  Content-Type: text/markdown; charset=utf-8\n  Link: <${origin}/>; rel="alternate"; type="text/html"`,
    ...["robots.txt", "sitemap.xml", "llms.txt", "evidence-quarantine.json"].map((file) => `/${file}\n  Cache-Control: no-store`),
  ];
  const files = {
    "/404.html": '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
      + '<title>Page unavailable | fastest.ai</title></head><body><main><h1>Page unavailable</h1>'
      + '<p><a href="/wiki/">Browse the current wiki</a></p></main></body></html>\n',
  };
  if (battle) {
    const archive = renderBattleArchive(battle.records,
      { origin, release: catalogRelease, prefix: "/", interactive: !review }, battle.titleSignals, styles);
    files[battleArchivePath + "index.html"] = archive.html;
    files[battleArchiveMarkdown] = archive.markdown;
    headers.push(
      battleArchivePath + "\n  Link: <" + origin + battleArchiveMarkdown + '>; rel="alternate"; type="text/markdown"',
      battleArchiveMarkdown + "\n  Content-Type: text/markdown; charset=utf-8\n  Link: <" + origin + battleArchivePath + '>; rel="alternate"; type="text/html"',
    );
  }
  for (const entry of entries) {
    const { id, title, summary, md, html, neighbors, aliases, source, entity, evidence, methods, media, kind } = entry;
    const route = wikiHtmlRoute(id);
    const alternate = mdRoute(id);
    const backlinksHtml = neighbors.length ? `<section><h2>Graphify backlinks</h2><ul>
${neighbors.map((target) => `<li><a href="${wikiHtmlRoute(target)}">${escape(pages[target].title)}</a></li>`).join("\n")}
</ul></section>` : "";
    files[route + "index.html"] = `<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
${pageHead({ origin, route, alternate, title: title + " | fastest.ai", summary, release })}
</head><body><main class="wiki-release" data-page="${id}">
<nav aria-label="Wiki resources"><a href="/">Explorer</a><a href="/wiki/">Wiki home</a><a href="${alternate}">Markdown</a></nav>
<h1>${escape(title)}</h1>
<p>${escape(summary)}</p>
${html}
${id === "research" ? `<p><a href="${research.html}">Open the released research library</a> · <a href="${research.md}">Library Markdown</a> · <a href="/wiki/evidence-updates">Evidence updates</a></p>` : ""}
${backlinksHtml}
<p class="wiki-release-ids"><a href="/wiki/manifest.json">${release}</a> · Page ${id} · Source <code>${source}</code>${entity ? " · Entity " + escape(entity) : ""}${evidence ? " · Evidence " + escape(evidence) : ""}</p>
</main></body></html>\n`;
    files[alternate] = frontmatter({
      title, summary, kind, page: id, route, redirects: aliases.map(wikiHtmlRoute), entity, evidence, methods, media,
      release, locale: "en", status: "published", source,
    }) + `\n# ${markdown(title)}\n\n${markdown(summary)}\n\n[HTML](${route}) · [Release manifest](/wiki/manifest.json)\n\n${md}\n`
      + (id === "research" ? `\n[Open the released research library](${research.md}) · [Evidence updates](/wiki/evidence-updates.md)\n` : "")
      + (neighbors.length
        ? "\n## Graphify backlinks\n\n" + neighbors.map((target) => `- [${markdown(pages[target].title)}](${mdRoute(target)})\n`).join("")
        : "");
    headers.push(`${route}\n  Link: <${origin + alternate}>; rel="alternate"; type="text/markdown"`);
    headers.push(`${alternate}\n  Content-Type: text/markdown; charset=utf-8\n  Link: <${origin + route}>; rel="alternate"; type="text/html"`);
  }

  const home = { origin, route: "/", alternate: "/index.md", release,
    title: "fastest.ai | Local AI benchmark explorer",
    summary: review ? "Browse the public wiki, research library, and pinned hardware, model and runtime catalogs."
      : "Compare local AI hardware, models, and costs. Read the methods and evidence behind each comparison." };
  const catalogManifest = `/catalog/${catalogRelease}/manifest.json`;
  const homeBody = `<main class="wiki-release release-fallback">
<h1>fastest.ai</h1><p>Also known as ${alternateName}.</p>${review
    ? '<p><strong>Non-production review</strong> · <a href="/review-manifest.json">Review manifest</a></p>' : ""}<p>${home.summary}</p>
<nav aria-label="Released content"><a href="/wiki/">Wiki</a><a href="${research.html}">Research library</a>
<a href="/index.md">Markdown</a><a href="/wiki/manifest.json">${release}</a>${directories.map(([title, path]) => `<a href="${path}">${title}</a>`).join("")}${review ? `<a href="${catalogManifest}">Catalog manifest</a>` : ""}${advisorUrl ? `<a href="${escape(advisorUrl)}">Guided advisor</a>` : ""}${battle ? `<a href="${battleArchivePath}">Hardware battles</a>` : ""}</nav>
<section data-home-highlights${availableHighlights.length ? "" : " hidden"}><h2>Research highlights</h2><ul>
${availableHighlights.map(({ href, title, summary }) => `<li><a href="${href}">${escape(title)}</a> · ${escape(summary)}</li>`).join("\n")}
</ul></section>
</main>`;
  files["/index.md"] = frontmatter({
    page: "home", route: "/", locale: "en", status: "published", release, source: "wiki/highlights.json",
  }) + `\n# fastest.ai\n\nAlso known as ${alternateName}.\n\n${review ? "Non-production review · [Review manifest](/review-manifest.json)\n\n" : ""}${home.summary}\n\n[Wiki](/wiki/index.md) · [Research library](${research.md}) · [Release manifest](/wiki/manifest.json)${directories.map(([title, path]) => ` · [${title}](${path}.md)`).join("")}${review ? ` · [Catalog manifest](${catalogManifest})` : ""}${battle ? ` · [Hardware battles](${battleArchiveMarkdown})` : ""}\n`
    + (availableHighlights.length ? "\n## Research highlights\n\n" + availableHighlights.map((entry) =>
      `- [${markdown(entry.title)}](${entry.markdown}) · ${markdown(entry.summary)}\n`).join("") : "");
  headers.push(`/\n  Link: <${origin}/index.md>; rel="alternate"; type="text/markdown"`);

  const canonicalRoutes = ["/", ...(review ? [] : ["/prices"]), ...(battle ? [battleArchivePath] : []), ...entries.map(({ id }) => wikiHtmlRoute(id)), research.html].sort();
  const citationUrls = [
    `- [Evidence updates](${origin}/wiki/evidence-updates.md)`,
    `- [Current wiki release](${origin}/wiki/manifest.json)`,
    `- [Research library](${origin + research.md}): Approved research references and timestamped methods`,
    `- [Research release manifest](${origin + researchRoot}manifest.json)`,
    ...(catalogRelease ? [`- [Catalog release manifest](${origin + catalogManifest})`] : []),
    ...(battle ? [`- [Hardware battles](${origin + battleArchiveMarkdown}): Configurations and decision factors for exact matchups`] : []),
    ...(catalogOpenApi ? [`- [Catalog search (OpenAPI)](${origin + catalogOpenApi}): Hardware, machines, model repositories, and runtimes from this snapshot`] : []),
  ];
  files["/robots.txt"] = `User-agent: *\n${review ? "Disallow" : "Allow"}: /\nSitemap: ${origin}/sitemap.xml\n`;
  files["/sitemap.xml"] = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + canonicalRoutes.map((route) => `  <url><loc>${escape(origin + route)}</loc></url>\n`).join("") + "</urlset>\n";
  files["/llms.txt"] = `# fastest.ai\n\n> ${home.summary}\n\n## Release references\n\n${citationUrls.join("\n")}\n\n## Wiki\n\n${entries.map(({ id, title, summary }) =>
    `- [${markdown(title)}](${origin + mdRoute(id)}): ${markdown(summary)}`).join("\n")}\n`;
  files["/wiki/manifest.json"] = JSON.stringify({
    release, locale: "en", researchRelease, catalogRelease,
    ...(catalogOpenApi && { catalogApi: { endpoint: catalogApiPath, openapi: catalogOpenApi } }),
    pages: entries.map(({ id, source, entity, evidence }) => ({ id, source, entity, evidence, html: wikiHtmlRoute(id), markdown: mdRoute(id) })),
    highlights: availableHighlights.map(({ id, type, href, markdown, priority, starts, ends, source }) =>
      ({ id, type, href, markdown, priority, starts, ends, source })),
  }, null, 2) + "\n";
  if (!review) files["/_routes.json"] = JSON.stringify({
    version: 1, include: ["/", "/index", "/index.html", "/index.md", "/api/feedback",
      "/prices", "/prices/", "/prices.html", "/api/price-comparison", "/api/runtime-releases",
      ...(catalogOpenApi ? [catalogApiPath, "/api/battle-popularity"] : []),
      "/research/*", "/wiki/*", "/catalog/*", "/catalog-data/*", "/downloads/*",
      ...(battle ? ["/battles", "/battles/*", battleArchiveMarkdown] : []),
      "/robots.txt", "/sitemap.xml", "/llms.txt", "/evidence-quarantine.json"], exclude: [],
  }, null, 2) + "\n";
  files["/_redirects"] = [...redirects].flatMap(([old, id]) => [
    `/wiki/${old} ${wikiHtmlRoute(id)} 301`, `${wikiHtmlRoute(old)} ${wikiHtmlRoute(id)} 301`,
    `${mdRoute(old)} ${mdRoute(id)} 301`,
  ]).join("\n") + "\n";
  files["/_headers"] = headers.join("\n\n") + "\n";
  // A rebuilt Pages output must drop old routes, including formerly published pages.
  await Promise.all([
    rm(join(output, "wiki"), { recursive: true, force: true }),
    rm(join(output, battleArchivePath), { recursive: true, force: true }),
    rm(join(output, battleArchiveMarkdown), { force: true }),
  ]);
  await Promise.all(Object.entries(files).map(async ([name, value]) => {
    const target = join(output, name);
    await mkdir(dirname(target), { recursive: true });
    await writeFile(target, value);
  }));
  return { homeHead: pageHead(home), homeBody, highlights: availableHighlights, publicPages: pages };
}
