import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { catalogOpenApi } from "./catalog-api.mjs";
import { readHardwareCatalog } from "./catalog-hardware-build.mjs";
import { modelIdPattern, modelShard } from "./catalog-paths.mjs";

const sha256 = (bytes) => createHash("sha256").update(bytes).digest("hex");
const upstream = {
  commit: "26450cccaf3a3f14b1822875f2473847a744a718",
  sha256: "298dbdf36913e1071e62dd07033b0bdf2672a208d71838d2e96d1f464fbd723a",
  commitDate: "2026-11-18T14:59:13Z",
};

function readPublisherEvaluations(rows, id, revision, cardUrl) {
  if (!Array.isArray(rows)) throw new Error("Invalid publisher evaluations for " + id);
  return rows.map(({ benchmark, version, scorePercent, harness, source, cardRevision, cardLine }) => {
    if (cardRevision !== revision) throw new Error("Publisher evaluation revision does not match " + id);
    const url = URL.parse(source);
    if (!url || url.protocol !== "https:" || url.username || url.password || url.href !== source ||
        ![benchmark, version, harness].every(value => typeof value === "string" && value.trim()) ||
        !Number.isFinite(scorePercent) || scorePercent < 0 || scorePercent > 100 ||
        !Number.isSafeInteger(cardLine) || cardLine < 1) {
      throw new Error("Invalid publisher evaluation for " + id);
    }
    return { benchmark, version, scorePercent, harness, source, cardUrl: cardUrl + "#L" + cardLine,
      evidenceClass: "publisher_reported", executionHardware: null };
  });
}

function readSupplement(bytes, source, identities, discovery) {
  const { capturedAt, models } = JSON.parse(bytes);
  const date = value => /^\d{4}-\d{2}-\d{2}$/.test(value) &&
    Number.isFinite(Date.parse(value)) && new Date(value).toISOString().slice(0, 10) === value;
  if (!date(capturedAt) || !Array.isArray(models)) throw new Error("Invalid reviewed model supplement");
  const usedIds = new Set([
    ...source.models.map(row => row.id), ...Object.keys(identities),
    ...[...discovery.popular, ...discovery.small].map(row => row.id),
  ]);
  const hasDigest = value => /^[a-f0-9]{64}$/.test(value);
  const hasModalities = values => Array.isArray(values) && values.length > 0 &&
    values.every(value => typeof value === "string" && value.trim());
  const supplementalModels = models.map(({ id, revision, revisionDate, cardSha256, license, licenseName,
    licenseSha256, parameters, inputs, outputs, task, publisherEvaluations = [] }) => {
    const apache = license === "apache-2.0";
    if (!modelIdPattern.test(id) || usedIds.has(id) || !/^[a-f0-9]{40}$/.test(revision) ||
        !date(revisionDate) || revisionDate > capturedAt || !hasDigest(cardSha256) ||
        !(apache || (license && licenseName && hasDigest(licenseSha256))) ||
        typeof task !== "string" || !task.trim() || typeof parameters !== "string" || !parameters.trim() ||
        !hasModalities(inputs) || !hasModalities(outputs)) {
      throw new Error("Invalid or duplicate reviewed model repository: " + id);
    }
    usedIds.add(id);
    const source = "https://huggingface.co/" + id;
    const pinned = source + "/blob/" + revision;
    const cardUrl = pinned + "/README.md";
    const evaluations = readPublisherEvaluations(publisherEvaluations, id, revision, cardUrl);
    return {
      id, name: id, source, license, detail: task,
      supplemental: {
        capturedAt, revision, revisionDate, parameters, inputs, outputs,
        cardUrl, cardSha256,
        ...(evaluations.length > 0 && { publisherEvaluations: evaluations }),
        infoUrl: "https://huggingface.co/api/models/" + id + "/revision/" + revision,
        licenseName: apache ? "Apache License 2.0" : licenseName,
        licenseUrl: apache ? "https://www.apache.org/licenses/LICENSE-2.0" : pinned + "/LICENSE",
        ...(!apache && { licenseSha256 }),
      },
    };
  });
  const publisherResults = supplementalModels.reduce((total, row) =>
    total + (row.supplemental.publisherEvaluations?.length ?? 0), 0);
  return {
    supplement: {
      capturedAt, sha256: sha256(bytes), repositories: models.length, publisherResults,
      scope: publisherResults ? "repository-metadata-and-selected-publisher-results" : "repository-metadata-only",
    },
    supplementalModels,
  };
}

export async function readCatalogModelFiles(directory) {
  const [sourceBytes, identityBytes, discoveryBytes, supplementBytes] = await Promise.all([
    readFile(join(directory, "catalog-models.json")),
    readFile(join(directory, "catalog-identities.json")),
    readFile(join(directory, "model-discovery.json")),
    readFile(join(directory, "catalog-model-supplements.json")),
  ]);
  const source = JSON.parse(sourceBytes);
  if (source.commit !== upstream.commit) throw new Error("Review the new catalog source and its SHA-256 before publishing");
  const identities = JSON.parse(identityBytes);
  const discovery = JSON.parse(discoveryBytes);
  return {
    sourceBytes, identityBytes, source,
    identities, discovery, ...readSupplement(supplementBytes, source, identities, discovery),
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
  const digest = sha256(Buffer.concat([models.sourceBytes, models.identityBytes, runtimeBytes,
    Buffer.from(hardwareSource.digest, "hex"), ...(models.supplement ? [Buffer.from(models.supplement.sha256, "hex")] : [])]));
  return writeCatalogProjection(output, prepareCatalogRelease({ ...models, hardware: hardwareSource, runtimes, digest }));
}

export function prepareCatalogRelease({ source, identities, discovery, sourceManifest, hardware, runtimes, digest,
  snapshotId, topologies, supplement, supplementalModels = [] }) {
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

  for (const row of [...source.models, ...supplementalModels]) {
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
  if (source.sourceRows !== source.models.length + source.duplicateRows + source.rejectedRows) {
    throw new Error("Model catalog counts do not reconcile");
  }

  for (const id of Object.keys(identities)) {
    if (!ids.has(id)) throw new Error("Reviewed identity has no catalog record: " + id);
  }
  const reviewed = Object.values(identities);
  const manifest = {
    release,
    ...(snapshotId && {
      snapshotId,
      discovery: { capturedAt, source: rankingSource, popular: discovery.popular.length, small: discovery.small.length },
      modelShardCounts: Object.fromEntries([...shards].map(([key, rows]) => [key, rows.length])),
    }),
    source: sourceManifest,
    ...(supplement && { supplement }),
    hardware: hardware.manifest,
    artifactScope: "Selected upstream artifacts have individually pinned repository revisions and upstream digests. External benchmark caches are excluded.",
    coverage: {
      sourceRows: source.sourceRows,
      publishedRows: source.models.length,
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
    ...(manifest.snapshotId ? [writeFile(join(target, "openapi.json"), JSON.stringify(catalogOpenApi(release), null, 2) + "\n")] : []),
    writeFile(join(data, "runtimes.json"), JSON.stringify(runtimes)),
    writeFile(join(data, "cards.json"), JSON.stringify(hardware.catalog.cards)),
    writeFile(join(data, "machines.json"), JSON.stringify(hardware.catalog.machines)),
    ...[...shards].map(([key, rows]) => writeFile(join(data, key + ".json"), JSON.stringify(rows))),
  ]);
  return release;
}
