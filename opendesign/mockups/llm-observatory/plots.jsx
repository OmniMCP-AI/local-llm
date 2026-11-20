import React, { useEffect, useId, useRef, useState } from "react";
import { quoteCurrency, useLocale } from "./locale";

const ink = "var(--color-ink)";
const muted = "var(--color-muted)";
const rule = "var(--color-rule)";
const accent = "var(--color-accent)";
const reference = "var(--color-accent-2)";
const paper = "var(--color-paper)";
const paper2 = "var(--color-paper-2)";
const paper3 = "var(--color-paper-3)";
const targetInset = "var(--color-chart-inset)";
const mutedBar = "var(--color-chart-bar)";
const markStyle = ".plot-mark{cursor:pointer}.plot-mark .plot-focus{opacity:0}.plot-mark:hover .plot-focus,.plot-mark:focus-visible .plot-focus{opacity:1}";

function usePlotWidth(initialWidth, visible = true) {
  const plot = useRef(null);
  const [width, setWidth] = useState(initialWidth);
  useEffect(() => {
    if (!visible || !plot.current || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(([entry]) => {
      const measured = Math.floor(entry.contentRect.width);
      if (measured > 0) setWidth(measured);
    });
    observer.observe(plot.current);
    return () => observer.disconnect();
  }, [visible]);
  return [plot, width];
}

function niceStep(maximum, count) {
  const proposed = Math.max(maximum / count, 0.0001);
  const magnitude = 10 ** Math.floor(Math.log10(proposed));
  const factor = [1, 2, 2.5, 4, 5, 8, 10].find((value) => value * magnitude >= proposed);
  return factor * magnitude;
}

function number(value) {
  return Number(value.toFixed(4)).toLocaleString("en-US", { maximumFractionDigits: 4 });
}

function hasTarget(target) {
  return Number.isFinite(target) && target >= 0;
}

function useMarkPreview(onSelect) {
  const [hovered, setHovered] = useState(null);
  const [focused, setFocused] = useState(null);
  const active = hovered ?? focused;
  useEffect(() => {
    if (!active) return;
    const dismiss = (event) => {
      if (event.key === "Escape") {
        setHovered(null);
        setFocused(null);
      }
    };
    window.addEventListener("keydown", dismiss);
    return () => window.removeEventListener("keydown", dismiss);
  }, [active]);
  const events = (point, selected, label) => {
    const activate = () => {
      setHovered(null);
      setFocused(null);
      onSelect(point.id);
    };
    return {
      role: "button",
      tabIndex: 0,
      "aria-pressed": selected,
      "aria-label": label,
      onPointerEnter: (event) => { if (event.pointerType !== "touch") setHovered(point.id); },
      onPointerLeave: () => setHovered((current) => current === point.id ? null : current),
      onFocus: (event) => { if (event.currentTarget.matches(":focus-visible")) setFocused(point.id); },
      onBlur: () => setFocused(null),
      onClick: activate,
      onKeyDown: (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          activate();
        }
      },
    };
  };
  return { active, events };
}

function PlotPreview({ point, width, height, workload, region }) {
  const { t, formatMoney, locale } = useLocale();
  const maxWidth = Math.min(264, width - 12);
  const x = point.x + maxWidth + 16 < width ? point.x + 10 : point.x - maxWidth - 10;
  const left = Math.max(6, Math.min(x, width - maxWidth - 6));
  const vertical = point.y < height / 2 ? { top: point.y + 10 } : { bottom: height - point.y + 10 };
  const value = new Intl.NumberFormat(locale, { maximumFractionDigits: 4 }).format(point.value);
  return <div aria-hidden="true" className="plot-preview" style={{ left, width: maxWidth, ...vertical }}>
    <strong>{point.name}</strong>
    {point.detail && <p lang="en">{point.detail}</p>}
    <dl>
      {region && Number.isFinite(point.price) && <div><dt>{t("Build price", "整机价格")}</dt><dd><bdi>{formatMoney(point.price, quoteCurrency(region))}</bdi></dd></div>}
      <div><dt>{t("Performance", "性能")}</dt><dd><bdi>{value} {t(workload.unit, workload.unit)}</bdi></dd></div>
    </dl>
    {!point.eligible && <span>{t("Context only", "仅供参考")}</span>}
  </div>;
}

function accessiblePointLabel(point, workload, price, t) {
  const timing = number(point.value) + " " + t(workload.unit, workload.unit);
  return [point.name, point.detail, price, timing, point.eligible ? null : t("Context only", "仅供参考"), t("Open details", "查看详情")].filter(Boolean).join(", ");
}

