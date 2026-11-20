import React, { useEffect, useId, useState } from "react";
import { ArrowUpRight, CircuitBoard, Cpu, Monitor, Pause, Play, StepForward, Terminal } from "lucide-react";
import { catalogPath } from "./catalog-paths.mjs";
import { cardPhotoExample, draftFitEstimate, draftFitRequest, fitArtifactLabel, fitScenario, inferenceStages, scalingReportUrl, scalingUnavailable, topologyPresets, topologyReports as reports, topologyView } from "./topology.mjs";

const hardware = __FASTEST_HARDWARE_DIRECTORY__;
const catalogRelease = __FASTEST_CATALOG_RELEASE__;
const replaceable = [
  "nvidia-geforce-rtx-4090", "nvidia-geforce-rtx-3090", "nvidia-geforce-rtx-3060-12gb",
  "nvidia-geforce-rtx-5060-ti-16gb", "amd-radeon-instinct-mi50-32gb", "intel-arc-b580",
].map((id) => hardware.cards.find((card) => card.id === id)).filter(Boolean);

function catalogLink(kind, record) {
  return record && (catalogRelease ? "/" + catalogPath(catalogRelease, kind, record.id) : record.source);
}

function DiagramNode({ selection, name, label, detail, active, icon: Icon, selected, onSelect }) {
  return <button type="button" className="tech-node" data-active={active} aria-pressed={selected === selection}
    onClick={() => onSelect(selection)}>
    <Icon size={19} aria-hidden="true" />
    <span><strong>{name}</strong><small>{label}</small>{detail && <small>{detail}</small>}</span>
  </button>;
}

function DiagramBoard({ view, step, selected, onSelect, playing }) {
  const selection = { selected, onSelect };
  return <div className="tech-board" data-playing={playing} aria-label="Topology diagram">
    <div className="tech-board-endpoints">
      <DiagramNode {...selection} selection="host" name={view.isHost ? "Coordination" : "Host system"}
        label={view.isHost ? "Runtime placement unknown" : view.report.hostModel ?? "Host parts not reported"}
        icon={Cpu} active={step === 0} />
      <DiagramNode {...selection} selection="client" name="Client" label="Generated tokens" icon={Terminal} active={step === 2} />
    </div>
    <div className="tech-board-slots">
      {view.parts.map((part) => <DiagramNode key={part.slot} {...selection} selection={part.slot}
        name={`${view.partName} ${part.slot}`} label={part.label} detail={view.isHost ? null : part.memory ?? "VRAM unknown"}
        icon={view.isHost ? Monitor : CircuitBoard} active={step === 1} />)}
    </div>
    {view.links.length > 0 && <ul className="tech-links" aria-label="Documented connections">
      {view.links.map(({ label, slots, state, source }) => <li key={label} data-state={state}>
        <a href={source} target="_blank" rel="noreferrer">{view.partName} {slots.join(" ↔ ")} · {label} <ArrowUpRight size={13} aria-hidden="true" /></a>
      </li>)}
    </ul>}
    <p className="tech-board-caption">{view.isHost ? "Host transport" : "Inter-card links"} · {view.connection ?? (view.installedCount === 1 ? "Single-card layout" : "Unknown")}</p>
    {!view.draft && view.report.note && <p className="tech-board-caption">{view.report.note}</p>}
  </div>;
}

