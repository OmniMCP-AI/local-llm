import React, { useEffect, useMemo, useRef, useState } from "react";
import { ArrowDownRight, ArrowUpRight, ChevronLeft, ChevronRight, Cpu, Layers3, List, Search } from "lucide-react";
import hardwareCatalog from "./catalog-hardware.json";
import modelCatalog from "./catalog-models.json";
import { useLocale } from "./locale";

const pageSize = 30;
const runtimes = [
  {
    id: "llama.cpp", name: "llama.cpp", detail: "Local inference / GGUF runtime",
    detailZh: "本地推理，支持 GGUF 模型",
    source: "https://github.com/ggml-org/llama.cpp",
  },
  {
    id: "sglang", name: "SGLang", detail: "Model serving / request scheduling and batching",
    detailZh: "模型服务，支持请求调度和批处理",
    source: "https://github.com/sgl-project/sglang",
  },
  {
    id: "vllm", name: "vLLM", detail: "Model serving / concurrency and KV-cache management",
    detailZh: "模型服务，支持并发推理和 KV 缓存管理",
    source: "https://github.com/vllm-project/vllm",
  },
];

const tabs = [
  {
    key: "cards", title: "Cards", icon: Cpu, rows: hardwareCatalog.cards, scope: "Graphics card references",
    titleZh: "显卡", scopeZh: "显卡资料",
    description: "Card names and source records from the research inventory and llmfit lookup. A catalog entry is not a measured result.",
    descriptionZh: "显卡名称与来源来自研究资料和 llmfit 硬件表。目录条目可能尚无实测数据。",
  },
  {
    key: "machines", title: "Machines", icon: Layers3, rows: hardwareCatalog.machines, scope: "Research profile records",
    titleZh: "整机", scopeZh: "整机配置记录",
    description: "Machine and configuration records in the research source. Partial profiles remain visible and may omit some build components.",
    descriptionZh: "浏览研究来源中的整机与配置记录。信息尚不完整的配置也会保留，部分配件可能未记录。",
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
  const [query, setQuery] = useState("");
  const [license, setLicense] = useState("");
  const [page, setPage] = useState(1);
  const tableTop = useRef(null);
  useEffect(() => {
    if (!initialKind) return;
    setActive(validKind(initialKind));
    setQuery("");
    setLicense("");
    setPage(1);
  }, [initialKind]);

  const tab = tabs.find((entry) => entry.key === active);
  const filtered = useMemo(() => {
    const terms = query.toLowerCase().trim().split(/\s+/).filter(Boolean);
    if (terms.length === 0 && !license) return tab.rows;
    return tab.rows.filter((row) => {
      if (license === "__missing" && row.license) return false;
      if (license && license !== "__missing" && row.license !== license) return false;
      const text = [row.id, row.name, row.detail, row.detailZh].join(" ").toLowerCase();
      return terms.every((term) => text.includes(term));
    });
  }, [query, license, tab]);
  const pages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const current = Math.min(page, pages);
  const start = (current - 1) * pageSize;
  const rows = filtered.slice(start, start + pageSize);
  const scope = t(tab.scope, tab.scopeZh);
  const search = t("Search " + tab.title.toLowerCase(), "搜索" + tab.titleZh);
  const interval = `${number.format(start + 1)}–${number.format(start + rows.length)}`;
  const matches = number.format(filtered.length);
  const total = number.format(tab.rows.length);

  function selectTab(key) {
    if (key === active) return;
    setActive(key);
    setQuery("");
    setLicense("");
    setPage(1);
    go?.("#catalog/" + key);
  }

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
      <div className="catalog-tools" ref={tableTop}>
        <label className="deep-search">
          <Search size={16} aria-hidden="true" />
          <input type="search" aria-label={search} placeholder={active === "models" ? t("Search owner/model or metadata", "搜索组织名、模型名或元数据") : search} value={query} onChange={(event) => {
            setQuery(event.target.value);
            setPage(1);
          }} />
        </label>
        {active === "models" && <label className="catalog-filter"><span>{t("License tag", "许可证")}</span>
          <select value={license} onChange={(event) => { setLicense(event.target.value); setPage(1); }}>
            <option value="">{t("Any", "全部")}</option><option value="__missing">{t("Not listed", "未列出")}</option>
            {licenseTags.map((tag) => <option key={tag} value={tag}>{tag}</option>)}
          </select>
        </label>}
        <p className="catalog-count" role="status" aria-atomic="true">
          {rows.length ? t("{interval} of {matches}", "第 {interval} 条，共 {matches} 条", { interval, matches }) : t("No results", "没有结果")}
          {(query.trim() || license) && <span>{t(" / {total} in catalog", " / 目录共 {total} 条", { total })}</span>}
        </p>
        {pages > 1 && <Pager page={current} pages={pages} onPage={setPage} number={number} label={t("Catalog pages at top", "顶部目录分页")} />}
      </div>

      {rows.length ? <div className="catalog-table-wrap">
        <table aria-label={scope} className="catalog-table">
          <thead><tr><th scope="col">{active === "models" ? t("Repository", "仓库") : t("Name", "名称")}</th><th scope="col">{active === "models" ? t("Model metadata", "模型元数据") : t("Record scope", "记录范围")}</th><th scope="col">{t("Source", "来源")}</th></tr></thead>
          <tbody>{rows.map((row) => {
            const separator = row.id.indexOf("/");
            const modelId = active === "models" && separator > 0;
            return <tr key={row.id}>
              <th scope="row">{modelId ? <a className="catalog-model-id" href={safeSource(row.source)} target="_blank" rel="noopener noreferrer"><span>{row.id.slice(0, separator + 1)}</span>{row.id.slice(separator + 1)}</a> : <>
                <strong>{row.name}</strong>{row.id !== row.name && <small>{row.id}</small>}
              </>}</th>
              <td>{active === "models" ? <div className="catalog-tags">
                {row.detail.split(" · ").filter(Boolean).map((value, index) => <span key={index}>{t(value, sourceLabelsZh[value] ?? value)}</span>)}
                {row.license && <span title={t("Model license metadata from the source catalog", "源目录中的模型许可证元数据")}>{row.license}</span>}
              </div> : formatSourceDetail(row, t)}</td>
              <td><SourceLink href={row.source} label={t("Open source for {name}", "查看 {name} 的来源", { name: row.name })}>{active === "models" ? "Hugging Face" : t("Open source", "查看来源")}</SourceLink></td>
            </tr>;
          })}</tbody>
        </table>
      </div> : <p className="catalog-empty">{t("Try a different name, ID, or detail.", "试试其他名称、ID 或关键词。")}</p>}

      {pages > 1 && <div className="catalog-bottom"><Pager page={current} pages={pages} onPage={pageFromBottom} number={number} label={t("Catalog pages at bottom", "底部目录分页")} /></div>}

      {active === "models" && <details className="catalog-provenance">
        <summary>{t("Source, coverage, and MIT notice", "来源、收录范围和 MIT 声明")}</summary>
        <p>{t(modelCatalog.note, "模型元数据来自固定版本的 llmfit 目录，每条记录链接至原始 Hugging Face 仓库。目录许可证不适用于模型权重。模型许可信息以原始仓库为准。")}</p>
        <p>{t("{count} upstream records at", "上游共 {count} 条记录，版本", { count: number.format(modelCatalog.sourceRows) })} <code>{modelCatalog.commit}</code></p>
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
