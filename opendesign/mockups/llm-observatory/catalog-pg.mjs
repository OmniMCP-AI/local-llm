import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { readdir, readFile } from "node:fs/promises";
import { join, relative } from "node:path";
import { fileURLToPath } from "node:url";
import { readCatalogModelFiles } from "./catalog-release-build.mjs";
import { modelRepositoryMap } from "./catalog-search.mjs";
import { readCatalogPhotos } from "./catalog-topology-build.mjs";
import { machineBuildRegistry } from "./catalog-hardware-build.mjs";
import { readEvidenceState, withdrawnPublisherSource } from "./evidence-state.mjs";
import { estimateBattleTitles } from "./battle-title-signals.mjs";

const project = new URL(".", import.meta.url);
const docs = new URL("../../../docs/", project);
const seed = new URL("Local-AI-Comparison-Platform/YouTube-Local-LLM-Transcripts/", docs);
const hardwareSourceDirectory = "opendesign/mockups/llm-observatory/";
const manufacturerSourceFile = "catalog-source-additions.json";
const hardwareSourceFiles = [manufacturerSourceFile, machineBuildRegistry];
const manufacturerSourcePath = hardwareSourceDirectory + manufacturerSourceFile;
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
  const { source, hardware, runtimes, identities, discovery, sourceManifest, topologies, photos,
    supplement, supplementalModels, battleTitleSignals } = catalog;
  return sha256(encode(canonicalJson([
    { ...source, models: byId(source.models) }, hardware.manifest, byId(hardware.catalog.cards),
    byId(hardware.catalog.machines), byId(runtimes), identities, discovery, sourceManifest, topologies, photos,
    ...(supplement ? [supplement, byId(supplementalModels)] : []),
    ...(battleTitleSignals ? [battleTitleSignals] : []),
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

function topologyRecords(reports, machines, documents, photos) {
  const machineById = new Map(machines.map(row => [row.id, row]));
  const digestByPath = new Map(documents.map(([path, digest]) => [path, digest]));
  const records = {
    topology_media: Object.entries(photos).map(([id, photo]) => [id, encode(photo)]),
    topology_revision: [],
    topology_node: [],
    topology_link: [],
  };
  const topologies = [];
  for (const { id, devices, links = [], hosts: reportedHosts = [], ...report } of reports) {
    const machine = machineById.get(id);
    if (!machine) continue;
    const sourcePath = machine.kind === "Complete factory configuration" ? manufacturerSourcePath
      : relative(fileURLToPath(docs), fileURLToPath(new URL(`hardware-profiles/${id}.md`, seed)));
    const sourceDigest = digestByPath.get(sourcePath);
    const isHost = report.group === "hosts";
    const normalizedDevices = devices.map(({ photo = null, card = null, ...part }, index) => ({
      ...part, slot: index + 1, photo, card,
    }));
    const hosts = isHost ? Array.from({ length: report.hostCount }, (_, index) => ({
      slot: index + 1, label: report.hostModel,
    })) : reportedHosts.toSorted((a, b) => a.slot - b.slot);
    const parts = [...normalizedDevices, ...hosts];
    const partSlots = new Set(parts.map(({ slot }) => slot));
    if (!sourceDigest || machine.source !== report.source ||
        (isHost ? !hosts.length || !report.hostModel || devices.length : report.count !== devices.length || !devices.length) ||
        partSlots.size !== parts.length || hosts.some(({ slot, label }) => !Number.isInteger(slot) || slot < 1 || !label) ||
        normalizedDevices.some(({ card, photo }) => (card && !machine.cardIds.includes(card)) || (photo && !photos[photo])) ||
        links.some(({ slots }) => slots.length !== 2 || slots[0] === slots[1] ||
          slots.some(slot => !partSlots.has(slot)))) {
      throw new Error("Topology lacks a matching sourced profile, part or link: " + id);
    }
    const layout = { id, ...report, sourcePath, sourceDigest, devices: normalizedDevices, hosts, links };
    const photoIds = [...new Set(normalizedDevices.map(({ photo }) => photo).filter(Boolean))].sort();
    const revision = "topology-" + sha256(encode(canonicalJson([layout, photoIds.map(photo => photos[photo])])));
    topologies.push({ ...layout, revision });
    records.topology_revision.push([id, revision, topologies.length, sourcePath, encode({ ...report, sourceDigest })]);
    normalizedDevices.forEach(({ slot, photo, card, ...part }) => {
      records.topology_node.push([id, revision, slot, "card", card, photo, encode(part)]);
    });
    hosts.forEach(({ slot, ...part }) => {
      records.topology_node.push([id, revision, slot, "host", null, null, encode(part)]);
    });
    links.forEach(({ slots, ...link }, index) => {
      records.topology_link.push([id, revision, index + 1, ...slots, encode(link)]);
    });
  }
  return { topologies, records };
}

export async function importLocalCatalog(hardware, database = process.env.FASTEST_DATABASE_URL ?? "postgresql://localhost/localdecode_catalog",
  isPublisherWithdrawn) {
  const publisherFilter = isPublisherWithdrawn ?? withdrawnPublisherSource(await readEvidenceState());
  const [schema, modelFiles, runtimes, topics, inventory, series, references, observations, documents, reports, photos,
    hardwareSources, titleSample] = await Promise.all([
    readFile(new URL("catalog-pg.sql", project), "utf8"),
    readCatalogModelFiles(fileURLToPath(project), publisherFilter),
    ...["catalog-runtimes.json", "catalog-topics.json"].map(name => readJson(project, name)),
    ...["inventory.json", "llmfit/research/test-series.json", "llmfit/research/models.json", "llmfit/research/benchmarks.json"]
      .map(name => readJson(seed, name)),
    researchDocuments(),
    readJson(project, "catalog-topology.json"),
    readCatalogPhotos(project),
    Promise.all(hardwareSourceFiles.map(async name => {
      const source = await readFile(new URL(name, project), "utf8");
      return [hardwareSourceDirectory + name, sha256(source), source];
    })),
    readJson(project, "battle-title-sample.json"),
  ]);
  const { source: models, identities, discovery, sourceManifest, supplement, supplementalModels } = modelFiles;
  const { models: modelRows, ...modelMetadata } = models;
  const reviewedIdentities = Object.fromEntries(Object.entries(identities).map(([id, identity]) => [
    id, { ...identity, artifacts: identity.artifacts ?? [] },
  ]));
  const { cards, machines } = hardware.catalog;
  const battleTitleSignals = estimateBattleTitles(titleSample, hardware.catalog);
  documents.push(...hardwareSources);
  const { topologies, records: topologyTables } = topologyRecords(reports, machines, documents, photos);
  const byPosition = new Map(inventory.map(row => [Number(row.position), row.id]));
  const distinctVideos = new Map();
  for (const row of inventory) if (!distinctVideos.has(row.id)) distinctVideos.set(row.id, row);
  const { popular, small, ...discoveryCapture } = discovery;
  const collections = Object.entries({ popular, small });
  const expectedModelProfiles = new Set([...popular, ...small, ...supplementalModels].map(row => row.id));
  const records = {
    snapshot: [[encode({
      ...hardware.manifest,
      models: {
        source: { url: models.upstream, commit: models.commit, license: models.catalogLicense, licenseUrl: models.catalogLicenseUrl },
        discovery: discoveryCapture,
        supplement,
      },
      modelLicenseNotice: models.licenseNotice,
      battleTitleSample: titleSample,
      battleTitleSignals,
      pages: {
        hardware: hardware.manifest, modelMetadata, sourceManifest,
        projectionDigest: publicCatalogDigest({
          source: models, hardware, runtimes, identities: reviewedIdentities, discovery, sourceManifest, topologies, photos,
          supplement, supplementalModels, battleTitleSignals,
        }),
        runtimeProjects: runtimes.length,
        topologyRevisions: topologies.length,
        popular: popular.length, small: small.length,
      },
    })]],
    seed_document: documents,
    gpu: cards.map(row => [row.id, row.parent, encode(row)]),
    vendor_spec: cards.filter(row => row.vendorSpec).map(row => [row.id, row.vendorSpec.source, encode(row.vendorSpec)]),
    machine: machines.map(row => [row.id, encode(row)]),
    machine_gpu: machines.flatMap(row => row.cardIds.map(id => [row.id, id])),
    machine_part: machines.flatMap(row => (row.bom ?? []).map((part, index) => [row.id, index, encode(part)])),
    ...topologyTables,
    model_repository: Array.from(modelRepositoryMap(modelRows, supplementalModels).values(), row => {
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
  const { catalog, runtimes: importedRuntimes, modelManifest, modelLicenseNotice,
    topologies: importedTopologies, photos: importedPhotos, battleTitleSignals: importedTitleSignals } = readSnapshot(database, id);
  if (catalog.cards.length !== cards.length || catalog.machines.length !== machines.length) {
    throw new Error("PostgreSQL catalog coverage differs from the source");
  }
  if (modelManifest.inventory !== modelRows.length ||
    catalog.models.filter(row => row.supplemental).length !== supplement.repositories ||
    collections.some(([collection, rows]) => modelManifest[collection] !== rows.length) ||
    catalog.models.length !== expectedModelProfiles.size ||
    catalog.models.some(row => !expectedModelProfiles.has(row.id))) {
    throw new Error("PostgreSQL model coverage differs from the source");
  }
  return { ...hardware, catalog, snapshotId: id, runtimes: importedRuntimes, modelManifest, modelLicenseNotice,
    topologies: importedTopologies, photos: importedPhotos, battleTitleSignals: importedTitleSignals };
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
      'topologies', (
        SELECT coalesce(jsonb_agg(revision.document || jsonb_build_object(
          'id', revision.machine_id,
          'revision', revision.revision_id,
          'sourcePath', revision.source_path,
          'devices', coalesce(nodes.devices, '[]'::jsonb),
          'hosts', coalesce(nodes.hosts, '[]'::jsonb),
          'links', coalesce(links.documents, '[]'::jsonb)
        ) ORDER BY revision.ordinal), '[]'::jsonb)
        FROM fastest_catalog.topology_revision revision
        CROSS JOIN LATERAL (
          SELECT jsonb_agg(node.document || jsonb_build_object('slot', node.slot, 'card', node.gpu_id, 'photo', node.photo_id)
            ORDER BY node.slot) FILTER (WHERE node.kind = 'card') AS devices,
            jsonb_agg(node.document || jsonb_build_object('slot', node.slot)
              ORDER BY node.slot) FILTER (WHERE node.kind = 'host') AS hosts
          FROM fastest_catalog.topology_node node
          WHERE (node.snapshot_id, node.machine_id, node.revision_id) =
            (revision.snapshot_id, revision.machine_id, revision.revision_id)
        ) nodes
        CROSS JOIN LATERAL (
          SELECT jsonb_agg(link.document || jsonb_build_object('slots', jsonb_build_array(link.from_slot, link.to_slot))
            ORDER BY link.ordinal) AS documents
          FROM fastest_catalog.topology_link link
          WHERE (link.snapshot_id, link.machine_id, link.revision_id) =
            (revision.snapshot_id, revision.machine_id, revision.revision_id)
        ) links
        WHERE revision.snapshot_id = :'snapshot_id'
      ),
      'photos', (
        SELECT coalesce(json_object_agg(id, document ORDER BY id COLLATE "C"), '{}'::json)
        FROM fastest_catalog.topology_media WHERE snapshot_id = :'snapshot_id'
      ),
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
        LEFT JOIN ranked_models ranked ON ranked.repository_id = repository.id
        WHERE repository.snapshot_id = :'snapshot_id'
        ${full ? "" : "AND (ranked.rankings IS NOT NULL OR repository.document ? 'supplemental')"}
      ),
      'modelManifest', snapshot.document->'models' || jsonb_build_object(
        'inventory', (SELECT count(*) FROM fastest_catalog.model_repository
          WHERE snapshot_id = :'snapshot_id' AND (
            NOT (document ? 'supplemental') OR document #> '{supplemental,inUpstream}' = 'true'::jsonb
          )),
        'popular', (SELECT count(*) FROM ranked_models WHERE rankings ? 'popular'),
        'small', (SELECT count(*) FROM ranked_models WHERE rankings ? 'small')
      ),
      'modelLicenseNotice', snapshot.document->>'modelLicenseNotice',
      'battleTitleSignals', snapshot.document->'battleTitleSignals',
      'pages', snapshot.document->'pages'
    ) FROM fastest_catalog.snapshot snapshot WHERE snapshot.id = :'snapshot_id';
    COMMIT;`;
  const result = runCatalogSql(database, id, input, "PostgreSQL catalog read failed", !full);
  if (!result.trim()) throw new Error("PostgreSQL catalog snapshot was not found: " + id);
  const { runtimes, modelManifest, modelLicenseNotice, pages, topologies, photos, battleTitleSignals, ...catalog } = JSON.parse(result);
  return { catalog, runtimes, modelManifest, modelLicenseNotice, pages, topologies, photos, battleTitleSignals };
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
  const { catalog, runtimes, modelManifest, pages, topologies, photos, battleTitleSignals } = readSnapshot(database, id, true);
  if (!pages?.hardware?.coverage || !pages.modelMetadata || !pages.sourceManifest ||
      !pages.projectionDigest || !modelManifest?.discovery || !Number.isInteger(pages.topologyRevisions)) {
    throw new Error("PostgreSQL catalog snapshot has no Pages publication metadata: " + id);
  }
  const { cards, machines, models: records } = catalog;
  const { cards: cardCount, researchProfiles, upstreamPresets, manufacturerMachines, creatorBuilds = 0 } = pages.hardware.coverage;
  if (cards?.length !== cardCount || machines?.length !== researchProfiles + upstreamPresets + manufacturerMachines + creatorBuilds ||
      runtimes?.length !== pages.runtimeProjects || modelManifest.popular !== pages.popular || modelManifest.small !== pages.small ||
      topologies.length !== pages.topologyRevisions) {
    throw new Error("PostgreSQL catalog snapshot coverage does not match its publication metadata: " + id);
  }
  const identities = Object.create(null);
  const popular = [];
  const small = [];
  const models = [];
  const supplementalModels = [];
  for (const { identity, discovery, ...row } of records) {
    if (identity) identities[row.id] = identity;
    if (discovery?.popular) popular.push(discovery.popular);
    if (discovery?.small) small.push(discovery.small);
    if (row.supplemental) supplementalModels.push(row);
    if (!row.supplemental || row.supplemental.inUpstream) {
      const { supplemental, ...upstream } = row;
      models.push(upstream);
    }
  }
  const { supplement } = modelManifest;
  if (models.length !== modelManifest.inventory || supplementalModels.length !== (supplement?.repositories ?? 0)) {
    throw new Error("PostgreSQL model inventory differs from its publication metadata: " + id);
  }
  for (const rows of [popular, small]) {
    rows.sort((a, b) => a.rank - b.rank);
    if (rows.some(({ rank }, index) => rank !== index + 1)) throw new Error("PostgreSQL catalog rankings are incomplete: " + id);
  }
  const withoutRank = ({ rank, ...row }) => row;
  const projection = {
    snapshotId: id, runtimes, identities, topologies, photos, supplement, supplementalModels, battleTitleSignals,
    source: { ...pages.modelMetadata, models }, sourceManifest: pages.sourceManifest,
    discovery: { ...modelManifest.discovery, popular: popular.map(withoutRank), small: small.map(withoutRank) },
    hardware: { catalog: { cards, machines }, manifest: pages.hardware },
  };
  if (publicCatalogDigest(projection) !== pages.projectionDigest) {
    throw new Error("PostgreSQL catalog snapshot content does not match its publication digest: " + id);
  }
  return projection;
}
