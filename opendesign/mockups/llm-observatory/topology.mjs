import previewReports from "./catalog-topology.json" with { type: "json" };
import hardwareSources from "./catalog-hardware-sources.json" with { type: "json" };
import identities from "./catalog-identities.json" with { type: "json" };

export const topologyReports = typeof __FASTEST_TOPOLOGY_REPORTS__ === "undefined"
  ? previewReports
  : __FASTEST_TOPOLOGY_REPORTS__;

export function selectTopologyPresets(reports) {
  return [
  ["One card", "V005-HP-TEST"],
  ["Two cards", "V021-HP-C001"],
  ["Four cards", "V028-HP-E03"],
  ["Mixed cards", "V007-HP-E01"],
].map(([label, id]) => ({ label, report: reports.find((row) => row.id === id) }))
    .filter(({ report }) => report);
}

export const topologyPresets = selectTopologyPresets(topologyReports);

export const inferenceStages = [
  { title: "Load the model", note: "The host prepares weights, cache and workspace for the devices selected by the runtime." },
  { title: "Decode a token", note: "Each active device has its own memory. A split workload may need data exchange, depending on placement and runtime support." },
  { title: "Return output", note: "The runtime returns generated tokens to the client after the required computation and synchronization." },
];

const fitProfile = hardwareSources.upstream.presets.find(({ id }) => id === "llmfit-nvidia-rtx-4090");
const fitArtifact = identities["Qwen/Qwen2.5-0.5B-Instruct"].artifacts.find(({ quantization }) => quantization === "Q8_0");
const fitCard = "nvidia-geforce-rtx-4090";
const fitInputs = Object.freeze({
  machine: fitProfile.id,
  artifact: fitArtifact.sha256,
  runtime: "llama.cpp",
  context: "4096",
  ram_reserved_gib: "8",
  vram_reserved_gib: "2",
});
export const fitScenario = {
  id: "fit-example",
  scope: "example",
  name: "llmfit test host with an alternate GPU",
  group: "single",
  count: 1,
  source: `https://github.com/AlexsJones/llmfit/blob/${hardwareSources.upstream.commit}/${fitProfile.path}`,
  devices: [{ label: "RTX 3060 12 GB", card: "nvidia-geforce-rtx-3060-12gb", photo: "rtx-3060", memory: "12 GB" }],
  hostModel: `${fitProfile.memoryGb} GB system RAM (llmfit example assumptions)`,
};

const photosByCard = {
  "nvidia-geforce-rtx-4090": "rtx-4090",
  "nvidia-geforce-rtx-3090": "rtx-3090",
  "nvidia-geforce-rtx-3060": "rtx-3060",
  "nvidia-geforce-rtx-3060-12gb": "rtx-3060",
  "intel-arc-b580": "arc-b580",
};

export function cardPhotoExample(photo, cards) {
  if (!photo) return undefined;
  const card = cards.find(({ id }) => photosByCard[id] === photo);
  return card && {
    id: photo,
    scope: "example",
    name: `${card.name} component example`,
    group: "single",
    count: 1,
    source: card.source,
    devices: [{ label: card.name, card: card.id, memory: card.memory, photo }],
  };
}

export function topologyView(report, replacements = {}) {
  const isHost = report.group === "hosts";
  const draft = Object.keys(replacements).length > 0;
  const partName = isHost ? "Host" : "Card";
  const reportedMemory = /^(\d+)\s*GB(?:\s*each)?$/i.exec(report.memory ?? "")?.[1];
  const sourceParts = isHost
    ? Array.from({ length: report.hostCount }, () => ({ label: report.hostModel }))
    : report.devices;
  const parts = sourceParts.map((part, index) => {
    const slot = index + 1;
    const replacement = replacements[slot];
    if (!replacement) return {
      ...part, slot, memory: part.memory ?? (reportedMemory ? `${reportedMemory} GB` : null), placement: draft ? null : part.placement ?? null,
    };
    return {
      slot, card: replacement.id, label: replacement.name,
      memory: replacement.memory ?? (report === fitScenario && replacement.id === fitCard ? "24 GB (llmfit example)" : null),
      photo: photosByCard[replacement.id], placement: null,
    };
  });
  const activeCount = draft ? null : report.activeCount ?? null;
  return {
    report, parts, partName, draft, isHost, activeCount,
    installedCount: isHost ? null : report.count,
    links: (report.links ?? []).filter(({ slots }) => slots.every((slot) => !replacements[slot])),
    connection: draft ? null : report.connection,
    mixed: !isHost && (new Set(parts.map(({ label }) => label)).size > 1
      || new Set(parts.map(({ memory }) => memory).filter(Boolean)).size > 1),
  };
}

export function draftFitRequest(view) {
  if (!view.draft || view.report !== fitScenario || view.parts[0]?.card !== fitCard) return null;
  return fitInputs;
}

export function draftFitEstimate(result, request) {
  const { artifact, runtime, machine, assumptions, engine, estimate } = result ?? {};
  if (result?.kind !== "fit_estimate" || result.status !== "estimated" || !estimate
      || machine?.id !== request.machine || artifact?.sha256 !== request.artifact || runtime?.id !== request.runtime
      || assumptions?.context_tokens !== Number(request.context)
      || assumptions?.ram_reserved_gib !== Number(request.ram_reserved_gib)
      || assumptions?.vram_reserved_gib !== Number(request.vram_reserved_gib)
      || engine?.revision !== hardwareSources.upstream.commit || estimate.quantization !== fitArtifact.quantization
      || !Number.isFinite(estimate.memory_required_gib) || !Number.isFinite(estimate.memory_available_gib)) return null;
  return estimate;
}

export function fitArtifactLabel() {
  return `${fitArtifact.path} · 4,096 tokens · 8 GiB reserved RAM · 2 GiB reserved VRAM`;
}