function labelPositions(points, bounds, reserved) {
  const occupied = [
    ...points.map((point) => ({
      left: point.x - 7, right: point.x + 7, top: point.y - 7, bottom: point.y + 7,
    })),
    ...reserved,
  ];
  return points.map((point) => {
    const width = point.short.length * 6.25 + 5;
    const placements = [
      [point.x + 11, point.y - 7],
      [point.x + 11, point.y + 14],
      [point.x - width - 9, point.y - 7],
      [point.x - width - 9, point.y + 14],
      [point.x - width / 2, point.y - 14],
      [point.x - width / 2, point.y + 23],
    ];
    const found = placements.find(([x, y]) => {
      const box = { left: x - 1, right: x + width, top: y - 10, bottom: y + 3 };
      if (box.left < bounds.left || box.right > bounds.right + 9 ||
          box.top < bounds.top + 6 || box.bottom > bounds.bottom + 4) return false;
      if (occupied.some((other) => (
        box.left < other.right + 2 && box.right > other.left - 2 &&
        box.top < other.bottom + 2 && box.bottom > other.top - 2
      ))) return false;
      occupied.push(box);
      return true;
    });
    return found ? { ...point, labelX: found[0], labelY: found[1] } : point;
  });
}

export function ScatterPlot({ points, workload, region, budget, target, selectedId, onSelect, showFrontier }) {
  const { t, formatMoney, displayCurrency } = useLocale();
  const sourceCurrency = quoteCurrency(region);
  const shortMoney = (value) => formatMoney(value, sourceCurrency, { notation: "compact", maximumFractionDigits: 1 });
  const headingId = useId();
  const [plot, width] = usePlotWidth(688);
  const preview = useMarkPreview(onSelect);
  const height = 282;
  const extent = { left: 43, right: width - 25, top: 31, bottom: height - 41 };
  const prices = points.map((point) => point.price);
  const values = points.map((point) => point.value);
  const showBudget = Number.isFinite(budget) && budget >= 0;
  const showTarget = hasTarget(target);
  const priceExtent = Math.max(...prices, showBudget ? budget : 0, region === "cn" ? 24000 : 3200);
  const valueExtent = Math.max(...values, showTarget ? target : 0, 1);
  const xStep = niceStep(priceExtent * 1.04, width < 390 ? 3 : 5);
  const yStep = niceStep(valueExtent * 1.09, 5);
  const xMax = Math.ceil(priceExtent * 1.055 / xStep) * xStep;
  const yMax = Math.ceil(valueExtent * 1.09 / yStep) * yStep;
  const x = (value) => extent.left + value / xMax * (extent.right - extent.left);
  const y = (value) => {
    const position = value / yMax * (extent.bottom - extent.top);
    return workload.lowerBetter ? extent.top + position : extent.bottom - position;
  };
  const xTicks = Array.from({ length: Math.round(xMax / xStep) + 1 }, (_, index) => index * xStep);
  const yTicks = Array.from({ length: Math.round(yMax / yStep) + 1 }, (_, index) => index * yStep);
  const budgetX = showBudget ? x(budget) : extent.left;
  const targetY = showTarget ? y(target) : extent.top;
  const regionWidth = budgetX - extent.left;
  const regionHeight = targetY - extent.top;
  const regionLabel = showBudget && showTarget && regionWidth >= 122 && regionHeight >= 25;
  const targetLabel = showTarget ? `Target ${number(target)} ${workload.unit}` : "";
  const targetLabelWidth = targetLabel.length * 6.3;
  const reserved = [];
  if (regionLabel) reserved.push({ left: extent.left, right: extent.left + 122, top: extent.top, bottom: extent.top + 22 });
  const targetLabelY = targetY < extent.top + 15 ? targetY + 14 : targetY - 6;
  if (showTarget) reserved.push({ left: extent.right - targetLabelWidth, right: extent.right, top: targetLabelY - 11, bottom: targetLabelY + 3 });
  const candidates = points.slice().sort((a, b) => Number(b.id === selectedId) - Number(a.id === selectedId)
    || Number(b.eligible) - Number(a.eligible));
  const marks = labelPositions(candidates.map((point) => ({ ...point, x: x(point.price), y: y(point.value) })), extent, reserved);
  const frontier = marks.filter((point) => point.eligible && !marks.some((other) => {
    if (!other.eligible || other.id === point.id || other.price > point.price) return false;
    const equalOrBetter = workload.lowerBetter ? other.value <= point.value : other.value >= point.value;
    return equalOrBetter && (other.value !== point.value || other.price < point.price);
  })).sort((a, b) => a.price - b.price);
  const axisName = workload.lowerBetter ? `Time (${workload.unit})` : `Decode speed (${workload.unit})`;
  const previewPoint = marks.find((point) => point.id === preview.active);

  return (
    <div className="plot-interactive">
     <svg ref={plot} className="plot-svg" viewBox={`0 0 ${width} ${height}`} width="100%" role="group" aria-labelledby={headingId}>
      <title id={headingId}>{`Build price versus ${axisName.toLowerCase()}.${showBudget && showTarget ? " The shaded area meets both targets." : ""}`}</title>
      <style>{markStyle}</style>
      <g aria-hidden="true" fontSize="11" fill={muted}>
        {showBudget && showTarget && (
          <rect x={extent.left} y={extent.top} width={regionWidth} height={regionHeight} fill={targetInset} />
        )}
        {yTicks.map((tick) => (
          <g key={tick}>
            <line x1={extent.left} x2={extent.right} y1={y(tick)} y2={y(tick)} stroke={rule} />
            <text x={extent.left - 8} y={y(tick) + 4} textAnchor="end">{number(tick)}</text>
          </g>
        ))}
        {xTicks.map((tick) => (
          <g key={tick}>
            <line x1={x(tick)} x2={x(tick)} y1={extent.top} y2={extent.bottom} stroke={rule} />
            <text x={x(tick)} y={extent.bottom + 16} textAnchor="middle">{shortMoney(tick)}</text>
          </g>
        ))}
        {showBudget && (
          <g>
            <line x1={budgetX} x2={budgetX} y1={extent.top} y2={extent.bottom} stroke={reference} strokeDasharray="4 4" />
            <text x={budgetX + (budgetX > extent.right - 67 ? -5 : 6)} y={extent.top - 7}
              textAnchor={budgetX > extent.right - 67 ? "end" : "start"} fill={ink} fontWeight="650">
              {t("Budget", "预算") + " " + shortMoney(budget)}
            </text>
          </g>
        )}
        {showTarget && (
          <g>
            <line x1={extent.left} x2={extent.right} y1={targetY} y2={targetY} stroke={reference} strokeDasharray="4 4" />
            <text x={extent.right - 3} y={targetLabelY}
              textAnchor="end" fill={ink} paintOrder="stroke" stroke={paper2} strokeWidth="3" fontWeight="650">
              {targetLabel}
            </text>
          </g>
        )}
        {regionLabel && <text x={extent.left + 9} y={extent.top + 16} fill={ink} fontWeight="650">Meets both targets</text>}
        <text x={extent.left} y="12" fill={ink} fontWeight="600">{axisName}</text>
        <text x={(extent.left + extent.right) / 2} y={height - 4} textAnchor="middle">{t("Build price", "整机价格")} ({displayCurrency(sourceCurrency)})</text>
      </g>
      {showFrontier && frontier.length > 1 && (
        <polyline aria-hidden="true" points={frontier.map((point) => `${point.x},${point.y}`).join(" ")}
          fill="none" stroke={accent} strokeOpacity=".76" strokeWidth="1.65" strokeDasharray="3 4" />
      )}
      {marks.length === 0 && (
        <text x={width / 2} y={height / 2} textAnchor="middle" fill={muted} fontSize="12">No setups with price and performance</text>
      )}
      {marks.slice().reverse().map((point) => {
        const selected = selectedId === point.id;
        const fill = point.eligible ? (selected ? accent : mutedBar) : paper;
        const stroke = point.eligible ? accent : muted;
        const label = accessiblePointLabel(point, workload, formatMoney(point.price, sourceCurrency), t);
        return (
          <g key={point.id} className="plot-mark" {...preview.events(point, selected, label)}>
            <circle cx={point.x} cy={point.y} r="14" fill={paper} fillOpacity="0" />
            <circle className="plot-focus" cx={point.x} cy={point.y} r="10.5" fill="none" stroke={reference} strokeWidth="1.5" />
            {selected && <circle cx={point.x} cy={point.y} r="9" fill={stroke} fillOpacity=".2" stroke={stroke} strokeOpacity=".46" />}
            <circle cx={point.x} cy={point.y} r={selected ? 5.6 : 4.6} fill={fill} stroke={stroke} strokeWidth={selected ? 1.75 : 1.25} />
            {point.labelX !== undefined && (
              <text x={point.labelX} y={point.labelY} fill={selected ? ink : muted}
                fontWeight={selected ? "700" : "500"} fontSize="11"
                paintOrder="stroke" stroke={paper2} strokeWidth="3">{point.short}</text>
            )}
          </g>
        );
      })}
     </svg>
     {previewPoint && <PlotPreview point={previewPoint} width={width} height={height} workload={workload} region={region} />}
    </div>
  );
}

