import React, { useEffect, useState } from "react";
import { ArrowUpRight, Pause, Play } from "lucide-react";
import { COST_DEFAULTS, COST_LIMITS, COST_PROFILES, calculateCost } from "./cost-data";
import { useLocale } from "./locale";

const methods = [
  { id: "bill", label: ["Parts and upgrades", "配件与升级"], note: ["Price each GPU, then account for card count, CPU, RAM, storage, and platform costs. GPU-only mode assumes the rest of the host is already suitable.", "先计算单卡价格和显卡数量，再计入 CPU、内存、存储和平台成本。仅升级显卡的方案假定现有主机已满足要求。"], source: [["Used-build parts estimate", "二手装机配件估算"], "mjR-LJmHg_I", 143] },
  { id: "memory", label: ["Memory and speed value", "显存与速度性价比"], note: ["Compare the GPU bill per installed GB and the full bill per assumed token/s. Physical VRAM across cards only serves a workload if its runtime can use the intended split.", "比较每 GB 显存的显卡成本，以及每单位推理速度的整机成本。只有推理框架支持所选的拆分方式，工作负载才能利用多张卡的物理显存。"], source: [["Price, memory and speed comparison", "价格、显存与速度对比"], "2L_RB-XqisE", 46] },
  { id: "energy", label: ["Wall power and cooling", "整机功耗与制冷"], note: ["Compute active and idle energy from wall watts × hours ÷ 1,000. External cooling adds the chosen percentage of IT energy. Fans measured at the wall are already included.", "运行与空闲电量分别按插座功率 × 小时 ÷ 1,000 计算。外部制冷按设备耗电量的一定比例另计。已包含在插座测量中的风扇耗电无需重复计算。"], source: [["Wall power across inference phases", "推理各阶段的整机功耗"], "MhZABCEOUWY", 473] },
  { id: "running", label: ["Monthly running cost", "每月运行成本"], note: ["Apply the electricity tariff to IT and external cooling kWh, then add monthly maintenance. The tariff is held constant across operating hours.", "以同一电价计算设备和外部制冷用电，再加上月度维护费。各时段使用相同电价。"], source: [["Wall power across inference phases", "推理各阶段的整机功耗"], "MhZABCEOUWY", 473] },
  { id: "cloud", label: ["API and GPU rental", "API 与 GPU 租赁"], note: ["API input and output are billed separately. A rental bills the effective hours needed to produce the same output plus paid idle time. Fixed subscriptions, request minima, and egress are outside the model.", "API 分别计算输入和输出费用。GPU 租赁计入获得相同输出所需的有效时长和付费空闲时长。固定订阅费、最低请求费用及出站流量费未纳入估算。"], source: [["Stopping an idle rental", "停止空闲的租赁实例"], "FVDEiBqFLBU", 1519] },
  { id: "unit", label: ["Cost per million output tokens", "每百万输出 token 的成本"], note: ["Divide each bill by the same useful output volume. The local ownership figure includes the selected horizon's hardware cost minus resale. Cloud API cost includes the chosen input-to-output ratio.", "用各方案成本除以同一有效输出量。本地总成本包含所选周期内的硬件支出，扣除期末残值。云 API 成本按所选输入与输出比例计算。"], source: [["Hardware price in API output tokens", "将硬件价格折算为 API 输出量"], "JPHT9AvoPSA", 1360] },
  { id: "payback", label: ["Ownership and payback", "持有成本与回本期"], note: ["Simple payback divides today's local outlay by monthly savings against the chosen cloud baseline. The chart shows nominal cash paid, including any terminal resale. The table also shows discounted cost.", "静态回本期等于本地初始支出除以相对所选云方案的每月节省额。图表展示扣除期末残值后的名义现金支出，表格同时显示折现成本。"], source: [["Annual volume and years of use", "年度用量与使用年限"], "JPHT9AvoPSA", 1360] },
  { id: "volume", label: ["Volume crossover", "用量成本交点"], note: ["Hold the horizon and assumptions constant as monthly demand changes. Local and rental curves stop where available hours cannot serve the requested volume.", "固定持有周期和其他假设，仅改变月度需求。超过可用时长所能满足的产量后，本地和租赁曲线停止。"], source: [["Local and API output-volume comparison", "本地与 API 输出量对比"], "JPHT9AvoPSA", 1360] },
  { id: "risk", label: ["Discounting and sensitivity", "折现与敏感性"], note: ["Change one input at a time to 50% or 150% of its selected value, within the editor's bounds. Discount month-end costs and resale using the effective monthly rate. Positive present-value savings favor local.", "每次仅调整一项输入，在允许范围内取当前值的 50% 和 150%。以实际月折现率折算月末支出与期末残值。节省现值为正表示本地方案更省。"] },
];
const upfrontInputs = [
  ["gpuUnitUsd", ["GPU per card", "单张显卡"], "USD"], ["cpuUsd", ["CPU", "CPU"], "USD"],
  ["ramUsd", ["System memory", "系统内存"], "USD"], ["platformUsd", ["Board, case, PSU and cooling hardware", "主板、机箱、电源与散热硬件"], "USD"],
  ["storageUsd", ["Storage", "存储"], "USD"],
];
const operationsInputs = [
  ["onlineHours", ["Local online time", "本地开机时间"], ["h/month", "小时/月"]], ["outputTps", ["Effective local output", "本地有效输出速度"], "tokens/s"],
  ["activeWatts", ["Active wall draw", "运行时插座功率"], "W"], ["idleWatts", ["Idle wall draw", "空闲时插座功率"], "W"],
  ["electricityUsdPerKwh", ["Electricity tariff", "电价"], "USD/kWh"], ["coolingPct", ["External cooling", "外部制冷"], ["% of IT kWh", "% 设备耗电量"]],
  ["maintenanceUsd", ["Maintenance", "维护费"], ["USD/month", "USD/月"]],
];
const cloudInputs = [
  ["inputPerOutput", ["Billed input per output token", "每个输出 token 对应的计费输入"], ["ratio", "比率"]],
  ["cloudInputUsdPerM", ["API input", "API 输入"], ["USD/M tokens", "USD/百万 tokens"]],
  ["cloudOutputUsdPerM", ["API output", "API 输出"], ["USD/M tokens", "USD/百万 tokens"]],
  ["rentalUsdPerHour", ["Rental price", "租赁价格"], ["USD/h", "USD/小时"]],
  ["rentalOutputTps", ["Effective rental output", "租用 GPU 有效输出速度"], "tokens/s"],
  ["rentalIdleHours", ["Billed rental idle", "计费空闲时长"], ["h/month", "小时/月"]],
];
const ownershipInputs = [["annualDiscountPct", ["Annual discount rate", "年折现率"], "%"], ["resaleUsd", ["Estimated terminal resale", "期末估计残值"], "USD"]];
const alternatives = { local: ["Local", "本地"], api: ["Cloud API", "云 API"], rental: ["GPU rental", "GPU 租赁"], tie: ["Equal cost", "成本相同"] };
const series = Object.entries({ localUsd: alternatives.local, apiUsd: alternatives.api, rentalUsd: alternatives.rental });
const bomLabels = { gpu: "显卡", cpu: "CPU", ram: "系统内存", platform: "主板、机箱、电源与散热硬件", storage: "存储" };
const sensitivityFields = {
  monthlyOutputM: ["每月输出量", "百万输出 tokens"],
  electricityUsdPerKwh: ["电价", "USD/kWh"],
  coolingPct: ["外部制冷耗电", "%"],
  cloudOutputUsdPerM: ["API 输出价格", "USD/百万输出 tokens"],
  rentalUsdPerHour: ["GPU 租赁价格", "USD/小时"],
};

