import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import { hardwareIdPattern } from "./catalog-paths.mjs";
import { readCatalogPhotos } from "./catalog-topology-build.mjs";

const sha256 = (bytes) => createHash("sha256").update(bytes).digest("hex");
export const machineBuildRegistry = "catalog-machine-builds.json";
const seedPath = "docs/Local-AI-Comparison-Platform/YouTube-Local-LLM-Transcripts";
const unreported = "Not reported in available captions";
const fact = (value) => value && value !== unreported ? value : null;
const key = (name) => name.toLowerCase().replace(/[^a-z0-9]+/g, "");
const unique = (values) => [...new Set(values.filter(Boolean))];
const upstreamLink = (commit, path) => `https://github.com/AlexsJones/llmfit/blob/${commit}/${path}`;
const profileKind = (profile) => /^(GPU product|Creator-reviewed mining GPU)/.test(profile.role)
  ? "Component reference" : "Partial configuration";

function index(rows) {
  const entries = new Map(rows.map((row) => [row.id, row]));
  if (entries.size !== rows.length) throw new Error("Duplicate hardware identity");
  return entries;
}

function researchMemory(profile, native, exceptions) {
  const perDevice = fact(profile.vram_per_gpu);
  return {
    // Aggregate, unclear, and configured limits cannot establish installed capacity.
    system: native ? `${native.total_ram_gb} GB ${native.unified_memory ? "unified memory" : "system RAM"} (creator reported)` : null,
    perDevice: /^\d+\s*GB(?:\s*(?:each|per\s*card))?$/i.test(perDevice ?? "") ? perDevice : null,
    aggregate: fact(profile.aggregate_vram),
    allocation: null,
    ...exceptions,
  };
}

function reviewedMachineRows(builds, cards, withdrawnCards, isWithdrawn) {
  index(builds);
  return builds.filter(({ id, source, cardIds, name, buildSource, bom, video }) => {
    if (!hardwareIdPattern.test(id) || !source?.startsWith("https://") || !name ||
        !buildSource?.platform || !buildSource.author || !buildSource.locator ||
        !bom?.length || bom.some(({ category, part }) => !category || !part) ||
        cardIds.some(card => !cards.has(card) && !withdrawnCards.has(card)) ||
        (video && (!/^[\w-]{11}$/.test(video.id) || source !== ("https://www.youtube.com/watch?v=" + video.id) ||
          !video.title || (video.start !== undefined && (!Number.isSafeInteger(video.start) || video.start < 0))))) {
      throw new Error("Invalid reviewed machine: " + id);
    }
    return ![id, source].some(isWithdrawn) && cardIds.every(card => cards.has(card));
  }).map(({ gallery, ...machine }) => ({
    ...machine,
    kind: "Creator-reported build",
    bom: machine.bom.map(part => ({ ...part, source: machine.source, locator: machine.buildSource.locator })),
    ...(gallery && !isWithdrawn(gallery.source) ? { gallery } : {}),
  }));
}

function reviewedResearchVideos(reviews, profiles) {
  const videos = new Map();
  for (const { id, title, credit, profiles: profileIds } of reviews) {
    if (!/^[\w-]{11}$/.test(id) || !title?.trim() || !credit?.trim() || !profileIds?.length) {
      throw new Error("Invalid research video: " + id);
    }
    for (const profileId of profileIds) {
      const profile = profiles.get(profileId);
      const capture = /^https:\/\/www\.youtube\.com\/watch\?v=([\w-]{11})&t=(\d+)s$/.exec(profile?.source_url);
      if (!capture || capture[1] !== id || !Number.isSafeInteger(Number(capture[2])) ||
          profileKind(profile) !== "Partial configuration" || videos.has(profileId)) {
        throw new Error("Invalid machine profile for research video: " + profileId);
      }
      videos.set(profileId, { id, title, credit, start: Number(capture[2]) });
    }
  }
  return videos;
}

