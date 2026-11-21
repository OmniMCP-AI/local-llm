const escape = value => String(value).replace(/[&<>"']/g, char => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
})[char]);

const formatNumber = new Intl.NumberFormat("en", { maximumSignificantDigits: 15 }).format;
const tickNumber = new Intl.NumberFormat("en", { maximumFractionDigits: 8 }).format;

export const axisTitle = ({ label, unit }) => unit ? `${label} (${unit})` : label;
const valueText = (axis, value) => axis.formatValue?.(value) ??
  `${typeof value === "number" ? formatNumber(value) : value}${axis.unit ? " " + axis.unit : ""}`;
const tickText = (axis, value) => axis.formatTick?.(value) ?? axis.tickLabels?.[value] ?? (typeof value === "number" ? tickNumber(value) : value);
const percent = value => `${(value * 100).toFixed(5)}%`;
const svgCoord = value => (value * 1000).toFixed(3);

function numericAxis(values, { zero = true, reverse = false, tickCount = 5, domain } = {}) {
  const minimum = Math.min(...values, ...(zero ? [0] : []));
  const maximum = Math.max(...values, ...(zero ? [0] : []));
  if (minimum === maximum && !zero && !domain) return { at: () => .5, ticks: [minimum] };
  const range = maximum - minimum || Math.max(1, Math.abs(maximum) * .1);
  const approximate = (domain ? domain[1] - domain[0] : range) / tickCount;
  const magnitude = 10 ** Math.floor(Math.log10(approximate));
  const step = magnitude * [1, 2, 2.5, 4, 5, 10].find(factor => factor * magnitude >= approximate);
  const low = domain?.[0] ?? Math.floor(minimum / step) * step;
  const high = domain?.[1] ?? Math.max(low + step, Math.ceil((maximum + range * .03) / step) * step);
  const tickStart = Math.ceil(low / step);
  const tickEnd = Math.floor((high + step * 1e-9) / step);
  const valuesAtTicks = Array.from({ length: Math.max(0, tickEnd - tickStart + 1) }, (_, i) => (tickStart + i) * step);
  const normal = value => (value - low) / (high - low);
  return { at: reverse ? value => 1 - normal(value) : normal, ticks: valuesAtTicks, low, high };
}

function categoricalAxis(values) {
  const ticks = [...new Set(values)];
  const indices = new Map(ticks.map((value, index) => [value, index]));
  return { at: value => (indices.get(value) + .5) / ticks.length, ticks };
}

function axisMarkup(ticks, at, axis, direction) {
  const count = Math.min(ticks.length, 5);
  const shown = count === 1 ? ticks : Array.from({ length: count }, (_, index) => ticks[Math.round(index * (ticks.length - 1) / (count - 1))]);
  return shown.map((value, index) =>
    `<span class="coordinate-tick coordinate-tick-${direction}${index % 2 ? " coordinate-tick-minor" : ""}" style="--at:${percent(at(value))}"><span>${escape(tickText(axis, value))}</span></span>`
  ).join("");
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
    : actionable ? `type="button" aria-pressed="${selected}"` : 'role="img" tabindex="0"';
  const tag = point.href ? "a" : actionable ? "button" : "span";
  const barHeight = percent(Math.abs(baseline - point.top));
  const barStyle = `--bar-width:${width};--bar-height:${barHeight};--bar-top:${percent(Math.min(baseline, point.top))}`;
  const bar = kind === "bar" ? `<i class="coordinate-bar-shape" style="${location};${barStyle}" aria-hidden="true"></i>` : "";
  const mark = `<${tag} class="coordinate-mark" ${attributes} data-point-id="${escape(point.id)}" aria-label="${name}, ${xLabel} ${xValue}, ${yLabel} ${yValue}${detail ? ", " + detail : ""}" style="${location}${kind === "bar" ? ";" + barStyle : ""}"></${tag}>`;
  return `<div class="coordinate-point${selected ? " coordinate-selected" : ""}${point.highlighted ? " coordinate-highlighted" : ""}${point.context ? " coordinate-context" : ""}" data-series="${escape(point.series ?? "")}">${bar}${mark}
<div aria-hidden="true" class="coordinate-popup" style="${location}"><strong>${name}</strong>${detail ? `<p>${detail}</p>` : ""}
<dl><div><dt>${xLabel}</dt><dd>${xValue}</dd></div><div><dt>${yLabel}</dt><dd>${yValue}</dd></div></dl></div></div>`;
}

