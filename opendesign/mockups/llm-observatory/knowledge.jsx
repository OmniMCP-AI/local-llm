import { markdownBlocks, markdownInline } from "./wiki-markdown.mjs";
import React, { useState } from "react";
import { ArrowLeft, ArrowUpRight, BookOpen, CircuitBoard, Cpu, FileText, GitBranch, Monitor, Search } from "lucide-react";
import { configurations } from "./scenarios";
import { ProfileBenchmarks } from "./profile-benchmarks";
import topologyReports from "./catalog-topology.json";
import { TechnologyDiagram } from "./technology";
import { ResearchLibrary, useResearchLabels } from "./research-library";
import { quoteCurrency, useLocale } from "./locale";

const documents = __FASTEST_WIKI_DOCUMENTS__;
const publicRoutes = __FASTEST_WIKI_PUBLIC_ROUTES__;
const graph = __FASTEST_WIKI_GRAPH__;
const pictures = __FASTEST_HARDWARE_ASSETS__;
export const wikiEntry = (slug) => documents[slug];
const demo = "Prototype data";
const machines = configurations.filter(({ kind }) => kind !== "cloud");
const memory = { "rtx-4090":"24 GB VRAM", "rtx-3090":"24 GB VRAM", "rtx-3060":"12 GB VRAM", "m4-pro":"24 GB unified", "m4-max":"64 GB unified", "rtx-5090":"32 GB VRAM", "arc-b580":"12 GB VRAM" };
const modelEntries = [
  { id: "qwen25-7b", name: "Qwen2.5 7B Instruct", family: "Qwen", parameters: "7B", source: "https://huggingface.co/Qwen/Qwen2.5-7B-Instruct", runs: {} },
  { id: "qwen25-14b", name: "Qwen2.5 14B Instruct", family: "Qwen", parameters: "14B", source: "https://huggingface.co/Qwen/Qwen2.5-14B-Instruct", runs: { "rtx-4090":[78,64], "rtx-3090":[55,43], "rtx-3060":[23,null], "m4-pro":[27,19] } },
  { id: "llama31-8b", name: "Llama 3.1 8B Instruct", family: "Llama", parameters: "8B", source: "https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct", runs: { "rtx-4090":[132,110], "rtx-3090":[92,75], "rtx-3060":[46,32] } },
];
const basis = { measured:"Lab example", community:"Community example", estimate:"Fit estimate", untested:"No result" };
const format = new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 });
const chip = (machine) => machine.id.startsWith("m4-") ? "Apple Silicon" : machine.id.startsWith("arc-") ? "Intel Arc" : "NVIDIA GeForce";
const backend = (machine) => machine.id.startsWith("m4-") ? "Metal" : machine.id.startsWith("arc-") ? "oneAPI" : "CUDA";
const getModelRuns = (model, machine, context, quant) => {
  if (quant !== "q4") return null;
  if (model.id === "qwen25-7b") return machine.measurements.text[context] ?? null;
  return model.runs[machine.id]?.[context === "long" ? 1 : 0] ?? null;
};
const artifactId = (model, quant) => model.id + "-gguf-" + (quant === "q4" ? "q4-k-m" : "q8-0");
const evidenceId = (model, machine, context, quant) => model.id === "qwen25-7b" && quant === "q4"
  ? "DEMO/" + machine.id + "/text/" + context
  : "DEMO/" + machine.id + "/" + artifactId(model, quant) + "/" + context;
const benchmarkRuns = (quant) => modelEntries.flatMap((model) => machines.map((machine) => ({
  id: machine.id + "/" + model.id, model, machine, backend: backend(machine),
  short: getModelRuns(model, machine, "short", quant),
  long: getModelRuns(model, machine, "long", quant),
})));

function routeFor(slug) {
  const doc = documents[slug];
  if (doc?.kind === "machine") return "#machines/" + slug;
  if (doc?.kind === "model") return "#models/" + slug;
  if (slug === "runtimes") return "#catalog/runtimes";
  if (["explorer", "prices", "agents", "machines", "models", "catalog", "goals"].includes(slug)) return "#" + slug;
  return slug === "index" ? "#wiki" : "#wiki/" + slug;
}

function Link({ to, go, children, className }) {
  return <a href={to} className={className} onClick={(event) => {
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    go(to);
  }}>{children}</a>;
}

