const uuid = /^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/;
const goalRoute = /^\/goals\/([a-f0-9]{64})\.json$/;
const costRevision = /^v1-[a-f0-9]{64}$/;
const parameters = new Set(["release", "goal", "cost"]);

function json(body, status = 200) {
  return Response.json(body, {
    status,
    headers: { "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff" },
  });
}

function originFor(value) {
  if (!value) return null;
  try {
    const url = new URL(value);
    return url.protocol === "https:" && url.href === url.origin + "/" ? url.origin : null;
  } catch {
    return null;
  }
}

function pinnedPath(value, origin) {
  if (!value || value.length > 600 || !/^\/(goals\/|costs\.json)/.test(value)) return null;
  const url = new URL(value, origin);
  return url.origin === origin && !url.hash && !url.username && !url.password ? url : null;
}

async function readJSON(url) {
  try {
    const response = await fetch(url, {
      cache: "no-store", redirect: "error", signal: AbortSignal.timeout(8000),
    });
    return {
      status: response.status,
      value: response.ok ? await response.json() : null,
    };
  } catch {
    return { status: 503, value: null };
  }
}

export async function onRequestGet({ request, env }) {
  const query = new URL(request.url).searchParams;
  const releaseId = query.get("release") ?? env.FASTEST_PRICE_RELEASE ?? null;
  if ([...query.keys()].some((key) => !parameters.has(key) || query.getAll(key).length !== 1)
      || (query.has("release") && !uuid.test(releaseId))) {
    return json({ status: "invalid", releaseId: null }, 400);
  }
  const origin = originFor(env.FASTEST_RELEASE_ORIGIN);
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

  const upstream = await readJSON(new URL(`/price-releases/${releaseId}/prices.json`, origin));
  if (upstream.status === 410) return json({ status: "withdrawn", releaseId }, 410);
  if (upstream.status === 404) return json({ status: "missing", releaseId }, 404);
  const price = upstream.value;
  if (price?.result_type !== "regional-price-cohort" || price.schema_version !== 1
      || price.release_id !== releaseId || price.status !== "published" || !Array.isArray(price.offers)) {
    return json({ status: "unavailable", releaseId }, 503);
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
    status: "published", releaseId, price,
    decision: matchingDecision ? goal : null,
    economics: revision && cost?.revision === revision && Array.isArray(cost.payback) ? cost : null,
  });
}
