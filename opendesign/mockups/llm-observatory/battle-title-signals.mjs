const watchUrl = (id) => new URL(`/watch?v=${id}`, "https://www.youtube.com").href;
const ascending = (a, b) => a < b ? -1 : Number(a > b);

export function estimateBattleTitles({ observedOn, videos }, catalog) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(observedOn) || !Array.isArray(videos) ||
      new Set(videos.map(({ id }) => id)).size !== videos.length ||
      videos.some(({ id, title }) => !/^[A-Za-z0-9_-]{11}$/.test(id) || typeof title !== "string" || !title.trim())) {
    throw new Error("Invalid reviewed YouTube title sample");
  }

  const pairs = Object.fromEntries(["cards", "machines"].map(kind => {
    const eligible = new Set(catalog[kind]
      .filter(row => kind === "cards" || row.kind !== "Component reference").map(row => row.id));
    const matches = new Map();
    for (const video of videos) {
      const members = [...new Set(video[kind] ?? [])].filter(id => eligible.has(id)).sort(ascending);
      for (const [index, left] of members.entries()) {
        for (const right of members.slice(index + 1)) {
          const key = `${left}/${right}`;
          if (!matches.has(key)) matches.set(key, { left, right, sources: [] });
          matches.get(key).sources.push(watchUrl(video.id));
        }
      }
    }
    return [kind, Array.from(matches.values(), pair => ({
      ...pair, count: pair.sources.length, sources: pair.sources.sort(ascending),
    })).sort((a, b) => b.count - a.count || ascending(a.left, b.left) || ascending(a.right, b.right))];
  }));
  return { sampleSize: videos.length, observedOn, pairs };
}
