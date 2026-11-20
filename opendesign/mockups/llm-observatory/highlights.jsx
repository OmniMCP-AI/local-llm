import React, { useEffect, useId, useState } from "react";
import { ArrowUpRight, BookOpen, ChevronLeft, ChevronRight, CircuitBoard, MessageSquare, Pause, Play } from "lucide-react";
import { useLocale } from "./locale";

const highlights = __FASTEST_WIKI_HIGHLIGHTS__;
const icons = { news: BookOpen, configuration: CircuitBoard, "research-request": MessageSquare };

const reducedMotion = "(prefers-reduced-motion: reduce)";

export function Highlights({ go }) {
  const { t } = useLocale();
  const contentId = useId();
  const [index, setIndex] = useState(0);
  const [automatic, setAutomatic] = useState(() => !window.matchMedia(reducedMotion).matches);
  const [hovered, setHovered] = useState(false);
  const [focused, setFocused] = useState(false);
  const rotating = highlights.length > 1 && automatic && !hovered && !focused;

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

  if (highlights.length === 0) return null;

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
    {highlights.length > 1 && <div className="research-highlights-controls">
      <button type="button" aria-label={rotationAction} aria-controls={contentId} title={rotationAction}
        onClick={() => setAutomatic((value) => !value)}><Toggle size={15} aria-hidden="true" /></button>
      <button type="button" aria-label={previous} aria-controls={contentId} title={previous}
        onClick={() => move(-1)}><ChevronLeft size={17} aria-hidden="true" /></button>
      <span className="research-highlights-position" aria-hidden="true">{index + 1} / {highlights.length}</span>
      <button type="button" aria-label={next} aria-controls={contentId} title={next}
        onClick={() => move(1)}><ChevronRight size={17} aria-hidden="true" /></button>
    </div>}
    <div id={contentId} className="research-highlights-items" aria-live={rotating ? "off" : "polite"} aria-atomic="true">
      {highlights.map(({ id, title, titleZh, summary, detailZh, href, type }, position) => {
        const Icon = icons[type];
        const active = position === index;
        const internal = href.startsWith("#");
        return <a key={id} className="research-highlight" href={href} data-active={active}
          aria-hidden={!active} tabIndex={active ? undefined : -1}
          onClick={internal ? (event) => {
            if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0) return;
            event.preventDefault();
            go(href);
          } : undefined}>
          <Icon size={19} aria-hidden="true" />
          <span><strong>{t(title, titleZh)}</strong><small>{t(summary, detailZh)}</small></span>
          <ArrowUpRight size={16} aria-hidden="true" />
        </a>;
      })}
    </div>
  </section>;
}