export function renderCoordinatePlot({
  title, xAxis, yAxis, points, selectedId, onSelect, kind = "scatter", guides = [], targetArea, frontier = [], segments = [],
  showLabels = false, labelsLabel = "Show point labels", emptyText = "No comparable values are available.",
  interactiveZoom = false, zoom = { start: 0, end: 1 },
}) {
  const valid = points.filter(({ x, y }) => (xAxis.categorical ? x != null : Number.isFinite(x)) && Number.isFinite(y));
  if (!valid.length) return `<p class="coordinate-empty" role="status">${escape(emptyText)}</p>`;
  const scaleFor = (axis, key) => numericAxis([
    ...valid.map(point => point[key]), ...guides.filter(guide => guide.axis === key).map(guide => guide.value),
  ], axis);
  const categories = [...new Set(valid.map(point => point.x))];
  const fullX = xAxis.categorical ? categoricalAxis(categories) : scaleFor(xAxis, "x");
  const zoomed = zoom.start > 0 || zoom.end < 1;
  const first = Math.min(categories.length - 1, Math.floor(zoom.start * categories.length));
  const last = Math.max(first + 1, Math.ceil(zoom.end * categories.length));
  const visibleCategories = categories.slice(first, last);
  const domain = !xAxis.categorical && zoomed && Number.isFinite(fullX.low) && Number.isFinite(fullX.high)
    ? [fullX.low + (fullX.high - fullX.low) * zoom.start, fullX.low + (fullX.high - fullX.low) * zoom.end] : null;
  const x = xAxis.categorical ? categoricalAxis(visibleCategories) : domain ? numericAxis(valid.map(point => point.x), { ...xAxis, domain }) : fullX;
  const visible = !zoomed ? valid : xAxis.categorical
    ? valid.filter(point => visibleCategories.includes(point.x))
    : domain ? valid.filter(point => point.x >= domain[0] && point.x <= domain[1]) : valid;
  const y = scaleFor(yAxis, "y");
  const pointsAt = visible.map(point => ({ ...point, left: x.at(point.x), top: 1 - y.at(point.y) }));
  const linePoints = xAxis.categorical ? pointsAt : valid.map(point => ({ ...point, left: x.at(point.x), top: 1 - y.at(point.y) }));
  const topFor = value => 1 - y.at(value);
  const baseline = Math.max(0, Math.min(1, topFor(0)));
  const lines = [];
  if (kind === "line") {
    const bySeries = new Map();
    for (const point of [...linePoints].sort((left, right) => left.left - right.left)) {
      const series = point.series ?? "";
      if (!bySeries.has(series)) {
        const segment = [];
        bySeries.set(series, segment);
        lines.push(segment);
      } else if (point.breakBefore) {
        const segment = [];
        bySeries.set(series, segment);
        lines.push(segment);
      }
      bySeries.get(series).push(point);
    }
  }
  const byId = new Map(linePoints.map(point => [point.id, point]));
  for (const ids of [...segments, frontier]) lines.push(ids.map(id => byId.get(id)).filter(Boolean));
  const paths = lines.filter(points => points.length > 1).map(points =>
    `<polyline data-series="${escape(points[0].series ?? "")}" points="${points.map(point => `${svgCoord(point.left)},${svgCoord(point.top)}`).join(" ")}" />`).join("");
  const areaHeight = targetArea && topFor(targetArea.y);
  const area = targetArea ? `<div class="coordinate-target-area" style="--area-width:${percent(Math.max(0, Math.min(1, x.at(targetArea.x))))};--area-height:${percent(areaHeight)};top:0"></div>` : "";
  const width = `min(3.5rem, ${percent(.58 / Math.max(1, x.ticks.length))})`;
  const pointText = point => `${escape(point.name)} · ${escape(point.xLabel ?? xAxis.label)}: ${escape(point.xText ?? valueText(xAxis, point.x))} · ${escape(point.yLabel ?? yAxis.label)}: ${escape(point.yText ?? valueText(yAxis, point.y))}${point.detail ? " · " + escape(point.detail) : ""}`;
  const selected = valid.find(point => point.id === selectedId);
  const labelList = valid.map(point => `<li>${pointText(point)}</li>`).join("");
  return `<div class="coordinate-plot coordinate-${kind}" role="group" aria-label="${escape(title)}" dir="ltr">
<div class="coordinate-heading"><strong>${escape(axisTitle(yAxis))}</strong><label><input type="checkbox"${showLabels ? " checked" : ""}> ${escape(labelsLabel)}</label></div>
${interactiveZoom ? `<div class="coordinate-zoom" role="group" aria-label="Zoom ${escape(title)}"><button type="button" data-zoom="in">Zoom in</button><button type="button" data-zoom="out"${zoomed ? "" : " disabled"}>Zoom out</button><button type="button" data-zoom="previous"${zoom.start > 0 ? "" : " disabled"}>Previous</button><button type="button" data-zoom="next"${zoom.end < 1 ? "" : " disabled"}>Next</button><button type="button" data-zoom="reset"${zoomed ? "" : " disabled"}>Reset zoom</button></div>` : ""}
<div class="coordinate-viewport" tabindex="0"><div class="coordinate-canvas"><div class="coordinate-grid">
  ${area}
  <div aria-hidden="true">${axisMarkup(x.ticks, x.at, xAxis, "x")}${axisMarkup(y.ticks, topFor, yAxis, "y")}</div>
  ${paths ? `<svg class="coordinate-line" viewBox="0 0 1000 1000" preserveAspectRatio="none" aria-hidden="true">${paths}</svg>` : ""}
  ${guides.filter(guide => guide.axis !== "x" || !domain || (guide.value >= domain[0] && guide.value <= domain[1])).map(guide => `<span class="coordinate-guide coordinate-guide-${guide.axis}" style="--at:${percent(guide.axis === "x" ? x.at(guide.value) : topFor(guide.value))}" aria-hidden="true"></span>`).join("")}
  ${pointsAt.map(point => markMarkup(point, xAxis, yAxis, selectedId, Boolean(onSelect), kind, baseline, width)).join("")}
</div>
<div class="coordinate-x-title">${escape(axisTitle(xAxis))}</div></div></div>
${guides.length ? `<p class="coordinate-guide-key">${guides.map(guide => `${escape(guide.label)}: ${escape(valueText(guide.axis === "x" ? xAxis : yAxis, guide.value))}`).join(" · ")}</p>` : ""}
${selected ? `<p class="coordinate-selection">${pointText(selected)}</p>` : ""}
<ul class="coordinate-label-list" tabindex="0">${labelList}</ul></div>`;
}


