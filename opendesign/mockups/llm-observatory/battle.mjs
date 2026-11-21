import { catalogPath, topologyRevisionHref } from "./catalog-paths.mjs";
import { cardRatings } from "./catalog-position.mjs";

export const battleKinds = {
  cards: ["GPUs", "显卡"],
  machines: ["Machines", "整机"],
};

const suggestions = {
  cards: [
    ["nvidia-geforce-rtx-5090", "nvidia-geforce-rtx-4090", "Flagship upgrade", "旗舰升级",
      "Check whether your model and context need the extra VRAM, then confirm the exact board fits your case and power supply.",
      "先看模型和上下文是否需要额外显存，再核对具体板卡的机箱空间与电源要求。"],
    ["nvidia-geforce-rtx-4090", "nvidia-geforce-rtx-3090", "Same nominal capacity", "标称容量相同",
      "Both have 24 GB of nominal VRAM. Compare your workload on each generation and check the condition and warranty of the exact board.",
      "两者标称显存均为 24 GB。用你的工作负载比较两代显卡，并核对具体板卡的成色和保修。"],
    ["amd-radeon-rx-7900-xtx", "nvidia-geforce-rtx-3090", "Runtime compatibility", "推理框架兼容性",
      "Both have 24 GB of nominal VRAM. Check the runtime, acceleration backend and driver support for the operating system you plan to use.",
      "两者标称显存均为 24 GB。确认目标操作系统支持所用推理框架、加速后端和驱动。"],
    ["nvidia-rtx-a6000", "nvidia-geforce-rtx-5090", "Used workstation vs. new GeForce", "二手工作站显卡与新款 GeForce",
      "Check whether your workload needs the A6000’s 48 GB of ECC memory. On a used board verify condition, cooling, warranty, and the exact card’s connectors.",
      "确认工作负载是否需要 A6000 的 48 GB ECC 显存。购买二手板卡时核对成色、散热、保修和具体接口。"],
    ["nvidia-cmp-170hx-hynix", "nvidia-geforce-rtx-5060-ti-16gb", "Mining card vs. new GeForce", "矿卡与新款 GeForce",
      "The CMP entry contains a creator-reported modification. Verify actual installed and usable memory, display requirements, driver support, and board condition before relying on it.",
      "CMP 记录包含创作者报告的改装。选购前请核对实际安装及可用显存、显示需求、驱动支持和板卡成色。"],
    ["nvidia-geforce-rtx-2080-ti-original-11gb", "nvidia-geforce-rtx-5060-ti-16gb", "Older GeForce vs. current GeForce", "老款与现款 GeForce",
      "Check whether 11 GB covers your weights and context. Confirm your runtime and driver still support the older GPU and inspect the board if buying used.",
      "确认 11 GB 能否容纳模型权重和上下文。核对老款显卡的推理框架和驱动支持，购买二手板卡时检查成色。"],
    ["amd-radeon-rx-9070-xt", "nvidia-geforce-rtx-5070-ti", "16 GB across vendors", "跨品牌 16 GB 显卡",
      "Check your exact runtime and driver combination, then compare case clearance and connectors for the specific retail boards.",
      "确认所用推理框架与驱动的组合，再核对选购板卡的机箱空间和供电接口。"],
    ["amd-radeon-rx-6800-xt", "nvidia-geforce-rtx-5060-ti-16gb", "Older Radeon vs. current GeForce", "老款 Radeon 与现款 GeForce",
      "Both list 16 GB of nominal VRAM. Check backend support for the RX 6800 XT and the exact board’s cooling and connectors.",
      "两者标称显存均为 16 GB。请核对 RX 6800 XT 的后端支持，以及具体板卡的散热和供电接口。"],
    ["nvidia-geforce-rtx-3090", "nvidia-geforce-rtx-5060-ti-16gb", "More VRAM vs. lower rated power", "更多显存与更低额定功耗",
      "Check whether the workload fits in 16 GB. If it needs 24 GB, confirm that your case and power supply can accommodate the exact RTX 3090 board.",
      "确认工作负载是否能装入 16 GB。如果需要 24 GB，请核对机箱和电源能否适配具体的 RTX 3090 板卡。"],
    ["nvidia-rtx-a5000", "nvidia-geforce-rtx-5070-ti", "Used workstation vs. new GeForce", "二手工作站显卡与新款 GeForce",
      "Check whether your workflow needs the A5000’s ECC and 24 GB capacity. Verify fan condition and warranty for the actual used board.",
      "确认工作流是否需要 A5000 的 ECC 和 24 GB 容量，并检查实际二手板卡的风扇成色和保修。"],
    ["nvidia-geforce-rtx-3060-12gb", "intel-arc-b580", "12 GB across vendors", "跨品牌 12 GB 显卡",
      "Both list 12 GB of nominal VRAM. Compare support for the inference backend, model format and driver stack before you choose.",
      "两者标称显存均为 12 GB。选购前比较推理后端、模型格式及驱动支持。"],
    ["nvidia-geforce-rtx-5060-ti-16gb", "nvidia-geforce-rtx-5060-ti-8gb", "Memory variants", "显存版本",
      "Check whether the model weights, context cache and runtime overhead fit on the 8 GB variant.",
      "确认模型权重、上下文缓存和运行开销能否装入 8 GB 版本。"],
    ["nvidia-geforce-rtx-3090", "nvidia-geforce-rtx-5090", "Two-generation upgrade", "跨两代升级",
      "Check whether you need more than 24 GB of nominal VRAM and whether your case, cooling and power supply can support the replacement board.",
      "确认是否需要超过 24 GB 的标称显存，并检查机箱、散热和电源是否支持替换板卡。"],
    ["nvidia-geforce-rtx-4090", "nvidia-geforce-rtx-5080", "Previous flagship vs. current generation", "上代旗舰与现款显卡",
      "Check model and context fit at 16 GB and 24 GB before comparing your workload on each architecture.",
      "先确认模型和上下文在 16 GB 与 24 GB 显存下的适配情况，再比较两种架构上的工作负载。"],
    ["amd-radeon-rx-7900-xtx", "nvidia-geforce-rtx-4090", "24 GB across vendors", "跨品牌 24 GB 显卡",
      "Check both your runtime’s supported acceleration backends and the exact board requirements. Both list 24 GB of nominal VRAM.",
      "核对推理框架支持的加速后端和具体板卡要求。两者标称显存均为 24 GB。"],
    ["amd-radeon-ai-pro-r9700", "nvidia-geforce-rtx-5090", "Workstation Radeon vs. flagship GeForce", "Radeon 工作站显卡与 GeForce 旗舰",
      "Check your runtime’s backend requirements, board cooling and power needs. Compare matched results for the model and quantization you plan to run.",
      "核对推理后端要求、板卡散热和供电，再比较目标模型和量化方式下的同条件结果。"],
    ["nvidia-tesla-p40", "nvidia-geforce-rtx-5060-ti-16gb", "Used server accelerator vs. new GeForce", "二手服务器加速卡与新款 GeForce",
      "Check runtime support for the P40, host airflow for the passively cooled card, firmware compatibility, and the board’s condition and warranty.",
      "核对 P40 的推理框架支持、被动散热所需的机箱气流、固件兼容性、板卡成色及保修。"],
  ],
  machines: [
    ["apple-mac-mini-m4-24gb-512gb", "nvidia-dgx-spark-128gb-4tb", "Compact unified-memory systems", "紧凑型统一内存整机",
      "Check model fit and runtime support on each platform. The CPU and GPU share the installed memory pool.",
      "分别确认各平台的模型适配性和推理框架支持。CPU 和 GPU 共享已安装的内存。"],
    ["apple-mac-mini-m4-24gb-512gb", "apple-mac-mini-m6-24gb-512gb", "Same memory and storage tier", "相同内存与存储档位",
      "Check chip and runtime support. Both configurations list 24 GB unified memory and a 512 GB SSD.",
      "确认芯片和推理框架支持。两款配置均标注 24 GB 统一内存与 512 GB 固态硬盘。"],
    ["nvidia-dgx-spark-128gb-4tb", "tinybox-red-4x-mi300x-batch-2", "Shared pool vs. four accelerators", "共享内存与四加速卡",
      "Check memory per device and how the runtime distributes the model. The tinybox inventory spans four separate accelerators.",
      "核对单设备内存及推理框架的模型切分方式。tinybox 的显存分布在四个独立加速器上。"],
  ],
};

