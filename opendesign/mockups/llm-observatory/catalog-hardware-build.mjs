import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { join } from "node:path";

const sha256 = (bytes) => createHash("sha256").update(bytes).digest("hex");
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

export async function readHardwareCatalog(directory, isWithdrawn = () => false) {
  const [inventoryBytes, mappingsBytes, profileBytes, nativeBytes, specBytes, additionsBytes] = await Promise.all([
    readFile(join(directory, "catalog-hardware.json")),
    readFile(join(directory, "catalog-hardware-sources.json")),
    readFile(join(directory, "../../..", seedPath, "hardware-profiles.json")),
    readFile(join(directory, "../../..", seedPath, "llmfit/research/hardware.json")),
    readFile(join(directory, "gpu-vendor-specs.json")),
    readFile(join(directory, "catalog-source-additions.json")),
  ]);
  const inventory = JSON.parse(inventoryBytes);
  const { asOf, upstream, research, variants, cardMetadata, profileCards, memoryNotes } = JSON.parse(mappingsBytes);
  const vendor = JSON.parse(specBytes);
  const additions = JSON.parse(additionsBytes);
  const vendorSpec = (id) => {
    const source = [additions.specs[id], vendor.cards[id]].find(spec => spec && !isWithdrawn(spec.source));
    if (!source) return null;
    const { gallery, ...spec } = source;
    const scope = spec.scope ?? (/\/|\bor\b/.test(spec.facts["Memory configuration"] ?? "")
      ? "Multiple manufacturer configurations" : "Manufacturer product reference");
    return {
      capturedAt: source === additions.specs[id] ? additions.capturedAt : vendor.capturedAt,
      locator: `Manufacturer comparison table · ${spec.designation}`,
      ...spec, scope,
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
    if (!withdrawnProfiles.size && cardIds.some((id) => !cards.has(id))) throw new Error(`Unknown card in machine: ${id}`);
    return {
      id, name, source, kind, cardIds: cardIds.filter((id) => cards.has(id)),
      detail: kind === "Component reference" ? kind : `${kind} / ${profile.core_fields_reported} of ${profile.core_fields_total} build fields reported`,
      capture: source_url,
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
  const machineRows = [...machines, ...presets, ...manufacturerMachines];
  const catalog = {
    cards: [...cards.values()].map(({ explicitProfiles, resolveShortAliases, ...card }) => ({
      ...card,
      variants: [...cards.values()].filter((entry) => entry.parent === card.id).map(({ id, name }) => ({ id, name })),
      relatedMachines: machineRows.filter(machine => machine.kind !== "Component reference" && machine.cardIds.includes(card.id))
        .map(({ id, name }) => ({ id, name })),
    })).sort((a, b) => a.id.localeCompare(b.id, "en")),
    machines: machineRows,
  };
  index(catalog.machines);

  const manifest = {
    asOf,
    scope: "Pinned llmfit discrete memory-bandwidth lookup, its three HardwareProfile examples, the retained research hardware inventory, and selected manufacturer and board-partner product records. Integrated GPU lookup aliases do not identify a graphics card or a complete machine. Benchmark values and community caches are outside this snapshot.",
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
    },
    coverage: {
      cards: catalog.cards.length,
      cardsWithVendorSpecs: catalog.cards.filter(card => card.vendorSpec).length,
      cardsWithSpecificVendorSpecs: catalog.cards.filter(card => card.vendorSpec &&
        card.vendorSpec.scope !== "Multiple manufacturer configurations").length,
      cardsWithProductImageLinks: catalog.cards.filter(card => card.vendorSpec?.gallery).length,
      boardPartnerCards: catalog.cards.filter(card => card.vendorSpec?.scope === "Board-partner SKU").length,
      llmfitDiscreteMatchers: matchers.size,
      upstreamOnlyCards: upstreamOnly,
      researchOnlyCards: researchOnly,
      cardsWithBothSources: [...cards.values()].filter(row => row.lookupSource && row.relatedProfiles.length).length,
      manufacturerOnlyCards: [...cards.values()].filter(row => !row.lookupSource && !row.relatedProfiles.length).length,
      unresolvedCardReferences: catalog.cards.filter(({ kind }) => kind === "Unresolved family reference").length,
      researchProfiles: machines.length,
      researchComponentReferences: componentReferences,
      partialMachines: machines.length - componentReferences,
      upstreamPresets: presets.length,
      manufacturerMachines: manufacturerMachines.length,
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