function renderInline(line, go) {
  return markdownInline(line).map(({ type, text, href }, i) => {
    if (type === "link" && /^#[a-z0-9/-]+$/i.test(href)) return <Link key={i} to={href} go={go}>{text}</Link>;
    if (type === "link" && /^https:\/\//i.test(href)) return <a key={i} href={href} target="_blank" rel="noreferrer">{text}</a>;
    if (type === "strong") return <strong key={i}>{text}</strong>;
    if (type === "code") return <code key={i}>{text}</code>;
    return text;
  });
}

function Markdown({ doc, go }) {
  return <div className="wiki-prose">{markdownBlocks(doc.body).map(({ type, text, items }, i) => {
    if (type === "heading") return <h3 key={i}>{renderInline(text, go)}</h3>;
    if (type === "list") return <ul key={i}>{items.map((item, j) => <li key={j}>{renderInline(item, go)}</li>)}</ul>;
    return <p key={i}>{renderInline(text, go)}</p>;
  })}</div>;
}

function GraphLinks({ slug, go }) {
  const related = Array.from(new Set(graph.edges.flatMap(({ source, target }) => source === slug ? [target] : target === slug ? [source] : []))).filter((id) => documents[id] && id !== slug);
  if (!related.length) return null;
  return <section className="wiki-neighbors"><div className="wiki-title-line"><GitBranch size={16} aria-hidden="true" /><h2>Linked pages</h2></div>
    <ul>{related.map((id) => <li key={id}><Link to={routeFor(id)} go={go}>{documents[id].title} <ArrowUpRight size={12} aria-hidden="true" /></Link></li>)}</ul>
    <p>Graphify index of explicit Markdown links.</p>
  </section>;
}

export function WikiDetails({ slug, go, onCopy, initiallyOpen = false }) {
  const doc = documents[slug];
  if (!doc) return null;
  return <details className="wiki-details" open={initiallyOpen || undefined}>
    <summary><BookOpen size={16} aria-hidden="true" /> Wiki notes and sources</summary>
    <Markdown doc={doc} go={go} />
    {publicRoutes[slug] && <a href={publicRoutes[slug]}>Permalink to this wiki article</a>}
    <GraphLinks slug={slug} go={go} />
    <details className="wiki-source"><summary>View Markdown</summary>
      <pre><code>{doc.raw}</code></pre>
      <button className="btn outline" onClick={() => onCopy(doc.raw,"Markdown copied")}>Copy Markdown</button>
    </details>
  </details>;
}

function HardwarePhoto({ machine, catalog = false }) {
  const photo = pictures[machine.id];
  if (!photo) return <div className={"knowledge-photo no-photo " + (catalog ? "tile-photo" : "")}><CircuitBoard size={catalog ? 44 : 74} strokeWidth={1} aria-hidden="true" /><span>{backend(machine)} hardware</span></div>;
  return <figure className={"knowledge-photo " + (catalog ? "tile-photo" : "")}>
    <a className="photo-diagram-link" href={"#wiki/technology/" + machine.id} aria-label={"Explore " + machine.name + " in the technology diagram"}><img src={photo.data} alt={photo.alt} loading="lazy" /></a>
    <figcaption>{catalog ? "" : "Component reference. "}<a href={photo.source} target="_blank" rel="noreferrer">{photo.author || photo.credit}</a> / <a href={photo.licenseUrl} target="_blank" rel="noreferrer">{photo.license}</a> / resized</figcaption>
  </figure>;
}

function Catalog({ kind, go, onCopy }) {
  const [query, setQuery] = useState("");
  const machineCatalog = kind === "machines";
  const source = documents[kind];
  const list = (machineCatalog ? machines : modelEntries).filter((entry) => entry.name.toLowerCase().includes(query.trim().toLowerCase()));
  return <div className="deep-page">
    <div className="deep-heading"><div><h1>{source?.title ?? (machineCatalog ? "Machine profiles" : "Model library")}</h1>
      <p>{source?.summary ?? (machineCatalog ? "Explore builds, parts and models on each machine." : "Choose a model, then compare machines running the same artifact.")}</p></div>
      <label className="deep-search"><Search size={16} aria-hidden="true" /><input type="search" aria-label={machineCatalog ? "Find a machine" : "Find a model"} placeholder={machineCatalog ? "Find a machine" : "Find a model"} value={query} onChange={(e) => setQuery(e.target.value)} /></label>
    </div>
    {machineCatalog && <Link className="text-button" to="#catalog/machines" go={go}>Browse all source profiles <ArrowUpRight size={14} /></Link>}
    <div className="knowledge-catalog">{list.map((entry) => <article className="knowledge-tile" key={entry.id}>
      {machineCatalog ? <HardwarePhoto machine={entry} catalog /> : <div className="model-tile-figure"><span>{entry.parameters}</span><FileText size={24} strokeWidth={1} aria-hidden="true" /></div>}
      <div className="tile-body"><p>{machineCatalog ? chip(entry) + " / " + memory[entry.id] : entry.family + " / GGUF"}</p>
        <h2><Link to={"#" + kind + "/" + entry.id} go={go}>{documents[entry.id]?.title ?? entry.name} <ArrowUpRight size={16} aria-hidden="true" /></Link></h2>
        <p>{machineCatalog ? "Build checklist and model runs" : "Artifacts and hardware comparisons"}</p>
      </div>
    </article>)}</div>
    {!list.length && <div className="empty">No matches. <button className="text-button" onClick={() => setQuery("")}>Clear search</button></div>}
    <WikiDetails slug={kind} go={go} onCopy={onCopy} />
  </div>;
}

function Setting({ label, value, items, onChange }) {
  return <label className="select-field knowledge-select"><span>{label}</span><span className="select-wrap">
    <select value={value} onChange={(e) => onChange(e.target.value)}>{items.map(([id, name]) => <option key={id} value={id}>{name}</option>)}</select>
  </span></label>;
}

function BuildPlan({ machine, region, onCopy }) {
  const { t, formatMoney } = useLocale();
  const [draftMemory, setDraftMemory] = useState("reference");
  const [completed, setCompleted] = useState([]);
  const integrated = machine.id.startsWith("m4-");
  const systemRam = machine.detail.split(" · ").at(-1);
  const items = integrated ? [
    ["System", machine.name], ["Memory", memory[machine.id]], ["Storage and ports", "Choose at order time"],
    ["Power and cooling", "Factory design"],
  ] : [
    ["Graphics card", machine.name], ["Device memory", memory[machine.id]], ["System memory", draftMemory === "reference" ? systemRam : draftMemory + " GB (draft)"],
    ["Processor and motherboard", "Exact SKUs not supplied"], ["Power supply", "Confirm wattage, connectors and clearance"],
    ["Case, cooling and storage", "Select compatible parts"],
  ];
  const checks = integrated ? ["Confirm memory at order time", "Confirm storage and ports", "Verify runtime support"] :
    ["Check case clearance and power connectors", "Confirm motherboard, memory, and PSU compatibility", "Install the runtime and rerun the workload"];
  const changed = draftMemory !== "reference";
  return <section className="detail-section" id="machine-build">
    <div className="detail-heading"><div><h2>{integrated ? t("Purchase and setup plan", "采购与安装计划") : t("Build plan", "装机计划")}</h2><p>{t("Starting parts and checks. Unspecified components need verification.", "基础配件和检查事项。未列出的型号需要另行核对。")}</p></div>
      {!integrated && <Setting label="System memory" value={draftMemory} onChange={setDraftMemory} items={[["reference","Reference: " + systemRam],...["32","64","96","128"].map((value) => [value,value + " GB draft"])]} />}
    </div>
    {changed && <p className="detail-note">Draft build. Fit, price and benchmark results need to be checked again for this memory choice.</p>}
    <div className="build-grid"><dl className="part-list">{items.map(([part,value]) => <div key={part}><dt>{part}</dt><dd>{value}</dd></div>)}
      <div><dt>{t("Whole-build example", "整机示例")}</dt><dd>{changed ? t("Draft quote needed", "需要另行报价") : formatMoney(machine.prices[region], quoteCurrency(region))}</dd></div></dl>
      <div className="checklist"><h3>{integrated ? "Before you order" : "Before you build"}</h3>{checks.map((item) => <label key={item}><input type="checkbox" checked={completed.includes(item)} onChange={() => setCompleted(completed.includes(item) ? completed.filter((done) => done !== item) : [...completed,item])} />{item}</label>)}
        <button className="btn outline" onClick={() => onCopy(machine.name + (changed ? " (draft)" : " (sample reference)") + "\n" + items.map(([key,value]) => key + ": " + value).join("\n") + "\n\n" + checks.map((item) => (completed.includes(item) ? "[x] " : "[ ] ") + item).join("\n"),"Build plan copied")}>Copy build plan</button>
      </div>
    </div>
  </section>;
}

function ModelEvidence({ model, machine, context, quant, onClose }) {
  const { t, locale } = useLocale();
  const value = getModelRuns(model,machine,context,quant);
  return <div className="detail-note artifact-evidence" role="status">
    <div><strong>{machine.name} / {model.name}</strong><p>{artifactId(model,quant)} / {context === "short" ? "4K" : "32K"} context / {backend(machine)}</p>
      <p>{value == null ? t("No recorded result", "没有测试记录") : <><bdi>{value.toLocaleString(locale)} tok/s</bdi> / {t(basis[machine.kind])}</>} · {t(demo, "原型示例数据")}</p>
      {value != null && <code>{evidenceId(model,machine,context,quant)}</code>}</div>
    <button className="btn outline" onClick={onClose}>{t("Close details", "关闭详情")}</button>
  </div>;
}

function MachinePage({ machine, state, set, go, onCopy, addToCompare }) {
  const { t, formatMoney } = useLocale();
  const doc = documents[machine.id];
  const [quant, setQuant] = useState("q4");
  const summary = doc?.summary || machine.notes;
  return <div className="deep-page">
    <Link className="crumb" to="#machines" go={go}><ArrowLeft size={14} aria-hidden="true" /> Machine profiles</Link>
    <section className="deep-hero">
      <div className="deep-hero-copy"><h1>{doc?.title ?? machine.name}</h1><p>{summary}</p>
        <dl className="spec-line"><div><dt>{t("Memory pool", "内存容量")}</dt><dd>{memory[machine.id]}</dd></div><div><dt>{t("Runtime backend", "推理后端")}</dt><dd>{backend(machine)}</dd></div><div><dt>{t("Example build", "整机示例价")}</dt><dd>{formatMoney(machine.prices[state.region], quoteCurrency(state.region))}</dd></div></dl>
        <div className="deep-actions"><button className="btn dark" onClick={() => document.getElementById("machine-build")?.scrollIntoView()}>Build this machine</button><button className="btn outline" onClick={() => addToCompare(machine.id)}>Compare with other machines</button><Link to="#wiki/gpu-topology" go={go} className="text-button">GPU topology</Link></div>
      </div>
      <HardwarePhoto machine={machine} />
    </section>
    <section className="detail-section">
      <div className="detail-heading"><div><h2>{t("Models on this machine", "这台整机上的模型")}</h2><p>{t("Illustrative results for the selected quantization and context.", "所选量化版本和上下文的示例结果。")}</p></div></div>
      <div className="detail-controls">
        <Setting label={t("Artifact", "模型文件")} value={quant} onChange={setQuant} items={[["q4","GGUF Q4_K_M"],["q8","GGUF Q8_0"]]} />
        <Setting label={t("Context", "上下文")} value={state.context} onChange={(context) => set({context})} items={[["short",t("4K tokens", "4K tokens")],["long",t("32K tokens", "32K tokens")]]} />
      </div>
      <ProfileBenchmarks key={quant} runs={benchmarkRuns(quant)} type="machine" activeId={machine.id} context={state.context} go={go}
        renderEvidence={(run, onClose) => <ModelEvidence model={run.model} machine={run.machine} context={state.context} quant={quant} onClose={onClose} />} />
    </section>
    <BuildPlan key={machine.id} machine={machine} region={state.region} onCopy={onCopy} />
    <WikiDetails slug={machine.id} go={go} onCopy={onCopy} initiallyOpen />
  </div>;
}

function ModelPage({ model, state, set, go, onCopy }) {
  const { t } = useLocale();
  const doc = documents[model.id];
  const [quant, setQuant] = useState("q4");
  const [runtime, setRuntime] = useState("CUDA");
  return <div className="deep-page">
    <Link className="crumb" to="#models" go={go}><ArrowLeft size={14} aria-hidden="true" /> Model library</Link>
    <section className="deep-hero model-hero">
      <div className="deep-hero-copy"><h1>{doc?.title ?? model.name}</h1><p>{doc?.summary}</p>
        <dl className="spec-line"><div><dt>Model family</dt><dd>{model.family}</dd></div><div><dt>Parameters</dt><dd>{model.parameters}</dd></div><div><dt>Artifact format</dt><dd>GGUF</dd></div></dl>
        <div className="deep-actions"><a href={model.source} className="btn outline" target="_blank" rel="noreferrer">Hugging Face model card <ArrowUpRight size={14} /></a></div>
      </div>
      <div className="model-artifact"><FileText size={30} strokeWidth={1.25} aria-hidden="true" /><p>Artifact reference</p><strong>{artifactId(model,quant)}</strong><p>{demo}</p></div>
    </section>
    <section className="detail-section"><div className="detail-heading"><div><h2>{t("Machines for this model", "运行这个模型的整机")}</h2><p>{t("Illustrative results for the selected quantization and context.", "所选量化版本和上下文的示例结果。")}</p></div></div>
      <div className="detail-controls">
        <Setting label={t("Artifact", "模型文件")} value={quant} onChange={setQuant} items={[["q4","GGUF Q4_K_M"],["q8","GGUF Q8_0"]]} />
        <Setting label={t("Backend cohort", "推理后端组")} value={runtime} onChange={setRuntime} items={[["CUDA","CUDA"],["Metal","Metal"],["oneAPI","oneAPI"]]} />
        <Setting label={t("Context", "上下文")} value={state.context} onChange={(context) => set({context})} items={[["short",t("4K tokens", "4K tokens")],["long",t("32K tokens", "32K tokens")]]} />
      </div>
      <ProfileBenchmarks key={quant} runs={benchmarkRuns(quant)} type="model" activeId={model.id} context={state.context} runtime={runtime} onBackendChange={setRuntime} go={go}
        renderEvidence={(run, onClose) => <ModelEvidence model={run.model} machine={run.machine} context={state.context} quant={quant} onClose={onClose} />} />
    </section>
    <WikiDetails slug={model.id} go={go} onCopy={onCopy} initiallyOpen />
  </div>;
}

function ContextLens({ go }) {
  const matches = machines.filter((machine) => machine.kind === "measured" && machine.measurements.text.short != null && machine.measurements.text.long != null);
  const maximum = Math.max(...matches.flatMap((machine) => [machine.measurements.text.short,machine.measurements.text.long]),1);
  return <section className="detail-section context-lens"><div className="detail-heading"><div><h2>Context sensitivity</h2><p>Sample Qwen2.5 7B Q4_K_M decode speed on each machine at 4K and 32K. Each change is relative to that machine’s 4K result.</p></div></div>
    <div className="context-legend"><span><i />4K context</span><span><i />32K context</span><span>Decode speed (tok/s)</span></div>
    {matches.map((machine) => { const {short,long} = machine.measurements.text; const delta = (long / short - 1) * 100;
      return <div className="context-row" key={machine.id}><Link to={"#machines/" + machine.id} go={go}>{machine.name}</Link>
        <div className="context-bars"><div><i style={{"--bar": short/maximum*100+"%"}} /><span aria-label="4K decode speed">{short}</span></div>
          <div><i style={{"--bar": long/maximum*100+"%"}} /><span aria-label="32K decode speed">{long}</span></div></div>
        <strong className="numeric">{delta > 0 ? "+" : ""}{format.format(delta)}%</strong></div>;
    })}
    <p>First-token latency and memory peaks are still missing from this sample.</p>
  </section>;
}

function WikiPage({ slug, focus, go, onCopy }) {
  const label = useResearchLabels();
  const [query, setQuery] = useState("");
  const doc = documents[slug];
  if (!doc) return <UnknownPage name="Wiki home" to="#wiki" go={go} />;
  const search = query.trim().toLowerCase();
  const guides = Object.entries(documents).filter(([id,node]) => id !== "index" && node.kind === "guide");
  const results = Object.entries(documents).filter(([id,node]) => id !== "index" && [node.title,node.summary,node.body].join(" ").toLowerCase().includes(search));
  return <div className="deep-page wiki-page">
    {slug !== "index" && <Link className="crumb" to="#wiki" go={go}><ArrowLeft size={14} aria-hidden="true" /> Wiki home</Link>}
    {slug === "research" ? <ResearchLibrary go={go} /> : <div className="deep-heading"><div><h1>{doc.title}</h1><p>{doc.summary}</p></div>{slug === "index" && <label className="deep-search"><Search size={16} aria-hidden="true" /><input type="search" aria-label="Search the wiki" placeholder="Search the wiki" value={query} onChange={(e) => setQuery(e.target.value)} /></label>}</div>}
    {doc.use_cases && <nav className="research-topics" aria-label={label("ui","topic")}>
      {doc.use_cases.split(", ").map(id => <Link key={id} to={"#wiki/research?topic=" + id} go={go}>{label("topics",id)}</Link>)}
    </nav>}
    {slug === "index" && <Link className="btn outline" to="#wiki/research" go={go}><BookOpen size={15} />{label("ui","library")}</Link>}
    {slug === "index" && <div className="wiki-directory">
      {(search ? results : guides).map(([id,node]) => <article key={id}><h2><Link to={routeFor(id)} go={go}>{node.title} <ArrowUpRight size={14} aria-hidden="true" /></Link></h2><p>{node.summary}</p></article>)}
      {search && results.length === 0 && <p>No wiki pages match that search.</p>}
    </div>}
    {slug === "benchmark-method" && <ContextLens go={go} />}
    {slug === "gpu-topology" && <TopologyLens key={focus || "default"} initialProfile={focus} />}
    {slug === "technology" && <TechnologyDiagram key={focus || "default"} images={pictures} cardIds={[focus || "rtx-4090", focus === "rtx-3090" ? "rtx-3060" : "rtx-3090"]} />}
    <WikiDetails slug={slug} go={go} onCopy={onCopy} initiallyOpen />
  </div>;
}

function TopologyLens({ initialProfile }) {
  const { t } = useLocale();
  const opening = topologyReports.find((row) => row.id.toLowerCase() === initialProfile);
  const [view,setView] = useState(opening?.group ?? "multi");
  const [profile,setProfile] = useState(opening?.id ?? "V025-HP-E01");
  const options = [["single",t("One card", "单卡")],["multi",t("Multiple cards", "多卡")],["hosts",t("Multi-host", "多主机")]];
  const rows = topologyReports.filter((row) => row.group === view);
  const selected = rows.find((row) => row.id === profile) ?? rows[0];
  return <section className="detail-section topology-view" aria-labelledby="topology-profile-title">
    <div className="detail-heading"><div><h2 id="topology-profile-title">{t("Reported configurations", "已报道的配置")}</h2><p>{t("The diagram shows documented hardware. Bandwidth and scaling need separate measurements.", "图中显示有来源的硬件信息。带宽及扩展性能需要单独测量。")}</p></div></div>
    <div className="detail-controls" aria-label="Topology classes">{options.map(([id,label]) => <button type="button" key={id} aria-pressed={view === id} className={"btn outline " + (view === id ? "picked" : "")} onClick={() => setView(id)}>{label}</button>)}</div>
    {selected && <><Setting label={t("Show setup layout", "查看配置布局")} value={selected.id} onChange={setProfile} items={rows.map((row) => [row.id,row.name])} />
      <ReportedTopology key={selected.id} report={selected} /></>}
    <div className="table-wrap"><table>
      <thead><tr><th scope="col">Profile</th><th scope="col">Reported cards</th><th scope="col">Memory per GPU</th><th scope="col">Reported interconnect</th><th scope="col">Measured link bandwidth</th></tr></thead>
      <tbody>{rows.map((row) => <tr key={row.id}>
        <th scope="row"><a href={row.source} target="_blank" rel="noreferrer">{row.name} <ArrowUpRight size={12} aria-hidden="true" /></a><small>{row.id}</small></th>
        <td className="numeric">{row.count ?? "Unspecified"}</td><td>{row.memory ?? "Not reported"}</td>
        <td>{row.connection ?? "Not reported"}{row.note && <small>{row.note}</small>}</td><td>Not reported in this view</td>
      </tr>)}</tbody>
    </table></div>
    <p>{rows.length} source profiles in this group. Multi-host transport is shown separately from GPU-to-GPU links inside one machine.</p>
  </section>;
}

function ReportedTopology({ report }) {
  const { t } = useLocale();
  const [index,setIndex] = useState(0);
  const isHost = report.group === "hosts";
  const partName = isHost ? "Host" : "Card";
  const parts = isHost ? Array.from({length:report.hostCount}, () => ({ label:report.hostModel || "Host system", photo:null })) : report.devices;
  const links = report.links ?? [];
  const component = parts[index];
  const photo = pictures[component?.photo];
  return <div className="reported-topology">
    <div className="reported-topology-head"><strong>{report.name}</strong><span>{parts.length} reported {isHost ? (parts.length === 1 ? "host" : "hosts") : (parts.length === 1 ? "card" : "cards")}</span></div>
    <div className="reported-slots" aria-label="Reported hardware components" style={links.length ? {gridTemplateColumns:"repeat(" + parts.length + ", minmax(0,1fr))"} : undefined}>
      {parts.map((part,n) => {
        const image = pictures[part.photo];
        return <button key={n} type="button" aria-pressed={index === n} onClick={() => setIndex(n)}>
          {image ? <img src={image.data} alt={image.alt} loading="lazy" /> : <div className="reported-photo-placeholder">{isHost ? <Monitor size={26} aria-hidden="true" /> : <CircuitBoard size={26} aria-hidden="true" />}<span>{t("Photo unavailable", "暂无照片")}</span></div>}
          <strong>{partName} {n + 1}</strong><small>{part.label}</small>
        </button>;
      })}
      {links.map((link) => {
        const [first,last] = [...link.slots].sort((a,b) => a - b);
        return <div key={link.label + first + last} className="reported-edge" data-state={link.state}
          style={{gridColumn:(first + " / " + (last + 1)), "--edge-inset":(50 / (last - first + 1)) + "%"}}>
          <a href={link.source} target="_blank" rel="noreferrer">
            {link.label} <span>· {partName} {first} ↔ {partName} {last}</span>
            <ArrowUpRight size={12} aria-hidden="true" />
          </a>
        </div>;
      })}
    </div>
    <div className="reported-topology-caption" aria-live="polite">
      <p>{isHost ? "Individual accelerator counts per host are not established here." : "Reported memory per GPU: " + (report.memory ?? "not reported") + "."}</p>
      <p>Link or transport: {report.connection ?? "not reported"}. Exact endpoints and active paths are shown only when documented.</p>
      {photo && <p>Representative card photo, resized. <a href={photo.source} target="_blank" rel="noreferrer">{photo.author}</a> / <a href={photo.licenseUrl} target="_blank" rel="noreferrer">{photo.license}</a>. <a href={"#wiki/technology/" + component.photo}>See this card in the technology illustration</a>.</p>}
    </div>
  </div>;
}

function UnknownPage({ name, to, go }) {
  return <div className="deep-page"><div className="deep-heading"><div><h1>Page unavailable</h1><p>This entry is not part of the prototype slice.</p></div>
    <Link className="btn outline" to={to} go={go}>Return to {name}</Link></div></div>;
}

export function KnowledgePage({ screen, slug, focus, state, set, go, onCopy, addToCompare }) {
  if (screen === "Wiki") return <WikiPage key={slug || "index"} slug={slug || "index"} focus={focus} go={go} onCopy={onCopy} />;
  const kind = screen === "Machines" ? "machines" : "models";
  if (!slug) return <Catalog key={kind} kind={kind} go={go} onCopy={onCopy} />;
  if (kind === "machines") {
    const machine = machines.find((item) => item.id === slug);
    return machine ? <MachinePage key={slug} machine={machine} state={state} set={set} go={go} onCopy={onCopy} addToCompare={addToCompare} />
      : <UnknownPage name="machine profiles" to="#machines" go={go} />;
  }
  const model = modelEntries.find((item) => item.id === slug);
  return model ? <ModelPage key={slug} model={model} state={state} set={set} go={go} onCopy={onCopy} />
    : <UnknownPage name="model library" to="#models" go={go} />;
}

export function ExploreLenses({ go }) {
  const { t } = useLocale();
  return <nav className="lens-rail" aria-label={t("Research lenses", "研究视角")}>
    <Link to="#machines" go={go}><Monitor size={18} aria-hidden="true" /><span><strong>{t("Machine profiles", "整机档案")}</strong><small>{t("Parts, build plans and model runs", "配件、装机计划与模型测试")}</small></span></Link>
    <Link to="#models" go={go}><Cpu size={18} aria-hidden="true" /><span><strong>{t("Model library", "模型库")}</strong><small>{t("Exact artifacts across machines", "对比同一模型在各设备上的表现")}</small></span></Link>
    <Link to="#wiki/benchmark-method" go={go}><BookOpen size={18} aria-hidden="true" /><span><strong>{t("Context sensitivity", "上下文影响")}</strong><small>{t("4K and 32K decode evidence", "4K 与 32K 上下文的解码数据")}</small></span></Link>
    <Link to="#wiki/technology" go={go}><CircuitBoard size={18} aria-hidden="true" /><span><strong>{t("Technology in motion", "技术动画")}</strong><small>{t("Follow the GPU data path", "跟踪 GPU 数据流")}</small></span></Link>
  </nav>;
}
