const decimal = /^(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$/;
const datePattern = /^\d{4}-\d{2}-\d{2}$/;
const marketFields = ["market", "destination", "currency", "condition"];

function number(value) {
  return decimal.test(value ?? "") && Number.isFinite(Number(value)) ? Number(value) : null;
}

export function pricePerformanceOverview(goal, goalRelease, prices) {
  const { market, protocol, metrics, rows } = goal ?? {};
  if (goal?.release_id !== goalRelease || !marketFields.every(key => typeof market?.[key] === "string" && market[key].trim())
      || !/^[A-Z]{3}$/.test(market.currency)
      || metrics?.decode?.unit !== "tok/s" || typeof protocol !== "string" || !Array.isArray(rows)) return null;

  const byRelease = new Map(prices.filter(Boolean).map(price => [price.release_id, price]));
  const points = rows.flatMap(({ id, name, build_revision: revision, metrics: rowMetrics }) => {
    const { budget, decode } = rowMetrics ?? {};
    const price = byRelease.get(budget?.release_id);
    if (price?.data_class !== "authorized_observations" || price.scope?.kind !== "whole_build"
        || price.scope.id !== id || price.scope.revision_id !== revision || !revision
        || !marketFields.every(key => price[key] === market[key])
        || budget.status !== "available" || decode?.status !== "available"
        || !Number.isInteger(decode.sample_count) || decode.sample_count < 1) return [];

    const x = number(budget.value), y = number(decode.value);
    if (x === null || y === null || typeof name !== "string") return [];
    return [{ id: price.release_id, name, x, y, xText: `${budget.value} ${market.currency}`,
      yText: `${decode.value} tok/s`, detail: `${price.as_of} · ${decode.sample_count} samples` }];
  });
  return { goalRelease, protocol, ...Object.fromEntries(marketFields.map(key => [key, market[key]])), unit: "tok/s", points };
}

export function priceObservationPoints(price) {
  const citation = price.data_class === "reviewed_citations";
  const rows = citation ? price.references : price.offers;
  return (rows ?? []).flatMap((row, index) => {
    const day = citation ? row.observed_on : row.observed_at?.slice(0, 10);
    const y = number(row.price);
    if (!datePattern.test(day ?? "") || y === null || (!citation && row.currency !== price.currency)) return [];
    const x = Date.parse(day);
    if (!Number.isFinite(x)) return [];
    const name = citation ? row.marketplace : row.seller;
    return [{ id: `${day}/${index}`, name: name ?? price.scope.id, x, y,
      xText: day, yText: `${row.price} ${price.currency}`, detail: citation ? null : row.kind }];
  }).sort((first, second) => first.x - second.x);
}
