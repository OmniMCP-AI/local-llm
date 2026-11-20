import { filterResearch, readResearchFilters } from "./research-filter.mjs";

const form = document.querySelector("#research-filters");
const container = document.querySelector("#research-sources");
const status = document.querySelector("#filter-status");
const response = await fetch("./index.json");
if (!response.ok) throw new Error("Research release index is unavailable");
const { sources, vocabulary } = await response.json();
const params = new URLSearchParams(location.search);
const filters = readResearchFilters(params, vocabulary);
const labels = (facet, id) => [id, ...vocabulary[facet][id], ...(vocabulary.aliases[id] || [])].join(" ");

for (const [field, value] of Object.entries(filters)) form.elements.namedItem(field).value = value;
form.hidden = false;
const matches = filterResearch(sources, filters, "en", labels);
const cards = new Map([...container.children].map((card) => [card.dataset.source, card]));
for (const card of cards.values()) card.hidden = true;
for (const { source, records } of matches) {
  const card = cards.get(source.id);
  card.hidden = false;
  const matching = new Set(records.map(({ id }) => id));
  for (const record of card.querySelectorAll("[data-record]")) record.hidden = !matching.has(record.dataset.record);
  const detail = card.querySelector("details");
  if (detail) {
    detail.hidden = records.length === 0;
    detail.open = Boolean(filters.task || filters.dimension || filters.query);
    detail.querySelector("[data-record-count]").textContent = records.length;
  }
  container.append(card);
}
status.textContent = matches.length ? `${matches.length} ${matches.length === 1 ? "source" : "sources"}` : "No matching sources.";
