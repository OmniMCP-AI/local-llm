export function navigationRoutes(origin) {
  return {
    Explorer: "explorer", Compare: "goals", Battles: "battle",
    ...(origin ? { "Guided advisor": "advisor" } : {}),
    Methods: "methods", Costs: "costs", Catalog: "catalog", Machines: "machines", Models: "models", Wiki: "wiki", "Price watch": "prices", "For agents": "agents",
  };
}

const productionRoutes = {
  explorer: "/profiles", goals: "/goals", advisor: "/advisor", costs: "/costs",
  models: "/profiles#models",
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
  if (route === "machines") return "#catalog/machines";
  if (pages && route === "prices") return "/prices";
  if (pages && origin) {
    if (Object.hasOwn(productionRoutes, route)) return origin + productionRoutes[route];
    if (Object.hasOwn(pagesRoutes, route)) return pagesRoutes[route];
  }
  if (catalogPostgres && route === "models") return "#catalog/models";
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
