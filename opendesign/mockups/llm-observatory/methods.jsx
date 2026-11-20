import { useResearchLabels } from "./research-library";
import React, { useEffect, useState } from "react";
import { ArrowRight, ArrowUpRight, Pause, Play } from "lucide-react";
import { useLocale } from "./locale";

const fact = (name, value, detail, video, time, display) => ({ name, value, detail, video, time, display });
const scoreboard = "2L_RB-XqisE";
const dualCards = "1xmOTSUpBL0";
const macCluster = "4l4UWZGxvoc";
const strata = "qW2E2ay47dw";
const quality = "YcosZPh-kcI";
const cold = "MhZABCEOUWY";
const scoreboardScope = "Reported llama.cpp 7B scoreboard. Match artifact hash, context, batch and runtime before ranking hardware. These entries lack those controls.";

const groups = [
  { name: "Request speed", methods: [
    {
      id: "decode", title: "Decode", chart: "bars", scale: 200, unit: "tok/s",
      question: "How fast does output arrive after the first token?",
      scope: scoreboardScope,
      rows: [
        fact("RTX 5060 Ti", 97, "Reported generation rate.", scoreboard, 311),
        fact("RX 9070", 119, "Reported generation rate.", scoreboard, 351),
        fact("RX 7900 XTX", 191, "Reported generation rate.", scoreboard, 441),
        fact("RTX 3090", 172, "Reported generation rate.", scoreboard, 464),
        fact("RTX 4090", 190, "Reported generation rate.", scoreboard, 483),
      ],
    },
    {
      id: "prefill", title: "Prefill", chart: "bars", scale: 12000, unit: "tok/s",
      question: "How fast does the runtime process the input prompt?",
      scope: scoreboardScope + " Capture prompt length and cache state for this metric.",
      rows: [
        fact("RTX 5060 Ti", 3913, "Reported prompt processing rate.", scoreboard, 643),
        fact("RX 9070", 2860, "Reported prompt processing rate.", scoreboard, 648),
        fact("RX 7900 XTX", 3890, "Reported prompt processing rate.", scoreboard, 669),
        fact("RTX 3090", 5201, "Reported prompt processing rate.", scoreboard, 674),
        fact("RTX 4090", 10830, "Reported prompt processing rate.", scoreboard, 680),
      ],
    },
    {
      id: "first-token", title: "First token", unit: "s",
      question: "How long does the user wait for the first output token?",
      scope: "Measure from request submission to first token. Report queueing, loading and cache state. The example covers cold agent requests on one RTX 4090; exact artifact and prompt controls are missing.",
      steps: [
        ["Submit", "Start the user-perceived clock when the request is sent."],
        ["Queue & load", "A cold run can load weights or wait for capacity. Capture both conditions."],
        ["Prefill", "The runtime processes the input and builds any missing KV cache."],
        ["First token", "Stop the TTFT clock at the first streamed token. Record visible answer separately if reasoning is hidden."],
      ],
      rows: [
        fact("llama.cpp", 5, "Reported first cold agent request.", cold, 361, "≈5 s"),
        fact("NInfer", [12, 13], "Reported cold agent request. Approximate range as spoken.", cold, 363, "≈12–13 s"),
      ],
    },
  ] },
  { name: "Capacity & serving", methods: [
    {
      id: "context", title: "Context fit", chart: "bars", scale: 32, unit: "GB",
      question: "Can the model and its context fit in available memory?",
      scope: "Third-party estimates relayed by the creator for Qwen3.8 27B at 4-bit. File hash, KV format and runtime overhead are unknown. Confirm capacity with a run and record its offload.",
      threshold: 24,
      rows: [
        fact("Short conversation", 18, "Prompt size unspecified. Model and context estimate.", scoreboard, 786, "≈18 GB"),
        fact("64K context", 22, "Model and context estimate.", scoreboard, 790, "≈22 GB"),
        fact("128K context", 26, "Model and context estimate.", scoreboard, 790, "≈26 GB"),
      ],
    },
    {
      id: "serving", title: "Concurrent users", chart: "bars", scale: 400, unit: "tok/s",
      question: "How does adding users affect service and individual experience?",
      scope: "Creator-reported 27B run on a modified RTX 2080 Ti pair. Users, aggregate and per-user rates are as narrated. For a serving result, also record p95 TTFT, errors and the request mix.",
      series: ["Aggregate", "Per user"],
      rows: [
        fact("8 users", [251, 31], "Aggregate / per-user rates in the same observation.", dualCards, 563),
        fact("16 users", [376, 23], "Per-user rate approximate.", dualCards, 567, "376 / ≈23 tok/s"),
      ],
    },
    {
      id: "parallelism", title: "Work splitting", chart: "paired", scale: 60, unit: "tok/s",
      question: "Does layer split or tensor split work better for this run?",
      scope: "Owner reports presented by the creator. Rows come from different setups, with model and runtime fields incomplete. For a controlled test, keep the artifact, software and devices fixed and change only the split.",
      series: ["Layer split", "Tensor split"],
      rows: [
        fact("2 × RTX 3060", [33, 53], "Artifact and version unspecified.", "jEOIQ6Y7X6I", 429),
        fact("2 × RX 7900 XTX", [34, 47], "Artifact and version unspecified.", "jEOIQ6Y7X6I", 436),
        fact("4 × RTX 4090", [21, 48], "70B dense model discussed, exact artifact unspecified.", "jEOIQ6Y7X6I", 509),
      ],
    },
  ] },
  { name: "Topology & memory", methods: [
    {
      id: "links", title: "GPU link bandwidth", chart: "bars", scale: 100, unit: "GB/s",
      question: "How quickly can the two cards exchange data on the reported link?",
      scope: "Transport probe on a modified 2080 Ti pair with the optional NVLink bridge. Direction, payload and concurrency are unresolved. Benchmark tokens/s separately with each bridge state and runtime configuration.",
      extra: ["#wiki/gpu-topology", "Inspect the reported topology"],
      rows: [
        fact("Read–write probe", 74, "Reported transfer throughput.", dualCards, 689),
        fact("Multipath maximum", 87.5, "Reported peak under another transfer mode.", dualCards, 694),
      ],
    },
    {
      id: "hosts", title: "Multi-host transport", chart: "bars", scale: 20, unit: "tok/s",
      question: "What changes when the workload is spread across machines?",
      scope: "Creator-reported Exo/MLX runs with Llama 3.3 70B discussed. Pipeline and RDMA/tensor-sharded runs vary in both transport and strategy. Compare within matched host count and parallelism to isolate either effect.",
      rows: [
        fact("Two Mac Studios · pipeline", 5, "Creator-reported pipeline decode.", macCluster, 396),
        fact("Two Mac Studios · RDMA", 9, "Creator-reported decode with tensor sharding.", macCluster, 612),
        fact("Four Mac Studios · pipeline", 5, "Creator-reported pipeline decode.", macCluster, 411),
        fact("Four Mac Studios · RDMA", 15.5, "Llama 3.3 70B FP16 named for this run.", macCluster, 796),
      ],
    },
    {
      id: "tiers", title: "Memory tiers", chart: "bars", scale: 24, unit: "tok/s",
      question: "How does available host RAM affect a GPU/RAM/storage setup?",
      scope: "Reported same-GPU experiment varying the host RAM cap, with a trimmed DeepSeek artifact in the Strata discussion. Exact GPU SKU and runtime revision were not tied to the chart. Confirm memory placement, storage path and cache state.",
      rows: [
        fact("16 GB host RAM cap", 8, "Reported decode result.", strata, 718),
        fact("24 GB host RAM cap", 15, "Reported decode result.", strata, 718),
        fact("32 GB host RAM cap", 18, "Reported decode result.", strata, 718),
        fact("40 GB host RAM cap", 21, "Reported decode result.", strata, 718),
      ],
    },
  ] },
  { name: "Work & quality", methods: [
    {
      id: "workflow", title: "Workflow time",
      question: "How much time does the entire job take from request to checked result?",
      scope: "The source narrates read and write times for one coding step. The whole task could also include startup, tool calls and retries. Record total elapsed time separately over actual completed jobs.",
      steps: [
        ["Read context", "Collect the prompt, file context and tool output. Include repeated reads on long sessions."],
        ["Write", "Generate the edit or response. Count any reasoning and output under their own boundaries."],
        ["Run tools", "Measure external tool delay and retries as part of the job."],
        ["Check result", "Stop the workflow clock on a verified result or record a failure."],
      ],
      rows: [
        fact("Read phase", 1.5, "One coding step in a narrated same-PC example.", strata, 1084, "≈1.5 s"),
        fact("Write phase", 14, "Same narrated step. Complete job duration unavailable.", strata, 1084, "≈14 s"),
      ],
    },
    {
      id: "agent", title: "Agent task outcome",
      question: "Does the agent complete the work and preserve important details?",
      scope: "Creator examples on a single RTX 3060 using Strata. The observed thinking time and qualitative demonstrations have no controlled success rate. A comparison needs the same tools, rubric, time limit and task versions.",
      steps: [
        ["Fix the task", "Choose the same input, tool permissions and time limit for every setup."],
        ["Observe attempts", "Record retries, timeouts, unintended changes and valid completions."],
        ["Grade outputs", "Score only with a fixed rubric. Check detail-sensitive work like reading a corrected number."],
        ["Report outcomes", "Publish success counts alongside elapsed time and tool cost when those were recorded."],
      ],
      rows: [
        fact("Repository analysis", 617, "Narrated thinking time, with no total task duration.", "WOlXMUKJeuI", 122, "617 s thinking"),
        fact("Handwriting recognition", null, "Demonstration checks a corrected number. No standardized grade.", "WOlXMUKJeuI", 218, "Qualitative"),
        fact("Parallel sub-agents", null, "Batch and available memory restrictions discussed.", "WOlXMUKJeuI", 318, "Constraint noted"),
      ],
    },
    {
      id: "quality", title: "Repeat-trial quality", chart: "intervals", scale: 20, unit: "tasks",
      question: "How many tasks passed without fixes across repeated trials?",
      scope: "Creator's 20-task test, reporting three runs per variant and blind grading. A range reflects reported trial spread. A single count carries no inferred uncertainty. This is a small task-specific quality sample.",
      rows: [
        fact("Full-size Qwen", [11, 14], "Range of tasks without fixes.", quality, 260, "11–14 of 20"),
        fact("Bonsai", 10, "Reported count. Per-trial spread unavailable.", quality, 272, "10 of 20"),
        fact("Unsloth", 12, "Reported count. Per-trial spread unavailable.", quality, 288, "12 of 20"),
      ],
    },
  ] },
];

