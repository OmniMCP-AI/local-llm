// Bind source-wide quarantine to the public metadata that carries the same evidence.
export function withdrawnReference(index, approvals) {
  const sources = index.sources.filter(({ id }) => approvals[id]?.status === "withdrawn");
  const tokens = sources.flatMap(({ id, url, note, records }) => [
    id, url, note, ...records.flatMap(({ id, series }) => [id, series,
      id.match(/^V\d{3}(?=-P)/)?.[0]?.concat("-HP-")]),
    ...(/^youtube\/([\w-]{11})$/.exec(id)?.slice(1) ?? []),
  ]).filter(Boolean);
  return (value) => typeof value === "string" && tokens.some((token) => value.includes(token));
}
