const productionRoutes = {
  explorer: "/profiles", goals: "/goals", costs: "/costs",
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

export function navigationHref(route, pages, origin) {
  if (pages && route === "prices") return "/prices";
  if (pages && origin) {
    if (Object.hasOwn(productionRoutes, route)) return origin + productionRoutes[route];
    if (Object.hasOwn(pagesRoutes, route)) return pagesRoutes[route];
  }
  return "#" + route;
}
