import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { hardwareCard, renderCard } from "./catalog-card.mjs";
import { catalogPath } from "./catalog-paths.mjs";

export async function writeLocalHardwareProfiles(output, { catalog, digest, manifest, snapshotId }, license) {
  const release = "v1-" + digest.slice(0, 16);
  const root = join(output, "catalog", release);
  await Promise.all(Object.keys(catalog).map(kind => mkdir(join(root, kind), { recursive: true })));
  await Promise.all([
    writeFile(join(root, "manifest.json"), JSON.stringify({ release, snapshotId, hardware: manifest }, null, 2) + "\n"),
    writeFile(join(root, "LICENSE.txt"), license + "\n"),
    ...Object.entries(catalog).flatMap(([kind, rows]) => rows.flatMap(row => {
      const card = hardwareCard(row, release, kind, { local: true });
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
