import { releaseOrigin } from "../release-origin.mjs";

const fields = new Set(["machine", "artifact", "runtime", "context", "ram_reserved_gib", "vram_reserved_gib", "cpu_cores"]);
const headers = { "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" };
const unavailable = () => Response.json({ error: "Fit service unavailable." }, { status: 503, headers });

export async function onRequestGet({ request, env }) {
  const input = new URL(request.url);
  const params = input.searchParams;
  if (input.search.length > 1024 || [...params].some(([key, value]) =>
    !fields.has(key) || !value || value.length > 160 || params.getAll(key).length !== 1)) {
    return Response.json({ error: "Invalid fit query." }, { status: 400, headers });
  }
  const origin = releaseOrigin(env.FASTEST_RELEASE_ORIGIN);
  if (!origin) return Response.json({ error: "Fit service unavailable." }, { status: 404, headers });
  const upstream = new URL("/fit.json", origin);
  upstream.search = params.toString();
  try {
    const response = await fetch(upstream, {
      cache: "no-store", redirect: "error", signal: AbortSignal.timeout(8000),
      headers: { Accept: "application/json" },
    });
    if ([400, 404].includes(response.status)) {
      return Response.json({ error: "No fit estimate for these inputs." }, { status: response.status, headers });
    }
    if (!response.ok || !response.headers.get("Content-Type")?.startsWith("application/json")) return unavailable();
    return Response.json(await response.json(), { headers });
  } catch {
    return unavailable();
  }
}
