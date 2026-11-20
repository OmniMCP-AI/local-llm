const escape = (value) => String(value).replace(/[&<>"']/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
})[char]);
const markdown = (value) => String(value).replace(/[\\`*_{}\[\]<>]/g, "\\$&").replace(/\r?\n/g, " ");
const href = (url) => {
  if (url.startsWith("#wiki/")) return "/" + url;
  if (new URL(url).protocol === "https:") return url;
  throw new Error("Unsupported public research URL");
};
const link = (text, url) => `[${markdown(text)}](<${href(url)}>)`;
const anchor = (text, url) => `<a href="${escape(href(url))}">${escape(text)}</a>`;
const term = (index, facet, id) => index.vocabulary[facet][id][0];

function tags(index, source) {
  return Object.entries(source.topics).map(([id, locator]) => ({
    id, locator,
    label: term(index, "topics", id),
    url: locator.startsWith("https://") ? locator : source.url,
  }));
}

function recordFields(index, record) {
  return [
    ["Task", record.task ?? "Unspecified"],
    ["Task tags", record.topics.map((id) => term(index, "topics", id)).join(", ") || "Unspecified"],
    ["Measurement", `${term(index, "dimensions", record.dimension)} · ${record.metric}`],
    ["Setup", [record.hardware, record.model, record.runtime, record.quant].filter(Boolean).join(" / ")],
    ["Conditions", record.conditions],
    ["Evidence", record.evidence],
  ];
}

function sourceFields(index, source) {
  return [
    ["Publication type", term(index, "formats", source.format)],
    ["Publisher", source.publisher],
    ["Published", source.date ?? "Date unknown"],
    ["Source language", source.language ?? "Unknown"],
  ];
}

function renderSourceHtml(index, source) {
  const records = source.records.map((record) => `<section class="record" id="${escape(record.id)}" data-record="${escape(record.id)}">
<h4>${escape(record.task || record.metric)}</h4>
<p>${anchor(record.timestamp, record.url)} · ${anchor(record.series, record.seriesUrl)} · ${escape(record.id)}</p>
<dl>${recordFields(index, record).map(([key, value]) => `<dt>${escape(key)}</dt><dd>${escape(value || "Unknown")}</dd>`).join("")}</dl>
</section>`).join("\n");
  return `<article id="${escape(source.id)}" data-source="${escape(source.id)}">
<h2>${anchor(source.title, source.url)}</h2>
<p class="metadata">${sourceFields(index, source).map(([, value]) => escape(value)).join(" · ")}</p>
<p>${escape(source.context)}</p>
<p class="metadata">${escape(source.id)}${source.note ? " · " + anchor("Source note", source.note) : ""}</p>
<h3>Discussed use cases</h3>
<ul class="topics">${tags(index, source).map(({ id, label, url, locator }) =>
    `<li>${anchor(label, url)} <small>${escape(id)}${locator === url ? "" : " · " + escape(locator)}</small></li>`).join("")}</ul>
${records ? `<details><summary>Reported observations <span data-record-count>${source.records.length}</span></summary>${records}</details>` : "<p>No indexed observations.</p>"}
</article>`;
}

export function renderResearchHtml(index) {
  const options = (name, label, entries, blank = true) => `<label>${label}<select name="${name}">${blank ? '<option value="">All</option>' : ""}
${entries.map(([id, text]) => `<option value="${escape(id)}">${escape(text)}</option>`).join("")}</select></label>`;
  const labels = (facet) => Object.entries(index.vocabulary[facet]).map(([id, names]) => [id, names[0]]);
  const methods = index.methods.map((method) => `<section id="${escape(method.id)}">
<h3>${escape(method.title)}</h3><p>${escape(method.summary)} ${anchor(method.citation, method.url)}</p>
<p><strong>Use cases</strong> ${method.topics.map((id) =>
    `<a href="?topic=${encodeURIComponent(id)}">${escape(term(index, "topics", id))}</a>`).join(" · ")}</p>
<p><strong>${escape(method.gate.milestones)} release gates</strong> ${escape(method.gate.requirement)}</p>
</section>`).join("\n");
  return `<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Research library | fastest.ai</title>
<style>
body{color:#17212b;background:#f8f9fa;font:1rem/1.55 system-ui,sans-serif;margin:0}
main{max-width:58rem;margin:auto;padding:1.5rem 1rem 3rem}
a{color:#174e82;text-underline-offset:.18em} h1,h2,h3,h4{line-height:1.24}
h1{font-size:2.5rem;margin-bottom:.35em} h2,h3,p{margin:.65rem 0}
nav,.topics{display:flex;flex-wrap:wrap;gap:1rem} .topics{padding:0;list-style:none}
article,form,#methods{background:white;border:1px solid #d1d9e0;border-radius:.5rem;padding:1rem;margin:1rem 0}
form{display:grid;grid-template-columns:repeat(auto-fit,minmax(11rem,1fr));gap:1rem}
label,select,input{display:block;width:100%;box-sizing:border-box} select,input,button{font:inherit;padding:.4rem}
summary{cursor:pointer;font-weight:600} small,.metadata{color:#4b5864}
.record{border-top:1px solid #d1d9e0;margin-top:1rem} dl{display:grid;grid-template-columns:max-content 1fr;gap:.3rem 1rem}
dt{font-weight:600} dd{margin:0} #methods section{border-top:1px solid #d1d9e0;padding:.45rem 0}
[hidden]{display:none!important}
</style><script type="module" src="./library.mjs"></script></head><body><main>
<nav aria-label="Research library resources"><a href="/#wiki">Wiki</a><a href="#methods">Research methods</a>
<a href="./library.md">Markdown</a><a href="./index.json">Index data</a><a href="./graphify.json">Graphify index</a>
<a href="./manifest.json">Release manifest</a></nav>
<h1>Research library</h1>
<p>Discover the use cases publications discuss and inspect the task, measurement and evidence attached to each observation.</p>
<p class="metadata">Release ${escape(index.release)} · Vocabulary v${escape(index.taxonomyVersion)}</p>
<form id="research-filters" method="get" aria-label="Filter research" hidden>
<label>Search<input name="query" type="search"></label>
${options("format", "Publication type", labels("formats"))}
${options("topic", "Discussed use case", labels("topics"))}
${options("task", "Observation task", [...labels("topics"), ["unspecified", "Unspecified"]])}
${options("dimension", "Measurement", labels("dimensions"))}
${options("sort", "Sort", [["newest", "Newest first"], ["title", "Title"]], false)}
<div><button>Apply filters</button> <a href="./library.html">Clear filters</a></div>
</form>
<p id="filter-status" aria-live="polite">${index.sources.length} sources</p>
<section id="research-sources" aria-label="Research results">
${index.sources.map((source) => renderSourceHtml(index, source)).join("\n")}
</section>
<section id="methods"><h2>Timestamped research methods</h2>
${methods}
</section>
</main></body></html>
`;
}

export function renderResearchMarkdown(index) {
  const sources = index.sources.map((source) => [
    "## " + link(source.title, source.url), "",
    `${sourceFields(index, source).map(([key, value]) => `**${key}** ${markdown(value)}`).join(" · ")}`,
    "", `Source ID \`${source.id}\`${source.note ? " · " + link("Source note", source.note) : ""}`,
    "", markdown(source.context),
    "", "**Discussed use cases**", "",
    ...tags(index, source).map(({ id, label, url, locator }) =>
      `- ${link(label, url)} (\`${id}\`${locator === url ? "" : " · " + markdown(locator)})`),
    "",
    ...source.records.flatMap((record) => [
      "### " + markdown(record.task || record.metric), "",
      `Observation \`${record.id}\` · ${link(record.series, record.seriesUrl)} · ${link(record.timestamp, record.url)}`, "",
      ...recordFields(index, record).map(([key, value]) => `- **${key}** ${markdown(value || "Unknown")}`),
      "",
    ]),
    ...(source.records.length ? [] : ["No indexed observations.", ""]),
  ].join("\n"));
  const methods = index.methods.map((method) => [
    `### ${markdown(method.title)}`, "",
    `${markdown(method.summary)} ${link(method.citation, method.url)}`, "",
    `**Use cases** ${method.topics.map((id) => `[${term(index, "topics", id)}](./library.html?topic=${id})`).join(" · ")}`, "",
    `**${method.gate.milestones} release gates** ${markdown(method.gate.requirement)}`, "",
  ].join("\n"));
  return [
    "---", "title: Research library", "page: research",
    "release: " + index.release, "taxonomy: " + index.taxonomyVersion, "locale: en", "---", "",
    "# Research library", "",
    "[Filter the library](./library.html) · [Index data](./index.json) · [Graphify](./graphify.json) · [Release manifest](./manifest.json)", "",
    "Research discovery metadata. Publications and their observations retain independent use-case tags.", "",
    ...sources, "## Timestamped research methods", "", ...methods,
  ].join("\n");
}
