import { languageForCountry } from "../locale-settings.mjs";
import { homeHighlightHtml, homeHighlightMarkdown, observedHomeHighlight } from "../home-highlights.mjs";
import { runtimeReleaseWatch } from "../runtime-release-watch.mjs";

const policyPath = "/evidence-quarantine.json";
const noStore = { "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" };
const validators = ["ETag", "Last-Modified", "CDN-Cache-Control", "Cloudflare-CDN-Cache-Control"];
const conditionals = ["If-Match", "If-None-Match", "If-Modified-Since", "If-Unmodified-Since", "If-Range", "Range"];
const homeHtml = new Set(["/", "/index", "/index.html"]);
const checkedFile = new Set([...homeHtml, "/index.md", "/battles.md", "/sitemap.xml", "/robots.txt", "/llms.txt"]);
const checkedFolder = /^\/(wiki|research|catalog|catalog-data|downloads|battles)(?:\/|$)/;

function retirementNotice(request, status, message) {
  return new Response(request.method === "HEAD" ? null : message, {
    status, headers: { ...noStore, "Content-Type": "text/plain; charset=utf-8" },
  });
}

function decodedPath(url) {
  return decodeURIComponent(new URL(url).pathname).replace(/\/{2,}/g, "/");
}

export async function onRequestGet(context) {
  const { request, env } = context;
  let path;
  try {
    path = decodedPath(request.url);
  } catch {
    return retirementNotice(request, 400, "Invalid public path.\n");
  }
  const check = checkedFile.has(path) || checkedFolder.test(path);
  if (check) {
    try {
      const state = await env.ASSETS.fetch(new Request(new URL(policyPath, request.url), {
        headers: { "Cache-Control": "no-cache" },
      }));
      if (!state.ok) throw new Error("Quarantine policy unavailable");
      const { paths } = await state.json();
      if (paths.some((denied) => denied.endsWith("/*")
        ? path === denied.slice(0, -2) || path.startsWith(denied.slice(0, -1))
        : path === denied)) {
        return retirementNotice(request, 410, "Evidence was withdrawn from this public artifact.\n");
      }
    } catch {
      return retirementNotice(request, 503, "Public evidence unavailable.\n");
    }
  }
  const sensitive = check || path === policyPath;
  const requestHeaders = new Headers(request.headers);
  if (sensitive) {
    for (const name of conditionals) requestHeaders.delete(name);
    requestHeaders.set("Cache-Control", "no-cache");
  }
  const response = sensitive ? await context.next(new Request(request, { headers: requestHeaders })) : await context.next();
  if (sensitive && response.status === 304) return retirementNotice(request, 503, "Public evidence unavailable.\n");
  const contentType = response.headers.get("Content-Type")?.split(";", 1)[0].trim().toLowerCase();
  const html = response.status === 200 && contentType === "text/html";
  if (!sensitive && !html) return response;

  const language = html && request.method === "GET" && languageForCountry(request.cf?.country);
  const homeMarkdown = path === "/index.md" && contentType === "text/markdown";
  const manifest = path === "/wiki/manifest.json" && contentType === "application/json";
  const highlight = request.method === "GET" && response.status === 200 &&
    (homeMarkdown || manifest || (html && homeHtml.has(path))) && await observedHomeHighlight(env);
  const runtimeMarkdown = path === "/wiki/runtimes.md" && contentType === "text/markdown";
  const runtimeHtml = html && /^\/wiki\/runtimes(?:\/(?:index\.html)?)?$/.test(path);
  const watch = request.method === "GET" && response.status === 200 && (runtimeMarkdown || runtimeHtml)
    ? await runtimeReleaseWatch(env) : null;
  const showWatch = watch?.runtimes.length > 0;
  const headers = new Headers(response.headers);
  headers.set("Cache-Control", html ? "private, no-store" : "no-store");
  for (const name of validators) headers.delete(name);
  if (language || highlight || showWatch) headers.delete("Content-Length");
  const page = new Response(request.method === "HEAD" ? null : response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
  if (highlight && homeMarkdown) return new Response(homeHighlightMarkdown(await page.text(), highlight), page);
  if (highlight && manifest) {
    const content = await page.json();
    const { id, type, href, markdown, source, priority } = highlight;
    content.highlights.unshift({ id, type, href, markdown, source, priority });
    return new Response(JSON.stringify(content, null, 2) + "\n", page);
  }
  if (showWatch && runtimeMarkdown) {
    return new Response(await page.text() + `\n[Runtime release watch](<${watch.markdown}>)\n`, page);
  }
  if (!language && !highlight && !showWatch) return page;
  const rewriter = new HTMLRewriter();
  if (language) rewriter.on("html", { element: (element) => element.setAttribute("data-visitor-language", language) });
  if (highlight) {
    rewriter.on("[data-home-highlights]", { element: (element) => element.removeAttribute("hidden") })
      .on("[data-home-highlights] > ul", { element: (element) => element.prepend(homeHighlightHtml(highlight), { html: true }) });
  }
  if (showWatch) {
    const href = watch.html.replaceAll("&", "&amp;").replaceAll('"', "&quot;");
    rewriter.on('main[data-page="runtimes"] > h1', {
      element: element => element.after(`<p><a href="${href}">Runtime release watch</a></p>`, { html: true }),
    });
  }
  return rewriter.transform(page);
}

export const onRequestHead = onRequestGet;
