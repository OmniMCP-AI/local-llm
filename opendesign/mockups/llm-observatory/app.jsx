import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity, ArrowDown, ArrowDownRight, ArrowRight, ArrowUpRight,
  ChartScatter, Check, ChevronDown, CircleHelp, Clipboard, CodeXml,
  ExternalLink, Monitor, Plus, SlidersHorizontal,
  Table2, Wallet, X,
} from "lucide-react";
import { configurations, priceHistory, workloads } from "./scenarios";
import { ScatterPlot, PricePlot, RankingPlot } from "./plots";
import { ExploreLenses, KnowledgePage, WikiDetails, wikiEntry } from "./knowledge";
import { GoalPage } from "./goals";
import { FeedbackBubble } from "./feedback";
import { CatalogModelProfile, CatalogTopics, SourceCatalog } from "./catalog";
import { CostPage } from "./costs";
import { navigationHref } from "./release-origin.mjs";
import { Highlights } from "./highlights";
import { MethodsPage } from "./methods";
import { LocaleControls, LocaleProvider, LocaleStatus, quoteCurrency, useLocale } from "./locale";
import { SiteName } from "./site-name";

const release = "Demo snapshot, Nov 20, 2026";
const states = {
  measured: "Lab example", community: "Community example", estimate: "Fit estimate",
  untested: "Untested", cloud: "Cloud baseline",
};
const routes = {
  Explorer: "explorer", Compare: "goals",
  ...(__FASTEST_RELEASE_ORIGIN__ ? { "Guided advisor": "advisor" } : {}),
  Methods: "methods", Costs: "costs", Catalog: "catalog", Machines: "machines", Models: "models", Wiki: "wiki", "Price watch": "prices", "For agents": "agents",
};
const hrefFor = (route) => navigationHref(route, __FASTEST_PAGES__, __FASTEST_RELEASE_ORIGIN__);
const chineseRoutes = { Explorer: "探索", Compare: "目标对比", "Guided advisor": "配置顾问", Methods: "评测方法", Costs: "成本", Catalog: "目录", Machines: "整机", Models: "模型", Wiki: "知识库", "Price watch": "价格趋势", "For agents": "智能体" };
const chineseWorkload = { text: "文本生成", image: "图像生成", agent: "智能体任务" };
const defaults = {
  work: "text", context: "short", region: "us", budget: 2800, condition: "new",
  rule: "task", chart: "plot", machine: "rtx-3090", history: "rtx-3090", flow: "expert",
  compare: ["rtx-3060", "rtx-4090", "m4-pro"],
  textTarget: 100, imageTarget: 10, agentTarget: 60,
};
const validIds = new Set(configurations.map(({ id }) => id));
const spec = "https://github.com/OmniMCP-AI/local-llm/issues/1";
const research = "https://github.com/OmniMCP-AI/local-llm/tree/main/docs/Local-AI-Comparison-Platform";
const priceCeiling = { us: 5000, cn: 35000 };
const targetLimits = { text: { max: 250, step: 5 }, image: { max: 30, step: 1 }, agent: { max: 120, step: 5 } };
const meetsGoal = (value, target, work) => workloads[work].lowerBetter ? value <= target : value >= target;
const meta = (value) => value.replaceAll(" · ", " / ");
const amount = (value) => Number.isInteger(value) ? String(value) : value.toFixed(1);
const conditionOf = (row) => row.id === "rtx-3090" ? "used" : "new";
const conditionText = (row) => row.kind === "cloud" ? "Usage billing" : conditionOf(row) === "used" ? "Used GPU build" : "New build";
const rowValue = (row, work, context) => row.measurements[work][work === "text" ? context : "short"];
const versionKey = "fastest-review-v1";

function initialState() {
  let local = {};
  try { local = JSON.parse(localStorage.getItem(versionKey)) || {}; } catch {}
  const p = new URLSearchParams(location.search);
  const s = { ...defaults, ...local };
  const options = {
    work: Object.keys(workloads), context: ["short", "long"], region: ["us", "cn"],
    condition: ["new", "used", "all"], rule: ["task", "cuda"], chart: ["plot", "table"],
    flow: ["expert", "machine", "shop"],
  };
  for (const [key, values] of Object.entries(options)) {
    const value = p.get(key) ?? s[key];
    s[key] = values.includes(value) ? value : defaults[key];
  }
  for (const key of ["machine", "history"]) {
    const value = p.get(key) ?? s[key];
    s[key] = validIds.has(value) ? value : defaults[key];
  }
  const requested = p.get("budget") ?? s.budget;
  s.budget = Math.max(0, Math.min(priceCeiling[s.region], Number(requested) || 0));
  for (const [work, { max, step }] of Object.entries(targetLimits)) {
    const key = work + "Target";
    const value = Number(p.get(key) ?? s[key]);
    s[key] = Number.isFinite(value) ? Math.min(max, Math.max(step, Math.round(value / step) * step)) : defaults[key];
  }
  const compare = p.has("compare") ? p.get("compare").split(",") : s.compare;
  s.compare = [...new Set(Array.isArray(compare) ? compare.filter((id) => validIds.has(id)) : defaults.compare)].slice(0, 4);
  return s;
}