const categoryChinese = { "Request speed": "请求速度", "Capacity & serving": "容量与并发", "Topology & memory": "拓扑与内存", "Work & quality": "工作流与质量" };
const scoreboardScopeChinese = "来自视频转述的 llama.cpp 7B 测试榜单。对硬件排名时需固定模型文件、上下文、批量和运行时。这些记录没有完整控制条件。";
const methodChinese = {
  decode: ["解码", "首个词元输出后，生成速度有多快？", scoreboardScopeChinese],
  prefill: ["预填充", "运行时处理输入提示词的速度有多快？", scoreboardScopeChinese + "预填充还需记录提示词长度和缓存状态。"],
  "first-token": ["首词元延迟", "从提交请求到首个输出词元要等多久？", "从提交请求起测量首词元延迟。记录排队、加载与缓存状态。此处为单张 RTX 4090 的冷启动智能体请求示例，缺少完整模型文件和提示词控制条件。"],
  context: ["上下文容量", "可用内存能否容纳模型及其上下文？", "视频转述了 Qwen3.8 27B 4 位量化的第三方估算。模型文件哈希、KV 格式和运行时开销未知。通过实际运行验证容量并记录卸载情况。"],
  serving: ["并发用户", "用户增多时，总吞吐量和个人体验如何变化？", "创作者报告了两张改装 RTX 2080 Ti 的 27B 测试。用户数和总速率、单用户速率均为转述。验证服务能力时还应记录 p95 首词元延迟、错误和请求构成。"],
  parallelism: ["任务拆分", "按层拆分和张量拆分，哪种在本次运行中更有效？", "视频转述了多位用户的测试。各行的配置、模型和运行时信息不完整。要验证差异，固定模型文件、软件和设备，只更改拆分方式。"],
  links: ["显卡互联带宽", "在报告的连接条件下，两张显卡能以多快的速度交换数据？", "两张改装 RTX 2080 Ti 通过可选 NVLink 桥接的传输测试。传输方向、数据量和并发均未知。应另按各桥接状态和运行时配置测试词元速率。"],
  hosts: ["多机互联", "把工作负载分配到多台主机后，有什么变化？", "创作者报告了 Exo/MLX 运行，并讨论 Llama 3.3 70B。流水线和 RDMA 张量并行运行的传输与拆分方式均不同。隔离单项影响时，应固定主机数量并控制其他变量。"],
  tiers: ["内存层级", "主机内存上限如何影响显卡、内存与存储协同的系统？", "视频在 Strata 和裁剪版 DeepSeek 的讨论中报告了固定显卡、改变主机内存上限的实验。缺少确切显卡型号和运行时版本。验证时应记录数据放置、存储路径与缓存状态。"],
  workflow: ["工作流用时", "从发出请求到结果验收，完整任务要花多久？", "视频报告了一个编码步骤的读取与写入时间。完整工作流还可能包括初始化、工具调用和重试。总耗时应以实际完成的任务单独记录。"],
  agent: ["智能体任务结果", "智能体能完成工作并保留关键细节吗？", "此处为单张 RTX 3060 使用 Strata 的创作者示例。示例记录了思考时间和定性演示，缺少受控的任务成功率。比较时须固定工具、评分标准、时限和任务版本。"],
  quality: ["重复试验质量", "多次试验中，有多少任务无需返工就能通过？", "创作者的 20 项任务测试报告每个变体运行三次并盲评。区间表示已报告的试验差异，单一数值没有推断的误差区间。样本较小，结果限于这组任务。"],
};
const stepChinese = {
  "first-token": [
    ["提交请求", "发送请求时开始计时。"],
    ["排队与加载", "冷启动可能需要加载权重或等待空闲资源。记录这两种情况。"],
    ["预填充", "运行时处理输入并构建缺少的 KV 缓存。"],
    ["首个词元", "首次收到流式输出词元时结束计时。如果思考过程不可见，另记首个可见答案。"],
  ],
  workflow: [
    ["读取上下文", "收集提示词、文件上下文和工具输出。长任务中也要纳入重复读取。"],
    ["生成内容", "生成修改或回复，并分别计量思考过程与输出。"],
    ["运行工具", "将外部工具延迟和重试计入总用时。"],
    ["检查结果", "验证通过后结束计时。未通过时记录失败。"],
  ],
  agent: [
    ["固定任务", "各配置使用相同的输入、工具权限与时限。"],
    ["记录试验", "记录重试、超时、非预期修改和成功完成的结果。"],
    ["给结果评分", "使用固定评分标准，检查细节敏感任务，例如识别被改写的数字。"],
    ["报告结果", "报告通过任务数。如有记录，一并列出耗时与工具成本。"],
  ],
};
const chartChinese = {
  "Aggregate": "总吞吐量", "Per user": "单用户", "Layer split": "按层拆分", "Tensor split": "张量拆分",
  "Short conversation": "短对话", "64K context": "64K 上下文", "128K context": "128K 上下文",
  "8 users": "8 人并发", "16 users": "16 人并发", "Read–write probe": "读写传输", "Multipath maximum": "多路径峰值",
  "Two Mac Studios · pipeline": "2 台 Mac Studio · 流水线", "Two Mac Studios · RDMA": "2 台 Mac Studio · RDMA",
  "Four Mac Studios · pipeline": "4 台 Mac Studio · 流水线", "Four Mac Studios · RDMA": "4 台 Mac Studio · RDMA",
  "16 GB host RAM cap": "主机内存上限 16 GB", "24 GB host RAM cap": "主机内存上限 24 GB",
  "32 GB host RAM cap": "主机内存上限 32 GB", "40 GB host RAM cap": "主机内存上限 40 GB",
  "Read phase": "读取阶段", "Write phase": "写入阶段", "Repository analysis": "代码仓库分析",
  "Handwriting recognition": "手写识别", "Parallel sub-agents": "并行子智能体", "Full-size Qwen": "完整 Qwen",
  "11–14 of 20": "20 项中通过 11–14 项", "10 of 20": "20 项中通过 10 项", "12 of 20": "20 项中通过 12 项",
  "617 s thinking": "思考 617 秒", "Qualitative": "定性观察", "Constraint noted": "有使用限制", tasks: "任务数",
};