export function RankingPlot({ points, workload, region, target, selectedId, onSelect }) {
  const { t, formatMoney } = useLocale();
  const preview = useMarkPreview(onSelect);
  const headingId = useId();
  const ranked = points.filter(({ eligible, value }) => eligible && Number.isFinite(value) && value >= 0)
    .sort((a, b) => workload.lowerBetter ? a.value - b.value : b.value - a.value);
  const [plot, width] = usePlotWidth(688, ranked.length > 0);

  if (!ranked.length) return <p className="plot-caption">No comparable measurements for this workload and price cohort.</p>;

  const height = 282;
  const bounds = { left: 40, right: width - 14, top: 34, bottom: height - 39 };
  const drawTarget = hasTarget(target);
  const maximum = Math.max(...ranked.map(({ value }) => value), drawTarget ? target : 0, 1);
  const step = niceStep(maximum * 1.14, 4);
  const yMax = Math.ceil(maximum * 1.14 / step) * step;
  const y = (value) => bounds.bottom - value / yMax * (bounds.bottom - bounds.top);
  const ticks = Array.from({ length: Math.round(yMax / step) + 1 }, (_, index) => index * step);
  const slot = (bounds.right - bounds.left) / ranked.length;
  const barWidth = Math.min(76, slot * .48);
  const targetY = drawTarget ? y(target) : null;
  const axisName = workload.lowerBetter ? `Time (${workload.unit})` : `Decode speed (${workload.unit})`;
  const direction = workload.lowerBetter ? "lower is better" : "higher is better";
  const activeIndex = ranked.findIndex((point) => point.id === preview.active);
  const previewPoint = activeIndex < 0 ? null : {
    ...ranked[activeIndex], x: bounds.left + slot * (activeIndex + .5), y: y(ranked[activeIndex].value),
  };

  return (
    <div className="plot-interactive">
     <svg ref={plot} className="plot-svg" viewBox={`0 0 ${width} ${height}`} width="100%" role="group" aria-labelledby={headingId}>
      <title id={headingId}>{`Eligible setups ranked by ${axisName.toLowerCase()}, ${direction}.${drawTarget ? ` Target ${number(target)} ${workload.unit}.` : ""}`}</title>
      <style>{markStyle}</style>
      <g aria-hidden="true" fill={muted} fontSize="11">
        <text x={bounds.left} y="13" fill={ink} fontWeight="650">{axisName}</text>
        <text x={bounds.right} y="13" textAnchor="end">{workload.lowerBetter ? "Lower is better" : "Higher is better"}</text>
        {ticks.map((tick) => (
          <g key={tick}>
            <line x1={bounds.left} x2={bounds.right} y1={y(tick)} y2={y(tick)} stroke={rule} />
            <text x={bounds.left - 8} y={y(tick) + 4} textAnchor="end">{number(tick)}</text>
          </g>
        ))}
      </g>
      {ranked.map((point, index) => {
        const selected = selectedId === point.id;
        const center = bounds.left + slot * (index + .5);
        const top = y(point.value);
        const name = width < 455 ? point.short.split(/\s+/) : [point.short];
        const price = region && Number.isFinite(point.price) ? formatMoney(point.price, quoteCurrency(region)) : null;
        const label = accessiblePointLabel(point, workload, price, t);
        return (
          <g key={point.id} className="plot-mark" {...preview.events(point, selected, label)}>
            <rect x={center - slot / 2 + 2} y={bounds.top - 9} width={slot - 4}
              height={height - bounds.top + 3} fill={paper} fillOpacity="0" />
            <rect className="plot-focus" x={center - barWidth / 2 - 4} y={top - 4} width={barWidth + 8}
              height={bounds.bottom - top + 4} rx="3" fill="none" stroke={reference} strokeWidth="1.5" />
            <rect x={center - barWidth / 2} y={top} width={barWidth}
              height={bounds.bottom - top} fill={selected ? accent : mutedBar}
              fillOpacity={selected ? 1 : Math.max(.54, 1 - index * .12)} />
            <text x={center} y={top - 8} textAnchor="middle" fill={ink} fontSize="12"
              fontWeight={selected ? "750" : "650"} paintOrder="stroke" stroke={paper2} strokeWidth="3">{number(point.value)}</text>
            <text x={center} y={bounds.bottom + 17} textAnchor="middle" fill={selected ? ink : muted} fontSize="11"
              fontWeight={selected ? "700" : "500"}>{name.map((part, partIndex) => (
                <tspan key={partIndex} x={center} dy={partIndex ? "12" : "0"}>{part}</tspan>
              ))}</text>
          </g>
        );
      })}
      {drawTarget && (
        <g aria-hidden="true" pointerEvents="none">
          <line x1={bounds.left} x2={bounds.right} y1={targetY} y2={targetY} stroke={reference} strokeDasharray="4 4" />
          <text x={bounds.right - 2} y={targetY - 6} textAnchor="end" fill={ink} fontSize="11"
            fontWeight="650" paintOrder="stroke" stroke={paper3} strokeWidth="3">
            Target {number(target)} {workload.unit}
          </text>
        </g>
      )}
     </svg>
     {previewPoint && <PlotPreview point={previewPoint} width={width} height={height} workload={workload} region={region} />}
    </div>
  );
}

