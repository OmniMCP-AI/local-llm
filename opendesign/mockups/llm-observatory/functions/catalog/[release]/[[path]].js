import { hardwareCard, modelCard, renderCard, runtimeCard } from "../../../catalog-card.mjs";
import { catalogPath, catalogReleasePattern, hardwareIdPattern, modelIdPattern, modelShard, runtimeIdPattern } from "../../../catalog-paths.mjs";

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

  const row = (await asset.json()).find((entry) => entry.id === id);
  if (!row) return notFound();

  const card = isModel ? modelCard(row, release)
    : kind === "runtimes" ? runtimeCard(row) : hardwareCard(row, release, kind);
  const markdown = extension === "md";
  return new Response(renderCard(card, {
    release, pathname: "/" + catalogPath(release, kind, id, extension), markdown,
  }), {
    headers: {
      "Content-Type": `text/${markdown ? "markdown" : "html"}; charset=utf-8`,
      "X-Content-Type-Options": "nosniff",
    },
  });
}
