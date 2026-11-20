function containsWords(parts, words) {
  const text = parts.join(" ").toLocaleLowerCase();
  return words.every(word => text.includes(word));
}

export function filterResearch(sources, filters, locale, tagText) {
  const { format, topic, task, dimension, query, sort } = filters;
  const words = query.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  const testFilters = Boolean(task || dimension);
  const matches = [];
  for (const source of sources) {
    if (format && source.format !== format) continue;
    if (topic && !Object.hasOwn(source.topics, topic)) continue;
    const sourceMatch = !testFilters && containsWords([
      source.title, source.publisher, source.context, ...Object.keys(source.topics).map(id => tagText("topics", id)),
    ], words);
    const records = source.records.filter(record => {
      if (dimension && record.dimension !== dimension) return false;
      if (task === "unspecified" && record.task) return false;
      if (task && task !== "unspecified" && !record.topics.includes(task)) return false;
      return sourceMatch || containsWords([
        record.id, record.series, record.metric, record.task, record.hardware, record.model,
        record.runtime, record.quant, record.conditions, record.evidence, tagText("dimensions", record.dimension),
        ...record.topics.map(id => tagText("topics", id)),
      ], words);
    });
    if (sourceMatch || records.length) matches.push({ source, records });
  }

  const collator = new Intl.Collator(locale, { sensitivity: "base", numeric: true });
  return matches.sort(({ source: a }, { source: b }) => {
    if (sort !== "title" && a.date !== b.date) return (b.date || "").localeCompare(a.date || "");
    return collator.compare(a.title, b.title) || a.id.localeCompare(b.id);
  });
}

export function readResearchFilters(params, vocabulary) {
  const valid = (field, facet) => {
    const value = params.get(field);
    return Object.hasOwn(vocabulary[facet], value) ? value : "";
  };
  return {
    format: valid("format", "formats"),
    topic: valid("topic", "topics"),
    task: params.get("task") === "unspecified" ? "unspecified" : valid("task", "topics"),
    dimension: valid("dimension", "dimensions"),
    query: params.get("query") || "",
    sort: params.get("sort") === "title" ? "title" : "newest",
  };
}

export function researchReleaseUrl(release, filters = {}) {
  const params = new URLSearchParams(Object.entries(filters).filter(([key, value]) =>
    value && !(key === "sort" && value === "newest")));
  return `/research/${release}/library.html${params.size ? "?" + params.toString() : ""}`;
}
