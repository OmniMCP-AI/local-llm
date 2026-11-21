import { modelCard, renderCard, renderCardContent } from "./catalog-card.mjs";
import { catalogPath, modelCollectionPath, modelLookupPath, modelIdPattern, modelShard } from "./catalog-paths.mjs";

const { release, snapshot, runtimes } = document.querySelector("[data-model-lookup]").dataset;
const runtimeIds = new Set(runtimes.split(" "));
const repository = document.querySelector("#repository");
const status = document.querySelector("#lookup-status");
const result = document.querySelector("#lookup-result");

async function showModel(id) {
  if (!modelIdPattern.test(id)) {
    status.textContent = "Enter the full repository ID in owner/repository format.";
    return;
  }

  status.textContent = "Looking up the repository…";
  const response = await fetch(`/catalog-data/${release}/${modelShard(id)}.json`);
  if (!response.ok && response.status !== 404) throw new Error("Could not read model shard");
  const row = response.ok ? (await response.json()).find(entry => entry.id === id) : undefined;
  if (!row) {
    status.textContent = "No matching repository in this snapshot. Check the spelling and capitalization.";
    return;
  }

  const runtimeHref = (id, suffix = "") => runtimeIds.has(id)
    ? "/" + catalogPath(release, "runtimes", id).replace(/\.html$/, suffix) : null;
  const card = modelCard(row, release, { discoveryCapture: row.discoveryCapture, runtimeHref });
  const pathname = modelLookupPath(release);
  const markdown = renderCard(modelCard(row, release, { discoveryCapture: row.discoveryCapture,
    runtimeHref: id => runtimeHref(id, ".md") }), {
    release, pathname, markdown: true, review: {
      snapshotId: snapshot, htmlPath: pathname + "?q=" + encodeURIComponent(id),
      directory: { title: "Model catalog", path: modelCollectionPath(release) + ".md" },
    },
  });
  const mdLink = URL.createObjectURL(new Blob([markdown], { type: "text/markdown;charset=utf-8" }));
  result.innerHTML = renderCardContent(card, { mdLink, nested: true });
  result.querySelector('a[href^="blob:"]').download = id.split("/")[1] + ".md";
  status.textContent = "Repository found.";
}

const id = new URLSearchParams(location.search).get("q")?.trim() ?? "";
repository.value = id;
if (id) showModel(id).catch(() => { status.textContent = "Could not load the catalog. Try again."; });