// The release profiles are standalone HTML, so include the same renderer and
// chart-local state rather than depending on an app bundle or a server.
export function renderStandaloneCoordinatePlot(chart) {
  if (!chart.points.length) return renderCoordinatePlot(chart);
  const data = JSON.stringify(chart).replace(/</g, "\\u003c");
  return `<div data-coordinate-static><div data-coordinate-content>${renderCoordinatePlot({ ...chart, interactiveZoom: true })}</div><script type="application/json" data-coordinate-data>${data}</script></div>`;
}

function initStandalonePlots() {
  document.querySelectorAll("[data-coordinate-static]").forEach(root => {
    const chart = JSON.parse(root.querySelector("[data-coordinate-data]").textContent);
    const content = root.querySelector("[data-coordinate-content]");
    let zoom = { start: 0, end: 1 };
    let labels = false;
    content.addEventListener("change", event => {
      if (event.target.matches('input[type="checkbox"]')) labels = event.target.checked;
    });
    content.addEventListener("click", event => {
      const button = event.target.closest("button[data-zoom]");
      if (!button) return;
      const action = button.dataset.zoom;
      const width = zoom.end - zoom.start;
      if (action === "reset") zoom = { start: 0, end: 1 };
      else if (action === "previous" || action === "next") {
        const start = Math.max(0, Math.min(1 - width, zoom.start + (action === "next" ? width / 2 : -width / 2)));
        zoom = { start, end: start + width };
      } else {
        const nextWidth = Math.min(1, Math.max(1 / 64, width * (action === "in" ? .5 : 2)));
        const start = Math.max(0, Math.min(1 - nextWidth, (zoom.start + zoom.end - nextWidth) / 2));
        zoom = { start, end: start + nextWidth };
      }
      content.innerHTML = renderCoordinatePlot({ ...chart, showLabels: labels, interactiveZoom: true, zoom });
      const next = content.querySelector(`button[data-zoom="${action}"]`);
      (next.disabled ? content.querySelector('button[data-zoom="in"]') : next).focus();
    });
  });
}

export function standaloneCoordinateScript() {
  return `<script data-coordinate-script>(() => {
const escape = ${escape.toString()};
const formatNumber = new Intl.NumberFormat("en", { maximumSignificantDigits: 15 }).format;
const tickNumber = new Intl.NumberFormat("en", { maximumFractionDigits: 8 }).format;
const axisTitle = ${axisTitle.toString()};
const valueText = ${valueText.toString()};
const tickText = ${tickText.toString()};
const percent = ${percent.toString()};
const svgCoord = ${svgCoord.toString()};
${numericAxis.toString()}
${categoricalAxis.toString()}
${axisMarkup.toString()}
${markMarkup.toString()}
${renderCoordinatePlot.toString()}
(${initStandalonePlots.toString()})();
})();</script>`;
}
