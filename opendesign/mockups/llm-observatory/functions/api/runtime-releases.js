import { runtimeReleaseWatch } from "../../runtime-release-watch.mjs";

export async function onRequestGet({ env }) {
  const watch = await runtimeReleaseWatch(env);
  return Response.json(watch?.runtimes.length ? watch : { runtimes: [] }, {
    headers: { "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" },
  });
}
