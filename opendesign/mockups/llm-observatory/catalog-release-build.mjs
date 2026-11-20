import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { modelIdPattern, modelShard } from "./catalog-paths.mjs";

const sha256 = (bytes) => createHash("sha256").update(bytes).digest("hex");
const upstream = {
  commit: "26450cccaf3a3f14b1822875f2473847a744a718",
  sha256: "298dbdf36913e1071e62dd07033b0bdf2672a208d71838d2e96d1f464fbd723a",
  commitDate: "2026-11-18T14:59:13Z",
};

export async function writeCatalogRelease(directory, output) {
  const [sourceBytes, identityBytes, runtimeBytes] = await Promise.all([
    readFile(join(directory, "catalog-models.json")),
    readFile(join(directory, "catalog-identities.json")),
    readFile(join(directory, "catalog-runtimes.json")),
  ]);
  const source = JSON.parse(sourceBytes);
  if (source.commit !== upstream.commit) throw new Error("Review the new catalog source and its SHA-256 before publishing");
  const identities = JSON.parse(identityBytes);
  const runtimes = JSON.parse(runtimeBytes);
  const release = "v1-" + sha256(Buffer.concat([sourceBytes, identityBytes, runtimeBytes])).slice(0, 16);
  const target = join(output, "catalog", release);
  const shards = new Map();
  const ids = new Set();

  for (const row of source.models) {
    if (!modelIdPattern.test(row.id) || new URL(row.source).href !== "https://huggingface.co/" + row.id || ids.has(row.id)) {
      throw new Error("Invalid or duplicate published catalog identity: " + row.id);
    }
    ids.add(row.id);
    const key = modelShard(row.id);
    if (!shards.has(key)) shards.set(key, []);
    shards.get(key).push({ ...row, identity: identities[row.id] });
  }
  if (source.sourceRows !== ids.size + source.duplicateRows + source.rejectedRows) {
    throw new Error("Model catalog counts do not reconcile");
  }

  for (const id of Object.keys(identities)) {
    if (!ids.has(id)) throw new Error("Reviewed identity has no catalog record: " + id);
  }
  const reviewed = Object.values(identities);
  const manifest = {
    release,
    source: {
      ...upstream,
      url: source.upstream,
      projectionSha256: sha256(sourceBytes),
      license: source.catalogLicense,
      licenseUrl: source.catalogLicenseUrl,
    },
    artifactScope: "Selected upstream artifacts have individually pinned repository revisions and upstream digests. External benchmark caches are excluded.",
    coverage: {
      sourceRows: source.sourceRows,
      publishedRows: ids.size,
      duplicateRows: source.duplicateRows,
      rejectedRows: source.rejectedRows,
      withoutModelLicense: source.models.filter((row) => !row.license).length,
      withFamily: reviewed.filter((row) => row.family).length,
      withRepositoryRevision: reviewed.filter((row) => row.revision).length,
      withExactArtifacts: reviewed.filter((row) => row.artifacts?.length).length,
      exactArtifacts: reviewed.flatMap((row) => row.artifacts ?? []).length,
      runtimeProjects: runtimes.length,
    },
  };

  const data = join(output, "catalog-data", release);
  await Promise.all([mkdir(target, { recursive: true }), mkdir(data, { recursive: true })]);
  await Promise.all([
    writeFile(join(target, "manifest.json"), JSON.stringify(manifest, null, 2) + "\n"),
    writeFile(join(target, "LICENSE.txt"), source.licenseNotice + "\n"),
    writeFile(join(data, "runtimes.json"), JSON.stringify(runtimes)),
    ...[...shards].map(([key, rows]) => writeFile(join(data, key + ".json"), JSON.stringify(rows))),
  ]);
  return release;
}
