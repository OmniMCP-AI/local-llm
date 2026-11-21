import React, { useState } from "react";
import { ArrowUpRight, Check, CircleHelp, Plus, SlidersHorizontal, X } from "lucide-react";
import { evaluateGoalRows, goalMetricsForRegion, goalRows } from "./goal-data";
import { WikiDetails, wikiEntry } from "./knowledge";
import { useLocale } from "./locale";

const verdict = {
  meets: ["Meets every goal", "满足所有要求"], misses: ["Misses a goal", "有要求未达标"],
  unknown: ["Missing evidence", "证据不足"], context: ["Context only", "仅供参考"],
};
const kindLabel = {
  measured: ["Lab example", "实验示例"], community: ["Community example", "社区示例"],
  estimate: ["Estimate", "估算"], untested: ["No result", "暂无结果"],
};
const conditionName = { "New build": ["New build", "全新配置"], "Used GPU build": ["Used GPU build", "二手显卡配置"] };
const presets = [
  { id: "desk", title: ["Personal use", "个人使用"], tagline: ["Budget and output speed", "预算与输出速度"], priority: "decode", targets: { price: [1800,13000], decode: 100 } },
  { id: "team", title: ["Team serving", "团队服务"], tagline: ["Response time for four users", "四人并发响应时间"], priority: "userP95", targets: { price: [3000,22000], userP95: 12 } },
  { id: "efficient", title: ["Low energy", "低能耗"], tagline: ["Energy per request", "单次请求耗电量"], priority: "energy", targets: { decode: 45, energy: 0.2 } },
];
const metricChinese = {
  price: ["整机价格", "价格", "所选市场的整机购买报价示例，不含税费、运费和运行成本。RTX 3090 配置使用二手显卡。"],
  decode: ["输出速度", "解码", "生成开始后的每秒输出词元数。单次热启动请求，4K 上下文限制，使用相同的 Qwen2.5 7B Q4_K_M 文件。"],
  prefill: ["提示词处理速度", "预填充", "单用户热启动请求处理 512 个输入词元时的每秒输入词元数。"],
  userP95: ["四人并发响应时间", "四人并发 p95", "持续四人并发时，单次请求端到端时间的第 95 百分位数。每次请求有 512 个输入词元和 256 个输出词元。"],
  energy: ["单次请求耗电量", "耗电量", "单次热启动请求的整机插座耗电量，有 512 个输入词元和 256 个输出词元，不含请求之间的待机耗电。"],
};

const byId = (metrics, id) => metrics.find((metric) => metric.id === id);
function localizeMetric(metric, t) {
  const [label, short, description] = metricChinese[metric.id];
  return { ...metric, label: t(metric.label, label), short: t(metric.short, short), description: t(metric.description, description) };
}
function display(value, metric, { t, locale, formatMoney }) {
  if (value == null) return t("No result", "暂无结果");
  if (metric.id === "price") return formatMoney(value, metric.unit, { currencyDisplay: "code" });
  const figures = new Intl.NumberFormat(locale, { maximumFractionDigits: 2 });
  return figures.format(value) + " " + t(metric.unit, metric.unit);
}
const makeGoals = (preset, region) => Object.entries(preset.targets).map(([id, target]) => ({
  id, target: Array.isArray(target) ? target[region === "cn" ? 1 : 0] : target,
}));

function Field({ label, value, options, onChange }) {
  return <label className="select-field goal-field"><span>{label}</span><select value={value} onChange={(e) => onChange(e.target.value)}>
    {options.map(([id, name]) => <option key={id} value={id}>{name}</option>)}
  </select></label>;
}

function LimitControl({ goal, metric, commit, remove, canRemove }) {
  const { t } = useLocale();
  const unit = t(metric.unit, metric.unit);
  const label = metric.direction === "min"
    ? t("Maximum {metric}", "{metric}上限", { metric: metric.label.toLowerCase() })
    : t("Minimum {metric}", "{metric}下限", { metric: metric.label.toLowerCase() });
  return <li className="limit-row"><div><strong>{label}</strong><details><summary>{t("What this measures", "指标说明")}</summary><p>{metric.description}</p></details></div>
    <div className="limit-input"><input aria-label={label + " (" + unit + ")"} type="number" inputMode="decimal" min={metric.min} max={metric.max}
      step={metric.step} value={goal.target} onChange={(e) => {
        if (e.target.value === "") return commit(goal.id, "");
        const value = e.target.valueAsNumber;
        if (Number.isFinite(value)) commit(goal.id, value);
      }} onBlur={() => {
        const corrected = goal.target === "" ? metric.defaultTarget : Math.min(metric.max, Math.max(metric.min,goal.target));
        if (corrected !== goal.target) commit(goal.id,corrected);
      }} /><span>{unit}</span></div>
    <button className="icon-btn" type="button" aria-label={t("Remove {metric} goal", "删除{metric}要求", { metric: metric.label })} disabled={!canRemove} onClick={() => remove(goal.id)}><X size={15} /></button>
  </li>;
}

