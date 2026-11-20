import React, { useEffect, useId, useState } from "react";
import { ArrowUpRight, BookOpen, Calculator, ChevronLeft, ChevronRight, CircuitBoard, MessageSquare, Pause, Play, Terminal } from "lucide-react";
import { useLocale } from "./locale";

const highlights = [
  {
    title: "What will a local setup cost to run?",
    titleZh: "一套本地推理设备运行起来要花多少钱？",
    detail: "Compare purchase, electricity, cooling and cloud spend.",
    detailZh: "比较采购、电费、散热与云端开支。",
    href: "#costs", icon: Calculator,
  },
  {
    title: "How were these results measured?",
    titleZh: "这些结果是怎么测出来的？",
    detail: "See the workload, runtime and rules behind comparisons.",
    detailZh: "查看各项比较采用的工作负载、推理框架和测量规则。",
    href: "#methods", icon: BookOpen,
  },
  {
    title: "Two RTX 2080 Ti cards and an NVLink bridge",
    titleZh: "两张 RTX 2080 Ti 与 NVLink 桥接器",
    detail: "Inspect the reported setup and its optional GPU link.",
    detailZh: "查看研究中记录的双卡配置及其可选桥接方式。",
    href: "#wiki/gpu-topology/v029-hp-c001", icon: CircuitBoard,
  },
  {
    title: "Explore the inference runtime catalog",
    titleZh: "浏览推理框架目录",
    detail: "Find llama.cpp, SGLang, vLLM and card-specific tuning.",
    detailZh: "查看 llama.cpp、SGLang、vLLM 和各显卡系列的调优记录。",
    href: "#catalog/runtimes", icon: Terminal,
  },
  {
    title: "What should we test next?",
    titleZh: "下一项测试做什么？",
    detail: "Request a setup, model or workload through GitHub.",
    detailZh: "通过 GitHub 提交想测试的配置、模型或工作负载。",
    href: "https://github.com/OmniMCP-AI/local-llm/issues/new", icon: MessageSquare,
  },
];

const reducedMotion = "(prefers-reduced-motion: reduce)";

export function Highlights({ go }) {
  const { t } = useLocale();
  const contentId = useId();
  const [index, setIndex] = useState(0);
  const [automatic, setAutomatic] = useState(() => !window.matchMedia(reducedMotion).matches);
  const [hovered, setHovered] = useState(false);
  const [focused, setFocused] = useState(false);
  const rotating = automatic && !hovered && !focused;

  useEffect(() => {
    const preference = window.matchMedia(reducedMotion);
    const onChange = (event) => { if (event.matches) setAutomatic(false); };
    preference.addEventListener("change", onChange);
    return () => preference.removeEventListener("change", onChange);
  }, []);

  useEffect(() => {
    if (!rotating) return undefined;
    const timer = window.setInterval(() => setIndex((current) => (current + 1) % highlights.length), 9000);
    return () => window.clearInterval(timer);
  }, [rotating]);

  function move(direction) {
    setIndex((current) => (current + direction + highlights.length) % highlights.length);
  }

  const Toggle = automatic ? Pause : Play;
  const rotationAction = automatic ? t("Pause automatic rotation", "暂停自动轮播") : t("Start automatic rotation", "开启自动轮播");
  const previous = t("Previous highlight", "上一条精选");
  const next = t("Next highlight", "下一条精选");
  const heading = t("Research highlights", "研究精选");
  return <section className="research-highlights" aria-label={heading} aria-roledescription={t("carousel", "轮播")}
    onPointerEnter={(event) => { if (event.pointerType === "mouse") setHovered(true); }}
    onPointerLeave={() => setHovered(false)}
    onFocusCapture={() => setFocused(true)}
    onBlurCapture={(event) => { if (!event.currentTarget.contains(event.relatedTarget)) setFocused(false); }}>
    <strong className="research-highlights-label">{heading}</strong>
    <div className="research-highlights-controls">
      <button type="button" aria-label={rotationAction} aria-controls={contentId} title={rotationAction}
        onClick={() => setAutomatic((value) => !value)}><Toggle size={15} aria-hidden="true" /></button>
      <button type="button" aria-label={previous} aria-controls={contentId} title={previous}
        onClick={() => move(-1)}><ChevronLeft size={17} aria-hidden="true" /></button>
      <span className="research-highlights-position" aria-hidden="true">{index + 1} / {highlights.length}</span>
      <button type="button" aria-label={next} aria-controls={contentId} title={next}
        onClick={() => move(1)}><ChevronRight size={17} aria-hidden="true" /></button>
    </div>
    <div id={contentId} className="research-highlights-items" aria-live={rotating ? "off" : "polite"} aria-atomic="true">
      {highlights.map(({ title, titleZh, detail, detailZh, href, icon: Icon }, position) => {
        const active = position === index;
        const internal = href.startsWith("#");
        return <a key={href} className="research-highlight" href={href} data-active={active}
          aria-hidden={!active} tabIndex={active ? undefined : -1}
          onClick={internal ? (event) => {
            if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0) return;
            event.preventDefault();
            go(href);
          } : undefined}>
          <Icon size={19} aria-hidden="true" />
          <span><strong>{t(title, titleZh)}</strong><small>{t(detail, detailZh)}</small></span>
          <ArrowUpRight size={16} aria-hidden="true" />
        </a>;
      })}
    </div>
  </section>;
}
