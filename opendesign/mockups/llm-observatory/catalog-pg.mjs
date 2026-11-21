import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { readdir, readFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { readCatalogModelFiles } from "./catalog-release-build.mjs";

const project = new URL(".", import.meta.url);
const docs = new URL("../../../docs/", project);
const seed = new URL("Local-AI-Comparison-Platform/YouTube-Local-LLM-Transcripts/", docs);
const readJson = async (root, name) => JSON.parse(await readFile(new URL(name, root), "utf8"));
const encode = JSON.stringify;
const sha256 = (value) => createHash("sha256").update(value).digest("hex");

function canonicalJson(value) {
  if (Array.isArray(value)) return value.map(canonicalJson);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.keys(value).sort().map(key => [key, canonicalJson(value[key])]));
  }
  return value;
}

function publicCatalogDigest(catalog) {
  const byId = rows => rows.toSorted((a, b) => a.id < b.id ? -1 : Number(a.id > b.id));
  const { source, hardware, runtimes, identities, discovery, sourceManifest } = catalog;
  return sha256(encode(canonicalJson([
    { ...source, models: byId(source.models) }, hardware.manifest, byId(hardware.catalog.cards),
    byId(hardware.catalog.machines), byId(runtimes), identities, discovery, sourceManifest,
  ])));
}