function CheckText({ check, metric }) {
  const locale = useLocale();
  const { t } = locale;
  if (check.state === "pass") return <span className="goal-check pass"><Check size={13} aria-hidden="true" /> {t("{metric} passes", "{metric}达标", { metric: metric.short })}</span>;
  if (check.state === "unknown") return <span className="goal-check unknown">{t("{metric} unknown", "{metric}未知", { metric: metric.short })}</span>;
  const gap = display(Math.abs(check.value - check.target), metric, locale);
  return <span className="goal-check miss">{metric.direction === "min"
    ? t("{metric} is {gap} over", "{metric}超出 {gap}", { metric: metric.short, gap })
    : t("{metric} is {gap} short", "{metric}还差 {gap}", { metric: metric.short, gap })}</span>;
}

function Candidate({ row, metrics, priority, inspect }) {
  const locale = useLocale();
  const { t } = locale;
  const metric = byId(metrics,priority);
  return <article className="goal-candidate">
    <div className="candidate-head"><div><strong>{row.short}</strong><small>{row.tradeoff ? t("Tradeoff candidate", "权衡方案") : t(...verdict[row.status])}</small></div><span className="numeric">{display(row.metrics[priority],metric,locale)}</span></div>
    <div className="candidate-checks">{row.checks.map((check) => <CheckText key={check.id} check={check} metric={byId(metrics,check.id)} />)}</div>
    <button type="button" className="text-button" onClick={() => inspect(row)}>{t("Inspect metric details", "查看指标详情")} <ArrowUpRight size={13} /></button>
  </article>;
}

function Results({ rows, metrics, priority, ready, inspect, goals }) {
  const { t } = useLocale();
  const eligible = rows.filter((row) => row.status !== "context");
  const matches = eligible.filter((row) => row.status === "meets");
  const frontier = eligible.filter((row) => row.tradeoff);
  const first = matches[0] ?? frontier[0] ?? eligible[0];
  const second = (matches.length ? [...matches.slice(1), ...frontier] : [...frontier, ...eligible]).find((row) => row.id !== first?.id);
  const metricCount = new Set([...goals.map(({ id }) => id),priority]).size;
  const priorityLabel = byId(metrics,priority).label;
  const matchText = t(matches.length === 1 ? "{count} setup meets every goal" : "{count} setups meet every goal", "{count} 个配置满足所有要求", { count: matches.length });
  return <section className="goal-results" aria-labelledby="goal-result-title">
    <p className="goal-kicker">{t("Comparison result", "对比结果")}</p>
    <div className="goal-results-head" aria-live="polite">
      <h2 id="goal-result-title">{!ready ? t("Finish entering your limits", "请填写完整的要求") : matches.length === 0 ? t("No setup meets every goal", "没有配置满足所有要求") : matchText}</h2>
      <p>{!ready
        ? t("Each active limit needs a number in its stated range.", "请在每项允许的范围内输入数值。")
        : matches.length
          ? t("Matches are ordered by {metric}.", "符合要求的配置按{metric}排序。", { metric: priorityLabel.toLowerCase() })
          : t("See which requirement each candidate gives up. Your limits stay in place.", "查看每个候选配置在哪些要求上未达标。")}</p>
    </div>
    {ready && first && <Candidate row={first} metrics={metrics} priority={priority} inspect={inspect} />}
    {ready && second && <Candidate row={second} metrics={metrics} priority={priority} inspect={inspect} />}
    {ready && <p className="goal-cohort-note">{t(
      frontier.length === 1 ? "{count} tradeoff candidate across {metrics} selected metrics with complete example data." : "{count} tradeoff candidates across {metrics} selected metrics with complete example data.",
      "以示例数据完整的 {metrics} 项所选指标衡量，得到 {count} 个权衡方案。",
      { count: frontier.length, metrics: metricCount }
    )}</p>}
  </section>;
}

