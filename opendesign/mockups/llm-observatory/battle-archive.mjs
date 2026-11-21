import { escapeHtml, escapeMarkdown } from "./catalog-card.mjs";
import {
  battleEvidence, battleFactor, battleHref, battleKinds, battleMarkdown, battleRankings, battleScopeNote,
  battleSources, battleSuggestions,
} from "./battle.mjs";

export const battleArchivePath = "/battles/";
export const battleArchiveMarkdown = "/battles.md";
const title = "Hardware battles";
const summary = "Compare decision factors for exact GPU and machine pairings from the released catalog.";
const mentionTitle = "YouTube title mentions";
const number = new Intl.NumberFormat("en", { maximumFractionDigits: 2 });
const en = (english, chinese, values) => english.replace(/\{(\w+)\}/g, (_, key) => values[key]);
const htmlLink = (title, href) => '<a href="' + escapeHtml(href) + '">' + escapeHtml(title) + "</a>";

export function renderBattleArchive(records, urls, titleSignals, styles = "") {
  const sample = titleSignals && "Estimated from a sample of " + number.format(titleSignals.sampleSize) + " video titles"
    + (titleSignals.observedOn ? " as of " + titleSignals.observedOn : "") + ". Counts are unique videos that mention both configurations.";
  const sections = Object.entries(battleKinds).map(([kind, [label]]) => {
    const ranked = battleRankings(records, kind, titleSignals?.pairs?.[kind]);
    const pairs = battleSuggestions(records, kind);
    return { label, pairs, ranked };
  });
  const link = (href) => urls.origin + href;
  const pairLink = (pair) => "/" + battleHref(pair.kind, pair, urls.release);
  const pairName = ({ left, right }) => left.name + " vs. " + right.name;
  const archiveLink = htmlLink("Markdown", battleArchiveMarkdown);
  const catalogLink = "/catalog/" + urls.release + "/manifest.json";
  const formatSize = (pair) => number.format(pair.count) + (pair.count === 1 ? " video title" : " video titles");
  const renderValue = (value) => value ? value.source ? htmlLink(value.text, value.source) : escapeHtml(value.text) : "Unavailable";

  const html = '<!doctype html><html lang="en"><head><meta charset="utf-8">'
    + '<meta name="viewport" content="width=device-width,initial-scale=1">'
    + '<meta name="description" content="' + summary + '"><title>' + title + " | fastest.ai</title>"
    + '<link rel="canonical" href="' + escapeHtml(link(battleArchivePath)) + '">'
    + '<link rel="alternate" type="text/markdown" href="' + battleArchiveMarkdown + '">' + styles
    + "<style>.battle-archive section{margin-block:2rem}.battle-archive table{width:100%;table-layout:fixed;border-collapse:collapse;font-size:.92rem}"
    + ".battle-archive :is(th,td){padding:.55rem;text-align:start;vertical-align:top;border-bottom:1px solid #ccd7e2;overflow-wrap:anywhere}"
    + ".battle-archive th{background:#f4f7fa}.battle-archive td small{display:block;color:#4b5864}</style>"
    + '</head><body><main class="wiki-release battle-archive"><nav aria-label="Battle resources">'
    + htmlLink("Interactive battles", "/#battle") + archiveLink + htmlLink("Catalog manifest", catalogLink)
    + "</nav><h1>" + title + "</h1><p>" + summary + "</p><p>Catalog " + escapeHtml(urls.release) + "</p>"
    + sections.map(({ label, pairs, ranked }) => "<section><h2>" + label + "</h2>"
      + (ranked.length ? "<h3>" + mentionTitle + "</h3><p>" + escapeHtml(sample) + "</p><ul>"
        + ranked.map(pair => "<li>" + htmlLink(pairName(pair), pairLink(pair)) + " · " + formatSize(pair)
          + pair.sources.map((source, i) => " · " + htmlLink("Video " + (i + 1), source)).join("") + "</li>").join("") + "</ul>" : "")
      + "<h3>Suggested matchups</h3>"
      + pairs.map(pair => "<article><h4>" + escapeHtml(pairName(pair)) + "</h4><p>" + htmlLink("Open comparison", pairLink(pair))
        + " · " + escapeHtml(pair.reason[0]) + "</p><ul>"
        + pair.rows.filter(({ factor }) => factor).map(({ factor }) => "<li>" + escapeHtml(battleFactor(factor, en, number)) + "</li>").join("")
        + "<li>" + escapeHtml(pair.decision[0]) + "</li></ul>"
        + '<table><thead><tr><th scope="col">Specification</th><th scope="col">' + escapeHtml(pair.left.name)
        + '</th><th scope="col">' + escapeHtml(pair.right.name) + "</th></tr></thead><tbody>"
        + pair.rows.map(row => '<tr><th scope="row">' + escapeHtml(row.label[0])
          + (row.differentScope ? "<br><small>" + battleScopeNote[0] + "</small>" : "") + "</th><td>"
          + renderValue(row.left) + "</td><td>" + renderValue(row.right) + "</td></tr>").join("")
        + "</tbody></table>"
        + [pair.left, pair.right].map(product => "<p><strong>" + escapeHtml(product.name) + "</strong> · "
          + battleSources(pair, product, urls).map(({ label, href }) => htmlLink(label[0], href)).join(" · ") + "</p>").join("")
        + "<p>" + battleEvidence[0] + "</p></article>").join("")
      + "</section>").join("") + "</main></body></html>\n";

  const markdown = "# " + title + "\n\n" + summary + "\n\nCatalog " + urls.release + " · [Catalog manifest]("
    + link(catalogLink) + ") · [HTML](" + link(battleArchivePath) + ")\n\n"
    + sections.map(({ label, pairs, ranked }) => "## " + label + "\n\n"
      + (ranked.length ? "### " + mentionTitle + "\n\n" + escapeMarkdown(sample) + "\n\n"
        + ranked.map(pair => "- [" + escapeMarkdown(pairName(pair)) + "](" + link(pairLink(pair)) + ") · " + formatSize(pair)
          + pair.sources.map((source, i) => " · [Video " + (i + 1) + "](" + source + ")").join("")).join("\n") + "\n\n" : "")
      + "### Suggested matchups\n\n" + pairs.map(pair => battleMarkdown(pair, urls, "####")).join("\n")).join("\n");
  return { html, markdown };
}
