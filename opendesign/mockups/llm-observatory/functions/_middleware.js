import { languageForCountry } from "../locale-settings.mjs";

export async function onRequestGet(context) {
  const response = await context.next();
  const contentType = response.headers.get("Content-Type")?.split(";", 1)[0].trim().toLowerCase();
  if (response.status !== 200 || contentType !== "text/html") return response;

  const language = languageForCountry(context.request.cf?.country);
  const headers = new Headers(response.headers);
  headers.set("Cache-Control", "private, no-store");
  for (const name of ["ETag", "Last-Modified", "CDN-Cache-Control", "Cloudflare-CDN-Cache-Control"]) {
    headers.delete(name);
  }
  if (language) headers.delete("Content-Length");
  const page = new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
  if (!language) return page;

  return new HTMLRewriter()
    .on("html", { element: (element) => element.setAttribute("data-visitor-language", language) })
    .transform(page);
}
