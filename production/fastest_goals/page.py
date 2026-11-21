"""Accessible goal form, exact row table, and linked scatter plot."""

from decimal import Decimal
from html import escape
from urllib.parse import urlsplit

from . import ENTRIES, PRIVACY_LABELS, SERVING_ENTRY


STYLE = """
:root{color-scheme:light;--paper:#f7f6f1;--ink:#242b26;--muted:#475a4e;--line:#abb8ae;--accent:#145941}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:1rem/1.55 system-ui,sans-serif}
main{max-width:72rem;margin:auto;padding:clamp(1rem,4vw,3rem)}section{margin-top:2rem}h1,h2,h3,p{margin-top:0}
h1{font-size:clamp(2rem,5vw,3.25rem);line-height:1.12}h2{font-size:1.45rem;margin-bottom:.55rem}
a{color:var(--accent);text-underline-offset:.2em}a:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible,summary:focus-visible{outline:3px solid #a15606;outline-offset:3px}
nav{display:flex;gap:.6rem 1rem;flex-wrap:wrap;margin-bottom:1.5rem}nav a{padding:.4rem .2rem}nav a[aria-current]{font-weight:700}
.layout{display:grid;gap:1rem;grid-template-columns:minmax(0,1fr) minmax(0,1fr)}
.panel{border:1px solid var(--line);background:white;border-radius:.75rem;padding:clamp(1rem,3vw,1.5rem)}
form{display:grid;gap:1rem}.controls{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,11rem),1fr));gap:.75rem}
label{display:grid;gap:.15rem;font-weight:600}input,select,button{font:inherit;padding:.45rem;border:1px solid var(--line);border-radius:.3rem;min-height:2.75rem;min-width:0;background:white;color:var(--ink)}
button{width:max-content;max-width:100%;color:white;background:var(--accent);border-color:var(--accent);padding-inline:1rem}
small,.muted{color:var(--muted)}.result{border-top:4px solid var(--accent)}.result ul{padding-left:1.4rem}summary{cursor:pointer;color:var(--accent)}
.table-wrap{overflow:auto;padding:.2rem}table{border-collapse:collapse;width:100%;min-width:51rem;background:#fff;table-layout:fixed}
caption{text-align:left;font-weight:650;padding:.5rem 0}th,td{text-align:left;vertical-align:top;padding:.65rem;border-bottom:1px solid var(--line);overflow-wrap:anywhere}
thead th{background:#e8eee8}th:first-child{width:15%}th:last-child{width:27%}td strong,td small,th small{display:block}
.badge{font-weight:650}.pass{color:#145941}.miss{color:#913e17}.unknown{color:#544c1e}.ineligible{color:#622752}
:target{scroll-margin-top:1rem}tr:target{outline:3px solid var(--accent);outline-offset:-3px}
.chart{margin:1rem 0}.plot{height:18rem;position:relative;border-left:2px solid var(--muted);border-bottom:2px solid var(--muted);
background:repeating-linear-gradient(to top,transparent 0 calc(25% - 1px),#dfe6df calc(25% - 1px) 25%)}
.point-group{display:flex;gap:2px;position:absolute;transform:translate(-50%,50%);align-items:center}
.point{display:grid;place-items:center;color:#194630;background:#fbfff9;width:2.75rem;height:2.75rem;border:2px solid #194630;border-radius:50%;font-weight:700;text-decoration:none}
.point.pareto{border-radius:.25rem;background:var(--accent);color:white}.point:target{outline:3px solid #a15606;outline-offset:3px}
.bounds{display:flex;justify-content:space-between;gap:1rem}.units{font-variant-numeric:tabular-nums}.evidence{overflow-wrap:anywhere}
@media(max-width:50rem){.layout{grid-template-columns:1fr}}
"""


def _select(name, label, selected, options):
    choices = "".join(f'<option value="{escape(value)}"{" selected" if value == selected else ""}>{escape(text)}</option>'
                      for value, text in options)
    return f'<label>{escape(label)}<select name="{name}">{choices}</select></label>'


def _number(name, label, value, required, *, minimum=0, maximum="999999999999.99999999", step="any"):
    extra = " required" if required else ""
    inputmode = "numeric" if step == 1 else "decimal"
    return (f'<label>{escape(label)}<input name="{name}" type="number" value="{escape(value)}" '
            f'min="{minimum}" max="{maximum}" step="{step}" inputmode="{inputmode}"{extra}></label>')


def _label(metric):
    return f"{metric['label']} ({metric['unit']})"