function useCostFormats() {
  const { locale, t, formatMoney, displayCurrency } = useLocale();
  const unavailable = t("Unavailable", "无法计算");
  const formatNumber = (value, digits = 1) => value == null ? unavailable
    : value.toLocaleString(locale, { maximumFractionDigits: digits });
  const money = (value) => value == null ? unavailable
    : formatMoney(value, "USD", { minimumFractionDigits: 0, maximumFractionDigits: 2 });
  const axisMoney = (value) => formatMoney(value, "USD", { notation: "compact", minimumFractionDigits: 0, maximumFractionDigits: 1 });
  const alternative = (id) => t(...alternatives[id]);
  return { currency: displayCurrency("USD"), t, formatNumber, money, axisMoney, alternative };
}

const row = (label, value, detail) => ({ label, value, detail });

function AmountInput({ item, settings, options, set, t }) {
  const [key, label, unit] = item;
  return <label className="cost-field">
    <span>{t(...label)}</span>
    <span><input type="number" {...COST_LIMITS[key]} value={options[key] ?? settings[key]} onChange={(event) => set({ [key]: event.target.value })} /><small>{Array.isArray(unit) ? t(...unit) : unit}</small></span>
  </label>;
}

function Settings({ options, result, update, changeProfile, reset }) {
  const { t } = useLocale();
  const settings = { ...result.input, ...result.profile };
  const field = (item) => <AmountInput key={item[0]} item={item} settings={settings} options={options} set={update} t={t} />;
  return <aside className="cost-controls" aria-labelledby="cost-input-title">
    <div className="cost-control-head"><h2 id="cost-input-title">{t("Your assumptions", "估算参数")}</h2><button type="button" className="text-button" onClick={reset}>{t("Reset", "重置")}</button></div>
    <label className="cost-field">
      <span>{t("Local setup", "本地配置")}</span>
      <select value={settings.profileId} onChange={(event) => changeProfile(event.target.value)}>
        {COST_PROFILES.map(({ id, name }) => <option value={id} key={id}>{name}</option>)}
      </select>
    </label>
    <label className="cost-field">
      <span>{t("Purchase scope", "采购范围")}</span>
      <select value={settings.mode} onChange={(event) => update({ mode: event.target.value })}>
        <option value="build">{t("Full build", "整机装配")}</option><option value="reuse">{t("GPU-only upgrade", "仅升级显卡")}</option>
      </select>
    </label>
    {field(["monthlyOutputM", ["Monthly useful output", "每月有效输出量"], ["M tokens", "百万 tokens"]])}
    {field(["months", ["Ownership horizon", "持有周期"], ["months", "月"]])}
    <label className="cost-field">
      <span>{t("Payback baseline", "回本对照方案")}</span>
      <select value={settings.baseline} onChange={(event) => update({ baseline: event.target.value })}>
        <option value="api">{t("Cloud API", "云 API")}</option><option value="rental">{t("Hourly GPU rental", "按小时租赁 GPU")}</option>
      </select>
    </label>
    <div className="cost-advanced">
      {[[["Part prices", "配件价格"], upfrontInputs], [["Power and utilization", "功耗与利用率"], operationsInputs],
        [["Cloud pricing", "云端定价"], cloudInputs], [["Discounting and resale", "折现与残值"], ownershipInputs]].map(([label, fields]) =>
        <details key={label[0]}><summary>{t(...label)}</summary><div>{fields.map(field)}</div></details>)}
    </div>
  </aside>;
}

