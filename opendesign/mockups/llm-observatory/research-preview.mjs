import { readFile } from "node:fs/promises";

const seed = new URL("../../../docs/Local-AI-Comparison-Platform/YouTube-Local-LLM-Transcripts/llmfit/research/benchmarks.json", import.meta.url);

export async function withPreviewResults(index) {
  const envelopes = JSON.parse(await readFile(seed, "utf8"));
  const byId = new Map(envelopes.map(({ x_local_ai_research: { original_observation_and_conditions: row } }) =>
    [row.observation_id, row]));
  if (byId.size !== envelopes.length) throw new Error("Duplicate observation in the research seed");

  const sources = index.sources.map(source => source.format !== "video" ? source : ({
    ...source,
    records: source.records.map(record => {
      const row = byId.get(record.id);
      if (!row || row.source_url !== record.url || row.series_id !== record.series ||
          row.metric !== record.metric || row.conditions !== record.conditions) {
        throw new Error("Research observation does not match its source: " + record.id);
      }
      byId.delete(record.id);
      const { value, unit, comparison_baseline: baseline, uncertainty } = row;
      return { ...record, reportedResult: { value, unit, baseline, uncertainty } };
    }),
  }));
  if (byId.size) {
    throw new Error("Preview research observations must match the repository seed exactly");
  }
  return { ...index, sources };
}
