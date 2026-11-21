import { hardwareCard, modelCard, renderCard, runtimeCard } from "../../../catalog-card.mjs";
import { observedAgentTask } from "../../../catalog-agent-task.mjs";
import { catalogPath, catalogReleasePattern, hardwareIdPattern, modelIdPattern, modelShard, runtimeIdPattern } from "../../../catalog-paths.mjs";
import { releaseOrigin } from "../../../release-origin.mjs";
import { runtimeReleaseWatch } from "../../../runtime-release-watch.mjs";

const notFound = () => new Response("Catalog card unavailable", {
  status: 404,
  headers: { "Content-Type": "text/plain; charset=utf-8" },
});

export async function onRequestGet(context) {
  const { release, path = [] } = context.params;
  const [kind] = path;
  if (!["models", "runtimes", "cards", "machines"].includes(kind)) return context.next();

  const isModel = kind === "models";
  const [, id, extension] = /^(.*)\.(html|md)$/.exec(path.slice(1).join("/")) ?? [];
  const idPattern = isModel ? modelIdPattern : kind === "runtimes" ? runtimeIdPattern : hardwareIdPattern;
  const validId = idPattern.test(id ?? "");
  if (path.length !== (isModel ? 3 : 2) || !catalogReleasePattern.test(release) || !validId || !extension) {
    return notFound();
  }

  const file = isModel ? modelShard(id) : kind;
  const asset = await context.env.ASSETS.fetch(new Request(
    new URL(`/catalog-data/${release}/${file}.json`, context.request.url),
  ));
  if (!asset.ok || !asset.headers.get("content-type")?.includes("application/json")) return notFound();

  const entries = await asset.json();
  const row = entries.find((entry) => entry.id === id);
  if (!row) return notFound();

  const agentTask = isModel && await observedAgentTask(id, context.env);
  const isRuntime = kind === "runtimes";
  const watch = isRuntime ? await runtimeReleaseWatch(context.env) : null;
  const observation = watch?.runtimes.find(entry => entry.id === row.id && entry.repositoryUrl === row.source);
  const card = isModel ? modelCard(row, release, { discoveryCapture: row.discoveryCapture, agentTask })
    : isRuntime ? runtimeCard(row, { observation }) : hardwareCard(row, release, kind, { peers: kind === "cards" ? entries : [] });
  const markdown = extension === "md";
  return new Response(renderCard(card, {
    release, pathname: "/" + catalogPath(release, kind, id, extension), markdown,
    releaseOrigin: releaseOrigin(context.env.FASTEST_RELEASE_ORIGIN),
  }), {
    headers: {
      "Content-Type": `text/${markdown ? "markdown" : "html"}; charset=utf-8`,
      "X-Content-Type-Options": "nosniff",
      ...((agentTask || isRuntime) && { "Cache-Control": "no-store" }),
    },
  });
}