function Bars({ rows, format, animate }) {
  const low = Math.min(0, ...rows.map(({ value }) => value ?? 0));
  const high = Math.max(0, ...rows.map(({ value }) => value ?? 0));
  const extent = high - low || 1;
  const origin = -low / extent * 100;
  return <ul className="cost-bars" data-animate={animate}>
    {rows.map(({ label, value, detail }, index) => <li key={label}>
      <div><span>{label}</span><strong>{format(value)}</strong></div>
      {value != null && <div className="cost-bar-track" aria-hidden="true">
        <i style={{ left: origin + "%" }} />
        <span style={{ left: (value < 0 ? origin + value / extent * 100 : origin) + "%", width: Math.abs(value) / extent * 100 + "%" }} data-color={index % 3} data-negative={value < 0} />
      </div>}
      {detail && <small>{detail}</small>}
    </li>)}
  </ul>;
}

function LineFigure({ data, xKey, current, crossing, animate, xLabel }) {
  const { currency, t, formatNumber, axisMoney } = useCostFormats();
  const numbers = data.flatMap((entry) => series.map(([key]) => entry[key])).filter(Number.isFinite);
  const low = Math.min(0, ...numbers);
  const high = Math.max(1, ...numbers);
  const maxX = data.at(-1)[xKey] || 1;
  const x = (value) => 97 + value / maxX * 607;
  const y = (value) => 216 - (value - low) / (high - low || 1) * 183;
  return <div className="cost-lines" data-animate={animate}>
    <svg viewBox="0 0 740 264" role="img" aria-label={t("Cumulative cost in {currency} by {axis}", "按{axis}查看以 {currency} 显示的累计成本", { currency, axis: xLabel })}>
      {[0, 1, 2, 3, 4].map((index) => {
        const value = low + (high - low) * index / 4;
        return <g key={index}><line className="cost-grid" x1="96" x2="704" y1={y(value)} y2={y(value)} /><text x="85" y={y(value) + 4} textAnchor="end">{axisMoney(value)}</text></g>;
      })}
      {[0, 1, 2, 3, 4].map((index) => {
        const value = maxX * index / 4;
        return <text key={index} x={x(value)} y="241" textAnchor="middle">{formatNumber(value, 1)}</text>;
      })}
      <text x="399" y="260" textAnchor="middle">{xLabel}</text>
      {current && <line className="cost-marker" x1={x(current[xKey])} x2={x(current[xKey])} y1="29" y2="217" />}
      {series.map(([key]) => {
        const path = data.reduce((parts, entry, index) => {
          if (!Number.isFinite(entry[key])) return parts;
          const command = index > 0 && Number.isFinite(data[index - 1][key]) ? "L" : "M";
          return parts + command + x(entry[xKey]) + " " + y(entry[key]) + " ";
        }, "");
        return <g key={key} data-series={key}>
          <path d={path} pathLength="1" className="cost-trend" />
          {Number.isFinite(current?.[key]) && <circle cx={x(current[xKey])} cy={y(current[key])} r="4" />}
        </g>;
      })}
      {crossing && <circle className="cost-crossing" cx={x(crossing[xKey])} cy={y(crossing.localUsd)} r="6" />}
    </svg>
    <ul className="cost-legend">{series.map(([key, label]) => <li key={key} data-series={key}><i />{t(...label)}</li>)}</ul>
  </div>;
}

