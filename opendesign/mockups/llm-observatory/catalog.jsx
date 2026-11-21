import React, { useEffect, useMemo, useRef, useState } from "react";
import { ArrowDownRight, ArrowUpRight, ChevronLeft, ChevronRight, Cpu, Layers3, List, Search } from "lucide-react";
import topics from "./catalog-topics.json";
import { catalogPath } from "./catalog-paths.mjs";
import { modelCard, renderCard } from "./catalog-card.mjs";
import { CatalogCompare } from "./catalog-compare";
import { modelCollections, modelTags, queryModelCatalog } from "./catalog-search.mjs";
import { useLocale } from "./locale";

const pageSize = 30;
const modelIdentities = __FASTEST_MODEL_IDENTITIES__;
const modelCatalog = __FASTEST_MODEL_CATALOG__;
const discovery = __FASTEST_MODEL_DISCOVERY__;
const catalogRelease = __FASTEST_CATALOG_RELEASE__;
const localCatalogRelease = __FASTEST_LOCAL_CATALOG_RELEASE__;
const localModelIds = new Set(__FASTEST_LOCAL_MODEL_IDS__);
const manifestPath = (catalogRelease || localCatalogRelease) &&
  `${catalogRelease ? "" : "local-catalog/"}catalog/${catalogRelease || localCatalogRelease}/manifest.json`;
const runtimes = __FASTEST_RUNTIMES__;
const hardwareCatalog = __FASTEST_HARDWARE_DIRECTORY__;
const modifiedCardTag = "memory-modified";
const machineKinds = ["Creator-reported build", "Complete factory configuration", "Partial configuration", "Component reference", "llmfit example preset", "Manufacturer system reference"];
const machineRows = hardwareCatalog.machines.toSorted((left, right) =>
  Number(right.kind === "Creator-reported build") - Number(left.kind === "Creator-reported build"));
const runtimeCategories = [...new Set(runtimes.map(row => row.category))].sort();
const { byId: modelById, ...modelViews } = modelCollections(modelCatalog.models, discovery, __FASTEST_SUPPLEMENTAL_MODELS__);
const modelStats = new Map([...discovery.popular, ...discovery.small].map(row => [row.id, row]));

const tabs = [
  {
    key: "cards", title: "Cards", icon: Cpu, rows: hardwareCatalog.cards, scope: "Graphics card references",
    titleZh: "显卡", scopeZh: "显卡资料",
    description: "Browse stock GPUs and memory-modified variants with linked specifications, seller listings and research.",
    descriptionZh: "浏览原厂显卡与显存改装版，并查看对应规格、卖家商品页和研究资料。",
  },
  {
    key: "machines", title: "Machines", icon: Layers3, rows: machineRows, scope: "Machine and component records",
    titleZh: "整机", scopeZh: "整机与部件记录",
    description: "Browse real builds documented by their builders, factory configurations, hardware references, and llmfit example presets.",
    descriptionZh: "浏览装机者公开记录的实际配置、厂商出厂配置、硬件资料及 llmfit 示例配置。",
  },
  {
    key: "models", title: "Models", icon: List, rows: modelViews.all, scope: "Model metadata records",
    titleZh: "模型", scopeZh: "模型元数据",
    description: "Search the pinned llmfit snapshot and reviewed publisher metadata. Original repositories provide model files and terms.",
    descriptionZh: "搜索固定版本的 llmfit 目录和经过审核的发布方元数据。模型文件和使用条款请查阅原始仓库。",
  },
  {
    key: "runtimes", title: "Runtimes", icon: ArrowDownRight, rows: runtimes, scope: "Upstream runtime projects",
    titleZh: "推理框架", scopeZh: "上游推理框架",
    description: "Desktop apps, engines, servers, and libraries with pinned upstream versions and format and platform notes.",
    descriptionZh: "查看桌面应用、推理引擎、服务器与库的固定上游版本、格式与平台信息。",
  },
];
const licenseTags = Array.from(new Set(modelViews.all.map(({ license }) => license).filter(Boolean))).sort();
const validKind = (kind) => tabs.some((tab) => tab.key === kind) ? kind : "cards";
const sourceLabelsZh = {
  "Creator-reported build": "装机者公开配置",
  "Complete factory configuration": "完整出厂配置",
  "Manufacturer system reference": "厂商整机资料",
  "Partial configuration": "部分配置",
  "Component reference": "部件资料",
  "llmfit example preset": "llmfit 示例配置",
  "llmfit hardware lookup; no research benchmark linked": "llmfit 硬件表，暂无关联研究测试",
  "Reported component in research notes": "研究笔记中记录的部件",
  "GPU product/configuration reference;not a complete tested build": "显卡产品或配置资料，整机未作完整测试",
  "Caption-reported partial configuration /comparison;not a full build": "字幕记录的部分配置或对比，整机信息不完整",
  "configuration as explicitly narrated;creator/third-party claim,not independently verified": "视频口述配置，作者或第三方报告，尚未独立核实",
  "Text generation": "文本生成",
  "Image and text to text": "图文输入，文本输出",
  "Text to speech": "文字转语音",
  "Feature extraction": "特征提取",
  "Speech recognition": "语音识别",
  "Audio to audio": "音频转音频",
  "Sentence similarity": "句子相似度",
  "Image to text": "图像转文本",
};

