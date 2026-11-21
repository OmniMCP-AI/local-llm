"""Render the typed cost result for browsers and Markdown readers."""

from decimal import Decimal
from html import escape
import json
from urllib.parse import urlencode

from fastest_text.__main__ import markdown_text

from . import MAX_ACCEPTED, MAX_MONTHS, OPTION_LABELS


ROUTES = {
    "/costs": "text/html; charset=utf-8",
    "/costs.md": "text/markdown; charset=utf-8",
    "/costs.json": "application/json",
}
LABELS = {
    "feasible": "Within service assumptions",
    "unknown": "Service evidence unavailable",
    "infeasible": "Infeasible service",
    "missing_same_task_service_evidence": "Same-task evidence for quality, privacy, latency and capacity is unavailable",
    "quality_below_target": "Quality below target",
    "privacy_policy_unmet": "Privacy policy unmet",
    "latency_slo_unmet": "Latency SLO unmet",
    "insufficient_capacity": "Insufficient capacity",
    "infeasible_service": "No payback · infeasible service",
    "unknown_inputs": "Payback unavailable · missing inputs",
    "nonpositive_savings": "No payback · recurring savings are zero or negative",
    "beyond_horizon": "Payback beyond the selected horizon",
    "within_horizon": "Payback within the selected horizon",
    "monthly_accepted": "Monthly workload",
    "electricity": "Electricity tariff",
    "rental_hourly_rate": "Rental price",
    "api_output_rate": "API output price",
    "p95_latency_ms": "p95 completion latency (ms)",
    "seconds_per_attempt": "Capacity time per attempt (seconds)",
    "load_watts": "Load power at system wall (W)",
    "idle_watts": "Idle power at system wall (W)",
    "external_cooling_ratio": "External cooling (share of IT energy)",
    "hourly_rate": "Rate per hour",
    "input_per_million": "Uncached input per million tokens",
    "cached_input_per_million": "Cached input per million tokens",
    "output_per_million": "Output per million tokens",
    "load_kwh": "Load energy (kWh)",
    "idle_kwh": "Idle energy (kWh)",
    "cooling_kwh": "External cooling energy (kWh)",
}
TARIFF_HEADING = "Reviewed tariff references"
TARIFF_DESCRIPTION = "Quoted tariff components. Cost calculations require separately reviewed workload inputs."
TARIFF_UNITS = {
    "kwh": "kWh", "month": "month", "instance_hour": "instance hour",
    "million_input_tokens": "million input tokens", "million_cached_input_tokens": "million cached input tokens",
    "million_output_tokens": "million output tokens",
}
SERIES = (("#12565c", ""), ("#8f3b11", "10 4"), ("#37428f", "3 3"), ("#87416c", "9 3 2 3"))
TITLE = "Compare text workload costs"


def _label(key):
    return LABELS.get(key, key.replace("_", " ").capitalize())


def _show(item):
    return "—" if item is None else str(item)


def _query(result):
    assumptions = result["assumptions"]
    selection = {"scenario": result["scenario"], "monthly_accepted": assumptions["monthly_accepted"],
                 "months": assumptions["months"]}
    if result["estimate_kind"] == "reviewed" or "tariff_references" in result:
        selection["revision"] = result["revision"]
    return urlencode(selection)


def _intro(result):
    if result["estimate_kind"] == "illustrative":
        return "Illustrative estimates. The prices, service outcomes and power inputs are fictional examples."
    if result["estimate_kind"] == "reviewed":
        return "Reviewed, dated cost inputs for the pinned workload. Options with incomplete evidence have unavailable totals."
    return "No approved comparable prices or same-task measurements are available for these options."