function routeFrom(hash = location.hash) {
  const [path, query] = hash.slice(1).split("?");
  const [route, slug, focus] = path.split("/");
  const name = Object.keys(routes).find((entry) => routes[entry] === route) || "Explorer";
  const model = route === "catalog" && slug === "models" ? new URLSearchParams(query).get("model") : null;
  return { name, model, slug: /^[a-z0-9-]+$/.test(slug ?? "") ? slug : null, focus: /^[a-z0-9-]+$/.test(focus ?? "") ? focus : null };
}

function limitReason(row, { work, context, region, condition, rule }) {
  const value = rowValue(row, work, context);
  if (row.kind === "cloud") return value == null ? "No comparable run" : "Different cost basis";
  if (value == null) return "No run for these settings";
  if (row.kind === "community") return "Contributor conditions differ";
  if (row.kind === "estimate") return "Estimate only";
  if (rule === "cuda" && row.id.startsWith("m4")) return "Metal backend differs";
  if (row.prices[region] == null) return "No regional quote";
  if (condition !== "all" && conditionOf(row) !== condition) return "Outside price cohort";
  return null;
}

function Indicator({ kind }) {
  return <span className={"evidence-pill " + kind}><span aria-hidden="true" />{states[kind]}</span>;
}

function Select({ label, children, ...props }) {
  return <label className="select-field">
    <span>{label}</span>
    <span className="select-wrap"><select {...props}>{children}</select><ChevronDown size={15} aria-hidden="true" /></span>
  </label>;
}

function Modes({ active, onChoose }) {
  const { t } = useLocale();
  const items = [
    { id: "machine", icon: Monitor, title: t("Use my machine", "使用现有设备"), line: t("See what fits the hardware you have.", "查看当前硬件适合运行的模型。") },
    { id: "shop", icon: Wallet, title: t("Shop by budget", "按预算选购"), line: t("Find a setup at the right price.", "在预算内找到合适的配置。") },
    { id: "expert", icon: SlidersHorizontal, title: t("Expert compare", "高级对比"), line: t("Explore matched benchmarks and evidence.", "查看同条件下的评测与证据。") },
  ];
  return <div className="modes" aria-label="Choose a starting point">
    {items.map(({ id, icon: Icon, title, line }) => {
      const content = <><span className="mode-icon"><Icon size={19} aria-hidden="true" /></span>
        <span className="mode-text"><strong>{title}</strong><small>{line}</small></span>
        <ArrowUpRight size={17} className="mode-arrow" aria-hidden="true" /></>;
      const classes = "mode " + (active === id ? "active" : "");
      return __FASTEST_RELEASE_ORIGIN__
        ? <a key={id} className={classes} href={hrefFor("goals") + "?entry=" + (id === "shop" ? "budget" : id)}>{content}</a>
        : <button key={id} className={classes} aria-pressed={active === id} onClick={() => onChoose(id)}>{content}</button>;
    })}
  </div>;
}

function Header({ page, navigate }) {
  const { t } = useLocale();
  return <header className="site-header"><div className="nav-inner">
    <a href="#explorer" className="wordmark" onClick={(e) => { e.preventDefault(); navigate("Explorer", true); }}>
      <span className="brand-mark"><Activity size={19} strokeWidth={2.4} aria-hidden="true" /></span>
      <SiteName />
    </a>
    <nav aria-label={t("Main navigation", "主导航")}>{Object.entries(routes).map(([name, route]) => {
      const href = hrefFor(route);
      const internal = href.startsWith("#");
      return <a key={name} href={href} aria-current={internal && page === name ? "page" : undefined}
        onClick={internal ? (event) => { event.preventDefault(); navigate(name, true); } : undefined}>
        {t(name, chineseRoutes[name])}</a>;
    })}</nav>
    <LocaleControls />
  </div></header>;
}

function Hero({ onExplore, onMethod }) {
  const { t } = useLocale();
  return <section className="hero">
    <div className="hero-image" aria-hidden="true"><img src={__FASTEST_HERO_IMAGE__} alt="" fetchPriority="high" /></div>
    <div className="hero-content">
      <h1>{t("Find your fastest", "找到最快的")}<br />{t("local AI setup.", "本地 AI 配置。")}</h1>
      <p>{t("Compare what fits, how it performs, and what it costs.", "对比模型适配性、运行性能和总体成本。")}</p>
      <div className="hero-actions">
        {__FASTEST_RELEASE_ORIGIN__
          ? <a className="btn mint" href={hrefFor("explorer")}>{t("Explore benchmarks", "探索性能评测")} <ArrowUpRight size={16} aria-hidden="true" /></a>
          : <button className="btn mint" onClick={onExplore}>{t("Explore benchmarks", "探索性能评测")} <ArrowDown size={16} aria-hidden="true" /></button>}
        <button className="hero-link" onClick={onMethod}>{t("How we compare", "了解对比方法")} <ArrowUpRight size={15} aria-hidden="true" /></button>
      </div>
    </div>
  </section>;
}

