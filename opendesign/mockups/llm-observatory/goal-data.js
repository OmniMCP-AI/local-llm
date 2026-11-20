import { configurations } from "./scenarios";

// Every value here is illustrative. The standalone request and four-user
// measurements represent distinct example protocols for the same artifact.
const regionalPrice = {
  us: { unit: "USD", defaultTarget: 2200, step: 50, min: 0, max: 5000 },
  cn: { unit: "CNY", defaultTarget: 16000, step: 500, min: 0, max: 35000 },
};

export const goalMetrics = [
  {
    id: "price", label: "Build price", short: "Price", direction: "min", ...regionalPrice.us,
    description: "Example purchase quote for the whole system in the selected market. Taxes, shipping, and operating costs are excluded. The RTX 3090 build uses a used GPU.",
  },
  {
    id: "decode", label: "Output speed", short: "Decode", unit: "tok/s", direction: "max", defaultTarget: 85, step: 5, min: 5, max: 250,
    description: "Output tokens per second after generation starts. One warm request, a 4K context limit, and the same Qwen2.5 7B Q4_K_M artifact.",
  },
  {
    id: "prefill", label: "Prompt processing", short: "Prefill", unit: "tok/s", direction: "max", defaultTarget: 2500, step: 100, min: 100, max: 6000,
    description: "Input tokens processed per second on a warm, single-user request with a 512-token prompt. This rate measures a different phase from output speed.",
  },
  {
    id: "userP95", label: "4-user response time", short: "4-user p95", unit: "s", direction: "min", defaultTarget: 14, step: 1, min: 1, max: 45,
    description: "95th-percentile end-to-end time for an individual request under a sustained load of four concurrent users. Each request uses 512 input and 256 output tokens.",
  },
  {
    id: "energy", label: "Energy per request", short: "Energy", unit: "Wh", direction: "min", defaultTarget: 0.25, step: 0.01, min: 0.01, max: 0.60,
    description: "Whole-system wall energy during one warm request with 512 input and 256 output tokens. Excludes idle energy between requests and differs from peak watts.",
  },
];

export function goalMetricsForRegion(region = "us") {
  const price = regionalPrice[region];
  return price ? goalMetrics.map((metric) => metric.id === "price" ? { ...metric, ...price } : metric) : goalMetrics;
}

const additionalExamples = {
  "rtx-4090": { prefill: 4700, userP95: 8.6, energy: 0.23 },
  "rtx-3090": { prefill: 3100, userP95: 11.8, energy: 0.32 },
  "rtx-3060": { prefill: 1530, userP95: 26.4, energy: 0.19 },
  "m4-pro": { prefill: 1250, userP95: null, energy: 0.11 },
};

export function goalRows(region = "us") {
  return configurations.filter(({ kind }) => kind !== "cloud").map(({ id, name, short, detail, kind, prices, measurements }) => ({
    id, name, short, detail, kind,
    condition: id === "rtx-3090" ? "Used GPU build" : "New build",
    metrics: {
      price: Object.hasOwn(regionalPrice, region) ? prices[region] ?? null : null,
      decode: measurements.text.short ?? null,
      prefill: null, userP95: null, energy: null,
      ...additionalExamples[id],
    },
  }));
}

const metricsById = new Map(goalMetrics.map((metric) => [metric.id, metric]));
const measured = (value) => Number.isFinite(value) && value >= 0;
const compareMetric = (metric, a, b) => (metric.direction === "min" ? a - b : b - a);
const sortStatus = { meets: 0, misses: 1, unknown: 2, context: 3 };

export function evaluateGoalRows(rows, goals, priority) {
  const active = [...new Map(goals.filter(({ id, target }) => metricsById.has(id) && measured(target)).map((goal) => [goal.id, goal])).values()];
  const primary = metricsById.get(priority) ?? goalMetrics[0];
  const axes = [...new Set([...active.map(({ id }) => id), primary.id])].map((id) => metricsById.get(id));
  const evaluated = rows.map((row) => {
    const checks = active.map(({ id, target }) => {
      const value = row.metrics[id];
      if (!measured(value)) return { id, value: null, target, state: "unknown" };
      return { id, value, target, state: compareMetric(metricsById.get(id), value, target) <= 0 ? "pass" : "miss" };
    });
    const misses = checks.filter(({ state }) => state === "miss").length;
    const unknown = checks.some(({ state }) => state === "unknown");
    const status = row.kind !== "measured" ? "context" : misses > 0 ? "misses" : unknown ? "unknown" : "meets";
    return { ...row, checks, misses, status };
  });
  const complete = evaluated.filter((row) => row.kind === "measured" && axes.every(({ id }) => measured(row.metrics[id])));
  const frontier = new Set(complete.filter((row) => !complete.some((other) => {
    const differences = axes.map((metric) => compareMetric(metric, other.metrics[metric.id], row.metrics[metric.id]));
    return differences.every((difference) => difference <= 0) && differences.some((difference) => difference < 0);
  })).map(({ id }) => id));

  return evaluated.map((row) => ({ ...row, tradeoff: frontier.has(row.id) })).sort((a, b) => {
    const status = sortStatus[a.status] - sortStatus[b.status];
    if (status) return status;
    if (a.status === "misses" && a.misses !== b.misses) return a.misses - b.misses;
    const aValue = a.metrics[primary.id];
    const bValue = b.metrics[primary.id];
    if (measured(aValue) && measured(bValue)) return compareMetric(primary, aValue, bValue) || a.name.localeCompare(b.name);
    if (measured(aValue) !== measured(bValue)) return measured(aValue) ? -1 : 1;
    return a.name.localeCompare(b.name);
  });
}