def _form(service, result):
    selection, metrics = result["selection"], result["metrics"]
    entry = selection["entry"]
    nav = []
    for key, label in {**ENTRIES, SERVING_ENTRY: "Team serving"}.items():
        options = {**selection, "entry": key}
        if key != entry:
            if SERVING_ENTRY in {entry, key}:
                options = {"entry": key, "privacy": selection["privacy"]}
                if selection["machine"]:
                    options["machine"] = selection["machine"]
            else:
                for setting in ("x", "y", "priority"):
                    del options[setting]
                if not options["budget"]:
                    del options["budget"]
                if not options["machine"]:
                    del options["machine"]
        link = service.url(service.selection(options))
        current = ' aria-current="page"' if key == entry else ""
        nav.append(f'<a href="{escape(link)}"{current}>{label}</a>')
    machine_label = "Your current setup" if entry == "machine" else "Highlight a setup"
    fields = [_select("machine", machine_label, selection["machine"], [("", "No setup selected"), *service.machines.items()])]
    if entry == SERVING_ENTRY:
        goals = (
            ("user_p95", "Maximum worst-user p95", True), ("capacity", "Minimum aggregate output", True),
            ("wall_energy", "Maximum wall energy per accepted request", False),
        )
        help_text = "An empty wall-energy limit leaves energy open. Capacity counts only accepted output."
    else:
        goals = (
            ("budget", "Maximum build price", False), ("decode", "Minimum decode", True), ("prefill", "Minimum prefill", True),
        ) if entry == "budget" else (
            ("decode", "Minimum decode", True), ("prefill", "Minimum prefill", True), ("budget", "Maximum build price", False),
        )
        help_text = "An empty build-price field leaves the budget open. Quality requires every reviewed output to meet the pinned rubric."
    fields.extend(_number(name, f"{label} ({metrics[name]['unit']})", selection[name], required)
                  for name, label, required in goals)
    controls = [
        _select("privacy", "Execution privacy", selection["privacy"], PRIVACY_LABELS.items()),
        _select("priority", "Sort preference", selection["priority"],
                [(name, f"{metric['direction'].capitalize()} {_label(metric)}") for name, metric in metrics.items()]),
    ]
    axes = [(name, _label(metric)) for name, metric in metrics.items()]
    return (
        '<nav aria-label="Starting point">' + "".join(nav) + '</nav>'
        '<h2 id="goal-form">Your requirements</h2>'
        f'<form action="/goals/{service.release_id}" method="get" aria-labelledby="goal-form">'
        f'<input type="hidden" name="entry" value="{entry}">'
        '<div class="controls">' + "".join(fields + controls) + '</div>'
        f'<small>{help_text}</small>'
        '<details><summary>Chart axes</summary><div class="controls">'
        + _select("x", "Horizontal axis", selection["x"], axes)
        + _select("y", "Vertical axis", selection["y"], axes)
        + '</div></details><button>Compare setups</button></form>'
    )


def _summary(result, fit_enabled):
    rows = {row["id"]: row for row in result["rows"]}
    recommendation = result["recommendation"]
    output = []
    if recommendation:
        row = rows[recommendation]
        output.append(f'<h2>Supported choice</h2><p><a href="#goal-{row["id"]}">{escape(row["name"])}</a> meets every active goal.</p>')
    else:
        output.append("<h2>No setup meets every goal</h2><p>The exact results show which limits were missed and which evidence is missing.</p>")
    if result["alternatives"]:
        output.append("<h3>Alternatives</h3><ul>")
        for identifier in result["alternatives"]:
            row = rows[identifier]
            notes = " ".join(goal["reason"] for goal in row["goals"].values() if goal["status"] != "pass")
            output.append(f'<li><a href="#goal-{identifier}">{escape(row["name"])}</a> '
                          f'{escape(notes or "Meets every active goal.")}</li>')
        output.append("</ul>")
    counts = [f'{sum(row["status"] == status for row in rows.values())} {status}'
              for status in ("pass", "miss", "unknown", "ineligible")]
    output.append(f'<p class="muted">Cohort coverage · {", ".join(counts)}</p>')
    if result["selection"]["machine"]:
        own = rows[result["selection"]["machine"]]
        output.append(f'<p>Selected setup · <a href="#goal-{own["id"]}">{escape(own["name"])}</a></p>')
        if fit_enabled and result["selection"]["entry"] != SERVING_ENTRY and own["id"] == "rtx-4090":
            output.append('<p><a href="/fit?machine=llmfit-nvidia-rtx-4090">Open the RTX 4090 fit estimate</a> '
                          'to choose a model file and context.</p>')
    return "".join(output)


