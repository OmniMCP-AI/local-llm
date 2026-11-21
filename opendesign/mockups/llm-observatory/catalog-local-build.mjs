import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { hardwareCard, modelCard, renderCard, runtimeCard } from "./catalog-card.mjs";
import { catalogPath, modelIdPattern } from "./catalog-paths.mjs";

export async function writeLocalCatalogProfiles(output, {
  catalog, digest, manifest, modelManifest, snapshotId, runtimes = [], topologies = [],
}, license) {
  const release = "v1-" + (snapshotId ?? digest).slice(0, 16);
  const root = join(output, "catalog", release);
  const profiles = { ...catalog, runtimes };
  const topologyByMachine = new Map(topologies.map(({ id, revision }) => [id, revision]));
  const models = profiles.models ?? [];
  const owners = new Set(models.map(({ id }) => {
    if (!modelIdPattern.test(id)) throw new Error("Invalid local model identity: " + id);
    return id.split("/")[0];
  }));
  const coverage = {
    release, snapshotId, hardware: manifest,
    ...(modelManifest && { models: { ...modelManifest, profiles: models.length } }),
  };
  await Promise.all([
    ...Object.keys(profiles).map(kind => mkdir(join(root, kind), { recursive: true })),
    ...Array.from(owners, owner => mkdir(join(root, "models", owner), { recursive: true })),
  ]);
  await Promise.all([
    writeFile(join(root, "manifest.json"), JSON.stringify(coverage, null, 2) + "\n"),
    writeFile(join(root, "LICENSE.txt"), license + "\n"),
    ...Object.entries(profiles).flatMap(([kind, rows]) => rows.flatMap(row => {
      const card = kind === "runtimes" ? runtimeCard(row, { local: true })
        : kind === "models" ? modelCard(row, release, { runtimeRoot: "../..", discoveryCapture: modelManifest?.discovery })
          : hardwareCard(row, release, kind, {
            local: true, peers: kind === "cards" ? rows : [], topologyRevision: topologyByMachine.get(row.id),
          });
      return ["html", "md"].map(extension => {
        const path = catalogPath(release, kind, row.id, extension);
        return writeFile(join(output, path), renderCard(card, {
          release, pathname: path, markdown: extension === "md", local: true,
        }));
      });
    })),
  ]);
  return release;
}