function MethodLink({ to, go, children }) {
  return <a href={to} onClick={(event) => {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    go(to);
  }}>{children} <ArrowRight size={14} aria-hidden="true" /></a>;
}

function formatResult(row, method, t, figures) {
  if (row.display) return t(row.display, chartChinese[row.display]);
  const value = Array.isArray(row.value)
    ? row.value.map((item) => figures.format(item)).join(" / ")
    : figures.format(row.value);
  return value + " " + t(method.unit, chartChinese[method.unit]);
}

function MethodChart({ method }) {
  const { t, locale } = useLocale();
  const figures = new Intl.NumberFormat(locale, { maximumFractionDigits: 2 });
  const [threshold, setThreshold] = useState(method.threshold);
  const { scale, rows, series, chart, unit } = method;
  const fitting = threshold ? rows.filter((row) => row.value <= threshold).length : 0;
  const position = (value) => (100 * value / scale) + "%";
  const title = t(method.title, methodChinese[method.id][0]);
  return <figure className="method-figure" aria-label={t("{title} visual summary", "{title}图示", { title })}>
    <div className="method-plot" aria-hidden="true">
      <div className="method-axis"><span>{t(unit, chartChinese[unit])}</span><div>{[0, scale / 2, scale].map((tick) => <span key={tick}>{figures.format(tick)}</span>)}</div><span /></div>
      {rows.map((row) => {
        const [first, second] = Array.isArray(row.value) ? row.value : [row.value, row.value];
        return <div className="method-chart-row" key={row.name}>
          <span>{t(row.name, chartChinese[row.name])}</span>
          <div className="method-track">
            {chart === "bars" ? <>
              <i className="method-bar" style={{ width: position(first) }} />
              {Array.isArray(row.value) && <i className="method-bar alt" style={{ width: position(second) }} />}
            </> : <>
              <i className="method-interval" style={{ left: position(Math.min(first, second)), width: position(Math.abs(first - second)) }} />
              <i className="method-point" style={{ left: position(first) }} />
              {first !== second && <i className={"method-point" + (chart === "paired" ? " alt" : "")} style={{ left: position(second) }} />}
            </>}
            {threshold && <i className="method-threshold" style={{ left: position(threshold) }} />}
          </div>
          <strong>{formatResult(row, method, t, figures)}</strong>
        </div>;
      })}
    </div>
    {series && <figcaption className="method-key">{series.map((label, index) => <span key={label}><i className={index === 1 ? "alt" : ""} aria-hidden="true" />{t(label, chartChinese[label])}</span>)}</figcaption>}
    {threshold && <div className="method-capacity">
      <label><span>{t("Available device memory", "设备可用内存")} <strong>{threshold} GB</strong></span><input type="range" min="12" max="32" value={threshold} onChange={(event) => setThreshold(event.target.valueAsNumber)} /></label>
      <p aria-live="polite">{t("{fitting} of {total} estimates are at or below the selected capacity.", "{total} 项估算中有 {fitting} 项未超过所选容量。", { fitting, total: rows.length })}</p>
    </div>}
  </figure>;
}

