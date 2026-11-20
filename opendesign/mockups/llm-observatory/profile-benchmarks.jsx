import React, { useState } from "react";
import { ArrowUpRight } from "lucide-react";
import { useLocale } from "./locale";

const recorded = (value) => Number.isFinite(value) && value >= 0;
const cohort = (run) => run.machine.kind === "measured";
const identity = (run) => run.machine.name + " × " + run.model.name;

function openProfile(event, href, go) {
  if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
  event.preventDefault();
  go(href);
}

function CounterpartLink({ href, go, children }) {
  return <a href={href} onClick={(event) => openProfile(event, href, go)}>
    <span>{children}</span><ArrowUpRight size={13} aria-hidden="true" />
  </a>;
}

function ProfileRanking({ relevant, ranked, context, runtime, type, hrefFor, go, onSelect, selected, number }) {
  const { t } = useLocale();
  const counterpart = type === "machine" ? "model" : "machine";
  const unranked = relevant.filter((run) => !ranked.includes(run));
  const maximum = ranked[0]?.[context] || 1;
  const status = (run) => {
    if (!recorded(run[context])) return t("No result", "没有结果");
    if (run.machine.kind === "estimate") return t("Fit estimate", "适配估算");
    if (run.machine.kind === "community") return t("Community example", "社区示例");
    return t("Different backend", "不同推理后端");
  };
  return <div className="profile-ranking">
    <h3>{t("Decode speed ranking", "解码速度排名")}</h3>
    <p>{type === "machine"
      ? t("Fastest first. Models and tokenizers can differ. Throughput measures speed.", "按解码速度从高到低排列。模型和分词器可能不同，吞吐量只反映速度。")
      : t("Fastest first for the selected artifact and {backend} backend.", "所选模型文件在 {backend} 后端上的解码速度由高到低排列。", { backend: runtime })}</p>
    {ranked.length ? <ol className="profile-rank-list">
      {ranked.map((run) => {
        const speed = run[context];
        return <li key={run.id} className="profile-rank-row" data-speed={speed} data-selected={selected === run.id}>
          <span className="profile-rank-number">{number(ranked.findIndex((entry) => entry[context] === speed) + 1)}</span>
          <div className="profile-rank-main">
            <div>
              <CounterpartLink href={hrefFor(run)} go={go}>{run[counterpart].name}</CounterpartLink>
              <strong className="numeric"><bdi>{number(speed)} tok/s</bdi></strong>
            </div>
            <span className="profile-rank-track" aria-hidden="true"><i style={{ width: speed / maximum * 100 + "%" }} /></span>
          </div>
          <button type="button" className="text-button" aria-pressed={selected === run.id} onClick={() => onSelect(run)}>{t("View run", "查看记录")}</button>
        </li>;
      })}
    </ol> : <p className="profile-benchmark-empty">{t("No matched benchmark examples for this selection.", "此选项下没有匹配的测试示例。")}</p>}
    {unranked.length > 0 && <details className="profile-context" open={ranked.length === 0 || undefined}>
      <summary>{t("Unranked combinations ({count})", "未参与排名的组合（{count}）", { count: number(unranked.length) })}</summary>
      <ul>
        {unranked.map((run) => <li key={run.id} data-selected={selected === run.id}>
          <CounterpartLink href={hrefFor(run)} go={go}>{run[counterpart].name}</CounterpartLink>
          <span>{status(run)}{recorded(run[context]) && <> / <bdi>{number(run[context])} tok/s</bdi></>}</span>
        </li>)}
      </ul>
    </details>}
  </div>;
}