function ValueTable({ rows, format, label }) {
  const { t } = useLocale();
  return <table className="cost-value-table"><caption className="cost-sr-only">{label}</caption>
    <thead><tr><th scope="col">{t("Item", "比较项")}</th><th scope="col">{t("Value", "数值")}</th></tr></thead>
    <tbody>{rows.map(({ label: title, value, detail }) => <tr key={title}><th scope="row">{title}{detail && <small>{detail}</small>}</th><td className="numeric">{format(value)}</td></tr>)}</tbody>
  </table>;
}

function ComparisonRows({ monthly, totals, current, isTime }) {
  const { currency, t, money } = useCostFormats();
  return <table className="cost-value-table">
    <caption className="cost-sr-only">{isTime ? t("Ownership and cloud costs in {currency}", "持有与云端成本（{currency}）", { currency })
      : t("Volume scenario in {currency}", "用量情景（{currency}）", { currency })}</caption>
    <thead><tr><th scope="col">{t("Option", "方案")}</th>{isTime && <th scope="col">{t("Monthly", "每月")}</th>}<th scope="col">{t("At chart marker", "图表标记点")}</th>{isTime && <><th scope="col">{t("Horizon total", "周期总计")}</th><th scope="col">{t("Present value", "现值")}</th></>}</tr></thead>
    <tbody>{series.map(([key, name]) => <tr key={key}>
      <th scope="row">{t(...name)}</th>{isTime && <td>{money(monthly[key])}</td>}<td>{money(current[key])}</td>
      {isTime && <><td>{money(totals[key])}</td><td>{money(totals["discounted" + key[0].toUpperCase() + key.slice(1)])}</td></>}
    </tr>)}</tbody>
  </table>;
}