export const battleEvidence = [
  "Matched performance, price and measured energy data are unavailable for this comparison.",
  "此对比暂无同条件下的性能、价格与实测能耗数据。",
];

export function battleRecords(catalog) {
  return {
    cards: catalog.cards.map(({ id, name, memory, vendorSpec, variant, source }) => ({ id, name, memory, vendorSpec, variant, source })),
    machines: catalog.machines
      .filter(({ kind }) => kind !== "Component reference" && kind !== "Manufacturer system reference")
      .map(({ id, name, kind, memory, bom, gpu, detail, documentedPower, interconnect, configuration, source, capture,
        topologyRevision, fit }) => ({ id, name, kind, memory, bom, gpu, detail, documentedPower, interconnect,
        configuration, source, capture, topologyRevision, fit })),
  };
}

const https = (value) => {
  try {
    return new URL(value).protocol === "https:" ? value : null;
  } catch {
    return null;
  }
};
const cell = (text, source) => text ? { text, source: https(source) } : null;
const measurement = (value, unit, scope) => value != null ? { value, unit, scope } : null;
const row = (label, chinese, left, right, extra = {}) => ({ label: [label, chinese], left, right, ...extra });
const factSource = (product) => product.vendorSpec?.source;
const fact = (product, ...names) => names.map(name => product.vendorSpec?.facts[name]).find(Boolean);
const bareNumber = (value, unit) => /^\d+(?:\.\d+)?$/.test(value ?? "") ? value + " " + unit : value;
const ratedDifference = (left, right, name, positive, chinese) => {
  if (!left || !right || left.scope !== right.scope || left.unit !== right.unit || left.value === right.value) return null;
  return {
    name: left.value > right.value ? name[0] : name[1],
    quantity: Math.abs(left.value - right.value),
    unit: left.unit,
    message: ["{name} has {difference} " + positive + ".", "{name} " + chinese + " {difference}。"],
  };
};

