// Pages serves staged HTML files at their extensionless public URLs.
export function pagesFileRoutes(path) {
  if (path === "/index.html") return ["/", "/index", path];
  if (!path.endsWith(".html")) return [path];
  if (path.endsWith("/index.html")) {
    return [path.slice(0, -"index.html".length), path.slice(0, -".html".length), path,
      path.slice(0, -"/index.html".length)];
  }
  return [path.slice(0, -".html".length), path];
}

export function checkedPagesFile(path) {
  return /^\/(?:index\.(?:html|md)|robots\.txt|sitemap\.xml|llms\.txt|evidence-quarantine\.json)$/.test(path) ||
    /^\/(?:wiki|research|catalog|catalog-data|downloads)\//.test(path);
}
