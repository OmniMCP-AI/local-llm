import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { readdir, readFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const project = new URL(".", import.meta.url);
const docs = new URL("../../../docs/", project);
const seed = new URL("Local-AI-Comparison-Platform/YouTube-Local-LLM-Transcripts/", docs);
const readJson = async (root, name) => JSON.parse(await readFile(new URL(name, root), "utf8"));
const encode = JSON.stringify;
const sha256 = (value) => createHash("sha256").update(value).digest("hex");

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
  const [schema, models, identities, runtimes, discovery, topics, inventory, series, references, observations, documents] = await Promise.all([
    readFile(new URL("catalog-pg.sql", project), "utf8"),
    ...["catalog-models.json", "catalog-identities.json", "catalog-runtimes.json", "model-discovery.json", "catalog-topics.json"]
      .map(name => readJson(project, name)),
    ...["inventory.json", "llmfit/research/test-series.json", "llmfit/research/models.json", "llmfit/research/benchmarks.json"]
      .map(name => readJson(seed, name)),
    researchDocuments(),
  ]);
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
    })]],
    seed_document: documents,
    gpu: cards.map(row => [row.id, row.parent, encode(row)]),
    vendor_spec: cards.filter(row => row.vendorSpec).map(row => [row.id, row.vendorSpec.source, encode(row.vendorSpec)]),
    machine: machines.map(row => [row.id, encode(row)]),
    machine_gpu: machines.flatMap(row => row.cardIds.map(id => [row.id, id])),
    machine_part: machines.flatMap(row => (row.bom ?? []).map((part, index) => [row.id, index, encode(part)])),
    model_repository: models.models.map(row => {
      const { artifacts, ...identity } = identities[row.id] ?? {};
      return [row.id, encode(identities[row.id] ? { ...row, identity } : row)];
    }),
    model_artifact: models.models.flatMap(row => (identities[row.id]?.artifacts ?? []).map((entry, index) => [row.id, index, encode(entry)])),
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
    `WITH ranked_models AS (
      SELECT repository_id, jsonb_object_agg(collection, document || jsonb_build_object('rank', rank)) AS rankings
      FROM fastest_catalog.model_discovery
      WHERE snapshot_id = '${id}' AND collection IN ('popular', 'small')
      GROUP BY repository_id
    )
    SELECT json_build_object(
      'cards', (SELECT json_agg(document ORDER BY id COLLATE "C") FROM fastest_catalog.gpu WHERE snapshot_id = '${id}'),
      'machines', (SELECT json_agg(document ORDER BY id COLLATE "C") FROM fastest_catalog.machine WHERE snapshot_id = '${id}'),
      'runtimes', (SELECT json_agg(document ORDER BY id COLLATE "C") FROM fastest_catalog.runtime WHERE snapshot_id = '${id}'),
      'models', (
        SELECT coalesce(json_agg(repository.document || jsonb_build_object(
          'discovery', ranked.rankings,
          'identity', coalesce(repository.document->'identity', '{}'::jsonb) || jsonb_build_object('artifacts', (
            SELECT coalesce(jsonb_agg(artifact.document ORDER BY artifact.ordinal), '[]'::jsonb)
            FROM fastest_catalog.model_artifact artifact
            WHERE artifact.snapshot_id = repository.snapshot_id AND artifact.repository_id = repository.id
          ))
        ) ORDER BY repository.id COLLATE "C"), '[]'::json)
        FROM fastest_catalog.model_repository repository
        JOIN ranked_models ranked ON ranked.repository_id = repository.id
        WHERE repository.snapshot_id = '${id}'
      ),
      'modelManifest', snapshot.document->'models' || jsonb_build_object(
        'inventory', (SELECT count(*) FROM fastest_catalog.model_repository WHERE snapshot_id = '${id}'),
        'popular', (SELECT count(*) FROM ranked_models WHERE rankings ? 'popular'),
        'small', (SELECT count(*) FROM ranked_models WHERE rankings ? 'small')
      ),
      'modelLicenseNotice', snapshot.document->>'modelLicenseNotice'
    ) FROM fastest_catalog.snapshot snapshot WHERE snapshot.id = '${id}';`,
  ].join("\n");
  const result = spawnSync("psql", ["-X", "-w", "-qAt", "--set=ON_ERROR_STOP=1", "--dbname", database], {
    input, encoding: "utf8", maxBuffer: 32 * 1024 * 1024, timeout: 60_000,
  });
  if (result.error) throw result.error;
  if (result.status !== 0) throw new Error("PostgreSQL catalog import failed: " + result.stderr.trim());
  const { runtimes: importedRuntimes, modelManifest, modelLicenseNotice, ...catalog } = JSON.parse(result.stdout);
  if (catalog.cards.length !== cards.length || catalog.machines.length !== machines.length) {
    throw new Error("PostgreSQL catalog coverage differs from the source");
  }
  if (modelManifest.inventory !== models.models.length ||
    collections.some(([collection, rows]) => modelManifest[collection] !== rows.length) ||
    catalog.models.length !== expectedModelProfiles.size ||
    catalog.models.some(row => !expectedModelProfiles.has(row.id))) {
    throw new Error("PostgreSQL model coverage differs from the source");
  }
  return { ...hardware, catalog, snapshotId: id, runtimes: importedRuntimes, modelManifest, modelLicenseNotice };
}