const taskAndFormatTags = Array.from(new Set(modelViews.all
  .flatMap((row) => modelTags(row, modelIdentities[row.id]))
  .filter((value) => !value.endsWith(" parameters")))).sort();
const emptyFilters = { query: "", tag: "", license: "", page: 1, view: "popular" };

function catalogFiltersFromLocation() {
  const params = new URLSearchParams(location.hash.split("?")[1]);
  const page = Number(params.get("page"));
  const view = params.get("view");
  return {
    query: params.get("q") ?? "",
    tag: params.get("tag") ?? "",
    license: params.get("license") ?? "",
    page: Number.isSafeInteger(page) && page > 0 ? page : 1,
    view: Object.hasOwn(modelViews, view) ? view : "popular",
  };
}

function saveCatalogFilters(filters, paginate) {
  const params = new URLSearchParams();
  if (filters.query) params.set("q", filters.query);
  if (filters.tag) params.set("tag", filters.tag);
  if (filters.license) params.set("license", filters.license);
  if (filters.view !== "popular") params.set("view", filters.view);
  if (filters.page > 1) params.set("page", String(filters.page));
  const route = location.hash.split("?")[0] || "#catalog/models";
  const query = params.toString();
  const hash = route + (query ? "?" + query : "");
  if (hash === location.hash) return;
  try {
    if (paginate) history.pushState(null, "", hash);
    else history.replaceState(null, "", hash);
  } catch {
    location.hash = hash;
  }
}

function formatSourceDetail(row, t) {
  const build = row.detail.match(/^(.*) \/ (\d+) of 6 build fields reported$/);
  if (build) {
    const [, label, count] = build;
    return t(label, sourceLabelsZh[label] ?? label) + " / " + t(
      "{count} of 6 build fields reported", "已记录 6 项配置中的 {count} 项", { count },
    );
  }
  return t(row.detail, row.detailZh ?? sourceLabelsZh[row.detail] ?? row.detail);
}

const tuning = [
  { heading: ["NVIDIA GeForce and workstation cards", "NVIDIA GeForce 和工作站显卡"], body: ["Record the card, CUDA backend, runtime and driver, and whether decoding is single-user or batched.", "记录显卡、CUDA 后端、推理框架和驱动版本，并注明是单用户还是批量解码。"] },
  { heading: ["AMD Radeon and Instinct", "AMD Radeon 和 Instinct"], body: ["Track exact card support and the tested runtime backend as separate fields.", "分别记录支持的显卡型号与实测推理后端。"] },
  { heading: ["Intel Arc", "Intel Arc"], body: ["Track driver and runtime coverage per card and workload.", "按显卡型号和工作负载记录驱动与推理框架的支持情况。"] },
  { heading: ["Apple Silicon", "Apple 芯片"], body: ["Record chip, unified memory, and the tested runtime backend.", "记录芯片型号、统一内存容量和实测推理后端。"] },
  { heading: ["vGPU unlock", "vGPU 解锁"], body: ["Community case label. Compatibility, authorization, and results are unverified.", "社区案例，兼容性、授权情况和测试结果尚未核实。"] },
];

function safeSource(value) {
  try {
    const url = new URL(value);
    return url.protocol === "https:" && !url.username && !url.password ? url.href : undefined;
  } catch {
    return undefined;
  }
}