function Filters({ state, set, activeCount, target }) {
  const { t, formatMoney } = useLocale();
  const max = priceCeiling[state.region];
  const { max: targetMax, step: targetStep } = targetLimits[state.work];
  const workload = workloads[state.work];
  return <div className="filter-panel">
    <div className="filter-fields">
      <Select label={t("Workload", "工作负载")} value={state.work} onChange={(e) => set({ work: e.target.value })}>
        {Object.entries(workloads).map(([key, work]) => <option key={key} value={key}>{t(work.label, chineseWorkload[key])}</option>)}
      </Select>
      {state.work === "text" && <Select label={t("Context", "上下文")} value={state.context} onChange={(e) => set({ context: e.target.value })}>
        <option value="short">4K tokens</option><option value="long">32K tokens</option>
      </Select>}
      <Select label={t("Market", "报价市场")} value={state.region} onChange={(e) => set({ region: e.target.value, budget: e.target.value === "cn" ? 20000 : 2800 })}>
        <option value="us">{t("US", "美国")} (USD)</option><option value="cn">{t("China", "中国")} (CNY)</option>
      </Select>
      <Select label={t("Build condition", "成色")} value={state.condition} onChange={(e) => set({ condition: e.target.value })}>
        <option value="new">{t("New builds", "全新配置")}</option><option value="used">{t("Used GPU builds", "二手显卡配置")}</option><option value="all">{t("All quotes", "全部报价")}</option>
      </Select>
    </div>
    <label className="budget-field"><span><b>{t("Budget ceiling", "预算上限")}</b><strong>{formatMoney(state.budget, quoteCurrency(state.region))}</strong></span>
      <input aria-label={t("Budget ceiling", "预算上限")} aria-valuetext={formatMoney(state.budget, quoteCurrency(state.region))} type="range" min="0" max={max} step={state.region === "cn" ? 500 : 50} value={state.budget} style={{ "--progress": state.budget / max * 100 + "%" }} onChange={(e) => set({ budget: Number(e.target.value) })} />
      <small>{t(activeCount === 1 ? "{count} match within budget" : "{count} matches within budget", "预算内有 {count} 个配置", { count: activeCount })}</small>
    </label>
    <label className="budget-field target-field">
      <span><b>{t("Performance target", "性能目标")}</b><strong>{target} {workload.unit}</strong></span>
      <input aria-label={t("Performance target", "性能目标")} aria-valuetext={target + " " + workload.unit} type="range" min={targetStep} max={targetMax} step={targetStep} value={target}
        style={{ "--progress": (target - targetStep) / (targetMax - targetStep) * 100 + "%" }}
        onChange={(e) => set({ [state.work + "Target"]: Number(e.target.value) })} />
      <small>{workload.lowerBetter ? t("Maximum time", "最长耗时") : t("Minimum decode speed", "最低解码速度")}</small>
    </label>
  </div>;
}

function ResultCard({ row, state, workload, target, onEvidence, onCompare, picked }) {
  const { t, formatMoney } = useLocale();
  if (!row) return <aside className="result-card">
    <div className="result-kicker">{state.flow === "machine" ? "Fit check" : "Within your budget"}</div>
    <h3>{t("No eligible setup", "没有符合条件的配置")}</h3><p>{t("Raise the budget or change the build condition to see more options.", "提高预算或更换成色条件可查看更多配置。")}</p>
  </aside>;
  const value = rowValue(row, state.work, state.context);
  const machine = state.flow === "machine";
  const measuredHere = value != null && row.kind === "measured";
  return <aside className="result-card">
    <div className="result-kicker">{machine ? "Your selected machine" : state.condition === "all" ? "Quote in your budget" : "Fastest within your budget"}</div>
    <div className="result-reading" aria-live="polite">
      <strong>{value == null ? "—" : amount(value)} {value != null && <small>{workload.unit}</small>}</strong>
      <span>{value == null ? "Untested here" : measuredHere ? "Lab example" : states[row.kind]}</span>
    </div>
    <h3>{row.short === "M4 Pro" ? row.name : row.short + " build"}</h3>
    <p>{meta(row.detail)}</p>
    {machine && <div className="fit-line">{state.work === "text" ? row.fit.label : "Task-specific evidence"} <span>{state.work === "text" ? "Illustrative fit" : states[row.kind]}</span></div>}
    <div className="result-stats">
      <div><strong>{formatMoney(row.prices[state.region], quoteCurrency(state.region))}</strong><span>{conditionText(row)}</span></div>
      {value != null && <div><strong>{meetsGoal(value, target, state.work) ? "Meets target" : "Misses target"}</strong><span>{target} {workload.unit}</span></div>}
    </div>
    {machine && value == null && <small className="fit-caveat">No run for these settings. Open the evidence for details.</small>}
    <button className="btn result-action" onClick={() => onEvidence(row)}>{t("Inspect evidence", "查看证据")} <ArrowUpRight size={16} aria-hidden="true" /></button>
    <button className="result-secondary" aria-pressed={picked} onClick={() => onCompare(row.id)}>
      {picked ? <Check size={15} /> : <Plus size={15} />}{picked ? t("Added to comparison", "已加入对比") : t("Add to comparison", "加入对比")}
    </button>
    {row.kind !== "cloud" && <a className="text-button machine-page-link" href={"#machines/" + row.id}>Machine profile <ArrowUpRight size={14} aria-hidden="true" /></a>}
  </aside>;
}

