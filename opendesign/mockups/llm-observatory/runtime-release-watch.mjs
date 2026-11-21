import runtimeCatalog from "./catalog-runtimes.json" with { type: "json" };
import { releaseOrigin } from "./release-origin.mjs";

const watchPath = "/runtime-releases";
const schema = "fastest.ai/runtime-release-watch/v1";
const timestamp = (value) => typeof value === "string" && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/.test(value) &&
  Number.isFinite(Date.parse(value));
const releaseTag = /^[A-Za-z0-9_][A-Za-z0-9._/+~-]{0,127}$/;

function releaseDetails(release, repositoryUrl) {
  if (typeof release?.tag !== "string" || !releaseTag.test(release.tag) || !timestamp(release.published_at)) return null;
  const url = repositoryUrl + "/releases/tag/" + encodeURIComponent(release.tag);
  return release.source_url === url ? { tag: release.tag, url, publishedAt: release.published_at } : null;
}

export async function runtimeReleaseWatch(env) {
  const origin = releaseOrigin(env.FASTEST_RELEASE_ORIGIN);
  if (!origin) return null;
  const url = origin + watchPath;
  try {
    const response = await fetch(url + ".json", {
      cache: "no-store", redirect: "manual", signal: AbortSignal.timeout(5000),
      headers: { Accept: "application/json" },
    });
    if (response.status !== 200 || !response.headers.get("Content-Type")?.startsWith("application/json")) return null;
    const report = await response.json();
    if (report?.schema !== schema || !report.sources || !Array.isArray(report.releases) ||
      Object.values(report.sources).some(source => source?.mode === "fixture")) return null;

    const runtimes = [];
    for (const { id, source: repositoryUrl } of runtimeCatalog) {
      const source = report.sources[id];
      if (source?.mode !== "live" || !timestamp(source.last_successful_refresh) || typeof source.stale !== "boolean" ||
        repositoryUrl !== "https://github.com/" + source.repository) continue;
      const current = report.releases.find(release =>
        release?.runtime_id === id && release.status === "current" && release.prerelease === false);
      const release = releaseDetails(current, repositoryUrl);
      if (current && !release) continue;
      runtimes.push({
        id, repositoryUrl, watchUrl: url + "#runtime-" + id, feedUrl: repositoryUrl + "/releases",
        refreshedAt: source.last_successful_refresh, stale: source.stale, failed: Boolean(source.last_error),
        release,
      });
    }
    return { html: url, markdown: url + ".md", runtimes };
  } catch {
    return null;
  }
}
