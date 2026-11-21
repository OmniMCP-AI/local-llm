import React, { useEffect, useRef, useState } from "react";
import { ArrowRight, ArrowUpRight, Cable, Clipboard, Cpu, Layers3, Link2 } from "lucide-react";
import {
  battleEvidence, battleFactor, battleHref, battleKinds, battleMarkdown, battlePair,
  battleRankings, battleScopeNote, battleSources, battleSuggestions,
} from "./battle.mjs";
import { useLocale } from "./locale";

const records = __FASTEST_BATTLE_RECORDS__;
const titleSignals = __FASTEST_BATTLE_TITLE_SIGNALS__;
const release = __FASTEST_CATALOG_RELEASE__ || __FASTEST_LOCAL_CATALOG_RELEASE__;
const prefix = __FASTEST_CATALOG_RELEASE__ ? "/" : "local-catalog/";
const liveRankings = __FASTEST_CATALOG_POSTGRES__ && Boolean(release);
const urls = { release, prefix };

const options = Object.fromEntries(Object.keys(battleKinds).map(kind => {
  const seen = new Set();
  const duplicates = new Set();
  for (const { name } of records[kind]) {
    if (seen.has(name)) duplicates.add(name);
    seen.add(name);
  }
  const rows = records[kind].map(({ name, id }) => ({ id, label: duplicates.has(name) ? name + " · " + id : name }));
  return [kind, rows.sort((a, b) => a.label.localeCompare(b.label, "en"))];
}));

const navigate = (event, href, go, top) => {
  if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
  event.preventDefault();
  go(href, top);
};

function PairList({ pairs, selected, mode, go, t, number }) {
  return <ul className="battle-pair-list">{pairs.map(pair => {
    const { left, right, kind, reason, count, sources } = pair;
    const href = battleHref(kind, pair);
    const current = (left.id === selected?.left.id && right.id === selected?.right.id)
      || (right.id === selected?.left.id && left.id === selected?.right.id);
    return <li key={href}>
      <a className="battle-pair-link" href={href} onClick={event => navigate(event, href, go, true)}
        aria-current={current ? "true" : undefined}>
        <span><strong><bdi>{left.name}</bdi> <span>{t("vs.", "对比")}</span> <bdi>{right.name}</bdi></strong>
          {mode === "suggested" && <small>{t(...reason)}</small>}
          {mode === "popular" && <small>{t("{count} recorded", "已记录 {count} 次", { count: number.format(count) })}</small>}
          {mode === "titles" && <small>{count === 1 ? t("{count} video title", "{count} 条视频标题", { count: number.format(count) })
            : t("{count} video titles", "{count} 条视频标题", { count: number.format(count) })}</small>}
        </span><ArrowRight size={15} aria-hidden="true" />
      </a>
      {mode === "titles" && sources.length > 0 && <div className="battle-title-sources">
        {sources.map((href, i) => <a key={href} href={href} target="_blank" rel="noreferrer">
          {t("Video {number}", "视频 {number}", { number: number.format(i + 1) })}<ArrowUpRight size={12} aria-hidden="true" />
        </a>)}
      </div>}
    </li>;
  })}</ul>;
}

function ComparisonTable({ pair, t }) {
  const value = (entry) => entry
    ? entry.source ? <a href={entry.source} target="_blank" rel="noreferrer"><bdi>{entry.text}</bdi></a> : <bdi>{entry.text}</bdi>
    : <span className="battle-unavailable">{t("Unavailable", "暂不可用")}</span>;
  return <section aria-labelledby="battle-details-title">
    <h2 id="battle-details-title">{t("Specifications", "规格对比")}</h2>
    <table className="battle-table" aria-labelledby="battle-details-title">
      <thead><tr><th scope="col">{t("Specification", "规格")}</th>
        <th scope="col"><bdi>{pair.left.name}</bdi></th>
        <th scope="col"><bdi>{pair.right.name}</bdi></th>
      </tr></thead>
      <tbody>{pair.rows.map(row => <tr key={row.label[0]}>
        <th scope="row">{t(...row.label)}
          {row.differentScope && <small>{t(...battleScopeNote)}</small>}
        </th><td>{value(row.left)}</td><td>{value(row.right)}</td>
      </tr>)}</tbody>
    </table>
    <div className="battle-sources">{[pair.left, pair.right].map(product => <section key={product.id}>
      <h3><bdi>{product.name}</bdi></h3>
      <ul>{battleSources(pair, product, urls).map(({ label, href }) => <li key={href}>
        <a href={href}>{t(...label)} <ArrowUpRight size={13} aria-hidden="true" /></a>
      </li>)}</ul>
    </section>)}</div>
  </section>;
}