function MetricsTable({ rows, metrics, columns, inspect }) {
  const locale = useLocale();
  const { t } = locale;
  return <div className="table-wrap goal-table"><table>
    <thead><tr><th scope="col">{t("Setup", "配置")}</th><th scope="col">{t("Goal result", "达标结果")}</th>{columns.map((id) => {
      const metric = byId(metrics,id);
      return <th key={id} scope="col">{metric.short}<small>{id === "price" ? t("Display amount", "显示金额") : t(metric.unit, metric.unit)}</small></th>;
    })}<th scope="col">{t("Evidence", "证据")}</th></tr></thead>
    <tbody>{rows.map((row) => <tr key={row.id}><th scope="row"><a href={"#machines/" + row.id}>{row.name} <ArrowUpRight size={12} aria-hidden="true" /></a><small>{t(...conditionName[row.condition])}</small></th>
      <td><span className={"goal-verdict " + row.status}>{t(...verdict[row.status])}</span></td>
      {columns.map((id) => {
        const check = row.checks.find((candidate) => candidate.id === id);
        const metric = byId(metrics,id);
        const value = row.metrics[id];
        return <td key={id} className={check && row.status !== "context" ? "goal-cell " + check.state : "goal-cell"}>
          <span className="numeric">{display(value,metric,locale)}</span>{check && row.status !== "context" && <small>{check.state === "pass" ? t("Pass", "达标") : check.state === "miss" ? t("Miss", "未达标") : t("Unknown", "未知")}</small>}
        </td>;
      })}
      <td><button className="text-button" onClick={() => inspect(row)}>{t("Open details", "查看详情")}</button><small>{t(...kindLabel[row.kind])}</small></td>
    </tr>)}</tbody>
  </table></div>;
}

function MetricsDetail({ row, metrics, close }) {
  const locale = useLocale();
  const { t } = locale;
  return <section id="goal-metric-details" tabIndex="-1" className="goal-metric-details" aria-labelledby="goal-details-title">
    <div className="detail-heading"><div><h2 id="goal-details-title">{row.name}</h2><p>{t(...kindLabel[row.kind])}{t(". Values on this screen are illustrative and have separate test conditions.", "。页面数值均为示例，各指标有独立的测试条件。")}</p></div>
      <button className="btn outline" onClick={close}>{t("Close details", "关闭详情")}</button></div>
    <dl>{metrics.map((metric) => <div key={metric.id}><dt>{metric.label}</dt><dd className="numeric">{display(row.metrics[metric.id],metric,locale)}</dd><dd>{metric.description}</dd></div>)}</dl>
    <a className="text-button" href={"#machines/" + row.id}>{t("See machine profile", "查看整机档案")} <ArrowUpRight size={14} /></a>
  </section>;
}

