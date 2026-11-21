import React, { useLayoutEffect, useRef } from "react";
import { renderCoordinatePlot } from "./coordinate-plot.mjs";
import { coordinatePlotStyles } from "./coordinate-plot-styles.mjs";

export function CoordinatePlot({ onSelect, showLabels = false, ...chart }) {
  const labels = useRef(showLabels);
  const content = useRef(null);
  const focused = useRef(null);
  const markup = renderCoordinatePlot({ ...chart, onSelect, showLabels: labels.current });

  useLayoutEffect(() => {
    if (document.activeElement !== document.body || !focused.current) return;
    const mark = [...content.current.querySelectorAll("[data-point-id]")]
      .find(element => element.dataset.pointId === focused.current);
    mark?.focus({ preventScroll: true });
  }, [markup]);

  const handleClick = (event) => {
    if (event.target.matches("input[type=checkbox]")) labels.current = event.target.checked;
    const mark = event.target.closest("button[data-point-id]");
    if (mark) onSelect?.(mark.dataset.pointId);
  };
  return <>
    <style>{coordinatePlotStyles}</style>
    <div ref={content} onClick={handleClick}
      onFocus={(event) => { focused.current = event.target.dataset.pointId; }}
      onBlur={() => { focused.current = null; }}
      dangerouslySetInnerHTML={{ __html: markup }} />
  </>;
}
