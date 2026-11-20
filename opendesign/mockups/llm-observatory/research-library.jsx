import React, { useState } from "react";
import { ArrowUpRight, SlidersHorizontal } from "lucide-react";
import { useLocale } from "./locale";
import { filterResearch } from "./research-filter.mjs";
import vocabulary from "./wiki/context-vocabulary.json";
import index from "./wiki/research-index.json";

const languages = ["en", "zh-Hans", "es", "ja", "ko", "de", "hi", "fr", "ar"];
const taskIds = new Set(index.sources.flatMap(source => source.records.flatMap(record => record.topics)));
const allTopics = Object.keys(vocabulary.topics);
const options = {
  format: Object.keys(vocabulary.formats),
  topic: allTopics,
  task: [...allTopics.filter(id => taskIds.has(id)), "unspecified"],
  dimension: Object.keys(vocabulary.dimensions),
  sort: ["newest", "title"],
};
const groups = { format: "formats", topic: "topics", task: "topics", dimension: "dimensions", sort: "ui" };

export function useResearchLabels() {
  const { language, t } = useLocale();
  return (group, key) => {
    const labels = vocabulary[group][key];
    if (language === "zh-Hant") return t(labels[0], labels[1]);
    return labels[languages.indexOf(language)] ?? labels[0];
  };
}

function RecordList({ records, label, locale }) {
  const [limit, setLimit] = useState(5);
  return <div className="research-record-list">
    {records.slice(0, limit).map(record => <div className="research-record" key={record.id}>
      <div><strong>{record.task || record.metric}</strong> <a href={record.url} dir="ltr" target="_blank" rel="noreferrer">{record.timestamp} ↗</a></div>
      <small dir="ltr"><a href={record.seriesUrl} target="_blank" rel="noreferrer">{record.series}</a> / {record.id}</small>
      <dl>
        <dt>{label("ui", "dimension")}</dt><dd>{label("dimensions", record.dimension)} · {record.metric}</dd>
        <dt>{label("ui", "task")}</dt><dd>{record.topics.map(id => label("topics", id)).join(" · ") || label("ui", "unspecified")}</dd>
        <dt>{label("ui", "setup")}</dt><dd>{[record.hardware, record.model, record.runtime, record.quant].join(" / ")}</dd>
        <dt>{label("ui", "conditions")}</dt><dd>{record.conditions}</dd>
        <dt>{label("ui", "evidence")}</dt><dd>{record.evidence}</dd>
      </dl>
    </div>)}
    {limit < records.length && <button className="btn outline" onClick={() => setLimit(limit+10)}>{label("ui", "more")} ({(records.length-limit).toLocaleString(locale)})</button>}
  </div>;
}

function SourceCard({ source, records, label, locale, filters, onFilter }) {
  const stamp = source.topics[filters.topic];
  const url = stamp?.startsWith("https://") ? stamp : source.url;
  const local = url.startsWith("#");
  const date = source.date && new Intl.DateTimeFormat(locale, { dateStyle: "medium", timeZone: "UTC" }).format(new Date(source.date+"T00:00:00Z"));
  return <article className="research-card">
    <div className="research-byline"><b>{label("formats",source.format)}</b><span>{source.publisher}</span><span>{date || label("ui","undated")}</span></div>
    <h2><a href={url} target={local ? undefined : "_blank"} rel={local ? undefined : "noreferrer"}>{source.title} <ArrowUpRight size={15}/></a></h2>
    <p>{source.context}</p>
    <div className="research-topics" aria-label={label("ui","topic")}>{Object.keys(source.topics).map(topic =>
      <button key={topic} type="button" aria-pressed={filters.topic===topic} onClick={() => onFilter("topic",filters.topic===topic ? "" : topic)}>{label("topics",topic)}</button>
    )}</div>
    {records.length > 0 ? <details className="research-records"><summary>{label("ui","records")} <b>{records.length.toLocaleString(locale)}</b></summary>
      <RecordList records={records} label={label} locale={locale}/></details> : <small>{label("ui","no-records")}</small>}
    {source.note && <a className="research-note" href={source.note} target="_blank" rel="noreferrer">{label("ui","note")} ↗</a>}
  </article>;
}

function Results({ matches, label, locale, filters, onFilter }) {
  const [limit, setLimit] = useState(10);
  return <>
    <div aria-live="polite" className="research-count">{label("ui","sources")} <b>{matches.length.toLocaleString(locale)}</b></div>
    {!matches.length && <p>{label("ui","none")}</p>}
    <div className="research-list">{matches.slice(0,limit).map(({ source, records }) => <SourceCard key={source.id}
      source={source} records={records} label={label} locale={locale} filters={filters} onFilter={onFilter}/>)}</div>
    {limit < matches.length && <button className="btn outline" onClick={() => setLimit(limit+10)}>{label("ui","more")} ({(matches.length-limit).toLocaleString(locale)})</button>}
  </>;
}

export function ResearchLibrary({ go }) {
  const { locale } = useLocale();
  const label = useResearchLabels();
  const params = new URLSearchParams(location.hash.split("?")[1]);
  const filters = { query: params.get("query") || "" };
  for (const [key, values] of Object.entries(options)) {
    const selected = params.get(key);
    filters[key] = values.includes(selected) ? selected : key === "sort" ? "newest" : "";
  }
  function onFilter(key, value) {
    if (value) params.set(key, value);
    else params.delete(key);
    const hash = "#wiki/research" + (params.size ? "?" + params.toString() : "");
    if (key === "query") {
      try { history.replaceState(history.state, "", hash); } catch {}
    }
    go(hash, false);
  }
  function select(key) {
    return <label className="research-select">{label("ui",key)}
      <select value={filters[key]} onChange={e=>onFilter(key,e.target.value)}>
        {key!=="sort" && <option value="">{label("ui","all")}</option>}
        {options[key].map(id=><option key={id} value={id}>{label(id==="unspecified" ? "ui" : groups[key],id)}</option>)}
      </select></label>;
  }
  const testFilters = Boolean(filters.task || filters.dimension);
  const searchLabel = label("ui",testFilters ? "in-records" : "query");
  const tagText = (group, id) => [id, label(group, id), vocabulary[group][id][0],
    ...(vocabulary.aliases[id] || [])].join(" ");
  const matches = filterResearch(index.sources, filters, locale, tagText);
  return <section className="research-library">
    <header className="deep-heading"><div><h1>{label("ui","library")}</h1><p>{label("ui","intro")}</p></div></header>
    <div className="research-controls">
      <label className="research-select">{searchLabel}<input type="search" value={filters.query} onChange={e=>onFilter("query",e.target.value)}/></label>
      <div className="research-filter-row">{select("format")}{select("topic")}{select("sort")}</div>
      <details className="research-test-filters" open={testFilters || undefined}><summary><SlidersHorizontal size={15}/> {label("ui","test-context")}</summary>
        <div className="research-filter-row">{select("task")}{select("dimension")}</div>
      </details>
      {params.size > 0 && <button className="text-button" onClick={()=>go("#wiki/research",false)}>{label("ui","reset")}</button>}
    </div>
    <Results key={params.toString()} matches={matches} label={label} locale={locale} filters={filters} onFilter={onFilter}/>
  </section>;
}
