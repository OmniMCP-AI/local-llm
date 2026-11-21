const productionRoutes = {
  explorer: "/profiles", goals: "/goals", advisor: "/advisor", costs: "/costs",
  machines: "/profiles#machines", models: "/profiles#models",
};
const pagesRoutes = {
  methods: "/wiki/comparison-methods/", catalog: "/wiki/catalog/", wiki: "/wiki/", agents: "/wiki/agent-discovery/",
};

export function releaseOrigin(value) {
  if (!value) return null;
  try {
    const url = new URL(value);
    return url.protocol === "https:" && url.href === url.origin + "/" ? url.origin : null;
  } catch {
    return null;
  }
}

export function navigationHref(route, pages, origin, catalogPostgres = false) {
  if (pages && route === "prices") return "/prices";
  if (pages && origin) {
    if (Object.hasOwn(productionRoutes, route)) return origin + productionRoutes[route];
    if (Object.hasOwn(pagesRoutes, route)) return pagesRoutes[route];
  }
  if (catalogPostgres && (route === "machines" || route === "models")) return "#catalog/" + route;
  return "#" + route;
}

export const explorerDemo = "explorer-demo";

export function catalogHome(route, catalogPostgres, origin) {
  if (!catalogPostgres || (!origin && route === explorerDemo)) return null;
  return {
    catalog: "#catalog",
    prices: navigationHref("prices", true, origin),
    benchmarks: origin ? navigationHref("explorer", true, origin) : null,
    demo: origin ? null : "#" + explorerDemo,
  };
}