function publicMachineVideo({ video, buildSource }, isWithdrawn) {
  const watch = "https://www.youtube.com/watch?v=" + video.id;
  const source = watch + (video.start === undefined ? "" : "&t=" + video.start + "s");
  const thumbnail = "https://i.ytimg.com/vi/" + video.id + "/hqdefault.jpg";
  const embed = "https://www.youtube-nocookie.com/embed/" + video.id;
  const player = embed + (video.start ? "?start=" + video.start : "");
  if ([watch, source, thumbnail, embed, player].some(isWithdrawn)) return undefined;
  return { ...video, source, thumbnail, player, credit: video.credit ?? buildSource.author };
}

export async function readHardwareCatalog(directory, isWithdrawn = () => false) {
  const [inventoryBytes, mappingsBytes, profileBytes, nativeBytes, specBytes, additionsBytes, modifiedBytes,
    referenceBytes, buildBytes, gpuPhotoIds, photos, gpuPhotos] = await Promise.all([
    readFile(join(directory, "catalog-hardware.json")),
    readFile(join(directory, "catalog-hardware-sources.json")),
    readFile(join(directory, "../../..", seedPath, "hardware-profiles.json")),
    readFile(join(directory, "../../..", seedPath, "llmfit/research/hardware.json")),
    readFile(join(directory, "gpu-vendor-specs.json")),
    readFile(join(directory, "catalog-source-additions.json")),
    readFile(join(directory, "catalog-modified-gpus.json")),
    readFile(join(directory, "catalog-gpu-reference-evidence.json")),
    readFile(join(directory, machineBuildRegistry)),
    readFile(join(directory, "catalog-gpu-photo-ids.json"), "utf8").then(JSON.parse),
    readCatalogPhotos(pathToFileURL(join(directory, "catalog-hardware-build.mjs")), "machine"),
    readCatalogPhotos(pathToFileURL(join(directory, "catalog-hardware-build.mjs")), ["component", "gpu"]),
  ]);
  const inventory = JSON.parse(inventoryBytes);
  const { asOf: inventoryAsOf, upstream, research, variants, cardMetadata, profileCards, memoryNotes } = JSON.parse(mappingsBytes);
  const vendor = JSON.parse(specBytes);
  const additions = JSON.parse(additionsBytes);
  const modified = JSON.parse(modifiedBytes);
  const { reviewedAt, builds, photoIds, researchVideos = [] } = JSON.parse(buildBytes);
  const references = JSON.parse(referenceBytes);
  const vendorSpec = (id) => {
    const source = [additions.specs[id], vendor.cards[id]].find(spec => spec && !isWithdrawn(spec.source));
    if (!source) return null;
    const { gallery: retainedGallery, ...spec } = source;
    const reference = references.cards[id];
    const gallery = retainedGallery ?? reference?.gallery;
    const supplement = reference?.bandwidth && !spec.facts["Memory bandwidth"] && !isWithdrawn(reference.bandwidthSource);
    const scope = spec.scope ?? (/\/|\bor\b/.test(spec.facts["Memory configuration"] ?? "")
      ? "Multiple manufacturer configurations" : "Manufacturer product reference");
    return {
      capturedAt: source === additions.specs[id] ? additions.capturedAt : vendor.capturedAt,
      locator: `Manufacturer comparison table · ${spec.designation}`,
      ...spec, scope,
      ...(supplement ? {
        facts: { ...spec.facts, "Memory bandwidth": reference.bandwidth },
        bandwidthSource: reference.bandwidthSource,
      } : {}),
      ...(gallery && !isWithdrawn(gallery.source) ? { gallery } : {}),
    };
  };
  if (sha256(profileBytes) !== research.profilesSha256 || sha256(nativeBytes) !== research.nativeProfilesSha256) {
    throw new Error("Review the changed hardware research snapshot before publishing");
  }

  const profileRows = JSON.parse(profileBytes);
  const mappedProfiles = index(JSON.parse(nativeBytes).map((row) => ({
    id: row.x_local_ai_research.profile_id,
    native: row.llmfit_hardware_profile?.hardware,
  })));
  const inventoryProfiles = index(inventory.machines);
  const researchBase = `https://github.com/OmniMCP-AI/local-llm/blob/${research.commit}/${seedPath}`;
  const lookupSource = upstreamLink(upstream.commit, upstream.lookupPath);
  const matchers = new Map(upstream.discreteMatchers.map(([id, alias, line]) => [id, { alias, source: `${lookupSource}#L${line}` }]));
  if (matchers.size !== upstream.discreteMatchers.length) throw new Error("Duplicate llmfit hardware matcher");

  const profiles = index(profileRows.map((profile) => {
    const id = profile.profile_id;
    const inventoryRow = inventoryProfiles.get(id);
    if (!inventoryRow || !mappedProfiles.has(id) || inventoryRow.name !== profile.title || inventoryRow.source !== `${researchBase}/hardware-profiles/${id}.md`) {
      throw new Error(`Unreconciled research hardware profile: ${id}`);
    }
    return { ...profile, ...inventoryRow };
  }));
  if (profiles.size !== inventoryProfiles.size || profiles.size !== mappedProfiles.size) throw new Error("Hardware research inventory counts disagree");

  const researchVideoByProfile = reviewedResearchVideos(researchVideos, profiles);
  const withdrawnProfiles = new Set([...profiles.values()].filter(({ id, source_url, source }) =>
    [id, source_url, source].some(isWithdrawn)).map(({ id }) => id));
  const withdrawnCards = new Set();
  const cards = index([...inventory.cards, ...variants].flatMap((record) => {
    const metadata = { ...record, ...cardMetadata[record.id] };
    const matcher = matchers.get(record.id);
    const sourceProfile = /\/hardware-profiles\/([^/]+)\.md$/.exec(record.source ?? "")?.[1];
    const profileIds = unique([sourceProfile, ...(metadata.profiles ?? [])]);
    const allowedIds = profileIds.filter((id) => !withdrawnProfiles.has(id));
    const associatedProfiles = allowedIds.map((id) => {
      if (!profiles.has(id)) throw new Error(`Unknown card provenance profile: ${id}`);
      return { id, source: profiles.get(id).source };
    });
    const source = matcher?.source ?? associatedProfiles[0]?.source;
    if (!source && profileIds.length && !allowedIds.length) {
      withdrawnCards.add(record.id);
      return [];
    }
    if (!source) throw new Error(`Unreconciled hardware source: ${record.id}`);
    const brand = /^(amd|intel|nvidia)-/.exec(record.id)?.[1];
    const manufacturer = { amd: "AMD", intel: "Intel", nvidia: "NVIDIA" }[brand];
    return [{
      id: record.id,
      name: metadata.name,
      source,
      detail: record.detail ?? metadata.variant,
      manufacturer: metadata.manufacturer ?? manufacturer ?? "Unresolved",
      kind: ["amd-instinct-mi300", "t10-unresolved"].includes(record.id)
        ? "Unresolved family reference" : "Component reference",
      aliases: unique([...(metadata.aliases ?? []), matcher?.alias, ...allowedIds.map((id) => (
        id === "V019-HP-TEST" ? null : fact(profiles.get(id).gpu)
      ))]),
      lookupSource: matcher?.source ?? null,
      variant: metadata.variant ?? "Exact board revision unavailable",
      memory: metadata.memory ?? null,
      vendorSpec: vendorSpec(record.id),
      parent: metadata.parent ?? null,
      relatedProfiles: associatedProfiles,
      // Only explicit source/variant links can narrow a family reference to a specific board.
      explicitProfiles: (metadata.profiles ?? []).filter((id) => !withdrawnProfiles.has(id)),
      resolveShortAliases: metadata.resolveShortAliases ?? true,
    }];
  }));
  if ([...matchers.keys()].some((id) => !cards.has(id))) throw new Error("Missing eligible llmfit card matcher");
  for (const { id, name, manufacturer, variant, source, parent = null } of additions.cards) {
    if (isWithdrawn(source) || isWithdrawn(id)) {
      withdrawnCards.add(id);
      continue;
    }
    if (cards.has(id)) throw new Error(`Already cataloged GPU: ${id}`);
    const spec = vendorSpec(id);
    if (!spec || spec.source !== source) throw new Error(`Missing manufacturer specification for GPU: ${id}`);
    cards.set(id, {
      id, name, manufacturer, variant, source, detail: variant, kind: "Component reference",
      aliases: [], lookupSource: null, memory: null, parent,
      relatedProfiles: [], explicitProfiles: [],
      vendorSpec: spec,
    });
  }
  for (const { id, name, manufacturer, parent = null, ...modification } of index(modified.cards).values()) {
    const existing = cards.get(id);
    const primary = modification.evidence[0];
    if (isWithdrawn(id) || isWithdrawn(primary.source) || withdrawnCards.has(id)) {
      cards.delete(id);
      withdrawnCards.add(id);
      continue;
    }
    if (existing?.vendorSpec || (!existing && (!name || !(parent || manufacturer)))) {
      throw new Error(`Invalid identity for memory-modified GPU: ${id}`);
    }
    const capacity = modification.capacityGb == null ? "" : ` · ${modification.capacityGb} GB`;
    const detail = `Memory-modified GPU${capacity} · ${primary.kind}`;
    cards.set(id, {
      ...(existing ?? {
        id, name, parent, manufacturer: manufacturer ?? cards.get(parent)?.manufacturer,
        variant: detail, source: primary.source, kind: "Component reference", aliases: [],
        lookupSource: null, memory: null, relatedProfiles: [], explicitProfiles: [], vendorSpec: null,
      }),
      detail,
      modification: {
        ...modification,
        evidence: modification.evidence.filter(({ source }) => !isWithdrawn(source)),
      },
    });
  }
  let previousCardCount;
  do {
    previousCardCount = cards.size;
    for (const { id, parent } of cards.values()) {
      if (withdrawnCards.has(parent)) {
        cards.delete(id);
        withdrawnCards.add(id);
      }
    }
  } while (cards.size < previousCardCount);
  for (const { parent } of cards.values()) {
    if (parent && !cards.has(parent)) throw new Error(`Unknown card family: ${parent}`);
  }

  const names = new Map();
  for (const card of cards.values()) {
    if (card.parent) continue;
    const short = card.name.replace(/^(NVIDIA (?:GeForce |Tesla )?|AMD (?:Radeon |Instinct )?|Intel )/, "");
    for (const name of [card.name, ...(card.resolveShortAliases ? [short, ...card.aliases] : [])]) {
      const alias = key(name);
      const existing = names.get(alias);
      names.set(alias, !names.has(alias) || existing === card.id ? card.id : null);
    }
  }
  const machines = [...profiles.values()].filter(({ id }) => !withdrawnProfiles.has(id)).map((profile) => {
    const { id, name, source, source_url, linked_observation_ids } = profile;
    const kind = profileKind(profile);
    const explicit = [...cards.values()].filter((card) => card.explicitProfiles.includes(id));
    const cardIds = profileCards[id] ?? (explicit.length
      ? explicit.map((card) => card.id)
      : unique([names.get(key(profile.gpu))]));
    if (!withdrawnProfiles.size && cardIds.some(id => !cards.has(id) && !withdrawnCards.has(id))) {
      throw new Error(`Unknown card in machine: ${id}`);
    }
    const video = researchVideoByProfile.get(id);
    return {
      id, name, source, kind, cardIds: cardIds.filter((id) => cards.has(id)),
      detail: kind === "Component reference" ? kind : `${kind} / ${profile.core_fields_reported} of ${profile.core_fields_total} build fields reported`,
      capture: source_url,
      ...(video && { video }),
      coreFieldsReported: profile.core_fields_reported,
      coreFieldsTotal: profile.core_fields_total,
      missingCoreFields: profile.missing_core_fields,
      sourceMemory: [fact(profile.ram), fact(profile.vram_per_gpu)].filter(Boolean),
      memory: researchMemory(profile, mappedProfiles.get(id)?.native, memoryNotes[id]),
      interconnect: fact(profile.interconnect),
      associations: linked_observation_ids.length,
      bom: profile.bom.map((row) => ({
        category: row.category,
        part: fact(row.exact_part_model),
        quantity: fact(row.quantity),
        source: row.source_url,
      })),
    };
  });
  const presets = upstream.presets.map((preset) => ({
    id: preset.id,
    name: preset.name,
    source: upstreamLink(upstream.commit, preset.path),
    kind: "llmfit example preset",
    detail: "llmfit example preset",
    cardIds: unique([names.get(key(preset.gpu))]),
    memory: {
      system: `${preset.memoryGb} GB ${preset.unified ? "unified memory" : "system RAM"}`,
      perDevice: null,
      aggregate: null,
      allocation: null,
    },
    gpu: preset.gpu,
  }));
  const associations = machines.reduce((count, row) => count + row.associations, 0);
  const componentReferences = machines.filter((row) => row.kind === "Component reference").length;
  const upstreamOnly = [...cards.values()].filter((card) => card.lookupSource && !card.relatedProfiles.length).length;
  const researchOnly = [...cards.values()].filter(row => !row.lookupSource && row.relatedProfiles.length).length;
  const manufacturerMachines = additions.machines.filter(({ id, source, cardIds, bom = [], documentedPower }) =>
    // A factory build needs all of its component and configuration evidence.
    cardIds.every(card => cards.has(card)) &&
    ![id, source, ...bom.map(part => part.source), documentedPower?.source].some(isWithdrawn))
    .map(({ gallery, ...machine }) => ({
      ...machine, ...(gallery && !isWithdrawn(gallery.source) ? { gallery } : {}),
    }));
  const creatorBuilds = reviewedMachineRows(builds, cards, withdrawnCards, isWithdrawn);
  const knownBuilds = new Map([...builds, ...additions.machines].map(row => [row.id, row]));
  for (const [id, ids] of Object.entries(photoIds)) {
    const known = knownBuilds.get(id);
    if (!known || new Set(ids).size !== ids.length || ids.length + Number(Boolean(known.video)) > 3 ||
        ids.some(photoId => !Object.hasOwn(photos, photoId))) {
      throw new Error("Invalid machine photos: " + id);
    }
  }
  const machineRows = [...creatorBuilds, ...machines, ...presets, ...manufacturerMachines].map(({ video, ...row }) => {
    const gallery = (photoIds[row.id] ?? []).map(id => photos[id])
      .filter(photo => !isWithdrawn(photo.source));
    const published = video && publicMachineVideo({ video, buildSource: row.buildSource }, isWithdrawn);
    return { ...row, ...(gallery.length && { photos: gallery }), ...(published && { video: published }) };
  });
  const cardPhotos = new Map();
  for (const [cardId, { topology, photos: ids = [] }] of Object.entries(gpuPhotoIds)) {
    const photoSources = new Set();
    const photoDigests = new Set();
    if (!cards.has(cardId) && !withdrawnCards.has(cardId)) throw new Error("Unknown GPU for photo gallery: " + cardId);
    const gallery = [...(topology ? [topology] : []), ...ids].map(id => {
      const photo = gpuPhotos[id];
      if (!photo || photoSources.has(photo.source) || photoDigests.has(photo.sha256)) {
        throw new Error("Missing or duplicate GPU photo: " + cardId + " · " + id);
      }
      photoSources.add(photo.source);
      photoDigests.add(photo.sha256);
      return photo;
    }).filter(photo => !isWithdrawn(photo.source));
    if (gallery.length) cardPhotos.set(cardId, gallery);
  }
  const catalog = {
    cards: [...cards.values()].map(({ explicitProfiles, resolveShortAliases, ...card }) => ({
      ...card,
      ...(cardPhotos.has(card.id) && { photos: cardPhotos.get(card.id) }),
      variants: [...cards.values()].filter((entry) => entry.parent === card.id).map(({ id, name }) => ({ id, name })),
      relatedMachines: machineRows.filter(machine => machine.kind !== "Component reference" && machine.cardIds.includes(card.id))
        .map(({ id, name }) => ({ id, name })),
    })).sort((a, b) => a.id.localeCompare(b.id, "en")),
    machines: machineRows,
  };
  index(catalog.machines);

  const manifest = {
    asOf: reviewedAt > inventoryAsOf ? reviewedAt : inventoryAsOf,
    scope: "Pinned llmfit discrete memory-bandwidth lookup, its three HardwareProfile examples, the retained research hardware inventory, selected manufacturer and board-partner product records, source-backed aftermarket memory modifications, and reviewed creator build disclosures. Integrated GPU lookup aliases do not identify a graphics card or a complete machine. Benchmark values and community caches are outside this snapshot.",
    upstream: {
      commit: upstream.commit,
      commitDate: upstream.commitDate,
      lookup: lookupSource,
      lookupSha256: upstream.lookupSha256,
      presets: upstream.presets.map(({ path, sha256 }) => ({ source: upstreamLink(upstream.commit, path), sha256 })),
    },
    research: withdrawnProfiles.size ? { visibility: "rights-filtered" } : {
      commit: research.commit,
      profiles: `${researchBase}/hardware-profiles.json`,
      profilesSha256: research.profilesSha256,
      nativeProfiles: `${researchBase}/llmfit/research/hardware.json`,
      nativeProfilesSha256: research.nativeProfilesSha256,
    },
    vendorSpecs: {
      capturedAt: vendor.capturedAt, sha256: sha256(specBytes),
      additionsCapturedAt: additions.capturedAt, additionsSha256: sha256(additionsBytes),
      referenceCheckedOn: references.checkedOn, referenceSha256: sha256(referenceBytes),
    },
    modifiedGpus: { reviewedAt: modified.reviewedAt, sha256: sha256(modifiedBytes) },
    creatorBuilds: {
      reviewedAt, sha256: sha256(buildBytes),
      sourcesByPlatform: Object.fromEntries(Object.entries(Object.groupBy(creatorBuilds, row => row.buildSource.platform))
        .map(([platform, rows]) => [platform, rows.length])),
    },
    coverage: {
      cards: catalog.cards.length,
      memoryModifiedCards: catalog.cards.filter(card => card.modification).length,
      memoryModifiedWithSellerEvidence: catalog.cards.filter(card => card.modification?.evidence.some(
        ({ kind }) => kind === "Seller listing" || kind === "Seller service"
      )).length,
      cardsWithVendorSpecs: catalog.cards.filter(card => card.vendorSpec).length,
      cardsWithSpecificVendorSpecs: catalog.cards.filter(card => card.vendorSpec &&
        card.vendorSpec.scope !== "Multiple manufacturer configurations").length,
      cardsWithPhotos: catalog.cards.filter(card => card.photos?.length).length,
      cardsWithProductImageLinks: catalog.cards.filter(card => card.vendorSpec?.gallery).length,
      boardPartnerCards: catalog.cards.filter(card => card.vendorSpec?.scope === "Board-partner SKU").length,
      llmfitDiscreteMatchers: matchers.size,
      upstreamOnlyCards: upstreamOnly,
      researchOnlyCards: researchOnly,
      cardsWithBothSources: [...cards.values()].filter(row => row.lookupSource && row.relatedProfiles.length).length,
      manufacturerOnlyCards: [...cards.values()].filter(row => !row.lookupSource && !row.relatedProfiles.length && !row.modification).length,
      unresolvedCardReferences: catalog.cards.filter(({ kind }) => kind === "Unresolved family reference").length,
      researchProfiles: machines.length,
      researchComponentReferences: componentReferences,
      partialMachines: machines.length - componentReferences,
      partialMachinesWithSourceVideo: machineRows.filter(row => row.kind === "Partial configuration" && row.video).length,
      upstreamPresets: presets.length,
      manufacturerMachines: manufacturerMachines.length,
      creatorBuilds: creatorBuilds.length,
      completeBuilds: catalog.machines.filter(({ kind }) => kind === "Complete factory configuration").length,
      profilesWithCreatorReports: machines.filter((row) => row.associations > 0).length,
      profilesWithoutCreatorReports: machines.filter((row) => row.associations === 0).length,
      creatorReportedAssociations: associations,
      researchProfilesWithoutDiscreteCardLink: machines.filter((row) => !row.cardIds.length).length,
      reviewedMeasuredProfiles: 0,
      untestedProfiles: catalog.machines.length,
    },
  };
  return { catalog, manifest, digest: sha256(JSON.stringify({ catalog, manifest })) };
}
