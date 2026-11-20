import React, { useEffect, useId, useState } from "react";
import { ArrowUpRight, CircuitBoard, Cpu, Pause, Play, StepForward, Terminal } from "lucide-react";

const stages = ["Place the model", "Run a decode step", "Return output"];
const routes = [
  {
    id: "peer",
    name: "PCIe peer",
    explanation: "The two devices exchange data over PCIe without staging the payload in system memory. The platform and runtime must support peer access.",
  },
  {
    id: "host",
    name: "Host-staged PCIe",
    explanation: "Data moves from one GPU into host memory, then to the other GPU. The two transfers are shown separately.",
  },
  {
    id: "direct",
    name: "Direct device link",
    explanation: "The devices exchange data over a dedicated link instead of the PCIe path shown here. Both devices, the link, and the runtime must support it.",
  },
];
const nodes = {
  host: {
    icon: Cpu, title: "Host CPU", sub: "System memory",
    explanation: "The runtime coordinates model loading and assigns work to devices. In the host-staged example, system memory also carries the intermediate payload.",
  },
  gpuA: {
    icon: CircuitBoard, title: "GPU A", sub: "Local VRAM",
    explanation: "The first device holds its assigned weights, KV cache, and workspace. Its usable memory depends on what the runtime allocates and what else is using the card.",
  },
  gpuB: {
    icon: CircuitBoard, title: "GPU B", sub: "Separate VRAM",
    explanation: "The second device has its own memory budget. Splitting work does not make the cards one transparent memory pool.",
  },
  client: {
    icon: Terminal, title: "Client", sub: "Generated tokens",
    explanation: "The runtime returns generated tokens to the requesting client. The route illustrates data movement and does not estimate latency or throughput.",
  },
};

const hostA = { id: "hostA", shape: "M 160 200 H 328 V 108 H 520" };
const hostB = { id: "hostB", shape: "M 160 200 H 328 V 292 H 520" };
const returnA = { id: "returnA", shape: "M 520 108 H 700 V 200 H 850" };
const singleLoad = { id: "singleLoad", shape: "M 160 200 H 520" };
const singleReturn = { id: "singleReturn", shape: "M 520 200 H 850" };
const exchange = {
  peer: [{ id: "peer", shape: "M 520 108 V 292" }],
  direct: [{ id: "direct", shape: "M 603 108 V 292" }],
  host: [
    { id: "stageOut", shape: "M 520 108 H 365 V 174 H 160" },
    { id: "stageIn", shape: "M 160 227 H 365 V 292 H 520" },
  ],
};

function stageCopy(step, dual, route) {
  if (step === 0) return dual
    ? "The runtime allocates parts of the model and memory buffers to each device. The layout is an example, not a particular model partition."
    : "The runtime assigns the model and its working allocations to a single GPU. Any offload changes where part of the workload runs.";
  if (step === 1) return dual ? routes.find((entry) => entry.id === route).explanation
    : "The GPU computes the next token using the weights and cache already on the device. There is no inter-GPU exchange.";
  return "After the required computation and synchronization, the runtime returns generated tokens to the client.";
}

function viewedNodes(step, dual, route) {
  if (step === 0) return dual ? ["host", "gpuA", "gpuB"] : ["host", "gpuA"];
  if (step === 1) return dual ? ["gpuA", "gpuB", ...(route === "host" ? ["host"] : [])] : ["gpuA"];
  return ["gpuA", "client"];
}

function DiagramBoard({ dual, route, step, inspected, onInspect, playing, photos }) {
  const paths = dual ? [hostA, hostB, ...exchange[route], returnA] : [singleLoad, singleReturn];
  const activePaths = step === 0 ? (dual ? [hostA, hostB] : [singleLoad])
    : step === 1 ? (dual ? exchange[route] : []) : (dual ? [returnA] : [singleReturn]);
  const activeNodes = viewedNodes(step, dual, route);
  return <div className="tech-board" data-dual={dual} data-playing={playing}>
    <svg className="tech-traces" viewBox="0 0 1000 400" preserveAspectRatio="none" aria-hidden="true">
      {paths.map(({ id, shape }) => <path key={id} className="tech-trace" d={shape} vectorEffect="non-scaling-stroke" />)}
      {activePaths.map(({ id, shape }) => <React.Fragment key={id}>
        <path className="tech-trace tech-trace-on" d={shape} vectorEffect="non-scaling-stroke" />
        <path className="tech-trace tech-trace-flow" d={shape} vectorEffect="non-scaling-stroke" />
      </React.Fragment>)}
    </svg>
    {Object.entries(nodes).filter(([key]) => dual || key !== "gpuB").map(([key, config]) => {
      const Icon = config.icon;
      return <button key={key} type="button" className={`tech-node tech-node-${key}`}
        data-active={activeNodes.includes(key)} aria-pressed={inspected === key} onClick={() => onInspect(key)}>
        {photos[key] ? <img className="tech-node-photo" src={photos[key].data} alt="" /> : <Icon size={19} aria-hidden="true" />}
        <span><strong>{config.title}</strong><small>{config.sub}</small></span>
      </button>;
    })}
    <span className="tech-board-caption">Conceptual data path</span>
  </div>;
}