async function researchDocuments() {
  const directory = fileURLToPath(docs);
  const paths = (await readdir(directory, { recursive: true }))
    .filter(name => /\.(?:csv|json|md|txt)$/.test(name) && /^(?:Local-AI-Comparison-Platform|AI-Hardware-Project-Domains)\//.test(name))
    .sort();
  return Promise.all(paths.map(async (path) => {
    const bytes = await readFile(join(directory, path));
    return [path, sha256(bytes), bytes.toString("utf8")];
  }));
}

function copyRecords(table, id, records) {
  const escape = value => value == null ? "\\N" : String(value)
    .replaceAll("\\", "\\\\").replaceAll("\t", "\\t").replaceAll("\r", "\\r").replaceAll("\n", "\\n");
  const tuples = records.map(row => [id, ...row].map(escape).join("\t")).join("\n");
  if (!tuples) return "";
  return `CREATE TEMP TABLE temp_${table} (LIKE fastest_catalog.${table}) ON COMMIT DROP;
COPY temp_${table} FROM STDIN;
${tuples}
\\.
INSERT INTO fastest_catalog.${table} SELECT * FROM temp_${table} ON CONFLICT DO NOTHING;\n`;
}

export async function importLocalCatalog(hardware, database = process.env.FASTEST_DATABASE_URL ?? "postgresql://localhost/localdecode_catalog") {
  const [schema, modelFiles, runtimes, topics, inventory, series, references, observations, documents] = await Promise.all([
    readFile(new URL("catalog-pg.sql", project), "utf8"),
    readCatalogModelFiles(fileURLToPath(project)),
    ...["catalog-runtimes.json", "catalog-topics.json"].map(name => readJson(project, name)),
    ...["inventory.json", "llmfit/research/test-series.json", "llmfit/research/models.json", "llmfit/research/benchmarks.json"]
      .map(name => readJson(seed, name)),
    researchDocuments(),
  ]);
  const { source: models, identities, discovery, sourceManifest } = modelFiles;
  const { models: modelRows, ...modelMetadata } = models;
  const reviewedIdentities = Object.fromEntries(Object.entries(identities).map(([id, identity]) => [
    id, { ...identity, artifacts: identity.artifacts ?? [] },
  ]));
  const { cards, machines } = hardware.catalog;
  const byPosition = new Map(inventory.map(row => [Number(row.position), row.id]));
  const distinctVideos = new Map();
  for (const row of inventory) if (!distinctVideos.has(row.id)) distinctVideos.set(row.id, row);
  const { popular, small, ...discoveryCapture } = discovery;
  const collections = Object.entries({ popular, small });
  const expectedModelProfiles = new Set(collections.flatMap(([, rows]) => rows.map(row => row.id)));
  const records = {
    snapshot: [[encode({
      ...hardware.manifest,
      models: {
        source: { url: models.upstream, commit: models.commit, license: models.catalogLicense, licenseUrl: models.catalogLicenseUrl },
        discovery: discoveryCapture,
      },
      modelLicenseNotice: models.licenseNotice,
      pages: {
        hardware: hardware.manifest, modelMetadata, sourceManifest,
        projectionDigest: publicCatalogDigest({ source: models, hardware, runtimes, identities: reviewedIdentities, discovery, sourceManifest }),
        runtimeProjects: runtimes.length,
        popular: popular.length, small: small.length,
      },
    })]],
    seed_document: documents,
    gpu: cards.map(row => [row.id, row.parent, encode(row)]),
    vendor_spec: cards.filter(row => row.vendorSpec).map(row => [row.id, row.vendorSpec.source, encode(row.vendorSpec)]),
    machine: machines.map(row => [row.id, encode(row)]),
    machine_gpu: machines.flatMap(row => row.cardIds.map(id => [row.id, id])),
    machine_part: machines.flatMap(row => (row.bom ?? []).map((part, index) => [row.id, index, encode(part)])),
    model_repository: modelRows.map(row => {
      const { artifacts, ...identity } = identities[row.id] ?? {};
      return [row.id, encode(identities[row.id] ? { ...row, identity } : row)];
    }),
    model_artifact: modelRows.flatMap(row => (identities[row.id]?.artifacts ?? []).map((entry, index) => [row.id, index, encode(entry)])),
    model_discovery: collections.flatMap(([collection, rows]) =>
      rows.map((row, index) => [collection, index + 1, row.id, encode(row)])),
    runtime: runtimes.map(row => [row.id, encode(row)]),
    topic: topics.groups.flatMap(group => group.topics.map(topic => [group.label, topic.name, encode(topic)])),
    discovery_source: topics.refs.map(row => [row.href, encode(row)]),
    source_video: [...distinctVideos.values()].map(row => [row.id, encode(row)]),
    video_inventory_position: inventory.map(row => [Number(row.position), row.id, encode(row)]),
    test_series: series.map(row => [row.series_id, byPosition.get(Number(row.position)), encode(row)]),
    research_model: references.map(row => [row.x_local_ai_research.model_reference_id, encode(row)]),
    research_observation: observations.map(row => {
      const source = row.x_local_ai_research;
      const input = source.original_observation_and_conditions;
      return [source.observation_id, source.test_series_id, input.video_id, source.hardware_profile_id,
        source.model_reference_id, input.value, input.unit, encode(row)];
    }),
  };
  const id = sha256(encode([schema, hardware.digest, records]));
  const input = ["BEGIN;", "SET LOCAL lock_timeout = '10s';",
    "SELECT pg_advisory_xact_lock(7021920261121) AS import_lock \\gset", schema,
    ...Object.entries(records).map(([table, rows]) => copyRecords(table, id, rows)),
    `INSERT INTO fastest_catalog.current_snapshot VALUES (true, '${id}')
      ON CONFLICT (singleton) DO UPDATE SET snapshot_id = EXCLUDED.snapshot_id;`,
    "COMMIT;",
  ].join("\n");
  runCatalogSql(database, id, input, "PostgreSQL catalog import failed", true);
  const { catalog, runtimes: importedRuntimes, modelManifest, modelLicenseNotice } = readSnapshot(database, id);
  if (catalog.cards.length !== cards.length || catalog.machines.length !== machines.length) {
    throw new Error("PostgreSQL catalog coverage differs from the source");
  }
  if (modelManifest.inventory !== modelRows.length ||
    collections.some(([collection, rows]) => modelManifest[collection] !== rows.length) ||
    catalog.models.length !== expectedModelProfiles.size ||
    catalog.models.some(row => !expectedModelProfiles.has(row.id))) {
    throw new Error("PostgreSQL model coverage differs from the source");
  }
  return { ...hardware, catalog, snapshotId: id, runtimes: importedRuntimes, modelManifest, modelLicenseNotice };
}

function readSnapshot(database, id, full = false) {
  const input = `BEGIN READ ONLY;
    WITH ranked_models AS (
      SELECT repository_id, jsonb_object_agg(collection, document || jsonb_build_object('rank', rank)) AS rankings
      FROM fastest_catalog.model_discovery
      WHERE snapshot_id = :'snapshot_id' AND collection IN ('popular', 'small')
      GROUP BY repository_id
    )
    SELECT json_build_object(
      'cards', (SELECT json_agg(document ORDER BY id COLLATE "C") FROM fastest_catalog.gpu WHERE snapshot_id = :'snapshot_id'),
      'machines', (SELECT json_agg(document ORDER BY id COLLATE "C") FROM fastest_catalog.machine WHERE snapshot_id = :'snapshot_id'),
      'runtimes', (SELECT json_agg(document ORDER BY id COLLATE "C") FROM fastest_catalog.runtime WHERE snapshot_id = :'snapshot_id'),
      'models', (
        SELECT coalesce(json_agg(repository.document || jsonb_build_object(
          'discovery', ranked.rankings,
          'identity', CASE WHEN repository.document ? 'identity' THEN repository.document->'identity' || jsonb_build_object('artifacts', (
            SELECT coalesce(jsonb_agg(artifact.document ORDER BY artifact.ordinal), '[]'::jsonb)
            FROM fastest_catalog.model_artifact artifact
            WHERE artifact.snapshot_id = repository.snapshot_id AND artifact.repository_id = repository.id
          )) END
        ) ORDER BY repository.id COLLATE "C"), '[]'::json)
        FROM fastest_catalog.model_repository repository
        ${full ? "LEFT JOIN" : "JOIN"} ranked_models ranked ON ranked.repository_id = repository.id
        WHERE repository.snapshot_id = :'snapshot_id'
      ),
      'modelManifest', snapshot.document->'models' || jsonb_build_object(
        'inventory', (SELECT count(*) FROM fastest_catalog.model_repository WHERE snapshot_id = :'snapshot_id'),
        'popular', (SELECT count(*) FROM ranked_models WHERE rankings ? 'popular'),
        'small', (SELECT count(*) FROM ranked_models WHERE rankings ? 'small')
      ),
      'modelLicenseNotice', snapshot.document->>'modelLicenseNotice',
      'pages', snapshot.document->'pages'
    ) FROM fastest_catalog.snapshot snapshot WHERE snapshot.id = :'snapshot_id';
    COMMIT;`;
  const result = runCatalogSql(database, id, input, "PostgreSQL catalog read failed", !full);
  if (!result.trim()) throw new Error("PostgreSQL catalog snapshot was not found: " + id);
  const { runtimes, modelManifest, modelLicenseNotice, pages, ...catalog } = JSON.parse(result);
  return { catalog, runtimes, modelManifest, modelLicenseNotice, pages };
}

function runCatalogSql(database, id, input, errorMessage, showDetails) {
  const result = spawnSync("psql", ["-X", "-w", "-qAt", "--set=ON_ERROR_STOP=1", `--set=snapshot_id=${id}`, "--dbname", database], {
    input, encoding: "utf8", maxBuffer: 32 * 1024 * 1024, timeout: 60_000,
  });
  if (result.error) throw new Error(errorMessage + " (" + result.error.code + ")");
  if (result.status !== 0) throw new Error(errorMessage + (showDetails ? ": " + result.stderr.trim() : ""));
  return result.stdout;
}

export function readPublishedCatalog(database, id) {
  const { catalog, runtimes, modelManifest, pages } = readSnapshot(database, id, true);
  if (!pages?.hardware?.coverage || !pages.modelMetadata || !pages.sourceManifest ||
      !pages.projectionDigest || !modelManifest?.discovery) {
    throw new Error("PostgreSQL catalog snapshot has no Pages publication metadata: " + id);
  }
  const { cards, machines, models: records } = catalog;
  const { cards: cardCount, researchProfiles, upstreamPresets, manufacturerMachines } = pages.hardware.coverage;
  if (cards?.length !== cardCount || machines?.length !== researchProfiles + upstreamPresets + manufacturerMachines ||
      runtimes?.length !== pages.runtimeProjects || modelManifest.popular !== pages.popular || modelManifest.small !== pages.small) {
    throw new Error("PostgreSQL catalog snapshot coverage does not match its publication metadata: " + id);
  }
  const identities = Object.create(null);
  const popular = [];
  const small = [];
  const models = records.map(({ identity, discovery, ...row }) => {
    if (identity) identities[row.id] = identity;
    if (discovery?.popular) popular.push(discovery.popular);
    if (discovery?.small) small.push(discovery.small);
    return row;
  });
  for (const rows of [popular, small]) {
    rows.sort((a, b) => a.rank - b.rank);
    if (rows.some(({ rank }, index) => rank !== index + 1)) throw new Error("PostgreSQL catalog rankings are incomplete: " + id);
  }
  const withoutRank = ({ rank, ...row }) => row;
  const projection = {
    snapshotId: id, runtimes, identities, source: { ...pages.modelMetadata, models }, sourceManifest: pages.sourceManifest,
    discovery: { ...modelManifest.discovery, popular: popular.map(withoutRank), small: small.map(withoutRank) },
    hardware: { catalog: { cards, machines }, manifest: pages.hardware },
  };
  if (publicCatalogDigest(projection) !== pages.projectionDigest) {
    throw new Error("PostgreSQL catalog snapshot content does not match its publication digest: " + id);
  }
  return projection;
}