function cardRows(left, right) {
  const products = [left, right];
  const names = products.map(({ name }) => name);
  const ratings = products.map(cardRatings);
  const sourced = (label, chinese, names, extra) => row(label, chinese,
    ...products.map(product => cell(fact(product, ...names), factSource(product))), extra);
  const capacity = ratings.map(({ capacity }) => measurement(capacity, "GB", "dedicated VRAM"));
  const bandwidth = ratings.map(({ bandwidth }, i) => {
    const value = fact(products[i], "Memory bandwidth", "Memory bandwidth (GB/s)");
    return measurement(bandwidth, "GB/s", /^up to /i.test(value ?? "") ? "upper bound" : "rated");
  });
  const power = ratings.map(({ power }) => measurement(power, "W", "rated graphics power"));

  return [
    row("Nominal VRAM", "标称显存", ...products.map(product => cell(
      bareNumber(fact(product, "Memory configuration", "Dedicated memory (GB)"), "GB"), factSource(product))),
    { factor: ratedDifference(...capacity, names, "more nominal VRAM", "的标称显存多") }),
    row("Memory reported by source", "来源报告的显存", ...products.map(product => cell(product.memory, product.source))),
    sourced("Aggregate module memory", "模块显存总量", ["Module memory (aggregate)"]),
    row("Rated memory bandwidth", "标称显存带宽", ...products.map(product =>
      cell(bareNumber(fact(product, "Memory bandwidth", "Memory bandwidth (GB/s)"), "GB/s"), factSource(product))),
    { factor: ratedDifference(...bandwidth, names, bandwidth.every(value => value?.scope === "upper bound")
      ? "higher peak memory bandwidth" : "higher rated memory bandwidth", "的标称显存带宽高"), differentScope: bandwidth.every(Boolean) && bandwidth[0].scope !== bandwidth[1].scope }),
    sourced("Aggregate module bandwidth", "模块总带宽", ["Module bandwidth (aggregate)"]),
    sourced("Memory bus", "显存位宽", ["Memory bus", "Memory bus (bits)"]),
    row("Rated graphics power", "标称显卡功耗",
      ...products.map(product => cell(bareNumber(fact(product, "Rated graphics power (W)"), "W"), factSource(product))),
      { factor: ratedDifference(...power, names, "higher rated graphics power", "的标称显卡功耗高") }),
    sourced("Rated board power", "标称板卡功耗", ["Board power (rated)"]),
    sourced("Maximum thermal design power", "最大热设计功耗", ["Maximum TDP (W)"]),
    sourced("Power connectors", "供电接口", ["Power connectors"]),
    row("Recommended system power", "建议整机电源功率",
      ...products.map(product => cell(bareNumber(fact(product, "Recommended system power (W)"), "W"), factSource(product)))),
    sourced("Board length or dimensions", "板卡长度或尺寸", ["Dimensions", "Board length"]),
    sourced("Slot width", "插槽厚度", ["Slot width"]),
    sourced("Form factor", "外形规格", ["Form factor", "Form factor and cooling"]),
    sourced("Cooling", "散热", ["Cooling", "Radiator dimensions"]),
    sourced("Host interface", "主机接口", ["Host interface"]),
    sourced("Interconnect", "互连", ["Interconnect"]),
    sourced("Architecture", "架构", ["Architecture"]),
    row("Specification scope", "规格适用范围", ...products.map(product => cell(product.vendorSpec?.scope, factSource(product)))),
    row("Board variant", "板卡版本", ...products.map(product => cell(product.variant, product.source))),
  ];
}

