import { Client } from "pg";
import { catalogReleasePattern, deniedCatalogPin, hardwareIdPattern } from "../../catalog-paths.mjs";
import { catalogApiPath } from "../../catalog-api.mjs";

const endpoint = "/api/battle-popularity";
const maxBodyBytes = 1024;
const fields = new Set(["release", "kind", "left", "right", "requestId"]);
const randomIdPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
const snapshotPattern = /^[0-9a-f]{64}$/;
const validRelease = release => typeof release === "string" && release.length === 19 && catalogReleasePattern.test(release);
const validKind = kind => kind === "cards" || kind === "machines";
const validId = id => typeof id === "string" && id.length <= 128 && hardwareIdPattern.exec(id)?.[0] === id;

function json(body, status = 200, headers) {
  return Response.json(body, {
    status,
    headers: { "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff", ...headers },
  });
}

const error = (code, status) => json({ error: code }, status);

async function readPayload(request) {
  if (!request.body) return null;
  const reader = request.body.getReader();
  const bytes = new Uint8Array(maxBodyBytes);
  let size = 0;
  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      if (size + value.length > bytes.length) {
        await reader.cancel().catch(() => {});
        return null;
      }
      bytes.set(value, size);
      size += value.length;
    }
    return JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes.subarray(0, size)));
  } catch {
    return null;
  } finally {
    reader.releaseLock();
  }
}

async function readAsset({ env, request }, path) {
  const response = await env.ASSETS.fetch(new Request(new URL(path, request.url), {
    headers: { "Cache-Control": "no-cache" },
  }));
  if (!response.ok || !response.headers.get("Content-Type")?.includes("application/json")) {
    throw new Error("Catalog asset unavailable");
  }
  return response.json();
}

async function resolveSnapshot(context, release) {
  const [{ paths }, wiki] = await Promise.all([
    readAsset(context, "/evidence-quarantine.json"),
    readAsset(context, "/wiki/manifest.json"),
  ]);
  if (paths.includes(endpoint) || paths.includes(catalogApiPath) || deniedCatalogPin(release, paths)) {
    return { failure: error("release_withdrawn", 410) };
  }
  if (wiki.catalogRelease !== release) return { failure: error("release_unavailable", 404) };

  const manifest = await readAsset(context, "/catalog/" + release + "/manifest.json");
  const { snapshotId } = manifest;
  // The deployment manifest identifies the exact snapshot even when another
  // PostgreSQL snapshot happens to have the same short prefix.
  if (manifest.release !== release || typeof snapshotId !== "string" || snapshotId.length !== 64 ||
      !snapshotPattern.test(snapshotId) || "v1-" + snapshotId.slice(0, 16) !== release) {
    return { failure: error("release_unavailable", 404) };
  }
  return { snapshotId };
}

async function query(connectionString, sql, params) {
  const client = new Client({ connectionString, connectionTimeoutMillis: 3000, query_timeout: 5000 });
  try {
    await client.connect();
    const { rows: [result] } = await client.query(sql, params);
    return result;
  } finally {
    await client.end();
  }
}

async function rank(context) {
  const params = new URL(context.request.url).searchParams;
  const release = params.get("release");
  const kind = params.get("kind");
  if (params.size !== 2 || !validRelease(release) || !validKind(kind)) return error("invalid_selection", 400);
  const connectionString = context.env.BATTLES_PG?.connectionString;
  if (!connectionString) return error("popularity_unavailable", 503);

  const { snapshotId, failure } = await resolveSnapshot(context, release);
  if (failure) return failure;
  const { pairs } = await query(connectionString, "SELECT fastest_battles.rank_comparisons($1, $2) AS pairs", [snapshotId, kind]);
  return pairs === null ? error("release_unavailable", 404) : json({ pairs });
}

async function record(context) {
  const { request } = context;
  const url = new URL(request.url);
  if (request.headers.get("Origin") !== url.origin) return error("origin_not_allowed", 403);
  if (url.search) return error("invalid_selection", 400);
  const type = request.headers.get("Content-Type")?.split(";", 1)[0].trim().toLowerCase();
  if (type !== "application/json") return error("expected_json", 415);

  const payload = await readPayload(request);
  if (!payload || typeof payload !== "object" || Array.isArray(payload) ||
      Object.keys(payload).some(key => !fields.has(key))) return error("invalid_selection", 400);
  const { release, kind, left, right, requestId } = payload;
  if (!validRelease(release) || !validKind(kind) || !validId(left) || !validId(right) || left === right ||
      typeof requestId !== "string" || requestId.length !== 36 || !randomIdPattern.test(requestId)) {
    return error("invalid_selection", 400);
  }

  const connectionString = context.env.BATTLES_PG?.connectionString;
  if (!connectionString) return error("popularity_unavailable", 503);
  const { snapshotId, failure } = await resolveSnapshot(context, release);
  if (failure) return failure;

  const { outcome } = await query(connectionString,
    "SELECT fastest_battles.record_comparison($1, $2, $3, $4, $5) AS outcome", [snapshotId, kind, left, right, requestId]);
  switch (outcome) {
    case "created": return json({ recorded: true }, 201);
    case "retry": return json({ recorded: true });
    case "conflict": return error("request_id_conflict", 409);
    case "invalid_pair": return error("invalid_selection", 400);
    case "snapshot_unavailable": return error("release_unavailable", 404);
    default: return error("popularity_unavailable", 503);
  }
}

export async function onRequest(context) {
  try {
    if (context.request.method === "GET") return await rank(context);
    if (context.request.method === "POST") return await record(context);
    return json({ error: "method_not_allowed" }, 405, { Allow: "GET, POST" });
  } catch {
    return error("popularity_unavailable", 503);
  }
}
