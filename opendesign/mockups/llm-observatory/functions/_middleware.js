import { languageForCountry } from "../locale-settings.mjs";

const policyPath = "/evidence-quarantine.json";
const noStore = { "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" };
const validators = ["ETag", "Last-Modified", "CDN-Cache-Control", "Cloudflare-CDN-Cache-Control"];
const conditionals = ["If-Match", "If-None-Match", "If-Modified-Since", "If-Unmodified-Since", "If-Range", "Range"];
const checkedFile = new Set(["/", "/index", "/index.html", "/index.md", "/sitemap.xml", "/robots.txt", "/llms.txt"]);
const checkedFolder = /^\/(wiki|research|catalog|catalog-data|downloads)(?:\/|$)/;

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
  const requestHeaders = new Headers(request.headers);
  if (check) {
    for (const name of conditionals) requestHeaders.delete(name);
    requestHeaders.set("Cache-Control", "no-cache");
  }
  const response = check ? await context.next(new Request(request, { headers: requestHeaders })) : await context.next();
  if (check && response.status === 304) return retirementNotice(request, 503, "Public evidence unavailable.\n");
  const contentType = response.headers.get("Content-Type")?.split(";", 1)[0].trim().toLowerCase();
  const html = response.status === 200 && contentType === "text/html";
  if (!check && !html && path !== policyPath) return response;

  const language = html && request.method === "GET" && languageForCountry(request.cf?.country);
  const headers = new Headers(response.headers);
  headers.set("Cache-Control", html ? "private, no-store" : "no-store");
  for (const name of validators) headers.delete(name);
  if (language) headers.delete("Content-Length");
  const page = new Response(request.method === "HEAD" ? null : response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
  if (!language) return page;
  return new HTMLRewriter()
    .on("html", { element: (element) => element.setAttribute("data-visitor-language", language) })
    .transform(page);
}

export const onRequestHead = onRequestGet;
