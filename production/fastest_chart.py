"""Shared point labels and exact-value tooltips for standalone SVG releases."""

from html import escape


def chart_with_labels(svg):
    return (
        '<div class="release-chart"><style>'
        '.release-chart .chart-point-label{display:none;pointer-events:none;font:10px system-ui;'
        'fill:#18314a;stroke:white;stroke-width:2.5px;paint-order:stroke}'
        '.release-chart:has(input:checked) .chart-point-label,'
        '.release-chart .chart-point:is(:hover,:focus-visible) .chart-point-label{display:inline}'
        '.release-chart .chart-point:is(:hover,:focus-visible) circle:not(.hit){stroke:#18314a;stroke-width:2}'
        '.release-chart label{display:inline-flex;align-items:center;gap:.35rem;margin:.25rem 0}'
        '</style><label><input type="checkbox"> Show point labels</label>'
        f'{svg}</div>'
    )


def point_details(x, y, summary, point_label, *, end=False):
    anchor = "end" if end else "start"
    label_x = x - 7 if end else x + 7
    return (
        f'<title>{escape(summary)}</title>'
        f'<text class="chart-point-label" x="{label_x:.3f}" y="{y - 7:.3f}" '
        f'text-anchor="{anchor}" aria-hidden="true">{escape(point_label)}</text>'
    )