def _source(locator):
    try:
        parsed = urlsplit(locator)
    except ValueError:
        return escape(locator)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return f'<a href="{escape(locator)}">{escape(locator)}</a>'
    return escape(locator)


def _serving_evidence(evidence):
    counts = evidence["counts"]
    parts = [
        f'<small>{counts["attempted"]} of {counts["planned"]} requests recorded · {counts["accepted"]} accepted · '
        f'{counts["failed"]} failed · {counts["timeout"]} timed out · {counts["rejected"]} rejected · '
        f'{counts["unrecorded"]} unrecorded</small>',
    ]
    if evidence["captured_duration_ms"] is not None:
        parts.append(f'<small>{evidence["accepted_output_tokens"]} accepted output tokens in '
                     f'{evidence["captured_duration_ms"]} ms of captured time</small>')
    for user in evidence["users"]:
        wait = f'{user["p95_ms"]} ms' if user["p95_ms"] is not None else "unavailable"
        parts.append(f'<small>User {user["user"]} · {user["accepted"]} accepted · p95 {wait}</small>')
    if evidence["wall_joules"] is not None:
        power = evidence["power"]
        parts.append(f'<small>{evidence["wall_joules"]} J total · {escape(power["boundary"])} · '
                     f'{escape(power["meter"])} · {power["start_ms"]}–{power["end_ms"]} ms</small>')
    failures = [attempt for attempt in evidence["attempts"] if attempt["outcome"] != "accepted"]
    if failures:
        parts.append('<details><summary>Unsuccessful requests</summary><ul>')
        for attempt in failures:
            parts.append(f'<li>User {attempt["user"]}, request {attempt["request"]} · {attempt["outcome"]} · '
                         f'{attempt["elapsed_ms"]} ms · {attempt["output_tokens"]} output tokens · '
                         f'{escape(attempt["reason"])}</li>')
        parts.append("</ul></details>")
    return "".join(parts)


def _table(result):
    metrics = result["metrics"]
    chart_ids = {point["id"] for point in result["chart"]["points"]}
    header = "".join(f'<th scope="col">{escape(_label(metric))}</th>' for metric in metrics.values())
    parts = ['<div class="table-wrap" role="region" aria-label="Scrollable exact goal results" tabindex="0">'
             '<table class="units"><caption>Exact goal results</caption><thead><tr><th scope="col">Setup</th>'
             '<th scope="col">Decision</th>' + header + '<th scope="col">Requirements and evidence</th></tr></thead><tbody>']
    for row in result["rows"]:
        identifier = row["id"]
        parts.append(f'<tr id="goal-{identifier}" tabindex="-1"><th scope="row">{escape(row["name"])}'
                     f'<small>{escape(row["backend"])}</small>')
        if identifier in chart_ids:
            parts.append(f'<small><a href="#point-{identifier}">Find on chart</a></small>')
        parts.append(f'</th><td class="badge {row["status"]}">{row["status"].capitalize()}</td>')
        for name, observation in row["metrics"].items():
            check = row["goals"].get(name)
            value = observation["value"]
            unit = metrics[name]["unit"]
            value_text = "No value" if value is None else f"{value} {unit}"
            parts.append(f'<td><strong>{escape(value_text)}</strong>')
            if check:
                direction = "Maximum" if metrics[name]["direction"] == "lower" else "Minimum"
                parts.append(f'<small>{direction} {escape(check["target"])} {unit}</small>'
                             f'<small class="badge {check["status"]}">{check["status"].capitalize()}</small>')
            reason = check["reason"] if check and check["status"] != "pass" else observation["reason"]
            if reason:
                parts.append(f'<small>{escape(reason)}</small>')
            if observation.get("sample_count") and "serving" not in row:
                parts.append(f'<small>{observation["sample_count"]} successful timed samples</small>')
            parts.append("</td>")
        parts.append('<td class="evidence">')
        for name, gate in row["gates"].items():
            parts.append(f'<small><span class="badge {gate["status"]}">{name.capitalize()} · {gate["status"]}</span> '
                         f'{escape(gate["reason"])}</small>')
            if gate.get("source"):
                parts.append(f'<small>{_source(gate["source"])}</small>')
        if row["run_source"]:
            evidence = row["run_source"]
            parts.append(f'<small>Run source · {_source(evidence["locator"])} · {escape(evidence["revision"])}</small>')
        if "serving" in row:
            parts.append(_serving_evidence(row["serving"]))
        quote = row["metrics"].get("budget")
        if quote and quote["value"] is not None:
            parts.append('<details><summary>Price evidence</summary>'
                         f'<small>{escape(quote["seller"])} · {escape(quote["observed_at"])}</small>'
                         f'<small>Quote · {_source(quote["source_locator"])}</small>'
                         f'<small>Price release · {escape(quote["release_id"])}</small>'
                         f'<small>Whole-build revision · {escape(row["build_revision"])}</small></details>')
        parts.append("</td></tr>")
    return "".join(parts) + "</tbody></table></div>"