function machineRows(left, right) {
  const products = [left, right];
  const names = products.map(({ name }) => name);
  const memoryScope = (value) => /unified/i.test(value ?? "") ? "unified"
    : /(?:DDR\d|system RAM)/i.test(value ?? "") ? "system RAM" : null;
  const installed = products.map(product => {
    const value = product.memory?.system;
    const scope = memoryScope(value);
    const match = /^(\d+(?:\.\d+)?) GB\b/.exec(value ?? "");
    return scope && match && product.kind === "Complete factory configuration"
      ? measurement(Number(match[1]), "GB", scope) : null;
  });
  const power = products.map(({ documentedPower }) => {
    const match = /^(\d+(?:\.\d+)?) W$/.exec(documentedPower?.value ?? "");
    return match ? measurement(Number(match[1]), "W", documentedPower.label) : null;
  });
  const memory = (label, chinese, key, extra) =>
    row(label, chinese, ...products.map(product => cell(product.memory?.[key], product.source)), extra);
  const fitted = products.map(product => measurement(product.fit?.memory_bandwidth_gbps, "GB/s", "rated unified memory bandwidth"));
  const bom = (product, pattern, fallback) => {
    const parts = product.bom?.filter(({ category, part }) => part && pattern.test(category));
    if (!parts?.length) return cell(fallback, product.source);
    return cell(parts.map(({ part }) => part).join(" · "), parts[0].source);
  };
  const components = (label, chinese, pattern, fallback = () => null) =>
    row(label, chinese, ...products.map(product => bom(product, pattern, fallback(product))));

  return [
    memory("Installed system memory", "已安装系统内存", "system", {
      factor: ratedDifference(...installed, names, installed.every(value => value?.scope === "unified")
        ? "more installed unified memory" : "more installed system RAM", "的已安装系统内存多"),
      differentScope: [left, right].every(product => memoryScope(product.memory?.system)) && memoryScope(left.memory.system) !== memoryScope(right.memory.system),
    }),
    memory("Dedicated VRAM per device", "每设备独立显存", "perDevice"),
    memory("Aggregate VRAM inventory", "显存总量", "aggregate"),
    memory("Reported memory limit", "报告的内存限制", "allocation"),
    row("Rated unified memory bandwidth", "标称统一内存带宽", ...products.map((product, i) =>
      cell(fitted[i] && fitted[i].value + " GB/s", product.fit?.chip_source)),
    { factor: ratedDifference(...fitted, names, "higher rated unified memory bandwidth", "的标称统一内存带宽高") }),
    row("Documented power rating", "已记录额定功率", ...products.map(({ documentedPower }) =>
      documentedPower && cell(documentedPower.value + " · " + documentedPower.label, documentedPower.source)),
    { factor: ratedDifference(...power, names, "higher " + (power[0]?.scope ?? "").toLowerCase(), "的同口径额定功率高"),
      differentScope: products.every(product => product.documentedPower) && left.documentedPower.label !== right.documentedPower.label }),
    components("Processor", "处理器", /^cpu$/i),
    components("Graphics and accelerators", "显卡与加速器", /^gpu$/i, product => product.gpu),
    components("Installed storage", "已安装存储", /storage/i),
    components("Platform and chassis", "平台与机箱", /motherboard|platform|chassis/i),
    components("Power supply", "电源", /power supply|^psu$/i),
    components("Cooling", "散热", /^cooling$/i),
    row("Interconnect", "互连", ...products.map(product => cell(product.interconnect, product.source))),
    row("Configuration", "配置", ...products.map(product => cell(product.configuration ?? product.detail, product.source))),
  ];
}

export function battlePair(records, kind, leftId, rightId) {
  if (!Object.hasOwn(battleKinds, kind) || leftId === rightId) return null;
  const left = records[kind].find(record => record.id === leftId);
  const right = records[kind].find(record => record.id === rightId);
  if (!left || !right) return null;
  const rows = (kind === "cards" ? cardRows(left, right) : machineRows(left, right))
    .filter((entry, i) => i === 0 || entry.left || entry.right
      || (kind === "cards" && ["Rated memory bandwidth", "Rated graphics power", "Board length or dimensions"].includes(entry.label[0]))
      || (kind === "machines" && ["Rated unified memory bandwidth", "Documented power rating", "Processor", "Installed storage", "Interconnect"].includes(entry.label[0])));
  const suggestion = suggestions[kind].find(([a, b]) => (a === leftId && b === rightId) || (b === leftId && a === rightId));
  const decision = suggestion?.slice(4) ?? (kind === "cards"
    ? ["Check runtime support, board dimensions, connectors and power supply for the exact SKU.", "确认具体型号的推理框架支持、板卡尺寸、供电接口与电源要求。"]
    : ["Check usable memory, the runtime on your operating system and any per-device limits before choosing.", "选购前确认可用内存、操作系统支持的推理框架以及单设备限制。"]);
  return { kind, left, right, rows, decision, reason: suggestion?.slice(2, 4) };
}