function ComponentInspector({ view, selected, images, onSelect, changePart, replacements }) {
  const part = view.parts.find(({ slot }) => slot === selected);
  const card = hardware.cards.find(({ id }) => id === part?.card);
  const source = catalogLink("cards", card);
  const name = part ? `${view.partName} ${part.slot} · ${part.label}` : selected === "host" ? "Host system" : "Client";
  const description = part ? (view.isHost ? "Accelerator inventory and workload placement within this host are unknown."
    : `${part.memory ?? "Unknown VRAM"}. ${part.placement ?? "Runtime placement unknown."}`)
    : selected === "host" ? "The host loads the model and coordinates device placement." : "The requesting client receives generated tokens.";
  return <aside className="tech-inspect" aria-label="Component inspection">
    <div className="tech-inspect-body" aria-live="polite">
      <h3>{name}</h3>
      <p>{description}</p>
      {source && <p><a href={source}>Card catalog and sources <ArrowUpRight size={13} aria-hidden="true" /></a></p>}
      <p><a href={__FASTEST_PAGES__ ? "/wiki/gpu-topology/" : "#wiki/gpu-topology"}>Read the topology guide</a></p>
    </div>
    <div className="tech-photos" aria-label="Component photo hotspots">
      {view.parts.map((item) => {
        const photo = images[item.photo];
        return <figure className="tech-photo" key={item.slot}>
          <button type="button" aria-label={`Select photo for ${view.partName.toLowerCase()} ${item.slot}`} aria-pressed={selected === item.slot}
            onClick={() => onSelect(item.slot)}>
            {photo ? <img src={photo.data} alt={photo.alt} loading="lazy" />
              : <div className="tech-photo-placeholder">{view.isHost ? <Monitor size={20} aria-hidden="true" /> : <CircuitBoard size={20} aria-hidden="true" />}<span>Photo unavailable</span></div>}
            <span>{view.partName} {item.slot}</span>
          </button>
          {photo && <figcaption>Representative · <a href={photo.source} target="_blank" rel="noreferrer">{photo.author}</a> · <a href={photo.licenseUrl} target="_blank" rel="noreferrer">{photo.license}</a> · resized</figcaption>}
        </figure>;
      })}
    </div>
    {part && !view.isHost && <label className="tech-swap">
      <span>Substitute {view.partName.toLowerCase()} {part.slot}</span>
      <select value={replacements[part.slot]?.id ?? ""} onChange={(event) => changePart(part.slot, event.target.value)}>
        <option value="">Original · {view.report.devices[part.slot - 1].label}</option>
        {replaceable.filter(({ id }) => id !== view.report.devices[part.slot - 1].card)
          .map(({ id, name }) => <option key={id} value={id}>{name}</option>)}
      </select>
    </label>}
  </aside>;
}

function Inventory({ view, sourceLink }) {
  return <details className="tech-inventory">
    <summary>Static topology and inference steps</summary>
    <div className="table-wrap"><table>
      <caption>{view.report.id} · {view.draft ? "Draft inventory" : "Reference inventory"}</caption>
      <thead><tr><th scope="col">Component</th><th scope="col">Identity</th><th scope="col">VRAM</th><th scope="col">Runtime placement</th></tr></thead>
      <tbody>{view.parts.map((part) => <tr key={part.slot}>
        <th scope="row">{view.partName} {part.slot}</th><td>{part.label}</td><td>{part.memory ?? "Unknown"}</td><td>{part.placement ?? "Unknown"}</td>
      </tr>)}</tbody>
    </table></div>
    <p>{view.links.length ? view.links.map(({ label, slots }) => `${label} (${view.partName.toLowerCase()} ${slots.join(" ↔ ")})`).join("; ")
      : view.installedCount === 1 ? "No inter-card link in the single-card layout." : "Link endpoints unknown."} Measured transport is unavailable in this view.</p>
    {!view.draft && view.report.note && <p>{view.report.note}</p>}
    <ol>{inferenceStages.map(({ title, note }) => <li key={title}><strong>{title}.</strong> {note}</li>)}</ol>
    <p><a href={sourceLink}>Original configuration and source records</a></p>
  </details>;
}