export function GoalPage({ state, set, go, onCopy }) {
  const { t, currency } = useLocale();
  const [activePreset, setPreset] = useState("desk");
  const [priority, setPriority] = useState(presets[0].priority);
  const [goals, setGoals] = useState(() => makeGoals(presets[0],state.region));
  const [condition, setCondition] = useState("New build");
  const [adding, setAdding] = useState(false);
  const [allColumns, setAllColumns] = useState(false);
  const [selected, setSelected] = useState(null);
  const metrics = goalMetricsForRegion(state.region).map((metric) => localizeMetric(metric, t));
  const priceUnit = byId(metrics, "price").unit;
  const ready = goals.every(({ id, target }) => {
    const metric = byId(metrics,id);
    return Number.isFinite(target) && target >= metric.min && target <= metric.max;
  });
  const rows = ready ? evaluateGoalRows(goalRows(state.region).filter((row) => row.condition === condition),goals,priority) : [];
  const columns = allColumns ? metrics.map(({ id }) => id) : [...new Set([...goals.map(({ id }) => id),priority])];
  const choices = metrics.filter(({ id }) => !goals.some((goal) => goal.id === id));
  const shown = rows.find((row) => row.id === selected);
  const doc = wikiEntry("goals");
  const inspect = (row) => {
    setSelected(row.id);
    requestAnimationFrame(() => document.getElementById("goal-metric-details")?.focus());
  };
  const update = (id, target) => {
    setPreset("");
    setGoals((current) => current.map((goal) => goal.id === id ? { id,target } : goal));
  };
  const pick = (preset) => {
    setPreset(preset.id);
    setPriority(preset.priority);
    setGoals(makeGoals(preset,state.region));
    setSelected(null);
  };
  const market = (region) => {
    if (region === state.region) return;
    const preset = presets.find((item) => item.id === activePreset);
    const newPrice = byId(goalMetricsForRegion(region),"price").defaultTarget;
    set({ region, budget: region === "cn" ? 20000 : 2800 });
    setGoals((current) => preset ? makeGoals(preset,region) : current.map((goal) => goal.id === "price" ? { id: "price", target: newPrice } : goal));
    setSelected(null);
  };
  return <div className="deep-page goals-page">
    <header className="deep-heading"><div><h1>{t(doc.title, "按目标对比")}</h1><p>{t(doc.summary, "按你的预算、性能和能耗要求筛选配置，再比较每种方案的取舍。")}</p></div><button className="btn outline" onClick={() => go("#wiki/benchmark-method")}><CircleHelp size={15} /> {t("How to compare", "如何对比")}</button></header>
    <div className="goal-preset-grid" aria-label={t("Starting points", "常用场景")}>{presets.map((preset) => <button key={preset.id} type="button" aria-pressed={activePreset === preset.id} onClick={() => pick(preset)}>
      <strong>{t(...preset.title)}</strong><span>{t(...preset.tagline)}</span>
    </button>)}</div>
    <div className="goal-workspace">
      <section className="goal-controls" aria-labelledby="goal-controls-title">
        <div className="goal-title-row"><SlidersHorizontal size={17} aria-hidden="true" /><h2 id="goal-controls-title">{t("Your requirements", "你的要求")}</h2></div>
        <div className="goal-settings">
          <Field label={t("Market", "市场")} value={state.region} options={[["us",t("US (USD)","美国 (USD)")],["cn",t("China (CNY)","中国 (CNY)")]]} onChange={market} />
          <Field label={t("Build condition", "配置成色")} value={condition} options={[["New build",t("New builds","全新配置")],["Used GPU build",t("Used GPU builds","二手显卡配置")]]} onChange={(value) => { setCondition(value); setSelected(null); }} />
        </div>
        {currency && currency !== priceUnit && <p className="goal-cohort-note">{t("Enter budget limits in {currency}.", "预算上限请以 {currency} 输入。", { currency: priceUnit })}</p>}
        <ul className="limit-list">{goals.map((goal) => <LimitControl goal={goal} metric={byId(metrics,goal.id)} key={goal.id}
          commit={update} canRemove={goals.length > 1} remove={(id) => { setPreset(""); setGoals((current) => current.filter((item) => item.id !== id)); }} />)}</ul>
        {choices.length > 0 && <div className="goal-add">
          <button type="button" className="btn outline" aria-expanded={adding} onClick={() => setAdding(!adding)}><Plus size={15} /> {t("Add a requirement", "添加要求")}</button>
          {adding && <div className="goal-add-options">{choices.map((metric) => <button type="button" className="text-button" key={metric.id} onClick={() => {
            setPreset(""); setGoals((current) => [...current,{id:metric.id,target:metric.defaultTarget}]); setAdding(false);
          }}>{metric.label}</button>)}</div>}
        </div>}
        <div className="goal-priority"><Field label={t("Prefer among matches", "达标配置排序")} value={priority} onChange={(id) => { setPriority(id); setPreset(""); }} options={metrics.map((metric) => [metric.id, metric.direction === "min"
          ? t("Lower {metric}", "{metric}更低", { metric: metric.label.toLowerCase() })
          : t("Higher {metric}", "{metric}更高", { metric: metric.label.toLowerCase() })])} />
          <p>{t("This sets the order of matching configurations.", "此选项用于排列符合要求的配置。")}</p></div>
      </section>
      <Results rows={rows} metrics={metrics} priority={priority} ready={ready} inspect={inspect} goals={goals} />
    </div>
    <section className="detail-section goal-evidence"><div className="detail-heading"><div><h2>{t("Compare exact values", "对比指标数值")}</h2>
      <p>{t("Sample Qwen2.5 7B Q4_K_M workloads. Single-user output speed and prefill, four-user p95 latency, and wall energy describe separate protocols.", "Qwen2.5 7B Q4_K_M 工作负载示例。单用户输出速度和预填充、四人并发 p95 延迟以及插座耗电量分别采用独立的测试方法。")}</p></div>
      <button className="btn outline" type="button" aria-pressed={allColumns} onClick={() => setAllColumns(!allColumns)}>{allColumns ? t("Show selected metrics", "只显示所选指标") : t("Show all metrics", "显示所有指标")}</button></div>
      {ready ? <MetricsTable rows={rows} metrics={metrics} columns={columns} inspect={inspect} /> : <div className="empty">{t("Enter valid limits to compare setups.", "请输入有效的限制值以对比配置。")}</div>}
      {shown && <MetricsDetail row={shown} metrics={metrics} close={() => setSelected(null)} />}
    </section>
    <WikiDetails slug="goals" go={go} onCopy={onCopy} />
  </div>;
}
