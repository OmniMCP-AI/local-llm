import React, { useEffect, useMemo, useRef, useState } from "react";
import { ArrowDownRight, ArrowUpRight, ChevronLeft, ChevronRight, Cpu, Layers3, List, Search } from "lucide-react";
import modelIdentities from "./catalog-identities.json";
import modelCatalog from "./catalog-models.json";
import runtimes from "./catalog-runtimes.json";
import { catalogPath } from "./catalog-paths.mjs";
import { modelTags, queryModelCatalog } from "./catalog-search.mjs";
import { useLocale } from "./locale";

const pageSize = 30;
const catalogRelease = __FASTEST_CATALOG_RELEASE__;
const hardwareCatalog = __FASTEST_HARDWARE_DIRECTORY__;
const machineKinds = ["Partial configuration", "Component reference", "llmfit example preset"];

const tabs = [
  {
    key: "cards", title: "Cards", icon: Cpu, rows: hardwareCatalog.cards, scope: "Graphics card references",
    titleZh: "显卡", scopeZh: "显卡资料",
    description: "Card identities and variants from the research inventory and pinned llmfit lookup.",
    descriptionZh: "显卡型号与版本来自研究资料和固定版本的 llmfit 硬件表。",
  },
  {
    key: "machines", title: "Machines", icon: Layers3, rows: hardwareCatalog.machines, scope: "Machine and component records",
    titleZh: "整机", scopeZh: "整机与部件记录",
    description: "Browse partial configurations, standalone component references and llmfit example presets.",
    descriptionZh: "浏览部分配置、独立部件资料和 llmfit 示例配置。",
  },
  {
    key: "models", title: "Models", icon: List, rows: modelCatalog.models, scope: "Model metadata records",
    titleZh: "模型", scopeZh: "模型元数据",
    description: "Search the pinned llmfit snapshot. The originating repositories are the source for model artifacts and their terms.",
    descriptionZh: "搜索固定版本的 llmfit 目录。模型文件和使用条款请查阅原始仓库。",
  },
  {
    key: "runtimes", title: "Runtimes", icon: ArrowDownRight, rows: runtimes, scope: "Upstream runtime projects",
    titleZh: "推理框架", scopeZh: "上游推理框架",
    description: "A starting registry of runtime projects. A project's presence does not establish support or performance on any listed machine.",
    descriptionZh: "这是首批推理框架项目。整机兼容性与性能请查阅对应的测试记录。",
  },
];
const licenseTags = Array.from(new Set(modelCatalog.models.map(({ license }) => license).filter(Boolean))).sort();
const validKind = (kind) => tabs.some((tab) => tab.key === kind) ? kind : "cards";
const sourceLabelsZh = {
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

const taskAndFormatTags = Array.from(new Set(modelCatalog.models
  .flatMap((row) => modelTags(row, modelIdentities[row.id]))
  .filter((value) => !value.endsWith(" parameters")))).sort();
const emptyFilters = { query: "", tag: "", license: "", page: 1 };

function modelFiltersFromLocation() {
  const params = new URLSearchParams(location.hash.split("?")[1]);
  const page = Number(params.get("page"));
  return {
    query: params.get("q") ?? "",
    tag: params.get("tag") ?? "",
    license: params.get("license") ?? "",
    page: Number.isSafeInteger(page) && page > 0 ? page : 1,
  };
}

function saveModelFilters(filters, paginate) {
  const params = new URLSearchParams();
  if (filters.query) params.set("q", filters.query);
  if (filters.tag) params.set("tag", filters.tag);
  if (filters.license) params.set("license", filters.license);
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
  const [filters, setFilters] = useState(() => initialKind === "models" ? modelFiltersFromLocation() : emptyFilters);
  const { query, tag, license, page } = filters;
  const tableTop = useRef(null);
  useEffect(() => {
    if (active !== "models") return;
    const restore = () => setFilters(modelFiltersFromLocation());
    window.addEventListener("popstate", restore);
    window.addEventListener("hashchange", restore);
    return () => {
      window.removeEventListener("popstate", restore);
      window.removeEventListener("hashchange", restore);
    };
  }, [active]);

  const tab = tabs.find((entry) => entry.key === active);
  const { rows, total: resultCount, pages, current, start } = useMemo(() => {
    if (tab.key === "models") return queryModelCatalog(tab.rows, modelIdentities, filters);
    const terms = query.toLowerCase().trim().split(/\s+/).filter(Boolean);
    const filtered = terms.length || tag ? tab.rows.filter((row) => {
      if (tag && row.kind !== tag) return false;
      const text = [row.id, row.name, row.detail, row.tag, ...(row.aliases ?? [])].join(" ").toLowerCase();
      return terms.every((term) => text.includes(term));
    }) : tab.rows;
    const pages = Math.max(1, Math.ceil(filtered.length / pageSize));
    const current = Math.min(page, pages);
    const start = (current - 1) * pageSize;
    return { rows: filtered.slice(start, start + pageSize), total: filtered.length, pages, current, start };
  }, [tab, filters, query, page, tag]);
  const hardwareTab = active === "cards" || active === "machines";
  const { asOf, coverage } = hardwareCatalog;
  const scope = t(tab.scope, tab.scopeZh);
  const search = t("Search " + tab.title.toLowerCase(), "搜索" + tab.titleZh);
  const interval = `${number.format(start + 1)}–${number.format(start + rows.length)}`;
  const matches = number.format(resultCount);
  const total = number.format(tab.rows.length);

  function selectTab(key) {
    if (key === active) return;
    setActive(key);
    setFilters(emptyFilters);
    go?.("#catalog/" + key);
  }

  function updateFilters(patch, paginate = false) {
    const next = { ...filters, page: 1, ...patch };
    setFilters(next);
    if (active === "models") saveModelFilters(next, paginate);
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
      </div>
      {hardwareTab && <p className="catalog-muted">
        {t("Snapshot {date}", "快照日期 {date}", { date: asOf })} ·{" "}
        {active === "cards" ? t("{cards} card references, {unresolved} unresolved", "共 {cards} 条显卡资料，其中 {unresolved} 条型号待确认", {
          cards: number.format(coverage.cards), unresolved: number.format(coverage.unresolvedCardReferences),
        }) : t("{complete} complete builds, {partial} partial configurations, {components} component references, {presets} example presets", "完整配置 {complete} 条、部分配置 {partial} 条、部件资料 {components} 条、示例配置 {presets} 条", {
          complete: number.format(coverage.completeBuilds), partial: number.format(coverage.partialMachines),
          components: number.format(coverage.researchComponentReferences), presets: number.format(coverage.upstreamPresets),
        })} ·{" "}{t("No reviewed benchmark results", "暂无经过审核的基准测试结果")}
        {catalogRelease && <> · <a className="catalog-source-link" href={`catalog/${catalogRelease}/manifest.json`}>{t("Snapshot sources and counts", "快照来源与数量")}</a></>}
      </p>}
      <div className="catalog-tools" ref={tableTop}>
        <label className="deep-search">
          <Search size={16} aria-hidden="true" />
          <input type="search" aria-label={search} placeholder={active === "models" ? t("Search owner/model or metadata", "搜索组织名、模型名或元数据") : search} value={query} onChange={(event) => updateFilters({ query: event.target.value })} />
        </label>
        {active === "machines" && <label className="catalog-filter"><span>{t("Record type", "记录类型")}</span>
          <select value={tag} onChange={(event) => updateFilters({ tag: event.target.value })}>
            <option value="">{t("Any", "全部")}</option>
            {machineKinds.map((value) => <option key={value} value={value}>{t(value, sourceLabelsZh[value])}</option>)}
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
        {pages > 1 && <Pager page={current} pages={pages} onPage={setPage} number={number} label={t("Catalog pages at top", "顶部目录分页")} />}
      </div>

      {rows.length ? <div className="catalog-table-wrap">
        <table aria-label={scope} className="catalog-table">
          <thead><tr><th scope="col">{active === "models" ? t("Repository", "仓库") : t("Name", "名称")}</th><th scope="col">{active === "models" ? t("Model metadata", "模型元数据") : t("Record scope", "记录范围")}</th><th scope="col">{t("Source", "来源")}</th></tr></thead>
          <tbody>{rows.map((row) => {
            const separator = row.id.indexOf("/");
            const modelId = active === "models" && separator > 0;
            const card = catalogRelease && (modelId || active === "runtimes" || hardwareTab) ? catalogPath(catalogRelease, active, row.id) : undefined;
            return <tr key={row.id}>
              <th scope="row">{modelId ? <a className="catalog-model-id" href={card ?? safeSource(row.source)} target={card ? undefined : "_blank"} rel={card ? undefined : "noopener noreferrer"}><span>{row.id.slice(0, separator + 1)}</span>{row.id.slice(separator + 1)}</a> : <>
                <strong>{card ? <a className="catalog-model-id" href={card}>{row.name}</a> : row.name}</strong>
                {row.tag ? <small>{row.tag}</small> : row.id !== row.name && <small>{row.id}</small>}
              </>}</th>
              <td>{active === "models" ? <div className="catalog-tags">
                {modelTags(row, modelIdentities[row.id]).map((value) => <span key={value}>{t(value, sourceLabelsZh[value] ?? value)}</span>)}
                {row.license && <span title={t("Model license metadata from the source catalog", "源目录中的模型许可证元数据")}>{row.license}</span>}
              </div> : formatSourceDetail(row, t)}</td>
              <td><SourceLink href={row.tag ? row.source + "/releases/tag/" + row.tag : row.source} label={t("Open source for {name}", "查看 {name} 的来源", { name: row.name })}>{active === "models" ? "Hugging Face" : t("Open source", "查看来源")}</SourceLink></td>
            </tr>;
          })}</tbody>
        </table>
      </div> : <p className="catalog-empty">{t("Try a different name, ID, or detail.", "试试其他名称、ID 或关键词。")}</p>}

      {pages > 1 && <div className="catalog-bottom"><Pager page={current} pages={pages} onPage={pageFromBottom} number={number} label={t("Catalog pages at bottom", "底部目录分页")} /></div>}

      {active === "models" && <details className="catalog-provenance">
        <summary>{t("Source, coverage, and MIT notice", "来源、收录范围和 MIT 声明")}</summary>
        <p>{t(modelCatalog.note, "模型元数据来自固定版本的 llmfit 目录，每条记录链接至原始 Hugging Face 仓库。目录许可证不适用于模型权重。模型许可信息以原始仓库为准。")}</p>
        <p>{t("{count} upstream records at", "上游共 {count} 条记录，版本", { count: number.format(modelCatalog.sourceRows) })} <code>{modelCatalog.commit}</code></p>
        {catalogRelease && <p><a className="catalog-source-link" href={`catalog/${catalogRelease}/manifest.json`}>{t("Release coverage and provenance", "发布版覆盖范围与来源")}</a></p>}
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