function CompareTable({ rows, state, workload, onEvidence, onCompare, onBrowse, all = false }) {
  const { t, formatMoney } = useLocale();
  return <section className="compare-section">
    {!all && <div className="section-heading">
      <div><h2>{t("Side-by-side comparison", "并排比较")}</h2><p>{t("Inspect exact values and why a setup is or isn’t comparable.", "查看具体数据及各配置的可比性条件。")}</p></div>
      <button className="btn outline" onClick={onBrowse}><Plus size={16} aria-hidden="true" /> {t("Add a setup", "添加配置")}</button>
    </div>}
    <div className={all ? "table-wrap embedded-table" : "table-wrap"}>
      {rows.length === 0 ? <div className="empty">Choose two or more setups to compare. <button className="text-button" onClick={onBrowse}>Browse setups <ArrowRight size={15} /></button></div> :
      <table>
        <thead><tr><th scope="col">{t("Setup", "配置")}</th><th scope="col">{workload.lowerBetter ? t("Completion time", "完成耗时") : t("Decode speed", "解码速度")}</th><th scope="col">{t("Build price", "整机价格")}</th><th scope="col">{t("Evidence", "证据")}</th><th scope="col">{t("Comparison", "可比性")}</th>{!all && <th scope="col" aria-label={t("Remove", "移除")} />}</tr></thead>
        <tbody>{rows.map((row) => {
          const value = rowValue(row, state.work, state.context);
          const reason = limitReason(row, state);
          return <tr key={row.id}>
            <th scope="row"><button className="table-name" onClick={() => onEvidence(row)}>{row.name} <ArrowUpRight size={14} /></button>{row.kind !== "cloud" && <a className="profile-link" href={"#machines/" + row.id} aria-label={"Machine page for " + row.name}>Profile</a>}<small>{meta(row.detail)}</small></th>
            <td className="numeric">{value == null ? "—" : amount(value) + " " + workload.unit}</td>
            <td className="numeric">{formatMoney(row.prices[state.region], quoteCurrency(state.region))}<small>{conditionText(row)}</small></td>
            <td><Indicator kind={value == null && row.kind !== "cloud" ? "untested" : row.kind} /></td>
            <td className="cohort-cell">{reason ?? <><Check size={15} /> Eligible</>}</td>
            {!all && <td><button className="icon-btn" aria-label={"Remove " + row.name} onClick={() => onCompare(row.id)}><X size={16} /></button></td>}
          </tr>;
        })}</tbody>
      </table>}
    </div>
  </section>;
}

const coverageColumns = [
  { work: "text", context: "short", label: "Text at 4K" },
  { work: "text", context: "long", label: "Text at 32K" },
  { work: "image", context: "short", label: "Image" },
  { work: "agent", context: "short", label: "Agent task" },
];

function CoverageMatrix({ onEvidence }) {
  return <details className="coverage-section">
    <summary>Workload coverage</summary>
    <p>Each column has its own unit and test conditions. Select a value to inspect its evidence.</p>
    <div className="table-wrap"><table>
      <thead><tr><th scope="col">Setup</th>{coverageColumns.map(({ label }) => (
        <th key={label} scope="col">{label}</th>
      ))}</tr></thead>
      <tbody>{configurations.map((row) => <tr key={row.id}>
        <th scope="row">{row.short}</th>
        {coverageColumns.map(({ work, context, label }) => {
          const value = rowValue(row, work, context);
          return <td key={label}>{value == null ? <span className="coverage-missing">No result</span> : <button className="coverage-value" aria-label={row.name + ", " + label + ": " + amount(value) + " " + workloads[work].unit + ", " + states[row.kind]} onClick={() => onEvidence(row, work, context)}>
            <span className="numeric">{amount(value)} {workloads[work].unit}</span><small>{states[row.kind]}</small>
          </button>}</td>;
        })}
      </tr>)}</tbody>
    </table></div>
  </details>;
}