def _tables(result):
    workload = result["workload"]
    basis = result["inputs"]["price_basis"]
    assumptions = result["assumptions"]
    options = result["options"]
    currency = basis["currency"]

    yield ("Workload and assumptions", ("Assumption", "Value"), [
        ("Task", workload["label"]),
        ("Workload revision", workload["revision"]),
        ("Text pilot and quality rubric", f'{workload["pilot_revision"]} · {workload["quality_rubric"]}'),
        ("Quality requirement", workload["quality"]),
        ("Privacy requirement", workload["privacy"]),
        ("Minimum acceptance rate", workload["minimum_acceptance_rate"]),
        ("Maximum p95 completion latency (ms)", workload["maximum_p95_latency_ms"]),
        ("Latency boundary", workload["latency_boundary"]),
        ("Text pilot evidence scope", workload["evidence_scope"]),
        ("Concurrent requests", workload["concurrency"]),
        ("Tokens per attempt (input / output)",
         f'{workload["input_tokens_per_attempt"]} / {workload["output_tokens_per_attempt"]}'),
        ("Token basis", workload["token_basis"]),
        ("Accepted tasks per month", assumptions["monthly_accepted"]),
        ("Planning horizon (months)", assumptions["months"]),
        ("Effective monthly discount rate", assumptions["monthly_discount_rate"]),
        ("Market and currency", f'{basis["market"]} · {currency}'),
        ("Price basis", basis["method"]),
        ("Price basis date", basis["as_of"]),
        ("Electricity tariff revision", basis["electricity"]["revision"]),
        (f"Electricity price ({currency}/kWh)", basis["electricity"]["per_kwh"]),
        ("Scenario revision", result["inputs"]["revision"]),
    ])

    if result["estimate_kind"] == "reviewed":
        yield ("Reviewed sources", ("Input", "Source", "Revision"), [
            (item.get("scope", "workload"), item["locator"], item["revision"]) for item in result["citations"]
        ])

    if "tariff_references" in result:
        yield (TARIFF_HEADING, ("Provider and offering", "Market and region", "Component", "Rate",
                               "Effective from", "Effective until (exclusive)", "Qualification",
                               "Source", "Source checked (UTC)", "Tariff revision"), [
            (f'{row["provider"]} · {row["offering"]}', f'{row["market"]} · {row["region"]}', row["component"],
             f'{row["currency"]} {row["amount"]} / {TARIFF_UNITS[row["unit"]]}',
             row["effective_from"], row["effective_until"], row["qualification"],
             (row["source"], row["citation"]["locator"]), row["checked_at"], row["revision"])
            for row in result["tariff_references"]["references"]
        ])

    yield (f"Cost at selected volume ({currency})", ("Metric", *OPTION_LABELS.values()), [
        ("Service", *(_label(item["service"]["status"]) for item in options.values())),
        ("Service qualifications", *(
            "; ".join(map(_label, item["service"]["reasons"])) or None for item in options.values()
        )),
        ("Attempts per month", *(item["service"]["attempts"] for item in options.values())),
        ("Active hours required per month", *(item["service"]["active_hours"] for item in options.values())),
        ("Maximum accepted tasks per month", *(item["service"]["maximum_monthly_accepted"] for item in options.values())),
        ("GPU-only value", *(item["purchase"]["gpu_only"] for item in options.values())),
        ("Reused parts value", *(item["purchase"]["reused_parts"] for item in options.values())),
        ("Whole-build value", *(item["purchase"]["whole_build"] for item in options.values())),
        ("Upfront cash", *(item["purchase"]["upfront"] for item in options.values())),
        ("Recurring cost per month", *(item["monthly"]["recurring_cost"] for item in options.values())),
        ("Terminal residual (cash inflow)", *(item["totals"]["terminal_residual"] for item in options.values())),
        ("Nominal total", *(item["totals"]["nominal_cost"] for item in options.values())),
        ("Discounted total", *(item["totals"]["discounted_cost"] for item in options.values())),
        ("Nominal cost per accepted task", *(item["totals"]["cost_per_accepted_task"] for item in options.values())),
    ])

    yield ("Simple payback", ("Choice", "Compared with", f"Monthly savings ({currency})", "Months", "Outcome"), [
        (OPTION_LABELS[row["option"]], OPTION_LABELS[row["baseline"]],
         row["monthly_savings"], row["payback_months"], _label(row["status"]))
        for row in result["payback"]
    ])

    yield (f"Sensitivity · nominal horizon cost ({currency})",
           ("Driver", "Case", "Value", *OPTION_LABELS.values()), [
        (_label(row["driver"]), row["level"].capitalize(),
         f'{row["value"]} {row["unit"]}' if row["value"] is not None else None, *(
             (entry["nominal_cost"] or "; ".join(map(_label, entry["reasons"])) or "Cost unavailable")
             if (entry := row["options"].get(option)) else None for option in OPTION_LABELS
         ))
        for row in result["sensitivity"]
    ])

    input_label = "Illustrative estimate" if result["estimate_kind"] == "illustrative" else "Reviewed input"
    for option, item in options.items():
        inputs = result["inputs"]["options"][option]
        service, tariff, parts = inputs["service"], inputs["operation"], item["purchase"]["parts"]
        yield (f'{item["label"]} · assumptions and monthly breakdown',
               ("Input or charge", f"Value (money in {currency})"), [
            ("Configuration", inputs["configuration"]),
            ("Service inputs", input_label if service else "No applicable measured service released"),
            *((_label(key), value) for key, value in (service or {}).items()),
            ("Operating inputs or tariff", input_label if tariff else "No applicable input or tariff released"),
            *((_label(key), value) for key, value in (tariff or {}).items()),
            *((_label(key), value) for key, value in item["monthly"].items()),
        ])
        if parts:
            yield (f'{item["label"]} · itemized build ({item["purchase"]["revision"]})',
                   ("SKU", "Part", "Condition", "Quantity", "Treatment", f"Unit ({currency})", f"Total ({currency})"), [
                (part["sku"], part["kind"], part["condition"], part["quantity"],
                 "Reused" if part["reused"] else "Purchase", part["unit_price"], part["extended_price"])
                for part in parts
            ])

    yield (f"Cumulative cost · exact values ({currency})", ("Month", *OPTION_LABELS.values()), [
        (row["month"], *(row[key] for key in OPTION_LABELS)) for row in result["cumulative_cost"]
    ])


