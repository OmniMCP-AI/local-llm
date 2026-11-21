const escape = value => String(value).replace(/[&<>"']/g, char => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
})[char]);

const formatNumber = new Intl.NumberFormat("en", { maximumSignificantDigits: 15 }).format;
const tickNumber = new Intl.NumberFormat("en", { maximumFractionDigits: 8 }).format;

export const axisTitle = ({ label, unit }) => unit ? `${label} (${unit})` : label;
const valueText = (axis, value) => axis.formatValue?.(value) ??
  `${typeof value === "number" ? formatNumber(value) : value}${axis.unit ? " " + axis.unit : ""}`;
const tickText = (axis, value) => axis.formatTick?.(value) ?? (typeof value === "number" ? tickNumber(value) : value);
const percent = value => `${(value * 100).toFixed(5)}%`;
const svgCoord = value => (value * 1000).toFixed(3);

function numericAxis(values, { zero = true, reverse = false, tickCount = 5, domain } = {}) {
  const minimum = Math.min(...values, ...(zero ? [0] : []));
  const maximum = Math.max(...values, ...(zero ? [0] : []));
  const range = maximum - minimum || Math.max(1, Math.abs(maximum) * .1);
  const approximate = range / tickCount;
  const magnitude = 10 ** Math.floor(Math.log10(approximate));
  const step = magnitude * [1, 2, 2.5, 4, 5, 10].find(factor => factor * magnitude >= approximate);
  const low = domain?.[0] ?? Math.floor(minimum / step) * step;
  const high = domain?.[1] ?? Math.max(low + step, Math.ceil((maximum + range * .03) / step) * step);
  const tickStart = Math.ceil(low / step);
  const tickEnd = Math.floor((high + step * 1e-9) / step);
  const valuesAtTicks = Array.from({ length: Math.max(0, tickEnd - tickStart + 1) }, (_, i) => (tickStart + i) * step);
  const normal = value => (value - low) / (high - low);
  return { at: reverse ? value => 1 - normal(value) : normal, ticks: valuesAtTicks };
}

function categoricalAxis(values) {
  const ticks = [...new Set(values)];
  const indices = new Map(ticks.map((value, index) => [value, index]));
  return { at: value => (indices.get(value) + .5) / ticks.length, ticks };
}

function axisMarkup(ticks, at, axis, direction) {
  const step = Math.max(1, Math.ceil(ticks.length / 8));
  return ticks.map((value, index) => {
    const marker = index % step === 0 || index === ticks.length - 1;
    if (!marker) return "";
    return `<span class="coordinate-tick coordinate-tick-${direction}${index % 2 ? " coordinate-tick-minor" : ""}" style="--at:${percent(at(value))}"><span>${escape(tickText(axis, value))}</span></span>`;
  }).join("");
}

function markMarkup(point, xAxis, yAxis, selection, actionable, kind, baseline, width) {
  const xValue = escape(point.xText ?? valueText(xAxis, point.x));
  const yValue = escape(point.yText ?? valueText(yAxis, point.y));
  const name = escape(point.name);
  const xLabel = escape(point.xLabel ?? xAxis.label);
  const yLabel = escape(point.yLabel ?? yAxis.label);
  const detail = point.detail ? escape(point.detail) : "";
  const location = `--column:${percent(point.left)};--row:${percent(point.top)}`;
  const selected = selection === point.id;
  const attributes = point.href ? `href="${escape(point.href)}"${selected ? ' aria-current="page"' : ""}`
    : actionable ? `type="button" aria-pressed="${selected}"` : 'tabindex="0"';
  const tag = point.href ? "a" : actionable ? "button" : "span";
  const bar = kind === "bar" ? `<i class="coordinate-bar" style="${location};--bar-width:${width};--bar-height:${percent(Math.abs(baseline - point.top))}" aria-hidden="true"></i>` : "";
  const mark = `<${tag} class="coordinate-mark" ${attributes} data-point-id="${escape(point.id)}" aria-label="${name}, ${xLabel} ${xValue}, ${yLabel} ${yValue}${detail ? ", " + detail : ""}" style="${location}"></${tag}>`;
  return `<div class="coordinate-point${selected ? " coordinate-selected" : ""}${point.highlighted ? " coordinate-highlighted" : ""}${point.context ? " coordinate-context" : ""}">${bar}${mark}
<span aria-hidden="true" class="coordinate-label" style="${location}">${escape(point.short ?? point.name)}</span>
<div aria-hidden="true" class="coordinate-popup" style="${location}"><strong>${name}</strong>${detail ? `<p>${detail}</p>` : ""}
<dl><div><dt>${xLabel}</dt><dd>${xValue}</dd></div><div><dt>${yLabel}</dt><dd>${yValue}</dd></div></dl></div></div>`;
}

