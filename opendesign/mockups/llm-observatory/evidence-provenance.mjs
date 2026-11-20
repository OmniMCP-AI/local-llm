// Bind source-wide quarantine to the public metadata that carries the same evidence.
export function withdrawnReference(index, approvals) {
  const sources = index.sources.filter(({ id }) => approvals[id]?.status === "withdrawn");
  const tokens = sources.flatMap(({ id, url, note, records }) => [
    id, url, note, ...records.flatMap((record) => [record.id, record.series]),
    ...(/^youtube\/([\w-]{11})$/.exec(id)?.slice(1) ?? []),
  ]).filter(Boolean);
  return (value) => typeof value === "string" && tokens.some((token) => value.includes(token));
}