def _curve(result):
    points = result["cumulative_cost"]
    months = result["assumptions"]["months"]
    values = [Decimal(row[key]) for row in points for key in OPTION_LABELS if row[key] is not None]
    if not values:
        return "<p>Cumulative cost is unavailable until at least one option has comparable service and price inputs.</p>"
    low, high = min(0, min(values)), max(0, max(values))
    span = high - low or 1
    width, height = 720, 245
    left, right, top, bottom = 104, 694, 22, 197
    legend, paths = [], []
    for (key, label), (color, dash) in zip(OPTION_LABELS.items(), SERIES):
        if points[0][key] is None:
            continue
        coords = " ".join(
            f'{left + (right - left) * row["month"] / months:.2f},'
            f'{bottom - (bottom - top) * (Decimal(row[key]) - low) / span:.2f}'
            for row in points
        )
        paths.append(f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="3" stroke-dasharray="{dash}"/>')
        legend.append(f'<li><svg width="24" height="12" aria-hidden="true"><path d="M 1 6 H 23" '
                      f'stroke="{color}" stroke-width="3" stroke-dasharray="{dash}"/></svg>{escape(label)}</li>')
    currency = escape(result["inputs"]["price_basis"]["currency"])
    return (
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-labelledby="curve-title" class="curve">'
        f'<title id="curve-title">Cumulative nominal cost in {currency} by month. An exact table follows.</title>'
        f'<path d="M {left} {top} H {right} M {left} {top} V {bottom} H {right}" fill="none" stroke="#a2afb3"/>'
        f'<g fill="currentColor" font-size="13"><text x="{left - 8}" y="{top + 4}" text-anchor="end">{high}</text>'
        f'<text x="{left - 8}" y="{bottom + 4}" text-anchor="end">{low}</text>'
        f'<text x="{left}" y="219" text-anchor="middle">Month 0</text>'
        f'<text x="{right}" y="219" text-anchor="end">Month {months}</text></g>'
        + "".join(paths) + "</svg><ul class='legend'>" + "".join(legend) + "</ul>"
    )


def _html_cell(value):
    if isinstance(value, tuple):
        label, url = value
        return f'<a href="{escape(url)}">{escape(label)}</a>'
    return escape(_show(value))


def _markdown_cell(value):
    if isinstance(value, tuple):
        label, url = value
        return f"[{markdown_text(label)}](<{url.replace('|', '%7C')}>)"
    return markdown_text(_show(value))


def _html_table(columns, rows, heading):
    headers = "".join(f'<th scope="col">{escape(column)}</th>' for column in columns)
    cells = "".join(
        f'<tr><th scope="row">{escape(_show(row[0]))}</th>'
        + "".join(f"<td>{_html_cell(value)}</td>" for value in row[1:]) + "</tr>"
        for row in rows
    )
    return (f'<div class="table-wrap" role="region" aria-label="{escape(heading)}" tabindex="0">'
            f"<table><thead><tr>{headers}</tr></thead><tbody>{cells}</tbody></table></div>")


def _render_html(result, query):
    monthly = result["assumptions"]["monthly_accepted"]
    months = result["assumptions"]["months"]
    view = "".join(
        f'<option value="{name}"{" selected" if name == result["scenario"] else ""}>{label}</option>'
        for name, label in (("evidence", "Public evidence"), ("illustrative", "Illustrative example"))
    )
    sections = []
    for title, columns, rows in _tables(result):
        table = _html_table(columns, rows, title)
        if title.startswith("Cumulative cost"):
            section = f'<h2>Cumulative cost ({result["inputs"]["price_basis"]["currency"]})</h2>{_curve(result)}'
            sections.append(section + f"<details><summary>{escape(title)}</summary>{table}</details>")
        else:
            note = f"<p>{TARIFF_DESCRIPTION}</p>" if title == TARIFF_HEADING else ""
            sections.append(f"<h2>{escape(title)}</h2>{note}{table}")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{TITLE} · fastest.ai</title>
<link rel="alternate" type="text/markdown" href="/costs.md?{escape(query)}">
<link rel="alternate" type="application/json" href="/costs.json?{escape(query)}">
<style>
body {{ margin: 0; background: #f5f7f6; color: #1b2629; font: 1rem/1.55 system-ui, sans-serif; }}
main, nav {{ max-width: 70rem; margin: auto; padding: 1rem; }}
h1, h2 {{ line-height: 1.2; text-wrap: balance; }}
h2 {{ margin-top: 2.5rem; }}
form {{ display: flex; align-items: end; flex-wrap: wrap; gap: .8rem 1.2rem; margin: 1.5rem 0; }}
label {{ display: grid; gap: .25rem; font-weight: 650; }}
input, select, button {{ font: inherit; min-height: 2.75rem; box-sizing: border-box; padding: .4rem .6rem; }}
button {{ background: #12565c; color: white; border: 1px solid #12565c; cursor: pointer; }}
a {{ color: #12565c; }} code {{ overflow-wrap: anywhere; }}
table {{ border-collapse: collapse; background: white; width: 100%; font-variant-numeric: tabular-nums; }}
th, td {{ padding: .55rem .7rem; text-align: left; border-bottom: 1px solid #d9e1e0; vertical-align: top; }}
thead {{ background: #e6eeeb; }} tbody th {{ font-weight: 650; }}
.table-wrap {{ overflow: auto; }}
.curve {{ width: 100%; background: white; }}
.legend {{ display: flex; flex-wrap: wrap; gap: .5rem 1.5rem; list-style-type: none; padding: 0; }}
.legend li {{ display: flex; align-items: center; gap: .35rem; }}
summary {{ cursor: pointer; font-weight: 650; }}
</style></head><body>
<nav><a href="/">fastest.ai</a></nav>
<main><h1>{TITLE}</h1><p>{_intro(result)}</p>
<form action="/costs">
<label>Scenario <select name="scenario">{view}</select></label>
<label>Accepted tasks per month <input name="monthly_accepted" type="number" required min="1" max="{MAX_ACCEPTED}" value="{monthly}"></label>
<label>Months <input name="months" type="number" required min="1" max="{MAX_MONTHS}" value="{months}"></label>
<button>Update comparison</button>
</form>
<p><a href="/costs.json?{escape(query)}">Typed JSON</a> · <a href="/costs.md?{escape(query)}">Markdown</a></p>
<p>Comparison revision <code>{escape(result["revision"])}</code></p>
<p>— indicates an unavailable value or a charge outside the option’s scope.</p>
{"".join(sections)}
</main></body></html>
"""


def render(result, path):
    if path == "/costs.json":
        return json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    query = _query(result)
    if path == "/costs":
        return _render_html(result, query)
    sections = [
        f"# {TITLE}", _intro(result),
        f'[HTML](/costs?{query}) · [Typed JSON](/costs.json?{query})',
        f'Comparison revision `{result["revision"]}`',
        "— indicates an unavailable value or a charge outside the option’s scope.",
    ]
    for title, columns, rows in _tables(result):
        sections.append(f"## {markdown_text(title)}")
        if title == TARIFF_HEADING:
            sections.append(TARIFF_DESCRIPTION)
        sections.append("\n".join("| " + " | ".join(map(_markdown_cell, row)) + " |"
                                  for row in (columns, ("---",) * len(columns), *rows)))
    return "\n\n".join(sections) + "\n"
