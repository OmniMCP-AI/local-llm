import { hardwareIdPattern } from "../catalog-paths.mjs";
import { releaseOrigin } from "../release-origin.mjs";

const headers = { "Cache-Control": "no-store", "Content-Type": "text/plain; charset=utf-8" };

export function onRequestGet({ request, env }) {
  const { searchParams } = new URL(request.url);
  const machine = searchParams.get("machine");
  if (searchParams.size > 1 || (searchParams.size && (!machine || machine.length > 160 || !hardwareIdPattern.test(machine)))) {
    return new Response("Invalid fit query.\n", { status: 400, headers });
  }
  const origin = releaseOrigin(env.FASTEST_RELEASE_ORIGIN);
  if (!origin) return new Response("Fit service unavailable.\n", { status: 404, headers });
  const url = new URL("/fit", origin);
  if (machine) url.searchParams.set("machine", machine);
  return new Response(null, { status: 307, headers: { ...headers, Location: url.href } });
}
