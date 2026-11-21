import { releaseOrigin } from "../../release-origin.mjs";

const uuid = /^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/;
const goalRoute = /^\/goals\/([a-f0-9]{64})\.json$/;
const costRevision = /^v1-[a-f0-9]{64}$/;
const parameters = new Set(["release", "goal", "cost"]);
const maxCohorts = 6;
const priceFailure = { withdrawn: 410, missing: 404, unavailable: 503 };

function json(body, status = 200) {
  return Response.json(body, {
    status,
    headers: { "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff" },
  });
}

function pinnedPath(value, origin) {
  if (!value || value.length > 600 || !/^\/(goals\/|costs\.json)/.test(value)) return null;
  const url = new URL(value, origin);
  return url.origin === origin && !url.hash && !url.username && !url.password ? url : null;
}

async function readJSON(url) {
  try {
    const response = await fetch(url, {
      cache: "no-store", redirect: "manual", signal: AbortSignal.timeout(8000),
    });
    return {
      status: response.status,
      value: response.ok ? await response.json() : null,
    };
  } catch {
    return { status: 503, value: null };
  }
}

function directoryIds(value) {
  if (typeof value !== "string" || value.length > maxCohorts * 40) return [];
  const ids = value.split(",").map((id) => id.trim());
  return ids.length <= maxCohorts && ids.every((id) => uuid.test(id)) ? [...new Set(ids)] : [];
}

async function readPrice(origin, id) {
  const upstream = await readJSON(new URL(`/price-releases/${id}/prices.json`, origin));
  if (upstream.status === 410) return { status: "withdrawn" };
  if (upstream.status === 404) return { status: "missing" };
  const price = upstream.value;
  if (price?.result_type !== "regional-price-cohort" || price.schema_version !== 1
      || price.release_id !== id || price.status !== "published" || !Array.isArray(price.offers)
      || (price.data_class === "reviewed_citations" && (price.offers.length || !Array.isArray(price.references)))) {
    return { status: "unavailable" };
  }
  return { status: "published", price };
}

function cohortSummary({ price }) {
  if (!["authorized_observations", "reviewed_citations"].includes(price?.data_class)
      || !["sku", "whole_build"].includes(price.scope?.kind)
      || ![price.market, price.currency, price.as_of, price.scope.id, price.scope.revision_id]
        .every((value) => typeof value === "string" && value.length > 0)) return null;
  const { kind, id, revision_id } = price.scope;
  return {
    releaseId: price.release_id, market: price.market, currency: price.currency, asOf: price.as_of,
    scope: { kind, id, revision_id }, dataClass: price.data_class,
    source: price.source_name ?? null, destination: price.destination ?? null, condition: price.condition ?? null,
  };
}

export async function onRequestGet({ request, env }) {
  const query = new URL(request.url).searchParams;
  const ids = directoryIds(env.FASTEST_PRICE_RELEASES);
  const releaseId = query.get("release") ?? (env.FASTEST_PRICE_RELEASE || ids[0] || null);
  if ([...query.keys()].some((key) => !parameters.has(key) || query.getAll(key).length !== 1)
      || (query.has("release") && !uuid.test(releaseId))) {
    return json({ status: "invalid", releaseId: null }, 400);
  }
  const origin = releaseOrigin(env.FASTEST_RELEASE_ORIGIN);
  if (!origin || !uuid.test(releaseId)) return json({ status: "missing", releaseId: null }, 404);

  const goalPath = pinnedPath(query.get("goal"), origin);
  const goalId = goalRoute.exec(goalPath?.pathname ?? "")?.[1];
  const costPath = pinnedPath(query.get("cost"), origin);
  const revision = costPath?.searchParams.get("revision");
  if ((query.has("goal") && !goalId)
      || (query.has("cost") && (costPath?.pathname !== "/costs.json" || !costRevision.test(revision)
        || costPath.searchParams.getAll("revision").length !== 1))) {
    return json({ status: "invalid", releaseId }, 400);
  }

  const selected = readPrice(origin, releaseId);
  const [result, entries] = await Promise.all([
    selected, Promise.all(ids.map((id) => id === releaseId ? selected : readPrice(origin, id))),
  ]);
  const directory = ids.length ? { cohorts: entries.map(cohortSummary).filter(Boolean) } : {};
  const { status, price } = result;
  if (!price) return json({ status, releaseId, ...directory }, priceFailure[status]);
  if (price.data_class === "reviewed_citations") {
    return json({ status, releaseId, price, decision: null, economics: null, ...directory });
  }
  costPath?.searchParams.delete("revision");
  const [goal, cost] = await Promise.all([
    goalId && readJSON(goalPath).then(({ value }) => value),
    revision && readJSON(costPath).then(({ value }) => value),
  ]);
  const matchingDecision = goal?.release_id === goalId && Boolean(goalId)
    && price.scope?.kind === "whole_build"
    && ["market", "destination", "currency", "condition"].every((key) => goal.market?.[key] === price[key])
    && Array.isArray(goal.rows) && goal.rows.some((row) => row.id === price.scope.id && row.build_revision === price.scope.revision_id
      && row.metrics?.budget?.release_id === releaseId);
  return json({
    status, releaseId, price, ...directory,
    decision: matchingDecision ? goal : null,
    economics: revision && cost?.revision === revision && Array.isArray(cost.payback) ? cost : null,
  });
}