function ComponentInspector({ selected, photo, photoDevice, onPhoto }) {
  const item = nodes[selected];
  const Icon = item.icon;
  const isGpu = selected === "gpuA" || selected === "gpuB";
  return <aside className="tech-inspect" aria-label="Selected component">
    <div className="tech-inspect-body" aria-live="polite">
      <div className="tech-inspect-title"><Icon size={19} aria-hidden="true" /><h3>{item.title}</h3></div>
      <p>{item.explanation}</p>
    </div>
    {photo ? <figure className="tech-photo">
      <button type="button" aria-pressed={isGpu} onClick={onPhoto} aria-label="Inspect the GPU shown in the diagram">
        <img src={photo.data} alt={photo.alt} />
        <span>{isGpu ? "Physical reference for " + photoDevice : "Inspect " + photoDevice}<ArrowUpRight size={13} aria-hidden="true" /></span>
      </button>
      <figcaption>Card reference, resized. {photo.source ? <a href={photo.source} target="_blank" rel="noreferrer">{photo.author || "Image source"}</a> : photo.author}{photo.license && <> / {photo.licenseUrl ? <a href={photo.licenseUrl} target="_blank" rel="noreferrer">{photo.license}</a> : photo.license}</>}. The diagram does not assume the pictured card supports this link.</figcaption>
    </figure> : <div className="tech-photo-placeholder"><CircuitBoard size={22} aria-hidden="true" /><span>No sourced photo for {photoDevice}.</span></div>}
  </aside>;
}

export function TechnologyDiagram({ images = {}, cardId, cardIds = [], initialCount = 1 }) {
  const id = useId();
  const [dual, setDual] = useState(initialCount === 2);
  const [route, setRoute] = useState("peer");
  const [step, setStep] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [inspected, setInspected] = useState("gpuA");
  const firstId = cardIds[0] ?? cardId;
  const photos = {
    gpuA: firstId ? images[firstId] : images["rtx-4090"] ?? Object.values(images)[0],
    gpuB: cardIds[1] ? images[cardIds[1]] : undefined,
  };
  const photoKey = inspected === "gpuB" ? "gpuB" : "gpuA";

  useEffect(() => {
    if (!playing) return undefined;
    const advance = window.setTimeout(() => {
      if (step === stages.length - 1) setPlaying(false);
      else setStep(step + 1);
    }, 2250);
    return () => window.clearTimeout(advance);
  }, [playing, step]);

  function topology(next) {
    setDual(next);
    setStep(0);
    setPlaying(false);
    if (!next && inspected === "gpuB") setInspected("gpuA");
  }

  function goTo(next) {
    setPlaying(false);
    setStep(next);
  }

  function togglePlay() {
    if (playing) return setPlaying(false);
    if (step === stages.length - 1) setStep(0);
    setPlaying(true);
  }

  return <section className="tech-lab" aria-labelledby={id + "-title"}>
    <header className="tech-header">
      <div>
        <h2 id={id + "-title"}>Follow one inference step</h2>
        <p>Switch the setup, play the flow, and select a component to see its role.</p>
      </div>
      <div className="tech-switches">
        <div className="tech-switch" role="group" aria-label="GPU count">
          <button type="button" aria-pressed={!dual} onClick={() => topology(false)}>One GPU</button>
          <button type="button" aria-pressed={dual} onClick={() => topology(true)}>Two GPUs</button>
        </div>
        {dual && <div className="tech-switch" role="group" aria-label="Illustrated device path">
          {routes.map((item) => <button type="button" key={item.id} aria-pressed={route === item.id}
            onClick={() => { setRoute(item.id); goTo(1); }}>{item.name}</button>)}
        </div>}
      </div>
    </header>

    <div className="tech-grid">
      <div className="tech-flow">
        <DiagramBoard dual={dual} route={route} step={step} inspected={inspected} onInspect={setInspected} playing={playing} photos={photos} />
        <ol className="tech-steps" aria-label="Inference stages">
          {stages.map((stage, index) => <li key={stage}>
            <button type="button" aria-current={step === index ? "step" : undefined} onClick={() => goTo(index)}>
              <span>{String(index + 1).padStart(2, "0")}</span>{stage}
            </button>
          </li>)}
        </ol>
        <div className="tech-step-notes">
          <p aria-live={playing ? "off" : "polite"}>{stageCopy(step, dual, route)}</p>
          <div className="tech-playbar" aria-label="Playback controls">
            <button type="button" className="btn outline" onClick={togglePlay}>{playing ? <Pause size={15} aria-hidden="true" /> : <Play size={15} aria-hidden="true" />}{playing ? "Pause" : "Play"}</button>
            <button type="button" className="btn outline" onClick={() => goTo((step + 1) % stages.length)}><StepForward size={15} aria-hidden="true" />Next</button>
          </div>
        </div>
      </div>
      <ComponentInspector selected={inspected} photo={photos[photoKey]} photoDevice={nodes[photoKey].title} onPhoto={() => setInspected(photoKey)} />
    </div>

    <dl className="tech-principles">
      <div><dt>Will the model fit?</dt><dd>Check weights, KV cache and workspace against usable VRAM on each device. Context length, quantization and batch size change those allocations.</dd></div>
      <div><dt>Device affinity</dt><dd>Check which GPU each worker and request uses. Placement, topology, driver support and runtime settings determine which paths are actually available.</dd></div>
    </dl>
    <p className="tech-disclaimer">Illustration only. The selected layout does not establish compatibility or a benchmark result.</p>
  </section>;
}