function RiskChart({ result, showTable, animate }) {
  const { t, money, formatNumber, alternative } = useCostFormats();
  const { input, sensitivity, totals } = result;
  const baseline = input.baseline;
  const mid = baseline === "api" ? totals.npvVsApiUsd : totals.npvVsRentalUsd;
  const scenarios = sensitivity.map((entry) => ({ ...entry, a: entry[baseline + "LowUsd"], b: entry[baseline + "HighUsd"] }));
  const values = scenarios.flatMap(({ a, b }) => [a, b]).filter(Number.isFinite);
  const low = Math.min(0, mid ?? 0, ...values);
  const high = Math.max(0, mid ?? 0, ...values);
  const position = (value) => (value - low) / (high - low || 1) * 100 + "%";
  return <>
    <p className="cost-result-text">{t("Present-value savings vs {baseline}", "相对{baseline}的节省现值", { baseline: alternative(baseline) })} <strong>{money(mid)}</strong></p>
    <div className="cost-table-wrap"><table className="cost-value-table">
      <thead><tr><th scope="col">{t("Assumption range", "参数范围")}</th>{!showTable && <th scope="col">{t("Effect on savings", "对节省额的影响")}</th>}<th scope="col">{t("Low input", "参数偏低")}</th><th scope="col">{t("High input", "参数偏高")}</th></tr></thead>
      <tbody>{scenarios.map(({ id, label, unit, low: inputLow, high: inputHigh, a, b }) => <tr key={id}>
        <th scope="row">{t(label, sensitivityFields[id][0])}<small>{formatNumber(inputLow, 3)}–{formatNumber(inputHigh, 3)} {t(unit, sensitivityFields[id][1])}</small></th>
        {!showTable && <td><div className="cost-range" data-animate={animate} aria-hidden="true">
          <i style={{ left: position(0) }} />
          {a != null && b != null && <span style={{ left: position(Math.min(a, b)), width: position(Math.abs(a - b) + low) }} />}
          {a != null && <b style={{ left: position(a) }} />}
          {b != null && <b style={{ left: position(b) }} />}
        </div></td>}
        <td>{money(a)}</td><td>{money(b)}</td>
      </tr>)}</tbody>
    </table></div>
  </>;
}