export function battleSuggestions(records, kind) {
  return suggestions[kind].map(([left, right]) => battlePair(records, kind, left, right)).filter(Boolean);
}

export function battleHref(kind, pair, release) {
  if (!pair) return "#battle/" + kind;
  const params = new URLSearchParams({ left: pair.left.id, right: pair.right.id });
  if (release) params.set("release", release);
  return "#battle/" + kind + "?" + params;
}

export const battleScopeNote = ["Different specification scopes", "规格口径不同"];

export function battleSources(pair, product, { release, prefix }) {
  return [
    ...(release ? [{ label: ["Exact catalog profile", "目录中的具体配置"], href: prefix + catalogPath(release, pair.kind, product.id) }] : []),
    ...[...new Set([https(product.vendorSpec?.source ?? product.source), https(product.capture ?? product.source)].filter(Boolean))]
      .map((href, index) => ({
        label: index === 0 ? ["Specification source", "规格来源"] : ["Source record", "原始记录"], href,
      })),
    ...(topologyRevisionHref(product.topologyRevision) ? [{ label: ["Topology revision", "拓扑版本"], href: topologyRevisionHref(product.topologyRevision, prefix === "/" ? "/" : "") }] : []),
  ];
}

export function battleFactor({ name, quantity, unit, message }, t, number) {
  return t(...message, { name, difference: number.format(quantity) + " " + unit });
}

const md = (value) => String(value).replace(/[\\|*_<>[\]\x60]/g, "\\$&").replace(/[\r\n]+/g, " ");
const en = (english, chinese, values) => english.replace(/\{(\w+)\}/g, (_, key) => values?.[key] ?? "");
const number = new Intl.NumberFormat("en", { maximumFractionDigits: 2 });

export function battleMarkdown(pair, urls, level = "#") {
  const { left, right, rows } = pair;
  const link = (href) => (urls.origin && href.startsWith("/") ? urls.origin : "") + href;
  const value = (entry) => entry ? md(entry.text) : "Unavailable";
  const factors = rows.flatMap(({ factor }) => factor ? ["- " + md(battleFactor(factor, en, number))] : []);
  const compareHref = urls.share ?? link("/" + battleHref(pair.kind, pair, urls.release));
  return [
    level + " " + md(left.name) + " vs. " + md(right.name),
    "[Open comparison](" + compareHref + ")" + (urls.release ? " · Catalog " + urls.release : ""),
    ...(pair.reason ? [md(pair.reason[0])] : []),
    ...factors,
    md(pair.decision[0]),
    [
      "| Specification | " + md(left.name) + " | " + md(right.name) + " |",
      "| --- | --- | --- |",
      ...rows.map(entry => "| " + md(entry.label[0]) + (entry.differentScope ? " (" + battleScopeNote[0] + ")" : "")
        + " | " + value(entry.left) + " | " + value(entry.right) + " |"),
    ].join("\n"),
    ...[left, right].map(product => "**" + md(product.name) + "** · " + battleSources(pair, product, urls)
      .map(({ label, href }) => "[" + label[0] + "](" + link(href) + ")").join(" · ")),
    battleEvidence[0],
  ].join("\n\n") + "\n";
}

export function battleRankings(records, kind, rows) {
  if (!Array.isArray(rows)) return [];
  const seen = new Set();
  return rows.flatMap(entry => {
    const { left, right, count, sources } = entry ?? {};
    if (!Number.isSafeInteger(count) || count < 1) return [];
    const pair = battlePair(records, kind, left, right);
    if (!pair) return [];
    const key = [left, right].sort().join("|");
    if (seen.has(key)) return [];
    seen.add(key);
    return [{ ...pair, count, sources: Array.isArray(sources) ? sources.filter(source => {
      try {
        const url = new URL(source);
        return url.origin === "https://www.youtube.com" && url.pathname === "/watch" && /^[A-Za-z0-9_-]{11}$/.test(url.searchParams.get("v") ?? "");
      } catch {
        return false;
      }
    }) : [] }];
  });
}