export function BattlePage({ slug, query, go, onCopy }) {
  const { locale, t } = useLocale();
  const kind = Object.hasOwn(battleKinds, slug) ? slug : "cards";
  const number = new Intl.NumberFormat(locale, { maximumFractionDigits: 2 });
  const [rankings, setRankings] = useState({});
  const [refresh, setRefresh] = useState(0);
  const [recordsByPair, setRecordsByPair] = useState({});
  const recording = useRef(new Map());

  useEffect(() => {
    if (!liveRankings) return;
    const controller = new AbortController();
    const params = new URLSearchParams({ release, kind });
    fetch("/api/battle-popularity?" + params, { signal: controller.signal })
      .then(response => response.ok ? response.json() : null)
      .then(data => {
        if (!controller.signal.aborted) {
          setRankings(state => ({ ...state, [kind]: battleRankings(records, kind, data?.pairs) }));
        }
      }).catch(() => {});
    return () => controller.abort();
  }, [kind, refresh]);

  const suggested = battleSuggestions(records, kind);
  const titles = battleRankings(records, kind, titleSignals?.pairs?.[kind]);
  const choices = options[kind];
  const params = new URLSearchParams(query);
  const left = params.get("left"), right = params.get("right");
  const requestedRelease = params.get("release");
  const mismatchedRelease = requestedRelease && requestedRelease !== release;
  const fromLink = battlePair(records, kind, left, right);
  const invalidLink = (params.has("left") || params.has("right")) && !fromLink;
  const selected = fromLink ?? suggested[0] ?? battlePair(records, kind, choices[0]?.id, choices[1]?.id);
  const pairKey = selected && [kind, ...[selected.left.id, selected.right.id].sort()].join("|");
  const status = recordsByPair[pairKey];

  function selectSide(side, id) {
    const next = battlePair(records, kind, side === "left" ? id : selected.left.id, side === "right" ? id : selected.right.id);
    if (next) go(battleHref(kind, next), false);
  }
  function shareLink() {
    return new URL(battleHref(kind, selected, release), location.href).href;
  }
  async function recordPair() {
    if (!liveRankings || !selected || !globalThis.crypto?.randomUUID) return;
    const previous = recording.current.get(pairKey);
    if (previous?.state === "pending" || previous?.state === "recorded") return;
    const requestId = previous?.requestId ?? crypto.randomUUID();
    const update = (state) => {
      recording.current.set(pairKey, { state, requestId });
      setRecordsByPair(current => ({ ...current, [pairKey]: state }));
    };
    update("pending");
    try {
      const response = await fetch("/api/battle-popularity", {
        method: "POST",
        signal: AbortSignal.timeout(8000),
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ release, kind, left: selected.left.id, right: selected.right.id, requestId }),
      });
      if (!response.ok || !(await response.json())?.recorded) throw new Error("Unavailable");
      update("recorded");
      setRefresh(value => value + 1);
    } catch {
      update("failed");
    }
  }

  return <div className="battle-page">
    <header className="battle-heading">
      <h1>{t("Hardware battles", "硬件对决")}</h1>
      <p>{t("Compare two GPUs or machines side by side and check what matters for your build.", "并排对比两款显卡或整机，找出影响配置选择的关键差异。")}</p>
    </header>
    <nav className="battle-kinds" aria-label={t("Hardware type", "硬件类型")}>{Object.entries(battleKinds).map(([id, label]) => {
      const href = battleHref(id);
      const Icon = id === "cards" ? Cpu : Layers3;
      return <a key={id} href={href} onClick={event => navigate(event, href, go, false)} aria-current={id === kind ? "page" : undefined}>
        <Icon size={17} aria-hidden="true" /> {t(...label)}
      </a>;
    })}</nav>
    {mismatchedRelease && <p className="battle-alert" role="status">{t(
      "The catalog release in this link is unavailable. Specifications shown are from the current release ({release}).",
      "此链接中的目录版本不可用，显示的是当前版本（{release}）的规格。", { release })}</p>}
    {invalidLink && <p className="battle-alert" role="status">{t(
      "This link does not identify two distinct configurations in this catalog. Showing an available pair.",
      "此链接没有指向目录中两个不同的配置，已显示可用配对。")}</p>}
    {selected ? <div className="battle-layout">
      <div className="battle-comparison">
        <div className="battle-pickers">
          {["left", "right"].map(side => <label className={"battle-picker battle-picker-" + side} key={side}>
            <span>{side === "left" ? t("Left configuration", "左侧配置") : t("Right configuration", "右侧配置")}</span>
            <select value={selected[side].id} onChange={event => selectSide(side, event.target.value)}>
              {choices.map(({ id, label }) => <option key={id} value={id}
                disabled={id === selected[side === "left" ? "right" : "left"].id}>{label}</option>)}
            </select>
          </label>)}
        </div>
        <div className="battle-actions">
          <button className="btn outline battle-find" aria-controls="battle-discovery"
            onClick={() => document.getElementById("battle-discovery")?.focus()}>
            {t("Find a matchup", "查找配对")}</button>
          <button className="btn outline" onClick={() => onCopy(shareLink(), t("Battle link copied", "已复制对比链接"))}>
            <Link2 size={16} aria-hidden="true" />{t("Copy link", "复制链接")}</button>
          <button className="btn outline" onClick={() => onCopy(battleMarkdown(selected, {
            ...urls, origin: location.origin === "null" ? "" : location.origin, share: shareLink(),
          }), t("Comparison Markdown copied", "已复制对比 Markdown"))}>
            <Clipboard size={16} aria-hidden="true" />{t("Copy Markdown", "复制 Markdown")}</button>
          {liveRankings && globalThis.crypto?.randomUUID && <button className="btn outline" onClick={recordPair}
            disabled={status === "pending" || status === "recorded"}
            aria-describedby="battle-record-purpose">
            {status === "pending" ? t("Recording…", "正在记录…") : status === "recorded" ? t("Pair recorded", "已记录此配对")
              : t("Count this comparison", "将此对比计入排名")}</button>}
        </div>
        {liveRankings && globalThis.crypto?.randomUUID && <p id="battle-record-purpose" className="battle-record" aria-live="polite">
          {status === "failed" ? t("Could not record this pair. You can try again.", "此配对未能记录，请重试。")
            : t("Counting is optional and contributes to the public 30-day ranking.", "可选择将此配对计入公开的 30 天排名。")}
        </p>}
        <section className="battle-decision" aria-labelledby="battle-decision-title">
          <h2 id="battle-decision-title">{t("Decision factors", "选购要点")}</h2>
          {selected.rows.some(({ factor }) => factor) && <ul>{selected.rows.map(({ label, factor }) => factor &&
            <li key={label[0]}>{battleFactor(factor, t, number)}</li>)}</ul>}
          <p>{t(...selected.decision)}</p>
          <p className="battle-evidence"><Cable size={16} aria-hidden="true" />{t(...battleEvidence)}</p>
        </section>
        <ComparisonTable pair={selected} t={t} />
      </div>
      <aside className="battle-discovery" id="battle-discovery" tabIndex={-1} aria-label={t("Find a matchup", "查找配对")}>
        {rankings[kind]?.length > 0 && <section>
          <h2>{t("Most compared", "对比最多")}</h2>
          <p>{t("Opt-in comparisons recorded over the last 30 UTC dates.", "最近 30 个 UTC 日期内主动记录的对比。")}</p>
          <PairList pairs={rankings[kind]} selected={selected} mode="popular" go={go} t={t} number={number} />
        </section>}
        {titles.length > 0 && <section>
          <h2>{t("YouTube title mentions", "YouTube 标题提及量")}</h2>
          <p>{t("Estimate from {count} reviewed video titles. Counts are unique videos mentioning both configurations.", "基于审核过的 {count} 条视频标题估算，统计同时提及两种配置的视频数。", { count: number.format(titleSignals.sampleSize) })}
            {titleSignals.observedOn && <> <time dateTime={titleSignals.observedOn}>{titleSignals.observedOn}</time></>}</p>
          <PairList pairs={titles} selected={selected} mode="titles" go={go} t={t} number={number} />
        </section>}
        {suggested.length > 0 && <section>
          <h2>{t("Suggested matchups", "建议配对")}</h2>
          <PairList pairs={suggested} selected={selected} mode="suggested" go={go} t={t} number={number} />
        </section>}
        {__FASTEST_PAGES__ && <a className="battle-archive-link" href="/battles/">
          {t("Read the battle archive", "查看对比存档")} <ArrowUpRight size={15} aria-hidden="true" /></a>}
      </aside>
    </div> : <p className="battle-alert">{t("This catalog has fewer than two configurations to compare.", "此目录中可对比的配置少于两个。")}</p>}
  </div>;
}
