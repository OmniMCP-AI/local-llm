import React, { useLayoutEffect, useRef, useState } from "react";
import { renderCoordinatePlot } from "./coordinate-plot.mjs";
import { coordinatePlotStyles } from "./coordinate-plot-styles.mjs";

export function CoordinatePlot({ onSelect, showLabels = false, ...chart }) {
  const labels = useRef(showLabels);
  const [zoom, setZoom] = useState({ start: 0, end: 1 });
  const zoomFocus = useRef(null);
  const content = useRef(null);
  const focused = useRef(null);
  const markup = renderCoordinatePlot({ ...chart, onSelect, showLabels: labels.current, interactiveZoom: true, zoom });

  useLayoutEffect(() => {
    if (zoomFocus.current) {
      const button = content.current.querySelector(`[data-zoom="${zoomFocus.current}"]`);
      (button?.disabled ? content.current.querySelector('[data-zoom="in"]') : button)?.focus();
      zoomFocus.current = null;
      return;
    }
    if (document.activeElement !== document.body || !focused.current) return;
    const mark = [...content.current.querySelectorAll("[data-point-id]")]
      .find(element => element.dataset.pointId === focused.current);
    mark?.focus({ preventScroll: true });
  }, [markup]);

  const handleClick = (event) => {
    if (event.target.matches("input[type=checkbox]")) labels.current = event.target.checked;
    const control = event.target.closest("button[data-zoom]");
    if (control) {
      const action = control.dataset.zoom;
      zoomFocus.current = action;
      setZoom(({ start, end }) => {
        const width = end - start;
        if (action === "reset") return { start: 0, end: 1 };
        if (action === "previous" || action === "next") {
          const next = Math.max(0, Math.min(1 - width, start + (action === "next" ? width / 2 : -width / 2)));
          return { start: next, end: next + width };
        }
        const nextWidth = Math.min(1, Math.max(1 / 64, width * (action === "in" ? .5 : 2)));
        const next = Math.max(0, Math.min(1 - nextWidth, (start + end - nextWidth) / 2));
        return { start: next, end: next + nextWidth };
      });
      return;
    }
    const mark = event.target.closest("button[data-point-id]");
    if (mark) onSelect?.(mark.dataset.pointId);
  };
  const handleKeyDown = (event) => {
    if (!onSelect || (event.key !== "Enter" && event.key !== " ")) return;
    const mark = event.target.closest("button[data-point-id]");
    if (!mark) return;
    event.preventDefault();
    onSelect(mark.dataset.pointId);
  };
  return <>
    <style>{coordinatePlotStyles}</style>
    <div ref={content} onClick={handleClick} onKeyDown={handleKeyDown}
      onFocus={(event) => { focused.current = event.target.dataset.pointId; }}
      onBlur={() => { focused.current = null; }}
      dangerouslySetInnerHTML={{ __html: markup }} />
  </>;
}