function DraftFit({ request }) {
  const [result, setResult] = useState({ state: "pending" });
  const query = new URLSearchParams(request).toString();
  useEffect(() => {
    const controller = new AbortController();
    fetch(`/fit.json?${query}`, { signal: controller.signal, headers: { Accept: "application/json" } })
      .then((response) => {
        if (!response.ok) throw new Error("Fit service unavailable");
        return response.json();
      })
      .then((payload) => {
        const estimate = draftFitEstimate(payload, request);
        if (!controller.signal.aborted) setResult(estimate ? { state: "estimated", estimate } : { state: "ineligible" });
      })
      .catch(() => { if (!controller.signal.aborted) setResult({ state: "unavailable" }); });
    return () => controller.abort();
  }, [query, request]);
  let output = "Checking the pinned fit service…";
  if (result.state === "estimated") {
    const { fit_level: level, run_mode: mode, memory_required_gib: required, memory_available_gib: available } = result.estimate;
    output = <>{level} · {mode} · {required.toFixed(2)} GiB required / {available.toFixed(2)} GiB available. <a href={`/fit.json?${query}`}>Estimate and sources</a></>;
  }
  if (result.state === "unavailable") output = "Unknown · pinned fit service unavailable on this deployment.";
  if (result.state === "ineligible") output = <>Unknown · no eligible estimate for these inputs. <a href={`${__FASTEST_RELEASE_ORIGIN__ ?? ""}/fit?${query}`}>See fit details</a>.</>;
  return <><span role="status">{output}</span><small>{fitArtifactLabel()}. This estimate uses the llmfit example host assumptions.</small></>;
}

function TopologySession({ report, images }) {
  const [selected, setSelected] = useState(1);
  const [replacements, setReplacements] = useState({});
  const [step, setStep] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(() => window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  const view = topologyView(report, replacements);
  const request = draftFitRequest(view);
  const inventoryScope = view.draft ? "planned" : report.scope === "example" ? "modeled" : "installed";
  const reference = catalogLink("machines", hardware.machines.find(({ id }) => id === report.id)) ?? report.source;
  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    function preferenceChanged(event) {
      setReducedMotion(event.matches);
      if (event.matches) setPlaying(false);
    }
    media.addEventListener("change", preferenceChanged);
    return () => media.removeEventListener("change", preferenceChanged);
  }, []);
  useEffect(() => {
    if (!playing || reducedMotion) return undefined;
    const timer = window.setTimeout(() => {
      if (step === inferenceStages.length - 1) setPlaying(false);
      else setStep(step + 1);
    }, 2250);
    return () => window.clearTimeout(timer);
  }, [playing, reducedMotion, step]);

  function goTo(next) {
    setStep(next);
    setPlaying(false);
  }

  function changePart(slot, id) {
    setReplacements((previous) => {
      const next = { ...previous };
      if (id) next[slot] = replaceable.find((card) => card.id === id);
      else delete next[slot];
      return next;
    });
    goTo(0);
  }

  return <>
    <div className="tech-meta">
      <div><strong>{view.draft ? "Draft build" : report.scope === "example" ? "Example scenario" : "Source-reported setup"}</strong> · <a href={reference}>{report.id}</a></div>
      <div>{view.isHost ? `${view.parts.length} hosts · accelerator counts unknown` : <>{view.installedCount} {inventoryScope} {view.installedCount === 1 ? "card" : "cards"} · Active cards {view.activeCount ?? "unknown"}</>}{view.mixed && " · Mixed devices · separate VRAM per card"}</div>
    </div>
    <div className="tech-grid">
      <div className="tech-flow">
        <DiagramBoard view={view} step={step} selected={selected} onSelect={setSelected} playing={playing} />
        <ol className="tech-steps" aria-label="Conceptual inference stages">
          {inferenceStages.map(({ title }, index) => <li key={title}>
            <button type="button" aria-current={step === index ? "step" : undefined} onClick={() => goTo(index)}>{title}</button>
          </li>)}
        </ol>
        <div className="tech-step-notes">
          <p aria-live={playing ? "off" : "polite"}>{inferenceStages[step].note}</p>
          <div className="tech-playbar" aria-label="Playback controls">
            <button type="button" className="btn outline" disabled={reducedMotion} onClick={() => {
              if (!playing && step === inferenceStages.length - 1) setStep(0);
              setPlaying(!playing);
            }}>{playing ? <Pause size={15} aria-hidden="true" /> : <Play size={15} aria-hidden="true" />}{playing ? "Pause" : "Play"}</button>
            <button type="button" className="btn outline" onClick={() => goTo((step + 1) % inferenceStages.length)}><StepForward size={15} aria-hidden="true" />Next step</button>
          </div>
          {reducedMotion && <p>Reduced motion is on. Use Next step or select a stage.</p>}
        </div>
        <p className="tech-disclaimer">Stage highlights illustrate inference. Physical links, runtime placement and measured transport depend on the source.</p>
      </div>
      <ComponentInspector view={view} selected={selected} onSelect={setSelected} images={images} changePart={changePart} replacements={replacements} />
    </div>
    {view.draft && <section className="tech-draft" aria-label="Draft fit and price">
      <h3>Draft fit and price</h3>
      <dl>
        <div><dt>Model fit</dt><dd>{request && (!__FASTEST_PAGES__ || __FASTEST_RELEASE_ORIGIN__) ? <DraftFit key={JSON.stringify(request)} request={request} />
          : request ? "Unknown · pinned fit service unavailable on this deployment."
            : "Unknown · this draft configuration has no matching native fit profile."}</dd></div>
        <div><dt>Whole-build price</dt><dd>Unknown · the draft lacks a complete parts list and a matching reviewed regional quote.</dd></div>
        <div><dt>Benchmark runs</dt><dd><a href={report.source}>{report.scope === "example" ? "Original scenario assumptions" : "Original profile and runs for reference"}</a>. The draft requires a new run.</dd></div>
      </dl>
      <button type="button" className="btn outline" onClick={() => { setReplacements({}); goTo(0); }}>Reset draft</button>
    </section>}
    <Inventory view={view} sourceLink={reference} />
  </>;
}

