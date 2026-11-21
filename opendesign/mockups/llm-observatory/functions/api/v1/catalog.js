import { catalogPath, catalogReleasePattern, deniedCatalogPin, modelIdPattern, modelShard } from "../../../catalog-paths.mjs";
import { catalogApiPath, catalogKinds, catalogMaxOffset, catalogPageSize, catalogQueryLength } from "../../../catalog-api.mjs";

const parameters = new Set(["kind", "revision", "q", "limit", "offset"]);

function json(body, status = 200) {
  return Response.json(body, {
    status,
    headers: { "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" },
  });
}

function fail(status, message) {
  return json({ error: message }, status);
}

function selection(url) {
  const query = new URL(url).searchParams;
  if ([...query.keys()].some(key => !parameters.has(key) || query.getAll(key).length !== 1)) return null;

  const kind = query.get("kind");
  const revision = query.get("revision");
  const term = (query.get("q") ?? "").trim().toLowerCase();
  const limit = query.get("limit") ?? String(catalogPageSize);
  const offset = query.get("offset") ?? "0";
  if (!catalogKinds.includes(kind) || (revision !== null && !catalogReleasePattern.test(revision)) ||
      term.length > catalogQueryLength || (kind === "models" && term && !modelIdPattern.test(term)) ||
      !/^[1-9]\d?$/.test(limit) || Number(limit) > catalogPageSize ||
      !/^(0|[1-9]\d*)$/.test(offset) || Number(offset) > catalogMaxOffset || (offset !== "0" && !revision)) return null;

  return { kind, revision, term, limit: Number(limit), offset: Number(offset) };
}

async function readAsset(context, path) {
  const response = await context.env.ASSETS.fetch(new Request(new URL(path, context.request.url), {
    headers: { "Cache-Control": "no-cache" },
  }));
  if (!response.ok || !response.headers.get("Content-Type")?.includes("application/json")) throw new Error("Catalog asset unavailable");
  return response.json();
}

// Each asset is one owner-prefix shard. Pinned counts let a page skip every preceding shard.
async function modelPage(read, counts, { term, offset, limit }) {
  async function load(key) {
    if (!/^[a-z0-9_][a-z0-9_.-]?$/.test(key)) throw new Error("Invalid catalog shard key");
    const rows = await read(key);
    if (!Array.isArray(rows) || rows.length !== counts[key]) throw new Error("Invalid catalog shard count");
    return rows;
  }

  if (term) {
    const key = modelShard(term);
    const rows = Object.hasOwn(counts, key) ? await load(key) : [];
    const matches = rows.filter(({ id }) => id.toLowerCase() === term);
    return { rows: matches.slice(offset, offset + limit), total: matches.length };
  }

  const keys = Object.keys(counts).sort();
  const total = keys.reduce((sum, key) => sum + counts[key], 0);
  const page = [];
  let skip = offset;
  for (const key of keys) {
    if (skip >= counts[key]) {
      skip -= counts[key];
      continue;
    }
    const rows = await load(key);
    page.push(...rows.slice(skip, skip + limit - page.length));
    skip = 0;
    if (page.length === limit) break;
  }
  return { rows: page, total };
}

async function catalogPage(read, modelShardCounts, query) {
  const { kind, term, limit, offset } = query;
  if (kind === "models") return modelPage(read, modelShardCounts, query);
  const entries = await read(kind);
  const matches = term ? entries.filter(({ id, name, detail, aliases = [] }) =>
    [id, name, detail, ...aliases].some(value => value?.toLowerCase().includes(term))) : entries;
  return { rows: matches.slice(offset, offset + limit), total: matches.length };
}

export async function onRequestGet(context) {
  const query = selection(context.request.url);
  if (!query) return fail(400, "Invalid catalog selectors. Pin the revision for subsequent pages.");

  try {
    const [{ paths }, wiki] = await Promise.all([
      readAsset(context, "/evidence-quarantine.json"),
      readAsset(context, "/wiki/manifest.json"),
    ]);
    const release = query.revision ?? wiki.catalogRelease;
    if (paths.includes(catalogApiPath) || deniedCatalogPin(release, paths)) return fail(410, "This catalog release was withdrawn.");
    if (!catalogReleasePattern.test(release) || release !== wiki.catalogRelease) return fail(404, "Catalog release unavailable.");

    const root = `/catalog/${release}`;
    const manifestUrl = root + "/manifest.json";
    const manifest = await readAsset(context, manifestUrl);
    if (!/^[a-f0-9]{64}$/.test(manifest.snapshotId) || !manifest.snapshotId.startsWith(release.slice(3))) return fail(404, "Catalog release unavailable.");

    const { kind, limit, offset } = query;
    const read = file => readAsset(context, `/catalog-data/${release}/${file}.json`);
    const { rows, total } = await catalogPage(read, manifest.modelShardCounts, query);
    const results = rows.map(row => ({
      id: row.id, name: row.name, detail: row.detail ?? null,
      source: row.vendorSpec?.source ?? row.source ?? null,
      html: "/" + catalogPath(release, kind, row.id),
      markdown: "/" + catalogPath(release, kind, row.id, "md"),
    }));
    return json({
      apiVersion: "1", revision: release, snapshotId: manifest.snapshotId, kind, manifest: manifestUrl,
      scope: "Catalog metadata. Benchmark measurements are published separately.",
      results, pagination: { limit, offset, total, nextOffset: offset + results.length < total ? offset + results.length : null },
    });
  } catch {
    return fail(503, "Catalog or withdrawal policy unavailable.");
  }
}