function MethodSteps({ steps, chinese }) {
  const { t } = useLocale();
  const [phase, setPhase] = useState(0);
  const [playing, setPlaying] = useState(false);
  const last = steps.length - 1;
  useEffect(() => {
    if (!playing) return;
    const timer = window.setTimeout(() => {
      if (phase >= last) setPlaying(false);
      else setPhase(phase + 1);
    }, 1400);
    return () => window.clearTimeout(timer);
  }, [phase, last, playing]);
  return <section className="method-timeline" aria-label={t("Illustrative phase sequence", "流程示意")}>
    <div className="method-timeline-header"><span>{t("Illustrative sequence · timing is schematic", "流程示意 · 播放时间为演示用")}</span>
      <button className="btn outline" type="button" onClick={() => {
        if (!playing && phase === last) setPhase(0);
        setPlaying(!playing);
      }}>{playing ? <Pause size={15} aria-hidden="true" /> : <Play size={15} aria-hidden="true" />}{playing ? t("Pause", "暂停") : t("Play steps", "播放步骤")}</button>
    </div>
    <ol>{steps.map(([name], index) => <li key={name}><button type="button" aria-pressed={phase === index} onClick={() => {
      setPlaying(false);
      setPhase(index);
    }}>{t(name, chinese[index][0])}</button></li>)}</ol>
    <p role="status">{t(steps[phase][1], chinese[phase][1])}</p>
  </section>;
}