export function TechnologyDiagram({ images = {}, focus, options }) {
  const id = useId();
  const sourceChoices = options ?? [...reports, fitScenario];
  const matchesPhoto = ({ devices }) => devices.some(({ photo }) => photo && photo === focus);
  const source = sourceChoices.find(({ id }) => id.toLowerCase() === focus?.toLowerCase())
    ?? sourceChoices.find((row) => row.count === 1 && matchesPhoto(row))
    ?? sourceChoices.find(matchesPhoto);
  const example = !options && !source && cardPhotoExample(focus, hardware.cards);
  const choices = example ? [...sourceChoices, example] : sourceChoices;
  const initial = source || example || (options ? choices[0] : topologyPresets[0]?.report || fitScenario);
  const [profile, setProfile] = useState(initial.id);
  const report = choices.find((row) => row.id === profile) ?? initial;
  return <section className="tech-lab" aria-labelledby={id + "-title"}>
    <header className="tech-header">
      <div>
        <h2 id={id + "-title"}>Explore the build topology</h2>
        <p>Inspect the installed hardware and step through a conceptual inference request.</p>
        <p>{scalingReportUrl ? <a href={scalingReportUrl}>Open the 1→N GPU scaling report</a> : scalingUnavailable}</p>
      </div>
      {!options && <div className="tech-switch" role="group" aria-label="GPU layouts">
        {[...topologyPresets, { label: "Fit example", report: fitScenario }].map(({ label, report: item }) => <button
          type="button" key={item.id} aria-pressed={report === item} onClick={() => setProfile(item.id)}>{label}</button>)}
      </div>}
      <label className="tech-profile"><span>Topology revision</span>
        <select value={report.id} onChange={(event) => setProfile(event.target.value)}>
          {choices.map(({ id, name }) => <option key={id} value={id}>{id} · {name}</option>)}
        </select>
      </label>
    </header>
    <TopologySession key={report.id} report={report} images={images} />
  </section>;
}