function CostChart({ method, result, showTable, animate }) {
  const { t, money, formatNumber, alternative } = useCostFormats();
  const { bom, hardware, capacity, input, monthly, profile, unit, totals, payback, crossover, timeline, volumeCurve } = result;
  const [month, setMonth] = useState(null);
  const [playing, setPlaying] = useState(false);
  const currentMonth = Math.min(month ?? input.months, input.months);
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  useEffect(() => {
    if (!playing) return;
    const timer = window.setTimeout(() => {
      const next = Math.min(currentMonth + Math.max(1, Math.ceil(input.months / 32)), input.months);
      setMonth(next);
      if (next === input.months) setPlaying(false);
    }, 190);
    return () => window.clearTimeout(timer);
  }, [currentMonth, input.months, playing]);
  const own = input.baseline;
  if (method === "payback" || method === "volume") {
    const isTime = method === "payback";
    const current = isTime ? timeline[currentMonth] : volumeCurve.find(({ volumeM }) => volumeM === input.monthlyOutputM);
    const crossing = !isTime && volumeCurve.find(({ volumeM }) => volumeM === crossover[own].volumeM);
    const shownPayback = payback[own];
    const crossingAt = crossover[own];
    const baselineName = alternative(own);
    const paybackMonths = formatNumber(shownPayback.months);
    const volume = formatNumber(crossingAt.volumeM, 2);
    const message = isTime
      ? shownPayback.monthlySavingsUsd == null ? t("Payback requires both options to serve the workload.", "只有两种方案都能满足工作负载，才能计算回本期。")
        : shownPayback.months == null ? t("No simple payback at these settings. Monthly savings are zero or negative.", "当前参数下无法回本。每月节省额为零或负数。")
          : shownPayback.months > input.months
            ? t("Simple payback vs {baseline} in {months} months, beyond the chosen horizon.", "相对{baseline}的静态回本期为 {months} 个月，超过所选持有周期。", { baseline: baselineName, months: paybackMonths })
            : t("Simple payback vs {baseline} in {months} months.", "相对{baseline}的静态回本期为 {months} 个月。", { baseline: baselineName, months: paybackMonths })
      : crossingAt.volumeM != null ? t("Cost crossover vs {baseline} at {volume}M output tokens/month.", "月输出 {volume} 百万 tokens 时，与{baseline}成本相同。", { baseline: baselineName, volume })
        : crossingAt.cheaperBelow === crossingAt.cheaperAbove && crossingAt.cheaperBelow != null
          ? crossingAt.cheaperBelow === "tie"
            ? t("Costs tie throughout the shared capacity.", "在两种方案都能运行的范围内，成本始终相同。")
            : t("{option} costs less across the shared capacity.", "在两种方案都能运行的范围内，{option}成本始终较低。", { option: alternative(crossingAt.cheaperBelow) })
          : t("No crossover within the modeled capacity.", "在估算的容量范围内，成本曲线没有交点。");
    return <>
      <p className="cost-result-text">{message}</p>
      {!showTable && <LineFigure data={isTime ? timeline : volumeCurve} xKey={isTime ? "month" : "volumeM"} current={current} crossing={crossing} animate={animate} xLabel={isTime ? t("Months", "月数") : t("Million useful output tokens per month", "每月有效输出量（百万 tokens）")} />}
      {isTime && <div className="cost-playback">
        <button type="button" className="btn outline" disabled={reduced} onClick={() => { if (!playing && currentMonth === input.months) setMonth(0); setPlaying(!playing); }}>
          {playing ? <Pause size={15} aria-hidden="true" /> : <Play size={15} aria-hidden="true" />}{playing ? t("Pause", "暂停") : t("Play timeline", "播放时间轴")}
        </button>
        <label><span>{t("Month {current} / {total}", "第 {current} 个月 / 共 {total} 个月", { current: formatNumber(currentMonth, 0), total: formatNumber(input.months, 0) })}</span><input type="range" aria-label={t("Month to inspect", "查看月份")} min="0" max={input.months} value={currentMonth} onChange={(event) => { setPlaying(false); setMonth(Number(event.target.value)); }} /></label>
      </div>}
      <div className="cost-table-wrap"><ComparisonRows monthly={monthly} totals={totals} current={current} isTime={isTime} /></div>
    </>;
  }
  if (method === "risk") return <RiskChart result={result} showTable={showTable} animate={animate} />;
  let renderValue = money;
  let rows;
  if (method === "bill") rows = [
    ...bom.map(({ id, label, usd, included }) => row(t(label, bomLabels[id]), usd, id === "gpu"
      ? t("{count} cards × {price}", "{count} 张 × {price}", { count: formatNumber(profile.gpuCount, 0), price: money(profile.gpuUnitUsd) })
      : !included ? t("Already owned in GPU-only mode", "仅升级显卡时沿用现有配件") : undefined)),
    row(t("Complete build", "整机成本"), hardware.fullBuildUsd),
    row(t("Cash due today", "初始支出"), hardware.upfrontUsd),
  ];
  if (method === "memory") {
    rows = COST_PROFILES.map(({ id }) => {
      const sample = id === profile.id ? result : calculateCost({ profileId: id });
      const installed = formatNumber(sample.hardware.vramGb);
      const pricePerSpeed = money(sample.hardware.fullBuildUsd / sample.profile.outputTps);
      return row(sample.profile.name, sample.hardware.usdPerVramGb,
        t("{memory} GB installed / {cost} per assumed token/s (full build)", "{memory} GB 显存 / 整机成本每 token/s 为 {cost}（按假定速度）", { memory: installed, cost: pricePerSpeed }));
    });
    renderValue = (value) => money(value) + " / GB";
  }
  if (method === "energy") {
    const activeHours = formatNumber(Math.min(capacity.localActiveHours, input.onlineHours));
    const idleHours = formatNumber(Math.max(0, input.onlineHours - capacity.localActiveHours));
    const activeWatts = formatNumber(profile.activeWatts);
    const idleWatts = formatNumber(profile.idleWatts);
    const cooling = formatNumber(input.coolingPct);
    rows = [
      row(t("Active compute", "推理用电"), monthly.activeKwh, t("{hours} h at {watts} W", "{hours} 小时 × {watts} W", { hours: activeHours, watts: activeWatts })),
      row(t("Idle host", "主机空闲用电"), monthly.idleKwh, t("{hours} h at {watts} W", "{hours} 小时 × {watts} W", { hours: idleHours, watts: idleWatts })),
      row(t("External cooling", "外部制冷"), monthly.coolingKwh, t("{percent}% of active and idle IT energy", "运行与空闲耗电量之和的 {percent}%", { percent: cooling })),
      row(t("Total metered energy and cooling", "设备与制冷用电合计"), monthly.activeKwh + monthly.idleKwh + monthly.coolingKwh),
    ];
    renderValue = (value) => formatNumber(value) + " kWh";
  }
  if (method === "running") rows = [
    row(t("IT electricity", "设备电费"), monthly.itElectricityUsd, t("{cost} per kWh", "每 kWh {cost}", { cost: money(input.electricityUsdPerKwh) })),
    row(t("External cooling electricity", "外部制冷电费"), monthly.coolingUsd),
    row(t("Maintenance", "维护费"), monthly.maintenanceUsd),
    row(t("Running cost to serve full demand", "满足全部需求的运行成本"), monthly.localUsd),
  ];
  if (method === "cloud") {
    const billInput = formatNumber(monthly.inputM);
    const billOutput = formatNumber(monthly.outputM);
    const billedHours = formatNumber(monthly.rentalBilledHours);
    const rentalIdle = formatNumber(input.rentalIdleHours);
    rows = [
      row(t("API input bill", "API 输入费用"), monthly.apiInputUsd, t("{volume}M input tokens", "{volume} 百万输入 tokens", { volume: billInput })),
      row(t("API output bill", "API 输出费用"), monthly.apiOutputUsd, t("{volume}M output tokens", "{volume} 百万输出 tokens", { volume: billOutput })),
      row(t("API monthly total", "API 月费用"), monthly.apiUsd),
      row(t("GPU rental monthly total", "GPU 月租赁费用"), monthly.rentalUsd,
        t("{hours} billed hours, including {idle} paid idle hours", "计费 {hours} 小时，其中空闲 {idle} 小时", { hours: billedHours, idle: rentalIdle })),
    ];
  }
  if (method === "unit") rows = [
    row(t("Local, including ownership", "本地，含持有成本"), unit.localUsd), row(t("Local, running only", "本地，仅运行成本"), unit.localRunningUsd),
    row(alternative("api"), unit.apiUsd), row(alternative("rental"), unit.rentalUsd),
  ];
  return showTable ? <ValueTable rows={rows} format={renderValue} label={t("Exact scenario values", "情景明细数值")} /> : <Bars rows={rows} format={renderValue} animate={animate} />;
}