def _chart(result):
    chart = result["chart"]
    x, y, points = chart["x"], chart["y"], chart["points"]
    metrics = result["metrics"]
    names = {row["id"]: row["name"] for row in result["rows"]}
    title = (f'<section id="goal-chart" aria-labelledby="chart-title"><h2 id="chart-title">'
             f'{escape(metrics[y]["label"])} by {escape(metrics[x]["label"].lower())}</h2>')
    if not points:
        return title + "<p>No eligible setup has exact values on both selected axes.</p></section>"

    def bounds(axis):
        values = [Decimal(point[axis]) for point in points]
        return min(values), max(values)

    def position(value, lower, upper):
        return 50 if lower == upper else 12 + 76 * float((value - lower) / (upper - lower))

    x_min, x_max = bounds("x")
    y_min, y_max = bounds("y")
    positions = {}
    for index, point in enumerate(points, start=1):
        left = position(Decimal(point["x"]), x_min, x_max)
        bottom = position(Decimal(point["y"]), y_min, y_max)
        label = (f'{names[point["id"]]} · {point["x"]} {metrics[x]["unit"]}, '
                 f'{point["y"]} {metrics[y]["unit"]} · {"Pareto" if point["pareto"] else "dominated"}')
        marker = "point pareto" if point["pareto"] else "point"
        anchor = (f'<a id="point-{point["id"]}" href="#goal-{point["id"]}" class="{marker}" '
                  f'aria-label="{escape(label)}" title="{escape(label)}">{index}</a>')
        positions.setdefault((left, bottom), []).append(anchor)
    markers = "".join(f'<div class="point-group" style="left:{left:.4f}%;bottom:{bottom:.4f}%">{"".join(anchors)}</div>'
                      for (left, bottom), anchors in positions.items())
    return (title + '<figure class="chart"><figcaption>Squares mark Pareto setups. Each marker opens its exact table row.'
            f'</figcaption><p class="muted">{escape(_label(metrics[y]))} · {y_min:f} to {y_max:f}</p>'
            f'<div class="plot">{markers}</div><p class="bounds muted"><span>{x_min:f}</span>'
            f'<span>{escape(_label(metrics[x]))}</span><span>{x_max:f}</span></p></figure></section>')


def render_goals(service, result, fit_enabled=False):
    selection = result["selection"]
    if selection["entry"] == SERVING_ENTRY:
        protocol = result["serving_protocol"]
        terms = f'{protocol["users"]} simultaneous users · {protocol["requests_per_user"]} requests per user'
        details = '<p>Protocol ' + escape(result["protocol"]) + '</p>' + "".join(
            f'<p>{escape(protocol[field])}</p>'
            for field in ("acceptance", "latency_boundary", "capacity_boundary", "wall_boundary")
        )
        text_link = ""
    else:
        market = result["market"]
        terms = f"One fixed text workload · {market['market']} · {market['currency']} · {market['condition'].replace('_', ' ')}"
        if market["destination"]:
            terms += f" · {market['destination']}"
        details = f'<p class="muted">Protocol {escape(result["protocol"])} · Quality rubric {escape(result["quality_rubric"])}</p>'
        text_link = f' · <a href="/goals/{service.release_id}/text-pilot.html">Text pilot evidence</a>'
    priority = result["metrics"][selection["priority"]]
    sort = f"{priority['direction']} {priority['label'].lower()}"
    return (
        '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
        f'<title>Compare setups by goal · fastest.ai</title><style>{STYLE}</style><main>'
        '<p><a href="/">fastest.ai</a> · <a href="/advisor">Guided advisor</a></p><h1>Compare setups by goal</h1>'
        f'<p>{escape(terms)} · sorted within results by {escape(sort)}</p>'
        f'<p><a href="{escape(service.url(selection))}">Share this pinned view</a> · '
        f'<a href="{escape(service.url(selection, ".json"))}">Exact data (JSON)</a>{text_link}</p>'
        '<div class="layout"><div class="panel">' + _form(service, result) + '</div>'
        '<div class="panel result">' + _summary(result, fit_enabled) + '</div></div>'
        '<section aria-labelledby="goal-detail-title"><h2 id="goal-detail-title">Compare the evidence</h2>'
        + details + _table(result) + '</section>' + _chart(result) + '</main></html>\n'
    )
