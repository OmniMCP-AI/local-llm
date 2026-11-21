"""Shared point labels and exact-value tooltips for standalone SVG releases."""

from html import escape
import json


def chart_with_labels(svg, *, left, right, start, end, date_axis=False):
    config = json.dumps({"left": left, "right": right, "start": start, "end": end, "dateAxis": date_axis}).replace("<", "\\u003c")
    return (
        '<div class="release-chart"><style>'
        '.release-chart .chart-point-label{display:none;pointer-events:none;font:10px system-ui;'
        'fill:#18314a;stroke:white;stroke-width:2.5px;paint-order:stroke}'
        '.release-chart:has(input:checked) .chart-point-label,'
        '.release-chart .chart-point:is(:hover,:focus-visible) .chart-point-label{display:inline}'
        '.release-chart .chart-point:is(:hover,:focus-visible) circle:not(.hit){stroke:#18314a;stroke-width:2}'
        '.release-chart label{display:inline-flex;align-items:center;gap:.35rem;margin:.25rem 0}'
        '.release-chart .chart-zoom{display:flex;flex-wrap:wrap;gap:.35rem;margin:.5rem 0}'
        '.release-chart .chart-zoom button{min-height:2.5rem;padding:.35rem .65rem}'
        '</style><label><input type="checkbox"> Show point labels</label>'
        f'<div class="chart-zoom" role="group" aria-label="Chart zoom">'
        f'<button type="button" data-chart-zoom="in">Zoom in</button>'
        f'<button type="button" data-chart-zoom="out" disabled>Zoom out</button>'
        f'<button type="button" data-chart-zoom="previous" disabled>Previous</button>'
        f'<button type="button" data-chart-zoom="next" disabled>Next</button>'
        f'<button type="button" data-chart-zoom="reset" disabled>Reset zoom</button></div>'
        f'{svg}<script data-chart-zoom-script>({CHART_ZOOM_SCRIPT})({config}, document.currentScript.parentElement);</script></div>'
    )


def point_details(x, y, summary, point_label, *, end=False):
    anchor = "end" if end else "start"
    label_x = x - 7 if end else x + 7
    return (
        f'<title>{escape(summary)}</title>'
        f'<text class="chart-point-label" x="{label_x:.3f}" y="{y - 7:.3f}" '
        f'text-anchor="{anchor}" aria-hidden="true">{escape(point_label)}</text>'
    )


CHART_ZOOM_SCRIPT = r"""function(config, root) {
  const svg = root.querySelector('svg');
  const marks = [...svg.querySelectorAll('.chart-point')].map(mark => ({ mark, x: Number(mark.querySelector('circle').getAttribute('cx')) }));
  const lines = [...svg.querySelectorAll('polyline')].map(line => ({ line, points: line.getAttribute('points').trim().split(/\s+/).map(pair => pair.split(',').map(Number)) }));
  const buttons = Object.fromEntries([...root.querySelectorAll('[data-chart-zoom]')].map(button => [button.dataset.chartZoom, button]));
  const labels = [...svg.querySelectorAll('[data-chart-x]')];
  const xStart = config.dateAxis ? Date.parse(config.start + 'T00:00:00Z') : Number(config.start);
  const xEnd = config.dateAxis ? Date.parse(config.end + 'T00:00:00Z') : Number(config.end);
  let start = 0, end = 1;
  const format = value => config.dateAxis ? new Date(value).toISOString().slice(0, 10) : new Intl.NumberFormat('en', { maximumFractionDigits: 4 }).format(value);
  function draw() {
    const width = end - start;
    const map = x => config.left + (x - config.left - (config.right - config.left) * start) / width;
    for (const { mark, x } of marks) {
      const next = map(x);
      mark.style.visibility = next < config.left || next > config.right ? 'hidden' : '';
      mark.setAttribute('transform', `translate(${next - x} 0)`);
    }
    for (const { line, points } of lines) {
      const visible = [];
      for (let i = 1; i < points.length; i++) {
        const [x1, y1] = points[i - 1], [x2, y2] = points[i];
        const a = map(x1), b = map(x2), low = Math.max(config.left, Math.min(a, b)), high = Math.min(config.right, Math.max(a, b));
        if (low > high) continue;
        const y = x => a === b ? y1 : y1 + (y2 - y1) * (x - a) / (b - a);
        visible.push(`${low},${y(low)}`, `${high},${y(high)}`);
      }
      line.setAttribute('points', visible.join(' '));
    }
    for (const label of labels) label.textContent = format(xStart + (xEnd - xStart) * (label.dataset.chartX === 'start' ? start : end));
    buttons.out.disabled = start === 0 && end === 1;
    buttons.reset.disabled = buttons.out.disabled;
    buttons.previous.disabled = start === 0;
    buttons.next.disabled = end === 1;
  }
  root.addEventListener('click', event => {
    const button = event.target.closest('button[data-chart-zoom]');
    if (!button) return;
    const action = button.dataset.chartZoom, width = end - start;
    if (action === 'reset') { start = 0; end = 1; }
    else if (action === 'previous' || action === 'next') {
      start = Math.max(0, Math.min(1 - width, start + (action === 'next' ? width / 2 : -width / 2)));
      end = start + width;
    } else {
      const nextWidth = Math.min(1, Math.max(1 / 64, width * (action === 'in' ? .5 : 2)));
      start = Math.max(0, Math.min(1 - nextWidth, (start + end - nextWidth) / 2));
      end = start + nextWidth;
    }
    draw();
    (button.disabled ? buttons.in : button).focus();
  });
}"""
