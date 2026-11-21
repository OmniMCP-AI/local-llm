import React from "react";
import { renderCoordinatePlot } from "./coordinate-plot.mjs";
import { coordinatePlotStyles } from "./coordinate-plot-styles.mjs";

export function CoordinatePlot({ onSelect, ...chart }) {
  const markup = renderCoordinatePlot({ ...chart, onSelect });
  const selectPoint = (event) => {
    const mark = event.target.closest("button[data-point-id]");
    if (mark) onSelect(mark.dataset.pointId);
  };
  return <>
    <style>{coordinatePlotStyles}</style>
    <div onClick={onSelect ? selectPoint : undefined} dangerouslySetInnerHTML={{ __html: markup }} />
  </>;
}