const historyDates = ["Aug 14", "Aug 28", "Sep 11", "Sep 25", "Oct 9", "Oct 23", "Nov 6", "Nov 20"];

export function PricePlot({ values, formatValue }) {
  const headingId = useId();
  const areaId = useId();
  const [plot, width] = usePlotWidth(668, Boolean(values?.length));
  const format = formatValue ?? ((value) => `$${value.toLocaleString("en-US")}`);
  if (!values?.length) return <p className="plot-caption">No price history is available for this configuration.</p>;

  const left = 60, right = width - 29, top = 14, bottom = 154, height = 181;
  const low = Math.min(...values);
  const high = Math.max(...values);
  const step = niceStep(Math.max(high - low, high * 0.08, 1), 3);
  const min = Math.floor((low - step * 0.2) / step) * step;
  const max = Math.ceil((high + step * 0.2) / step) * step;
  const x = (index) => values.length === 1 ? (left + right) / 2 : left + index / (values.length - 1) * (right - left);
  const y = (value) => bottom - (value - min) / (max - min) * (bottom - top);
  const coords = values.map((value, index) => `${x(index)},${y(value)}`).join(" ");
  const ticks = Array.from({ length: Math.round((max - min) / step) + 1 }, (_, index) => min + index * step);

  return (
    <svg ref={plot} className="plot-svg" viewBox={`0 0 ${width} ${height}`} width="100%" role="img" aria-labelledby={headingId}>
      <title id={headingId}>{`Illustrative build quotes from ${format(values[0])} to ${format(values.at(-1))}`}</title>
      <defs>
        <linearGradient id={areaId} x1="0" y1="0" x2="0" y2="1">
          <stop stopColor={accent} stopOpacity=".22" />
          <stop offset="1" stopColor={accent} stopOpacity=".02" />
        </linearGradient>
      </defs>
      <g aria-hidden="true" fill={muted} fontSize="11">
        {ticks.map((tick) => (
          <g key={tick}>
            <line x1={left} x2={right} y1={y(tick)} y2={y(tick)} stroke={rule} />
            <text x={left - 8} y={y(tick) + 4} textAnchor="end">{format(tick)}</text>
          </g>
        ))}
        {values.map((_, index) => (
          (width > 470 || index % 3 === 0 || index === values.length - 1) &&
          <text key={index} x={x(index)} y={height - 7} textAnchor="middle">{historyDates[index] ?? `Quote ${index + 1}`}</text>
        ))}
      </g>
      {values.length > 1 && <polygon points={`${x(0)},${bottom} ${coords} ${x(values.length - 1)},${bottom}`}
        fill={`url(#${areaId})`} />}
      <polyline points={coords} fill="none" stroke={accent} strokeWidth="2" strokeLinejoin="round" />
      {values.map((value, index) => (
        <circle key={index} cx={x(index)} cy={y(value)} r={index === values.length - 1 ? 4.25 : 3}
          fill={index === values.length - 1 ? accent : paper2} stroke={accent} strokeWidth="1.6">
          <title>{`${historyDates[index] ?? `Quote ${index + 1}`}, ${format(value)}`}</title>
        </circle>
      ))}
    </svg>
  );
}