function Drawer({ panel, close, state, onCompare, onEvidence, go }) {
  const { t, formatMoney } = useLocale();
  useEffect(() => {
    if (!panel) return;
    const prior = document.activeElement;
    const exit = (e) => {
      if (e.key === "Escape") close();
      if (e.key !== "Tab") return;
      const controls = [...document.querySelectorAll(".drawer a[href], .drawer button:not([disabled])")];
      const edge = e.shiftKey ? controls[0] : controls.at(-1);
      if (document.activeElement !== edge) return;
      e.preventDefault();
      (e.shiftKey ? controls.at(-1) : controls[0])?.focus();
    };
    document.addEventListener("keydown", exit);
    const target = document.getElementById("drawer-close");
    target?.focus();
    return () => { document.removeEventListener("keydown", exit); prior?.focus(); };
  }, [panel?.kind, panel?.row?.id]);
  if (!panel) return null;
  const work = workloads[state.work];
  const row = panel.row;
  const value = row ? rowValue(row, state.work, state.context) : null;
  const reason = row ? limitReason(row, state) : null;
  return <div className="overlay" onMouseDown={(e) => { if (e.target === e.currentTarget) close(); }}>
    <aside className="drawer" role="dialog" aria-modal="true" aria-labelledby="drawer-title">
      <div className="drawer-head"><span className="kicker">{panel.kind === "method" ? "Methodology" : panel.kind === "browse" ? "Setup catalog" : panel.kind === "price" ? "Price evidence" : "Evidence record"}</span><button id="drawer-close" className="icon-btn" onClick={close} aria-label="Close panel"><X size={21} /></button></div>
      {panel.kind === "method" ? <>
        <h2 id="drawer-title">{t("How we compare", "对比方法")}</h2>
        <p>{t("This Explorer uses sample benchmarks, quotes, and fit estimates. See Benchmark methods for video-sourced observations.", "探索页使用示例跑分、报价及适配性估计。带来源的视频案例见评测方法。")}</p>
        <a href="#methods" className="btn outline" onClick={(event) => { event.preventDefault(); go("#methods"); }}>{t("Benchmark methods", "评测方法")} <ArrowUpRight size={15} aria-hidden="true" /></a>
        <div className="drawer-group"><h3>Same task</h3><p>Match the workload, output requirements, and measurement scope. Setup and backend may differ where the task protocol allows it.</p></div>
        <div className="drawer-group"><h3>CUDA only</h3><p>Hold the CUDA execution settings fixed to compare different GPUs in the CUDA cohort. Other backends and weaker evidence stay visible as context.</p></div>
        <div className="drawer-group"><h3>Fit and measured performance</h3><p>Production fit estimates will come from the pinned llmfit core. Lab runs, contributor reports, estimates, and missing runs are labeled separately.</p></div>
        <div className="drawer-group"><h3>Chart targets</h3><p>The dashed line is your selected performance target. The shaded area in Tradeoffs combines that target with your budget. A point can meet both targets and still be ineligible for ranking if its evidence differs.</p></div>
        <div className="drawer-group method-links"><h3>Benchmark design references</h3>
          <a href="https://artificialanalysis.ai/articles/glm-5-2-is-the-new-leading-open-weights-model-on-the-artificial-analysis-intelligence-index" target="_blank" rel="noreferrer">Artificial Analysis: rankings and cost tradeoffs</a>
          <a href="https://artificialanalysis.ai/articles/artificial-analysis-intelligence-index-v5" target="_blank" rel="noreferrer">Artificial Analysis: Intelligence Index v5</a>
          <a href="https://arxiv.org/abs/2406.19314" target="_blank" rel="noreferrer">LiveBench paper</a>
          <a href="https://www.together.ai/blog/evaluate-and-benchmark-llms" target="_blank" rel="noreferrer">Together AI: evaluating LLM performance</a>
        </div>
        <a className="btn outline" href={spec} target="_blank" rel="noreferrer">Read the project spec <ExternalLink size={15} /></a>
      </> : panel.kind === "browse" ? <>
        <h2 id="drawer-title">Pick setups to compare</h2><p>Select up to four. Open any setup to read its evidence.</p>
        <div className="pick-list">{configurations.map((item) => <div key={item.id} className="pick-row">
          <button className="table-name" onClick={() => onEvidence(item)}>{item.name}<small>{meta(item.detail)}</small></button>
          <button className={"btn outline " + (state.compare.includes(item.id) ? "picked" : "")} disabled={state.compare.length >= 4 && !state.compare.includes(item.id)} onClick={() => onCompare(item.id)} aria-pressed={state.compare.includes(item.id)}>{state.compare.includes(item.id) ? <Check size={16} /> : <Plus size={16} />}{state.compare.includes(item.id) ? "Added" : "Add"}</button>
        </div>)}</div>
        <button className="btn dark" onClick={close}>View comparison <ArrowRight size={16} /></button>
      </> : panel.kind === "price" ? <>
        <h2 id="drawer-title">{row.name}</h2><p>Illustrative whole-build quotes in the US market.</p>
        <div className="evidence-result"><strong>{formatMoney(priceHistory[row.id].at(-1))}</strong><span>{t("Latest sample quote", "最新示例报价")}</span></div>
        <dl className="evidence-list">
          <div><dt>{t("Original quote", "原始报价")}</dt><dd>{priceHistory[row.id].at(-1).toLocaleString()} USD</dd></div>
          <div><dt>Cohort</dt><dd>US (USD) / {conditionText(row)}</dd></div>
          <div><dt>Coverage</dt><dd>8 sample observations, Aug 14 to Nov 20</dd></div>
          <div><dt>Cost scope</dt><dd>Whole build, before tax and shipping</dd></div>
          <div><dt>Evidence ID</dt><dd className="mono">DEMO/price/us/{row.id}</dd></div>
        </dl>
        <p>The example contains asking prices. Live availability and transaction prices require a separate source.</p>
      </> : <>
        <h2 id="drawer-title">{row.name}</h2><p>{meta(row.detail)}</p>
        {row.kind !== "cloud" && <div className="drawer-machine-action"><button className="btn outline" onClick={() => go("#machines/" + row.id)}>{t("Open machine profile", "打开整机档案")} <ArrowUpRight size={15} aria-hidden="true" /></button></div>}
        <Indicator kind={value == null && row.kind !== "cloud" ? "untested" : row.kind} />
        <div className="evidence-result"><strong>{value == null ? "—" : amount(value) + " " + work.unit}</strong><span>{work.title}</span></div>
        <dl className="evidence-list">
          <div><dt>Workload</dt><dd>{meta(work.artifact)}</dd></div>
          <div><dt>Protocol</dt><dd>{meta(work.method)}{state.work === "text" ? " / " + (state.context === "long" ? "32K" : "4K") + " context" : ""}</dd></div>
          <div><dt>{t("Build quote", "整机报价")}</dt><dd>{formatMoney(row.prices[state.region], quoteCurrency(state.region))} / {conditionText(row)}</dd></div>
          {row.prices[state.region] != null && <div><dt>{t("Original quote", "原始报价")}</dt><dd>{row.prices[state.region].toLocaleString()} {quoteCurrency(state.region)}</dd></div>}
          <div><dt>Eligibility</dt><dd>{reason ?? "Eligible for the active cohort"}</dd></div>
          <div><dt>Evidence ID</dt><dd className="mono">DEMO/{row.id}/{state.work}/{state.work === "text" ? state.context : "short"}</dd></div>
        </dl>
        <p>{row.notes}</p>
        {state.work === "text" && <div className="drawer-group"><h3>{row.fit.label}</h3><p>{row.fit.detail} Illustrative only.</p></div>}
        <a className="btn outline" href={research} target="_blank" rel="noreferrer">Open the research basis <ExternalLink size={15} /></a>
      </>}
    </aside>
  </div>;
}