function EvidenceTable({ method }) {
  const { t, locale } = useLocale();
  const figures = new Intl.NumberFormat(locale, { maximumFractionDigits: 2 });
  return <div className="table-wrap method-table"><table>
    <caption>{t("Source observations", "来源记录")}</caption>
    <thead><tr><th scope="col">{t("Case", "测试项目")}</th><th scope="col">{t("Reported result", "报告结果")}</th><th scope="col">{t("Conditions", "测试条件")}</th><th scope="col">{t("Source", "来源")}</th></tr></thead>
    <tbody>{method.rows.map((row) => {
      const name = t(row.name, chartChinese[row.name]);
      const minutes = Math.floor(row.time / 60);
      const seconds = row.time % 60;
      return <tr key={row.name}>
        <th scope="row">{name}</th><td className="numeric">{formatResult(row, method, t, figures)}</td><td lang="en">{row.detail}</td>
        <td><a href={"https://www.youtube.com/watch?v=" + row.video + "&t=" + row.time + "s"} target="_blank" rel="noreferrer"
          aria-label={t("Watch source for {name} at {minutes} minutes {seconds} seconds", "查看{name}的来源，定位至 {minutes} 分 {seconds} 秒", { name, minutes, seconds })}>
          {minutes}:{String(seconds).padStart(2, "0")} <ArrowUpRight size={13} aria-hidden="true" />
        </a></td>
      </tr>;
    })}</tbody>
  </table></div>;
}