export function CostPage({ go, initialMethod }) {
  const { currency, t, money, formatNumber, alternative } = useCostFormats();
  const [options, setOptions] = useState({});
  const [methodId, setMethod] = useState(methods.some(({ id }) => id === initialMethod) ? initialMethod : "payback");
  const [showTable, setShowTable] = useState(false);
  const result = calculateCost(options);
  const { capacity, input, hardware, monthly, payback } = result;
  const method = methods.find(({ id }) => id === methodId);
  const update = (changes) => setOptions((previous) => ({ ...previous, ...changes }));
  const changeProfile = (profileId) => setOptions((previous) => {
    const next = { ...previous, profileId };
    for (const [key] of Object.entries(COST_LIMITS)) if (!Object.hasOwn(COST_DEFAULTS, key)) delete next[key];
    return next;
  });
  const { months, monthlySavingsUsd } = payback[input.baseline];
  const baseline = alternative(input.baseline);
  const localMax = formatNumber(capacity.localMaxOutputM);
  const rentalMax = formatNumber(capacity.rentalMaxOutputM);
  const hoursNeeded = formatNumber(capacity.localActiveHours);
  return <div className="deep-page cost-page">
    <div className="deep-heading">
      <div><h1>{t("What will it cost to run?", "运行本地模型需要多少钱？")}</h1><p>{t("Price a local setup and compare ownership with hourly rental or a cloud API.", "估算本地配置的成本，并对比按小时租赁 GPU 和使用云 API。")}</p></div>
      <a className="btn outline" href="#methods" onClick={(event) => { event.preventDefault(); go("#methods"); }}>{t("Benchmark methods", "基准测试方法")} <ArrowUpRight size={15} aria-hidden="true" /></a>
    </div>
    <p className="cost-disclosure">{t("Edit the illustrative assumptions in USD. Results display in {currency}. Compare options that meet the same quality, latency, and availability requirements.",
      "估算参数以 USD 输入，结果以 {currency} 显示。示例数据仅用于比较，请对照满足相同质量、延迟和可用性要求的方案。", { currency })}</p>
    <dl className="cost-readouts">
      <div><dt>{t("Cash today", "初始支出")}</dt><dd>{money(hardware.upfrontUsd)}</dd></div>
      <div><dt>{t("Local running / month", "每月本地运行成本")}</dt><dd>{money(monthly.localUsd)}</dd></div>
      <div><dt>{t("Simple payback vs {baseline}", "相对{baseline}的静态回本期", { baseline })}</dt><dd>{monthlySavingsUsd == null ? t("Unavailable", "无法计算") : months == null ? t("No payback", "无法回本") : t("{months} mo", "{months} 个月", { months: formatNumber(months) })}</dd></div>
    </dl>
    <div className="cost-grid-outer">
      <Settings options={options} result={result} update={update} changeProfile={changeProfile} reset={() => setOptions({})} />
      <section className="cost-analysis" aria-labelledby="cost-analysis-title">
        <div className="cost-analysis-head">
          <label className="cost-field"><span>{t("Comparison view", "比较视图")}</span><select value={methodId} onChange={(event) => setMethod(event.target.value)}>
            {methods.map(({ id, label }) => <option key={id} value={id}>{t(...label)}</option>)}
          </select></label>
          <div className="segmented" role="group" aria-label={t("Presentation", "展示方式")}>
            <button type="button" className={!showTable ? "active" : ""} aria-pressed={!showTable} onClick={() => setShowTable(false)}>{t("Chart", "图表")}</button>
            <button type="button" className={showTable ? "active" : ""} aria-pressed={showTable} onClick={() => setShowTable(true)}>{t("Table", "表格")}</button>
          </div>
        </div>
        <h2 id="cost-analysis-title">{t(...method.label)}</h2>
        {(!capacity.localFeasible || !capacity.rentalFeasible) && <div className="cost-capacity" role="status">
          {!capacity.localFeasible && <p>{t("Local capacity is {volume}M output tokens per month. This demand would require {hours} active hours. Local ownership and full-demand unit economics are unavailable.", "本地每月最多输出 {volume} 百万 tokens，满足当前需求需要运行 {hours} 小时。暂无法估算满足全部需求的本地持有成本与单位成本。", { volume: localMax, hours: hoursNeeded })}</p>}
          {!capacity.rentalFeasible && <p>{t("Rental capacity is {volume}M output tokens per month. Rental costs for full demand are unavailable.", "租用 GPU 每月最多输出 {volume} 百万 tokens，暂无法估算满足全部需求的租赁成本。", { volume: rentalMax })}</p>}
        </div>}
        <CostChart key={methodId} method={methodId} result={result} showTable={showTable} animate={!showTable} />
        <div className="cost-method-note"><p>{t(...method.note)}</p>
          {method.source && <a href={"https://www.youtube.com/watch?v=" + method.source[1] + "&t=" + method.source[2] + "s"} target="_blank" rel="noreferrer">{t(...method.source[0])} <ArrowUpRight size={13} aria-hidden="true" /></a>}
          <a href="#wiki/comparison-methods">{t("Research and formula notes", "研究记录与公式说明")} <ArrowUpRight size={13} aria-hidden="true" /></a>
        </div>
      </section>
    </div>
  </div>;
}