export function renderCoordinatePlot({
  title, xAxis, yAxis, points, selectedId, onSelect, kind = "scatter", guides = [], targetArea, frontier = [],
  showLabels = false, labelsLabel = "Show point labels", emptyText = "No comparable values are available.",
}) {
  const valid = points.filter(({ x, y }) => (xAxis.categorical ? x != null : Number.isFinite(x)) && Number.isFinite(y));
  if (!valid.length) return `<p class="coordinate-empty" role="status">${escape(emptyText)}</p>`;
  const scaleFor = (axis, key) => numericAxis([
    ...valid.map(point => point[key]), ...guides.filter(guide => guide.axis === key).map(guide => guide.value),
  ], axis);
  const x = xAxis.categorical ? categoricalAxis(valid.map(point => point.x)) : scaleFor(xAxis, "x");
  const y = scaleFor(yAxis, "y");
  const pointsAt = valid.map(point => ({ ...point, left: x.at(point.x), top: 1 - y.at(point.y) }));
  const selected = pointsAt.find(point => point.id === selectedId);
  const topFor = value => 1 - y.at(value);
  const baseline = Math.max(0, Math.min(1, topFor(0)));
  const line = segments => segments.filter(segment => segment.length > 1).map(segment =>
    `<polyline points="${segment.map(point => `${svgCoord(point.left)},${svgCoord(point.top)}`).join(" ")}" />`).join("");
  const lineSegments = [[]];
  if (kind === "line") {
    for (const point of [...pointsAt].sort((left, right) => left.left - right.left)) {
      if (point.breakBefore) lineSegments.push([]);
      lineSegments.at(-1).push(point);
    }
  } else if (frontier.length > 1) {
    const order = new Map(frontier.map((id, index) => [id, index]));
    lineSegments[0] = pointsAt.filter(point => order.has(point.id))
      .sort((left, right) => order.get(left.id) - order.get(right.id));
  }
  const areaHeight = targetArea && topFor(targetArea.y);
  const area = targetArea ? `<div class="coordinate-target-area" style="--area-width:${percent(x.at(targetArea.x))};--area-height:${percent(yAxis.reverse ? areaHeight : 1 - areaHeight)};${yAxis.reverse ? "top:0" : "bottom:0"}"></div>` : "";
  const width = `min(3.5rem, ${percent(.58 / Math.max(1, x.ticks.length))})`;
  return `<div class="coordinate-plot coordinate-${kind}" role="group" aria-label="${escape(title)}" dir="ltr">
<div class="coordinate-heading"><strong>${escape(axisTitle(yAxis))}</strong><label><input type="checkbox"${showLabels ? " checked" : ""}> ${escape(labelsLabel)}</label></div>
<div class="coordinate-grid">
  ${area}
  <div aria-hidden="true">${axisMarkup(x.ticks, x.at, xAxis, "x")}${axisMarkup(y.ticks, topFor, yAxis, "y")}</div>
  ${lineSegments.some(segment => segment.length > 1) ? `<svg class="coordinate-line" viewBox="0 0 1000 1000" preserveAspectRatio="none" aria-hidden="true">${line(lineSegments)}</svg>` : ""}
  ${guides.map(guide => `<span class="coordinate-guide coordinate-guide-${guide.axis}" style="--at:${percent(guide.axis === "x" ? x.at(guide.value) : topFor(guide.value))}"><span>${escape(guide.label)}</span></span>`).join("")}
  ${pointsAt.map(point => markMarkup(point, xAxis, yAxis, selectedId, Boolean(onSelect), kind, baseline, width)).join("")}
</div>
<div class="coordinate-x-title">${escape(axisTitle(xAxis))}</div>
${selected ? `<span class="coordinate-selection">${escape(selected.name)}</span>` : ""}</div>`;
}