function SourceLink({ href, children, label }) {
  const { t } = useLocale();
  const safeHref = safeSource(href);
  return safeHref ? <a className="catalog-source-link" href={safeHref} target="_blank" rel="noopener noreferrer" aria-label={label}>
    {children} <ArrowUpRight size={13} aria-hidden="true" />
  </a> : <span className="catalog-muted">{t("Unavailable", "暂不可用")}</span>;
}

function PrototypeLink({ href, children, go }) {
  return <a className="text-button catalog-prototype-link" href={href} onClick={(event) => {
    if (!go || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    go(href);
  }}>{children} <ArrowUpRight size={13} aria-hidden="true" /></a>;
}

export function CatalogModelProfile({ id, go }) {
  const { t } = useLocale();
  const row = modelById.get(id);
  const params = new URLSearchParams(location.hash.split("?")[1]);
  params.delete("model");
  const index = "#catalog/models" + (params.size ? "?" + params : "");
  if (!row) return <section className="catalog-profile profile-shell">
    <PrototypeLink href={index} go={go}>{t("Back to models", "返回模型目录")}</PrototypeLink>
    <h1>{t("Model not found", "找不到模型")}</h1>
  </section>;

  const runtimeRoot = "local-catalog/catalog/" + localCatalogRelease;
  const card = modelCard({ ...row, identity: modelIdentities[row.id] }, localCatalogRelease, { runtimeRoot });
  const evaluation = card.publisherEvaluations;
  const localProfile = localModelIds.has(id) && "local-catalog/" + catalogPath(localCatalogRelease, "models", id);
  const markdown = localProfile ? null : renderCard(card, {
    release: localCatalogRelease, pathname: id + ".html", markdown: true, local: true,
  });
  const fields = rows => <dl className="profile-fields">{rows.map(([label, value, href]) => <div key={label}>
    <dt>{label}</dt><dd>{href ? <a href={href}>{value}</a> : value}</dd>
  </div>)}</dl>;
  return <article className="catalog-profile profile-shell">
    <PrototypeLink href={index} go={go}>{t("Back to models", "返回模型目录")}</PrototypeLink>
    <header className="profile-hero">
      <p className="profile-kicker">{t("Model repository", "模型仓库")}</p><h1><bdi>{id}</bdi></h1>
      <div className="profile-actions"><SourceLink href={row.source}>{t("Open source", "查看来源")}</SourceLink>
        {localProfile ? <>
          <a href={localProfile}>{t("Standalone profile", "独立资料页")}</a>
          <a href={localProfile.replace(/\.html$/, ".md")}>Markdown</a>
        </> : <a href={"data:text/markdown;charset=utf-8," + encodeURIComponent(markdown)} download={id.split("/")[1] + ".md"}>Markdown</a>}</div>
    </header>
    <section className="profile-section"><h2>{t("Repository details", "仓库详情")}</h2>{fields(card.fields)}</section>
    {card.sections.map(({ title, fields: rows }) => <section key={title} className="profile-section"><h2>{title}</h2>{fields(rows)}</section>)}
    {evaluation && <section className="profile-section"><h2>{evaluation.title}</h2><p>{evaluation.summary}</p>
      <table className="profile-chart-table">
        <thead><tr>{evaluation.headings.map(heading => <th key={heading} scope="col">{heading}</th>)}</tr></thead>
        <tbody>{evaluation.rows.map(([[benchmark, url], ...cells]) => <tr key={cells.at(-1)[1]}>
          <th scope="row"><a href={url}>{benchmark}</a></th>
          {cells.map(([value, href], i) => <td key={evaluation.headings[i + 1]}>{href ? <a href={href}>{value}</a> : value}</td>)}
        </tr>)}</tbody>
      </table>
    </section>}
    <section className="profile-section"><h2>{t("Evidence", "证据")}</h2><p>{card.evidence}</p></section>
  </article>;
}

export function CatalogTopics({ go }) {
  const { t } = useLocale();
  return <div className="deep-page source-catalog">
    <div className="deep-heading"><div><h1>{t("Catalog topics", "目录主题")}</h1>
      <p>{t("Browse hardware, models, tools and research by topic.", "按主题浏览硬件、模型、工具与研究。")}</p></div>
      <PrototypeLink href="#catalog/cards" go={go}>{t("Back to catalog", "返回目录")}</PrototypeLink>
    </div>
    {topics.groups.map(group => <section key={group.label} className="catalog-provenance">
      <h2>{t(group.label, group.zh)}</h2>
      <div className="catalog-nav">{group.topics.map(({ name, zh, href }) =>
        <PrototypeLink key={name} href={href} go={go}>{t(name, zh)}</PrototypeLink>)}</div>
    </section>)}
    <details className="catalog-provenance">
      <summary>{t("Discovery references", "发现来源")}</summary>
      <ul>{topics.refs.map(({ label, href }) => <li key={href}><SourceLink href={href}>{label}</SourceLink></li>)}</ul>
    </details>
  </div>;
}

function Pager({ page, pages, onPage, label, number }) {
  const { t } = useLocale();
  const current = number.format(page);
  const total = number.format(pages);
  return <nav className="catalog-pager" aria-label={label}>
    <button type="button" className="btn outline" disabled={page <= 1} onClick={() => onPage(page - 1)}>
      <ChevronLeft size={15} aria-hidden="true" /> {t("Previous", "上一页")}
    </button>
    <span>{t("Page {current} of {total}", "第 {current} 页，共 {total} 页", { current, total })}</span>
    <button type="button" className="btn outline" disabled={page >= pages} onClick={() => onPage(page + 1)}>
      {t("Next", "下一页")} <ChevronRight size={15} aria-hidden="true" />
    </button>
  </nav>;
}

export function SourceCatalog({ go, onCopy, initialKind }) {
  const { language, t } = useLocale();
  const number = useMemo(() => new Intl.NumberFormat(language), [language]);
  const [active, setActive] = useState(() => validKind(initialKind));
  const [filters, setFilters] = useState(catalogFiltersFromLocation);
  const [picks, setPicks] = useState([]);
  const [runtimeWatch, setRuntimeWatch] = useState(null);
  const { query, tag, license, page, view } = filters;
  const tableTop = useRef(null);
  useEffect(() => {
    if (active !== "models" && active !== "cards") return;
    const restore = () => setFilters(catalogFiltersFromLocation());
    window.addEventListener("popstate", restore);
    window.addEventListener("hashchange", restore);
    return () => {
      window.removeEventListener("popstate", restore);
      window.removeEventListener("hashchange", restore);
    };
  }, [active]);
  useEffect(() => {
    if (!__FASTEST_PAGES__ || active !== "runtimes") return;
    const controller = new AbortController();
    fetch("/api/runtime-releases", { cache: "no-store", signal: controller.signal })
      .then(response => response.ok ? response.json() : null)
      .then(watch => { if (watch?.runtimes?.length) setRuntimeWatch(watch); })
      .catch(() => {});
    return () => controller.abort();
  }, [active]);

  const tab = tabs.find((entry) => entry.key === active);
  const modelRows = modelViews[view];
  const { rows, total: resultCount, pages, current, start } = useMemo(() => {
    if (tab.key === "models") return queryModelCatalog(modelRows, modelIdentities, { ...filters, ranked: view !== "all" });
    const terms = query.toLowerCase().trim().split(/\s+/).filter(Boolean);
    const filtered = terms.length || tag ? tab.rows.filter((row) => {
      const category = row.memoryModified ? modifiedCardTag : row.category ?? row.kind;
      if (tag && category !== tag) return false;
      const text = [row.id, row.name, row.detail, row.tag, row.platform, ...(row.aliases ?? [])].join(" ").toLowerCase();
      return terms.every((term) => text.includes(term));
    }) : tab.rows;
    const pages = Math.max(1, Math.ceil(filtered.length / pageSize));
    const current = Math.min(page, pages);
    const start = (current - 1) * pageSize;
    return { rows: filtered.slice(start, start + pageSize), total: filtered.length, pages, current, start };
  }, [tab, filters, query, page, tag, view, modelRows]);
  const hardwareTab = active === "cards" || active === "machines";
  const comparable = active === "cards" || active === "models";
  const { asOf, coverage } = hardwareCatalog;
  const scope = t(tab.scope, tab.scopeZh);
  const search = t("Search " + tab.title.toLowerCase(), "搜索" + tab.titleZh);
  const interval = `${number.format(start + 1)}–${number.format(start + rows.length)}`;
  const matches = number.format(resultCount);
  const total = number.format(active === "models" ? modelRows.length : tab.rows.length);

  function selectTab(key) {
    if (key === active) return;
    setRuntimeWatch(null);
    setActive(key);
    setFilters(emptyFilters);
    setPicks([]);
    go?.("#catalog/" + key);
  }

  function updateFilters(patch, paginate = false) {
    const next = { ...filters, page: 1, ...patch };
    setFilters(next);
    if (active === "models" || active === "cards") saveCatalogFilters(next, paginate);
  }

  const setPage = (newPage) => updateFilters({ page: newPage }, true);

  function pageFromBottom(next) {
    setPage(next);
    tableTop.current?.scrollIntoView({ block: "start" });
  }

  return <div className="deep-page source-catalog">
    <div className="deep-heading">
      <div>
        <h1>{t("Source catalog", "资料目录")}</h1>
        <p>{t("Browse linked cards, machine records, models and runtimes. Use the detailed prototype pages to explore sample benchmarks and build plans.", "浏览带来源链接的显卡、整机、模型和推理框架。打开详情页查看基准测试与装机方案示例。")}</p>
      </div>
      <div className="catalog-prototype-links">
        <PrototypeLink href="#catalog/topics" go={go}>{t("Browse topics", "浏览主题")}</PrototypeLink>
        <PrototypeLink href="#wiki/inference-frameworks" go={go}>{t("Inference frameworks", "推理框架")}</PrototypeLink>
        {hardwareTab && <PrototypeLink href={"#battle/" + active} go={go}>{t("Hardware battles", "硬件对决")}</PrototypeLink>}
        <PrototypeLink href="#machines" go={go}>{t("Detailed prototype machines", "查看整机配置示例")}</PrototypeLink>
        <PrototypeLink href="#models/qwen25-7b" go={go}>{t("Compare a sample model", "比较模型运行表现")}</PrototypeLink>
        <PrototypeLink href="#wiki/gpu-topology" go={go}>{t("GPU topology", "GPU 拓扑")}</PrototypeLink>
      </div>
    </div>

    <div className="catalog-nav" aria-label={t("Catalog sections", "目录分类")}>
      {tabs.map(({ key, title, titleZh, icon: Icon, rows: entries }) => <button type="button" key={key} onClick={() => selectTab(key)} aria-pressed={active === key} className="catalog-tab">
        <Icon size={16} aria-hidden="true" /><span>{t(title, titleZh)}</span><span className="catalog-tab-count">{number.format(entries.length)}</span>
      </button>)}
    </div>

    <section aria-labelledby="catalog-scope">
      <div className="catalog-section-line">
        <div>
          <h2 id="catalog-scope">{scope}</h2>
          <p>{t(tab.description, tab.descriptionZh)}</p>
        </div>
        {active === "models" && <SourceLink href={modelCatalog.upstream} label={t("Open the pinned llmfit source catalog", "打开固定版本的 llmfit 源目录")}>
          {t("llmfit snapshot", "llmfit 快照")} <code>{modelCatalog.commit.slice(0, 8)}</code>
        </SourceLink>}
        {active === "runtimes" && runtimeWatch && <SourceLink href={runtimeWatch.html}>
          {t("Runtime release watch", "推理框架版本追踪")}
        </SourceLink>}
      </div>
      {hardwareTab && <p className="catalog-muted">
        {t("Snapshot {date}", "快照日期 {date}", { date: asOf })} ·{" "}
        {active === "cards" ? t("{cards} card references, {unresolved} unresolved", "共 {cards} 条显卡资料，其中 {unresolved} 条型号待确认", {
          cards: number.format(coverage.cards), unresolved: number.format(coverage.unresolvedCardReferences),
        }) : t("{complete} complete factory configurations, {partial} partial configurations, {components} component references, {systems} system references, {presets} example presets", "完整出厂配置 {complete} 条、部分配置 {partial} 条、部件资料 {components} 条、整机资料 {systems} 条、示例配置 {presets} 条", {
          complete: number.format(coverage.completeBuilds), partial: number.format(coverage.partialMachines),
          components: number.format(coverage.researchComponentReferences),
          systems: number.format(coverage.manufacturerMachines - coverage.completeBuilds), presets: number.format(coverage.upstreamPresets),
        })} ·{" "}
        {active === "machines" && coverage.creatorBuilds > 0 && <>{t("{builds} creator-reported builds", "装机者公开配置 {builds} 条", {
          builds: number.format(coverage.creatorBuilds),
        })} ·{" "}</>}
        {active === "cards" && <>{t("{specs} with manufacturer or board-partner specs", "{specs} 条附有厂商或板卡合作伙伴规格", {
          specs: number.format(coverage.cardsWithVendorSpecs),
        })} ·{" "}</>}
        {active === "cards" && coverage.memoryModifiedCards > 0 && <>{t("{modified} memory-modified variants", "{modified} 种显存改装版", {
          modified: number.format(coverage.memoryModifiedCards),
        })} ·{" "}</>}
        {t("No reviewed benchmark results", "暂无经过审核的基准测试结果")}
        {manifestPath && <> · <a className="catalog-source-link" href={manifestPath}>{t("Snapshot sources and counts", "快照来源与数量")}</a></>}
      </p>}
      {active === "models" && <>
        <div className="catalog-nav" aria-label={t("Model collections", "模型分类")}>
          {[
            ["popular", t("Popular", "热门"), discovery.popular.length],
            ["small", t("Small · ≤4B", "小模型 · ≤40 亿参数"), discovery.small.length],
            ...(modelViews.recent.length ? [["recent", t("Recent releases", "近期发布"), modelViews.recent.length]] : []),
            ["all", t("All models", "全部模型"), modelViews.all.length],
          ].map(([id, title, count]) => <button key={id} className="catalog-tab" type="button" aria-pressed={view === id}
            onClick={() => updateFilters({ view: id }, true)}>{title}<span className="catalog-tab-count">{number.format(count)}</span></button>)}
        </div>
        {view === "recent" && <p className="catalog-muted">
          {t("Reviewed publisher records, newest repository revisions first.", "经过审核的发布方记录，按仓库版本日期从新到旧排列。")}
        </p>}
        {(view === "popular" || view === "small") && <p className="catalog-muted">
          {t("Ranked by Hugging Face Hub downloads. Text-generation repositories with documented SafeTensors size.", "按 Hugging Face Hub 下载量排序。仅包含 SafeTensors 参数量已记录的文本生成仓库。")}{" "}
          <SourceLink href={discovery.source}>{discovery.capturedAt.slice(0, 10)}</SourceLink>
        </p>}
      </>}
      <div className="catalog-tools" ref={tableTop}>
        <label className="deep-search">
          <Search size={16} aria-hidden="true" />
          <input type="search" aria-label={search} placeholder={active === "models" ? t("Search owner/model or metadata", "搜索组织名、模型名或元数据") : search} value={query} onChange={(event) => updateFilters({ query: event.target.value })} />
        </label>
        {active === "cards" && coverage.memoryModifiedCards > 0 && <label className="catalog-filter"><span>{t("Card type", "显卡类型")}</span>
          <select value={tag} onChange={(event) => updateFilters({ tag: event.target.value })}>
            <option value="">{t("All cards", "全部显卡")}</option>
            <option value={modifiedCardTag}>{t("Memory-modified GPUs", "显存改装显卡")}</option>
          </select>
        </label>}
        {active === "machines" && <label className="catalog-filter"><span>{t("Record type", "记录类型")}</span>
          <select value={tag} onChange={(event) => updateFilters({ tag: event.target.value })}>
            <option value="">{t("Any", "全部")}</option>
            {machineKinds.map((value) => <option key={value} value={value}>{t(value, sourceLabelsZh[value])}</option>)}
          </select>
        </label>}
        {active === "runtimes" && <label className="catalog-filter"><span>{t("Project category", "项目分类")}</span>
          <select value={tag} onChange={(event) => updateFilters({ tag: event.target.value })}>
            <option value="">{t("Any", "全部")}</option>
            {runtimeCategories.map(category => <option key={category}>{category}</option>)}
          </select>
        </label>}
        {active === "models" && <label className="catalog-filter"><span>{t("Task or format", "任务或格式")}</span>
          <select value={tag} onChange={(event) => updateFilters({ tag: event.target.value })}>
            <option value="">{t("Any", "全部")}</option>
            {taskAndFormatTags.map((value) => <option key={value} value={value}>{t(value, sourceLabelsZh[value] ?? value)}</option>)}
          </select>
        </label>}
        {active === "models" && <label className="catalog-filter"><span>{t("License tag", "许可证")}</span>
          <select value={license} onChange={(event) => updateFilters({ license: event.target.value })}>
            <option value="">{t("Any", "全部")}</option><option value="__missing">{t("Not listed", "未列出")}</option>
            {licenseTags.map((tag) => <option key={tag} value={tag}>{tag}</option>)}
          </select>
        </label>}
        <p className="catalog-count" role="status" aria-atomic="true">
          {rows.length ? t("{interval} of {matches}", "第 {interval} 条，共 {matches} 条", { interval, matches }) : t("No results", "没有结果")}
          {(query.trim() || tag || license) && <span>{t(" / {total} in catalog", " / 目录共 {total} 条", { total })}</span>}
        </p>
        {comparable && picks.length > 0 && <a className="text-button" href="#catalog-comparison" onClick={event => {
          event.preventDefault();
          document.getElementById("catalog-comparison")?.scrollIntoView({ block: "start" });
        }}>{t("Compare ({count}/4)", "对比（{count}/4）", { count: number.format(picks.length) })}</a>}
        {pages > 1 && <Pager page={current} pages={pages} onPage={setPage} number={number} label={t("Catalog pages at top", "顶部目录分页")} />}
      </div>
      {rows.length ? <div className="catalog-table-wrap">
        <table aria-label={scope} className="catalog-table">
          <thead><tr>{comparable && <th scope="col" className="catalog-compare-column">{t("Compare", "对比")}</th>}<th scope="col">{active === "models" ? t("Repository", "仓库") : t("Name", "名称")}</th><th scope="col">{active === "models" ? t("Model metadata", "模型元数据") : t("Record scope", "记录范围")}</th><th scope="col">{t("Source", "来源")}</th></tr></thead>
          <tbody>{rows.map((row) => {
            const separator = row.id.indexOf("/");
            const modelId = active === "models" && separator > 0;
            const modelQuery = new URLSearchParams(location.hash.split("?")[1]);
            if (modelId) modelQuery.set("model", row.id);
            const card = catalogRelease
              ? "/" + catalogPath(catalogRelease, active, row.id)
              : modelId ? "#catalog/models?" + modelQuery
                : "local-catalog/" + catalogPath(localCatalogRelease, active, row.id);
            const sourceUrl = safeSource(row.vendorSpec?.source ?? row.source);
            const picked = picks.some(entry => entry.id === row.id);
            const observed = active === "runtimes" && runtimeWatch?.runtimes.find(entry =>
              entry.id === row.id && entry.repositoryUrl === row.source);
            return <tr key={row.id}>
              {comparable && <td className="catalog-compare-column"><label>
                <input type="checkbox" aria-label={t("Compare {name}", "对比 {name}", { name: row.name })}
                  checked={picked} disabled={!picked && picks.length >= 4} onChange={event => {
                    const checked = event.target.checked;
                    setPicks(current => checked ? [...current, row] : current.filter(entry => entry.id !== row.id));
                  }} />
              </label></td>}
              <th scope="row">{modelId ? <a className="catalog-model-id catalog-row-link" href={card}><span>{row.id.slice(0, separator + 1)}</span>{row.id.slice(separator + 1)}</a> : <>
                <strong><a className="catalog-model-id catalog-row-link" href={card}>{row.name}</a></strong>
                {row.tag ? <small>{observed ? t("Pinned {tag}", "固定版本 {tag}", { tag: row.tag }) : row.tag}</small>
                  : row.id !== row.name && <small>{row.id}</small>}
              </>}</th>
              <td>{active === "models" ? <div className="catalog-tags">
                {row.discovery && <><span>#{number.format(row.discovery.rank)}</span>
                  <span>{t("{count} downloads", "{count} 次下载", { count: number.format(row.discovery.downloads) })}</span>
                  <span>{t("{count} parameters", "{count} 参数", { count: number.format(row.discovery.parameters) })}</span>
                  {row.discovery.gated && <span>{t("Access approval", "需要访问许可")}</span>}
                </>}
                {row.supplemental && <span>{t("Revision {date}", "版本日期 {date}", { date: row.supplemental.revisionDate })}</span>}
                {modelTags(row, modelIdentities[row.id]).map((value) => <span key={value}>{t(value, sourceLabelsZh[value] ?? value)}</span>)}
                {row.license && <span title={t("Model license metadata from the source catalog", "源目录中的模型许可证元数据")}>{row.license}</span>}
              </div> : <>{row.category && <small>{row.category}</small>}
                {row.platform && <small>{t(row.kind, sourceLabelsZh[row.kind])} · {t(row.platform, row.platform === "Builder site" ? "装机者网站" : row.platform)}</small>}
                {formatSourceDetail(row, t)}
                {observed && <div className="catalog-runtime-release">
                  <small>{observed.release ? <>
                    {t("Last observed stable release", "最近观测到的稳定版")}{" "}
                    <a href={observed.release.url}><bdi>{observed.release.tag}</bdi></a>
                  </> : t("No stable release observed", "暂未观测到稳定版")}</small>
                  <small>{t("Last successful refresh", "上次成功刷新")}{" "}
                    <time dateTime={observed.refreshedAt}>{observed.refreshedAt}</time></small>
                  {observed.stale && <small>{t("Release feed is stale", "发布源数据已过时")}</small>}
                  {observed.failed && <small>{t("Latest refresh failed", "最近一次刷新失败")}</small>}
                </div>}
              </>}</td>
              <td className="catalog-row-source">
                <SourceLink href={sourceUrl} label={t("Open source for {name}", "查看 {name} 的来源", { name: row.name })}>{t("Open source", "查看来源")}</SourceLink>
                {sourceUrl && <small title={sourceUrl}><bdi>{sourceUrl.replace("https://", "")}</bdi></small>}
                {observed && <SourceLink href={observed.watchUrl}
                  label={t("Open release watch for {name}", "查看 {name} 的版本追踪", { name: row.name })}>
                  {t("Release watch", "版本追踪")}
                </SourceLink>}
              </td>
            </tr>;
          })}</tbody>
        </table>
      </div> : <p className="catalog-empty">{t("Try a different name, ID, or detail.", "试试其他名称、ID 或关键词。")}</p>}

      {pages > 1 && <div className="catalog-bottom"><Pager page={current} pages={pages} onPage={pageFromBottom} number={number} label={t("Catalog pages at bottom", "底部目录分页")} /></div>}

      {comparable && picks.length > 0 && <CatalogCompare kind={active} chosen={picks} modelStats={modelStats}
        clear={() => setPicks([])} remove={id => setPicks(current => current.filter(row => row.id !== id))} />}

      {active === "models" && <details className="catalog-provenance">
        <summary>{t("Source, coverage, and MIT notice", "来源、收录范围和 MIT 声明")}</summary>
        <p>{t(modelCatalog.note, "模型元数据来自固定版本的 llmfit 目录，每条记录链接至原始 Hugging Face 仓库。目录许可证不适用于模型权重。模型许可信息以原始仓库为准。")}</p>
        <p>{t("{count} upstream records at", "上游共 {count} 条记录，版本", { count: number.format(modelCatalog.sourceRows) })} <code>{modelCatalog.commit}</code></p>
        {manifestPath && <p><a className="catalog-source-link" href={manifestPath}>{t("Release coverage and provenance", "发布版覆盖范围与来源")}</a></p>}
        <SourceLink href={modelCatalog.catalogLicenseUrl}>{t("Upstream license", "上游许可证")}</SourceLink>
        <pre>{modelCatalog.licenseNotice}</pre>
        {onCopy && <button type="button" className="btn outline" onClick={() => onCopy(modelCatalog.licenseNotice, t("MIT notice copied", "已复制 MIT 声明"))}>{t("Copy MIT notice", "复制 MIT 声明")}</button>}
      </details>}

      {active === "runtimes" && <details className="catalog-provenance" open>
        <summary>{t("Card family tuning notes", "各显卡系列调优记录")}</summary>
        <p>{t("These are metadata fields and coverage questions for future comparisons.", "以下列出后续比较需要记录和验证的信息。")}</p>
        <dl className="catalog-tuning">
          {tuning.map(({ heading, body }) => <div key={heading[0]}><dt>{t(...heading)}</dt><dd>{t(...body)}</dd></div>)}
        </dl>
      </details>}
    </section>
  </div>;
}