function PricePage({ state, set, onEvidence }) {
  const { t, formatMoney, displayCurrency } = useLocale();
  const row = configurations.find((item) => item.id === state.history && priceHistory[item.id]) ?? configurations[1];
  const values = priceHistory[row.id];
  const change = Math.round((values.at(-1) / values[0] - 1) * 100);
  return <div className="interior">
    <div className="page-heading"><h1>{t(wikiEntry("prices").title, "价格趋势")}</h1><p>{t(wikiEntry("prices").summary, "按报价市场和配置查看历史价格。")}</p></div>
    <article className="panel price-panel">
      <div className="plot-head"><div><h2>{row.name}</h2><p>{t("US (USD) source", "美国（原始 USD）")} / {conditionText(row)} / {t("Illustrative quotes", "示例报价")} / {displayCurrency()}</p></div>
        <Select label={t("Select a setup", "选择配置")} value={row.id} onChange={(e) => set({ history: e.target.value })}>
          {configurations.filter((item) => priceHistory[item.id]).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
        </Select>
      </div>
      <div className="price-summary"><strong>{formatMoney(values.at(-1))}</strong><span><ArrowDownRight size={16} /> {t(change + "% over the period", "期间变化 " + change + "%")}</span></div>
      <div className="plot-shell"><PricePlot values={values} formatValue={formatMoney} /></div>
      <div className="plot-foot"><span>{t("8 sample observations, tax and shipping excluded", "8 个示例报价，不含税费和运费")}</span><button className="text-button" onClick={() => onEvidence(row)}>{t("Open setup evidence", "查看报价证据")} <ArrowUpRight size={15} /></button></div>
    </article>
  </div>;
}

function AgentPage({ onCopy }) {
  const { t } = useLocale();
  const [tool, setTool] = useState("compare_setups");
  const agents = {
    compare_setups: { label: t("Compare setups", "对比配置"), result: { cohort: "text.qwen2.5-7b.q4-k-m.4k", metric: "decode_tokens_per_second", rows: [{ id: "rtx-4090", value: 148, evidence_id: "DEMO/rtx-4090/text/short" }], excluded: [{ id: "rtx-5090", reason: "estimate_only" }], revision: "demo-2026-11-20" } },
    get_evidence: { label: t("Read evidence", "读取证据"), result: { id: "DEMO/rtx-4090/text/short", kind: "illustrative_lab_record", artifact: "Qwen2.5 7B Instruct Q4_K_M", context_tokens: 4096, warm: true, value: 148, unit: "tok/s", revision: "demo-2026-11-20" } },
    price_history: { label: t("Read prices", "读取价格"), result: { id: "rtx-3090", market: "US", currency: "USD", condition: "used_gpu_build", example_quotes: priceHistory["rtx-3090"], revision: "demo-2026-11-20" } },
  };
  const json = JSON.stringify(agents[tool].result, null, 2);
  return <div className="interior">
    <div className="page-heading"><h1>{t(wikiEntry("agents").title, "智能体接口")}</h1><p>{t(wikiEntry("agents").summary, "查看外部智能体查询网站证据的示例。")}</p><a className="text-button" href="#wiki/agent-discovery">{t("Crawler and agent discovery", "爬虫与智能体发现")} <ArrowUpRight size={14} aria-hidden="true" /></a></div>
    <article className="panel agent-panel"><div className="plot-head"><div><h2>{t("Evidence API examples", "证据 API 示例")}</h2><p>{t("Illustrative MCP tool responses", "MCP 工具响应示例")}</p></div><button className="btn outline" onClick={() => onCopy(json, t("JSON copied", "已复制 JSON"))}><Clipboard size={16} /> {t("Copy JSON", "复制 JSON")}</button></div>
      <div className="agent-tools">{Object.entries(agents).map(([key, info]) => <button className={"btn outline " + (tool === key ? "picked" : "")} aria-pressed={tool === key} key={key} onClick={() => setTool(key)}><CodeXml size={16} />{info.label}</button>)}</div>
      <pre dir="ltr"><code>{json}</code></pre>
    </article>
  </div>;
}

function App() {
  const { t, locale } = useLocale();
  const [state, setState] = useState(initialState);
  const [{ name: page, model, slug, focus }, setRoute] = useState(routeFrom);
  const [panel, setPanel] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [toast, setToast] = useState("");
  const [manualCopy, setManualCopy] = useState("");
  const set = (patch) => setState((old) => ({ ...old, ...patch }));
  useEffect(() => { try { localStorage.setItem(versionKey, JSON.stringify(state)); } catch {} }, [state]);
  useEffect(() => {
    if (!toast) return;
    const id = setTimeout(() => setToast(""), 2700);
    return () => clearTimeout(id);
  }, [toast]);
  useEffect(() => {
    const handle = () => { setRoute(routeFrom()); setPanel(null); window.scrollTo(0, 0); };
    window.addEventListener("hashchange", handle);
    window.addEventListener("popstate", handle);
    return () => { window.removeEventListener("hashchange", handle); window.removeEventListener("popstate", handle); };
  }, []);
  const explore = () => document.getElementById("explore")?.scrollIntoView({ behavior: "smooth", block: "start" });
  const go = (url, top = true) => {
    const hash = url.startsWith("#") ? url : "#" + url;
    setRoute(routeFrom(hash));
    setPanel(null);
    if (location.hash !== hash) {
      try { history.pushState(null, "", hash); }
      catch { location.hash = hash; }
    }
    if (top) window.scrollTo({ top: 0, behavior: "smooth" });
  };
  const navigate = (name, top) => go(routes[name], top);
  const copy = async (value, message) => {
    try { await navigator.clipboard.writeText(value); setToast(message); }
    catch { setManualCopy(value); }
  };
  const share = () => {
    const next = new URL(location.href);
    next.hash = "explorer";
    next.search = new URLSearchParams({ ...state, compare: state.compare.join(",") }).toString();
    copy(next.toString(), "Comparison link copied");
  };
  const onCompare = (id) => {
    if (!state.compare.includes(id) && state.compare.length >= 4) { setToast("You can compare up to four setups."); return; }
    set({ compare: state.compare.includes(id) ? state.compare.filter((item) => item !== id) : [...state.compare, id] });
  };
  const addToCompare = (id) => {
    const others = state.compare.filter((item) => item !== id);
    set({ compare: [id, ...others].slice(0, 4) });
    setSelectedId(id);
    go("#explorer", false);
    requestAnimationFrame(() => document.getElementById("comparison")?.scrollIntoView());
  };
  const onEvidence = (row) => { setSelectedId(row.id); setPanel({ kind: "evidence", row }); };
  const openMethod = () => setPanel({ kind: "method" });
  const openBrowse = () => setPanel({ kind: "browse" });
  const workload = workloads[state.work];
  const target = state[state.work + "Target"];
  const pointRows = configurations.map((row) => ({ ...row, price: row.prices[state.region], value: rowValue(row, state.work, state.context), eligible: !limitReason(row, state) }));
  const points = pointRows.filter(({ price, value }) => price != null && value != null);
  const matching = points.filter((row) => row.eligible && row.price <= state.budget);
  const best = [...matching].sort((a, b) => state.condition === "all" ? a.price - b.price : workload.lowerBetter ? a.value - b.value : b.value - a.value)[0];
  const result = state.flow === "machine" ? configurations.find((row) => row.id === state.machine) : best;
  const highlightedId = points.some((point) => point.id === selectedId) ? selectedId : result?.id;
  const showEvidence = (id) => onEvidence(configurations.find((row) => row.id === id));
  const comparisons = state.compare.map((id) => configurations.find((row) => row.id === id));
  return <>
    <Header page={page} navigate={navigate} />
    <main className="main-shell">
      <LocaleStatus />
      {page === "Explorer" ? <>
        <Hero onExplore={explore} onMethod={openMethod} />
        <Highlights go={go} />
        <Modes active={state.flow} onChoose={(flow) => { set({ flow }); requestAnimationFrame(explore); }} />
        <ExploreLenses go={go} />
        <section id="explore" className="explore-section">
          <div className="section-heading">
            <div><h2>{state.flow === "machine" ? t("What can my machine run?", "我的设备能运行哪些模型？") : state.flow === "shop" ? t("Find a build in your budget", "查找预算内的配置") : t(wikiEntry("explorer").title, "探索硬件与性能")}</h2><p>{state.flow === "machine" ? t("Choose a setup to see fit, benchmark evidence, and missing runs.", "选择配置后查看模型适配性、测试证据及缺失测试。") : t(wikiEntry("explorer").summary, "以工作负载、预算和测试条件为依据比较配置。")}</p></div>
            <div className="section-cta"><a className="btn dark" href={hrefFor("goals")}
              onClick={__FASTEST_RELEASE_ORIGIN__ ? undefined : (event) => { event.preventDefault(); go("#goals"); }}>
              <SlidersHorizontal size={16} /> {t("Compare by goals", "按目标对比")}</a><button className="btn outline" onClick={share}><ExternalLink size={16} /> {t("Share view", "分享视图")}</button></div>
          </div>
          {state.flow === "machine" && <div className="machine-select"><Select label="Your machine" value={state.machine} onChange={(e) => { set({ machine: e.target.value }); setSelectedId(e.target.value); }}>{configurations.filter((row) => row.kind !== "cloud").map((row) => <option key={row.id} value={row.id}>{row.name} / {row.detail.split(" · ").at(-1)}</option>)}</Select></div>}
          <Filters state={state} set={set} activeCount={matching.length} target={target} />
          <div className="explorer-grid">
            <article className="panel plot-panel">
              <div className="plot-head"><div><h3>{workload.title}</h3><p>{meta(workload.artifact)}</p></div><div className="segmented" aria-label="Chart or table">
                <button className={state.chart === "plot" ? "active" : ""} aria-label={t("Tradeoff chart", "取舍图")} aria-pressed={state.chart === "plot"} onClick={() => set({ chart: "plot" })}><ChartScatter size={15} /><span>{t("Tradeoffs", "取舍图")}</span></button>
                <button className={state.chart === "table" ? "active" : ""} aria-label={t("Table", "表格")} aria-pressed={state.chart === "table"} onClick={() => set({ chart: "table" })}><Table2 size={15} /><span>{t("Table", "表格")}</span></button>
              </div></div>
              <div className="plot-meta"><span>{meta(workload.method)}</span><label>Match
                <select value={state.rule} onChange={(e) => set({ rule: e.target.value })} aria-label="Matching rule"><option value="task">Same task</option><option value="cuda">CUDA only</option></select>
              </label></div>
              {state.chart === "plot" ? <div className="plot-shell"><ScatterPlot points={points} workload={workload} region={state.region} budget={state.budget} target={target} selectedId={highlightedId} onSelect={(id) => onEvidence(configurations.find((row) => row.id === id))} showFrontier={state.condition !== "all"} /></div> :
                <CompareTable rows={configurations} state={state} workload={workload} onEvidence={onEvidence} all />}
              <div className="plot-foot"><div className="legend"><span><i className="solid" />Eligible</span><span><i className="hollow" />Context only</span>{state.condition !== "all" ? <span><i className="dashed" />Efficiency frontier</span> : <span>Mixed build conditions</span>}<span><i className="area" />Both targets met</span></div><button className="text-button" onClick={openMethod}><CircleHelp size={15} /> Method</button></div>
            </article>
            <ResultCard row={result} state={state} workload={workload} target={target} onEvidence={onEvidence} onCompare={onCompare} picked={!!result && state.compare.includes(result.id)} />
          </div>
        </section>
        <section className="ranking-section" aria-labelledby="ranking-title">
          <div className="section-heading"><div><h2 id="ranking-title">{t("Benchmark ranking", "评测排名")}</h2>
            <p>{workload.label}. {workload.lowerBetter ? "Lower is better." : "Higher is better."} Only setups eligible for this comparison are ranked.</p>
          </div></div>
          <div className="panel ranking-panel">
            <div className="plot-shell"><RankingPlot points={points} workload={workload} region={state.region} target={target} selectedId={highlightedId} onSelect={showEvidence} /></div>
            <div className="plot-foot"><span>Select a bar to inspect the benchmark evidence.</span><button className="text-button" onClick={openMethod}><CircleHelp size={15} /> Method</button></div>
          </div>
        </section>
        <div id="comparison"><CompareTable rows={comparisons} state={state} workload={workload} onEvidence={onEvidence} onCompare={onCompare} onBrowse={openBrowse} /></div>
        <CoverageMatrix onEvidence={(row, work, context) => { set({ work, context }); onEvidence(row); }} />
        <WikiDetails slug="explorer" go={go} onCopy={copy} />
      </> : page === "Price watch" ? <><PricePage state={state} set={set} onEvidence={(row) => setPanel({ kind: "price", row })} /><WikiDetails slug="prices" go={go} onCopy={copy} /></>
        : page === "For agents" ? <><AgentPage onCopy={copy} /><WikiDetails slug="agents" go={go} onCopy={copy} /></>
        : page === "Compare" ? <GoalPage state={state} set={set} go={go} onCopy={copy} />
        : page === "Methods" ? <MethodsPage go={go} />
        : page === "Costs" ? <CostPage key={slug || "costs"} initialMethod={slug} go={go} />
        : page === "Catalog" && slug === "topics" ? <CatalogTopics go={go} />
        : page === "Catalog" && model ? <CatalogModelProfile id={model} go={go} />
        : page === "Catalog" || (page === "Models" && !slug) ? <>
          <SourceCatalog key={page + "/" + (slug || "")} initialKind={page === "Models" ? "models" : slug || "cards"} go={go} onCopy={copy} />
          <WikiDetails slug={slug === "runtimes" ? "runtimes" : page === "Models" ? "models" : "catalog"} go={go} onCopy={copy} />
        </> : <KnowledgePage screen={page} slug={slug} focus={focus} state={state} set={set} go={go} onCopy={copy} addToCompare={addToCompare} />}
      <footer><span>fastest.ai</span><small>{t("Demo snapshot", "演示快照")} / {new Intl.DateTimeFormat(locale, { dateStyle: "medium", timeZone: "UTC" }).format(Date.UTC(2026, 10, 20))}</small><button className="text-button" onClick={openMethod}>{t("Methodology", "评测方法")} <ArrowUpRight size={14} /></button></footer>
    </main>
    <Drawer panel={panel} close={() => setPanel(null)} state={state} onCompare={onCompare} onEvidence={onEvidence} go={go} />
    {!!toast && <div className="toast" role="status"><Check size={18} />{toast}</div>}
    {!!manualCopy && <div className="overlay"><div className="copy-dialog" role="dialog" aria-modal="true" aria-labelledby="copy-title"><h3 id="copy-title">Copy this value</h3><textarea aria-label="Value to copy" readOnly autoFocus onFocus={(e) => e.currentTarget.select()} value={manualCopy} /><button className="btn dark" onClick={() => setManualCopy("")}>Done</button></div></div>}
    <FeedbackBubble page={page} entity={slug} release={__FASTEST_PAGES__ && slug === "research" ? __FASTEST_RESEARCH_INDEX__.release : release} onCopy={copy} />
  </>;
}

createRoot(document.getElementById("root")).render(<LocaleProvider><App /></LocaleProvider>);
