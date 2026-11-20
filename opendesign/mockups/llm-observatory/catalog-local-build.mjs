import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { hardwareCard, renderCard, runtimeCard } from "./catalog-card.mjs";
import { catalogPath } from "./catalog-paths.mjs";

export async function writeLocalHardwareProfiles(output, { catalog, digest, manifest, snapshotId, runtimes = [] }, license) {
  const release = "v1-" + (snapshotId ?? digest).slice(0, 16);
  const root = join(output, "catalog", release);
  const profiles = { ...catalog, runtimes };
  await Promise.all(Object.keys(profiles).map(kind => mkdir(join(root, kind), { recursive: true })));
  await Promise.all([
    writeFile(join(root, "manifest.json"), JSON.stringify({ release, snapshotId, hardware: manifest }, null, 2) + "\n"),
    writeFile(join(root, "LICENSE.txt"), license + "\n"),
    ...Object.entries(profiles).flatMap(([kind, rows]) => rows.flatMap(row => {
      const card = kind === "runtimes" ? runtimeCard(row, { local: true })
        : hardwareCard(row, release, kind, { local: true, peers: kind === "cards" ? rows : [] });
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