function ProfileMap({ paired, highlighted, selected, onSelect, number }) {
  const { t } = useLocale();
  const maximum = Math.ceil(Math.max(1, ...paired.flatMap(({ short, long }) => [short, long])) / 25) * 25;
  const ticks = Array.from({ length: 5 }, (_, index) => maximum * index / 4);
  const x = (value) => 58 + 457 * value / maximum;
  const y = (value) => 226 - 209 * value / maximum;
  const currentName = t("This profile", "当前档案");
  const selectedName = t("Selected combination", "所选组合");
  const axisX = t("4K decode (tok/s)", "4K 解码（tok/s）");
  const axisY = t("32K decode (tok/s)", "32K 解码（tok/s）");
  return <div className="profile-map">
    <h3>{t("Performance map", "性能分布图")}</h3>
    <p>{t("Each point represents one model and machine with both context results. The map includes all backends for this quantization.", "每个点对应一个同时有两种上下文结果的模型与整机组合。分布图包含该量化版本的所有推理后端。")}</p>
    {paired.length === 0 ? <p className="profile-benchmark-empty">{t("No paired 4K and 32K examples for this quantization.", "此量化版本没有成对的 4K 与 32K 示例。")}</p> : <>
      <div className="profile-map-legend">
        <span><i data-current="true" aria-hidden="true" />{currentName}</span>
        <span><i aria-hidden="true" />{t("Other combinations", "其他组合")}</span>
        {selected && <span><i data-selected="true" aria-hidden="true" />{selectedName}</span>}
      </div>
      {highlighted.size === 0 && <p className="profile-map-missing">{t("This profile has no paired example at this quantization.", "当前档案在该量化版本下没有成对的测试示例。")}</p>}
      <svg className="profile-map-plot" viewBox="0 0 538 267" direction="ltr" role="group" aria-label={t("Interactive 4K and 32K throughput map", "可交互的 4K 与 32K 吞吐量分布图")}>
        <g className="profile-map-axis" aria-hidden="true">
          {ticks.map((tick) => <g key={tick}>
            <path d={`M ${x(tick)} 17 V 226 M 58 ${y(tick)} H 515`} />
            <text x={x(tick)} y="244" textAnchor="middle">{number(tick)}</text>
            <text x="48" y={y(tick) + 4} textAnchor="end">{number(tick)}</text>
          </g>)}
          <text x="286" y="263" textAnchor="middle">{axisX}</text>
          <text x="13" y="124" textAnchor="middle" transform="rotate(-90 13 124)">{axisY}</text>
        </g>
        {[...paired].sort((a, b) => Number(a.id === selected) - Number(b.id === selected) ||
          Number(highlighted.has(a.id)) - Number(highlighted.has(b.id))).map((run) => {
          const current = highlighted.has(run.id);
          const label = [identity(run), run.backend, `4K ${number(run.short)} tok/s`, `32K ${number(run.long)} tok/s`, current ? currentName : null].filter(Boolean).join(", ");
          return <g key={run.id} className="profile-map-point" data-current={current} data-selected={selected === run.id}
            data-run-id={run.id} role="button" tabIndex={0} aria-label={label} aria-pressed={selected === run.id}
            onClick={() => onSelect(run)} onKeyDown={(event) => {
              if (event.key !== "Enter" && event.key !== " ") return;
              event.preventDefault();
              onSelect(run);
            }}>
            <title>{label}</title>
            <circle className="profile-map-hit" cx={x(run.short)} cy={y(run.long)} r="14" />
            <circle className="profile-map-mark" cx={x(run.short)} cy={y(run.long)} r={current ? 7 : 5} />
            <circle className="profile-map-ring" cx={x(run.short)} cy={y(run.long)} r="10" />
            <circle className="profile-map-selection" cx={x(run.short)} cy={y(run.long)} r="13" />
          </g>;
        })}
      </svg>
      <details className="profile-map-data">
        <summary>{t("Exact map values", "分布图的确切数值")}</summary>
        <ul>{paired.map((run) => <li key={run.id} data-current={highlighted.has(run.id)} data-selected={selected === run.id}>
          <button type="button" className="text-button" aria-pressed={selected === run.id} onClick={() => onSelect(run)}>{identity(run)}</button>
          <span><bdi>4K {number(run.short)} tok/s</bdi> / <bdi>32K {number(run.long)} tok/s</bdi></span>
        </li>)}</ul>
      </details>
    </>}
  </div>;
}

export function ProfileBenchmarks({ runs, type, activeId, context, runtime, onBackendChange, go, renderEvidence }) {
  const { locale, t } = useLocale();
  const [selectedId, setSelectedId] = useState(null);
  const number = new Intl.NumberFormat(locale, { maximumFractionDigits: 2 }).format;
  const selected = runs.find((run) => run.id === selectedId);
  const viewpoint = selected?.[type].id ?? activeId;
  const relevant = runs.filter((run) => run[type].id === viewpoint);
  const ranked = relevant.filter((run) => cohort(run) && recorded(run[context]) && (type === "machine" || run.backend === runtime))
    .sort((a, b) => b[context] - a[context]);
  const paired = runs.filter((run) => cohort(run) && recorded(run.short) && recorded(run.long));
  const highlighted = new Set(paired.filter((run) => run[type].id === activeId).map((run) => run.id));
  const hrefFor = (run) => type === "machine" ? "#models/" + run.model.id : "#machines/" + run.machine.id;
  const onSelect = (run) => {
    setSelectedId(run.id);
    if (onBackendChange && run.backend !== runtime) onBackendChange(run.backend);
  };
  const clear = () => setSelectedId(null);
  return <>
    {selected && <div className="profile-benchmark-selection" aria-live="polite">
      <div>
        <strong>{t("Ranking for {profile}", "{profile}的排名", { profile: selected[type].name })}</strong>
        {type === "model" && selected.backend !== runtime && <p>{t("The selected {selectedBackend} run is shown for context. The ranking follows your {rankingBackend} filter.", "所选 {selectedBackend} 记录仅供参考。排名按 {rankingBackend} 筛选。", { selectedBackend: selected.backend, rankingBackend: runtime })}</p>}
        {!paired.includes(selected) && <p>{t("The selected run has no paired map point.", "所选记录没有对应的成对绘图数据。")}</p>}
      </div>
      <button type="button" className="text-button" onClick={clear}>{viewpoint === activeId ? t("Clear selection", "清除选择") : t("Return to this profile", "返回当前档案")}</button>
    </div>}
    <div className="profile-benchmarks">
      <ProfileRanking relevant={relevant} ranked={ranked} context={context} runtime={runtime} type={type}
        hrefFor={hrefFor} go={go} onSelect={onSelect} selected={selectedId} number={number} />
      <ProfileMap paired={paired} highlighted={highlighted} selected={selectedId} onSelect={onSelect} number={number} />
    </div>
    {selected && <div className="profile-selected-run">
      {renderEvidence(selected, clear)}
      <div>
        {(type !== "machine" || viewpoint !== activeId) && <CounterpartLink href={"#machines/" + selected.machine.id} go={go}>{t("Open machine profile", "打开整机档案")}</CounterpartLink>}
        {(type !== "model" || viewpoint !== activeId) && <CounterpartLink href={"#models/" + selected.model.id} go={go}>{t("Open model profile", "打开模型档案")}</CounterpartLink>}
      </div>
    </div>}
  </>;
}
