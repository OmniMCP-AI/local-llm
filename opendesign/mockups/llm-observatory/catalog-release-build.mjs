import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { readHardwareCatalog } from "./catalog-hardware-build.mjs";
import { modelIdPattern, modelShard } from "./catalog-paths.mjs";

const sha256 = (bytes) => createHash("sha256").update(bytes).digest("hex");
const upstream = {
  commit: "26450cccaf3a3f14b1822875f2473847a744a718",
  sha256: "298dbdf36913e1071e62dd07033b0bdf2672a208d71838d2e96d1f464fbd723a",
  commitDate: "2026-11-18T14:59:13Z",
};

export async function readCatalogModelFiles(directory) {
  const [sourceBytes, identityBytes, discoveryBytes] = await Promise.all([
    readFile(join(directory, "catalog-models.json")),
    readFile(join(directory, "catalog-identities.json")),
    readFile(join(directory, "model-discovery.json")),
  ]);
  const source = JSON.parse(sourceBytes);
  if (source.commit !== upstream.commit) throw new Error("Review the new catalog source and its SHA-256 before publishing");
  return {
    sourceBytes, identityBytes, source,
    identities: JSON.parse(identityBytes), discovery: JSON.parse(discoveryBytes),
    sourceManifest: {
      ...upstream, url: source.upstream, projectionSha256: sha256(sourceBytes),
      license: source.catalogLicense, licenseUrl: source.catalogLicenseUrl,
    },
  };
}

export async function writeCatalogRelease(directory, output, hardware, reviewedRuntimes, modelFiles) {
  const [models, runtimeBytes, hardwareSource] = await Promise.all([
    modelFiles ?? readCatalogModelFiles(directory),
    reviewedRuntimes ? Buffer.from(JSON.stringify(reviewedRuntimes)) : readFile(join(directory, "catalog-runtimes.json")),
    hardware ?? readHardwareCatalog(directory),
  ]);
  const runtimes = JSON.parse(runtimeBytes);
  const digest = sha256(Buffer.concat([models.sourceBytes, models.identityBytes, runtimeBytes, Buffer.from(hardwareSource.digest, "hex")]));
  return writeCatalogProjection(output, prepareCatalogRelease({ ...models, hardware: hardwareSource, runtimes, digest }));
}

export function prepareCatalogRelease({ source, identities, discovery, sourceManifest, hardware, runtimes, digest, snapshotId, topologies }) {
  const release = "v1-" + (snapshotId ?? digest).slice(0, 16);
  const shards = new Map();
  const ids = new Set();
  const ranks = new Map();
  const { capturedAt, source: rankingSource } = discovery;
  if (snapshotId) {
    for (const collection of ["popular", "small"]) {
      discovery[collection].forEach((row, index) => {
        if (!ranks.has(row.id)) ranks.set(row.id, {});
        ranks.get(row.id)[collection] = { ...row, rank: index + 1 };
      });
    }
  }

  for (const row of source.models) {
    if (!modelIdPattern.test(row.id) || new URL(row.source).href !== "https://huggingface.co/" + row.id || ids.has(row.id)) {
      throw new Error("Invalid or duplicate published catalog identity: " + row.id);
    }
    ids.add(row.id);
    const key = modelShard(row.id);
    if (!shards.has(key)) shards.set(key, []);
    shards.get(key).push({ ...row, identity: identities[row.id], ...(ranks.has(row.id) && {
      discovery: ranks.get(row.id), discoveryCapture: { capturedAt, source: rankingSource },
    }) });
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
    ...(snapshotId && { snapshotId, discovery: { capturedAt, source: rankingSource, popular: discovery.popular.length, small: discovery.small.length } }),
    source: sourceManifest,
    hardware: hardware.manifest,
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
      ...(topologies && { topologyRevisions: topologies.length }),
    },
  };
  const topologyByMachine = new Map(topologies?.map(({ id, revision }) => [id, revision]));
  const machines = hardware.catalog.machines.map(row => {
    const topologyRevision = topologyByMachine.get(row.id);
    return topologyRevision ? { ...row, topologyRevision } : row;
  });
  return { manifest, shards, hardware: { ...hardware, catalog: { ...hardware.catalog, machines } },
    runtimes, licenseNotice: source.licenseNotice };
}

export async function writeCatalogProjection(output, { manifest, shards, hardware, runtimes, licenseNotice }) {
  const { release } = manifest;
  const target = join(output, "catalog", release);
  const data = join(output, "catalog-data", release);
  await Promise.all([mkdir(target, { recursive: true }), mkdir(data, { recursive: true })]);
  await Promise.all([
    writeFile(join(target, "manifest.json"), JSON.stringify(manifest, null, 2) + "\n"),
    writeFile(join(target, "LICENSE.txt"), licenseNotice + "\n"),
    writeFile(join(data, "runtimes.json"), JSON.stringify(runtimes)),
    writeFile(join(data, "cards.json"), JSON.stringify(hardware.catalog.cards)),
    writeFile(join(data, "machines.json"), JSON.stringify(hardware.catalog.machines)),
    ...[...shards].map(([key, rows]) => writeFile(join(data, key + ".json"), JSON.stringify(rows))),
  ]);
  return release;
}
