export function modelTags(row, identity) {
  return [...new Set([
    ...row.detail.split(" · ").filter(Boolean),
    ...(identity?.artifacts?.map(({ format }) => format) ?? []),
  ])];
}

function byRepository(left, right) {
  const a = left.id.toLowerCase();
  const b = right.id.toLowerCase();
  if (a !== b) return a < b ? -1 : 1;
  if (left.id === right.id) return 0;
  return left.id < right.id ? -1 : 1;
}

export function modelRepositoryMap(upstream, supplemental) {
  const byId = new Map(upstream.map(row => [row.id, row]));
  if (byId.size !== upstream.length) throw new Error("Duplicate upstream model repository");
  for (const row of supplemental) {
    if (byId.get(row.id)?.supplemental || byId.has(row.id) !== (row.supplemental.inUpstream === true)) {
      throw new Error("Invalid or duplicate model supplement: " + row.id);
    }
    byId.set(row.id, row);
  }
  return byId;
}

export function modelCollections(upstream, discovery, supplemental) {
  const byId = modelRepositoryMap(upstream, supplemental);
  const all = [...byId.values()];
  const ranked = rows => rows.map((row, index) => ({
    ...byId.get(row.id), discovery: { ...row, rank: index + 1 },
  }));
  return { byId, all, recent: recentModels(supplemental), popular: ranked(discovery.popular), small: ranked(discovery.small) };
}

export function recentModels(rows) {
  return rows.filter(row => row.supplemental).sort((a, b) =>
    b.supplemental.revisionDate.localeCompare(a.supplemental.revisionDate) || byRepository(a, b));
}

export function queryModelCatalog(rows, identities, { query = "", tag = "", license = "", page = 1, pageSize = 30, ranked = false } = {}) {
  const terms = query.toLowerCase().trim().split(/\s+/).filter(Boolean);
  const matched = rows.filter((row) => {
    if (license === "__missing" && row.license) return false;
    if (license && license !== "__missing" && row.license !== license) return false;
    if (!terms.length && !tag) return true;
    const tags = modelTags(row, identities[row.id]);
    if (tag && !tags.includes(tag)) return false;
    const text = [row.id, row.name, row.license, ...tags].join(" ").toLowerCase();
    return terms.every((term) => text.includes(term));
  });
  if (!ranked) matched.sort(byRepository);
  const pages = Math.max(1, Math.ceil(matched.length / pageSize));
  const current = Math.max(1, Math.min(page, pages));
  const start = (current - 1) * pageSize;
  return { rows: matched.slice(start, start + pageSize), total: matched.length, pages, current, start };
}