export function MethodsPage({ go }) {
  const researchLabel = useResearchLabels();
  const { t } = useLocale();
  const [category, setCategory] = useState(0);
  const [choice, setChoice] = useState(0);
  const group = groups[category];
  const method = group.methods[choice];
  const [, question, scope] = methodChinese[method.id];
  return <div className="deep-page methods-page">
    <header className="deep-heading methods-heading">
      <div><h1>{t("Benchmark methods", "基准测试方法")}</h1><p>{t("Compare request speed, capacity, hardware links and the quality of completed work. Each view shows what was timed and which conditions matter.", "对比请求速度、容量、硬件互联和任务质量。每个视图都说明所测内容和关键条件。")}</p></div>
      <nav className="methods-links" aria-label={t("Related comparison views", "相关对比视图")}>
        <MethodLink to="#wiki/research" go={go}>{researchLabel("ui","library")}</MethodLink><MethodLink to="#costs" go={go}>{t("Cost lab", "成本实验室")}</MethodLink><MethodLink to="#wiki/comparison-methods" go={go}>{t("Methods wiki", "方法维基")}</MethodLink>
      </nav>
    </header>
    <div className="methods-picker" role="group" aria-label={t("Benchmark categories", "基准测试类别")}>{groups.map(({ name }, index) =>
      <button key={name} type="button" aria-pressed={category === index} onClick={() => {
        if (category !== index) { setCategory(index); setChoice(0); }
      }}>{t(name, categoryChinese[name])}</button>)}</div>
    <div className="methods-picker methods-subpicker" role="group" aria-label={t("{category} methods", "{category}方法", { category: t(group.name, categoryChinese[group.name]) })}>{group.methods.map(({ id, title }, index) =>
      <button key={id} type="button" aria-pressed={choice === index} onClick={() => setChoice(index)}>{t(title, methodChinese[id][0])}</button>)}</div>
    <article className="method-panel" aria-labelledby="current-method" key={method.id}>
      <header><h2 id="current-method">{t(method.question, question)}</h2><p>{t(method.scope, scope)}</p></header>
      {method.steps ? <MethodSteps steps={method.steps} chinese={stepChinese[method.id]} /> : <MethodChart method={method} />}
      <EvidenceTable method={method} />
      {method.extra && <div className="methods-links method-more"><MethodLink to={method.extra[0]} go={go}>{t(method.extra[1], "查看报告的硬件拓扑")}</MethodLink></div>}
    </article>
  </div>;
}
