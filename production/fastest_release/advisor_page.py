"""Accessible HTML for the bounded advisor result."""

from html import escape

from fastest_cost import MAX_ACCEPTED, MAX_MONTHS, OPTION_LABELS
from fastest_cost.render import LABELS as COST_LABELS
from fastest_goals import ENTRIES, METRICS, PRIVACY_LABELS
from fastest_goals.page import STYLE, _number, _select


ROUTE = "/advisor"


def _link(url, label):
    return f'<a href="{escape(url)}">{escape(label)}</a>'


def _configuration_fields(service, selection, entry):
    market = service.market
    fields = [f'<input type="hidden" name="entry" value="{entry}">']
    if entry == "machine":
        fields.append(_select("machine", "Your machine", selection.get("machine", ""),
                              [("", "Choose a machine"), *service.machines.items()]))
    for name in ("decode", "prefill"):
        fields.append(_number(name, f'Minimum {name} (tok/s)', selection.get(name, ""), False))
    if entry == "budget":
        fields.append(_number("budget", f'Maximum landed build price ({market["currency"]})',
                              selection.get("budget", ""), False))
    if entry == "expert":
        fields.append(_select("priority", "Sort preference", selection.get("priority", ""),
                              [("decode", "Highest decode throughput"), ("prefill", "Highest prefill throughput")]))
    if selection.get("revision") == service.release_id:
        fields.append(f'<input type="hidden" name="revision" value="{service.release_id}">')
    return fields


def _cost_fields(selection):
    return [
        '<input type="hidden" name="decision" value="cost">',
        _number("monthly_accepted", "Accepted tasks per month", selection.get("monthly_accepted", ""), False,
                minimum=1, maximum=MAX_ACCEPTED, step=1),
        _number("months", "Horizon (months)", selection.get("months", ""), False,
                minimum=1, maximum=MAX_MONTHS, step=1),
        _select("scenario", "Cost evidence", selection.get("scenario", "evidence"),
                [("evidence", "Public evidence"), ("illustrative", "Illustrative example")]),
    ]


def _form(service, selection, entry):
    nav = []
    for name, label in {**ENTRIES, "cost": "Compare costs"}.items():
        field = "decision" if name == "cost" else "entry"
        current = ' aria-current="page"' if name == entry else ""
        nav.append(f'<a href="{ROUTE}?{field}={name}"{current}>{label}</a>')
    fields = _cost_fields(selection) if entry == "cost" else _configuration_fields(service, selection, entry)
    fields.append(_select("privacy", "Workload privacy requirement", selection.get("privacy", ""),
                          [("", "Choose a requirement"), *PRIVACY_LABELS.items()]))
    return (
        f'<nav aria-label="Advisor decisions">{"".join(nav)}</nav><h2 id="advisor-form">Your requirements</h2>'
        f'<form action="{ROUTE}" method="get" aria-labelledby="advisor-form">'
        f'<div class="controls">{"".join(fields)}</div><button>Get advice</button></form>'
    )


def _configuration(service, result):
    comparison = result["comparison"]
    wizard = result["wizard"]
    market = comparison["market"]
    terms = " · ".join(value for value in (
        market["market"], market["currency"], market["condition"].replace("_", " "), market["destination"],
    ) if value)
    sources = {(source.get("cell_id"), source["kind"]): source for source in result["citations"]}
    parts = [f'<p>Market · {escape(terms)}</p>']
    for row in comparison["rows"]:
        identifier = row["id"]
        exact = f"{wizard}#goal-{identifier}"
        parts.append(f'<h3>{escape(service.machines[identifier])} · {escape(row["status"].capitalize())}</h3><ul>')
        for name, goal in row["goals"].items():
            value = "Unavailable" if goal["value"] is None else f'{goal["value"]} {goal["unit"]}'
            direction = "Maximum" if METRICS[name]["direction"] == "lower" else "Minimum"
            citation = "landed-quote" if name == "budget" else "text-run"
            reference = _link(exact, f'{METRICS[name]["label"]} evidence') if (identifier, citation) in sources else ""
            parts.append(
                f'<li>{METRICS[name]["label"]} · <strong class="units">{escape(value)}</strong> · '
                f'{direction} {escape(goal["target"])} {escape(goal["unit"])} · {escape(goal["status"].capitalize())}'
                f'<br><small>{escape(goal["reason"])} {reference}</small></li>'
            )
        for name, status in row["gates"].items():
            reference = _link(exact, "Privacy review") if name == "privacy" and (identifier, "privacy-review") in sources else ""
            parts.append(f'<li>{escape(name.capitalize())} · {escape(status.capitalize())} {reference}</li>')
        parts.append(f'</ul><p>{_link(exact, "View exact checks and evidence")}</p>')
    text_citation = sources[(None, "text-pilot")]
    parts.append("<p>" + _link(text_citation["url"], "Pinned text benchmark and method") + "</p>")
    parts.append('<p>' + _link(comparison["replay_url"], "Replay exact comparison (JSON)") + '</p>')
    return "".join(parts)


def _costs(data):
    assumptions = data["assumptions"]
    replay = data["replay_url"]
    calculator = "/costs?" + replay.partition("?")[2]
    parts = [f'<p>{assumptions["monthly_accepted"]:,} accepted tasks per month · {assumptions["months"]} months</p><ul>']
    for name, option in data["options"].items():
        nominal = option["nominal_cost"]
        total = "Total unavailable" if nominal is None else f'{nominal} {data["currency"]}'
        reasons = " · ".join(COST_LABELS.get(reason, reason.replace("_", " ").capitalize()) for reason in option["reasons"])
        parts.append(f'<li>{OPTION_LABELS[name]} · <strong class="units">{escape(total)}</strong> · '
                     f'{escape(option["execution"].capitalize())} processing'
                     + (f'<br><small>{escape(reasons)}</small>' if reasons else "")
                     + (f'<br><small>{_link(calculator, "Calculator inputs and breakdown")}</small>' if nominal is not None else "")
                     + '</li>')
    parts.append(f'</ul><p>{_link(replay, "Replay exact calculator (JSON)")}. '
                 'The calculator includes every option before the advisor applies the privacy requirement.</p>')
    return "".join(parts)


def _result(service, result):
    if not result:
        return ""
    heading = "Advisor request unavailable"
    details = ""
    if "error" in result:
        message = result["error"]
    else:
        heading = {"answer": "Supported configuration", "clarify": "More information needed",
                   "abstain": "Insufficient evidence"}[result["status"]]
        message = result["message"]
        if result["comparison"]:
            details = _configuration(service, result)
        if result["costs"]:
            costs = result["costs"]
            if result["status"] == "answer":
                heading = "Illustrative cost estimates" if costs["estimate_kind"] == "illustrative" else "Reviewed cost estimates"
            details = _costs(costs)
    return (
        '<section class="panel result" id="advisor-result" aria-labelledby="advisor-outcome">'
        f'<h2 id="advisor-outcome">{heading}</h2><p>{escape(message)}</p>{details}</section>'
    )


def render(service, selection, result):
    entry = "cost" if selection.get("decision") == "cost" else selection.get("entry", "expert")
    result_link = '<p><a href="#advisor-result">Jump to your result</a></p>' if result else ""
    return (
        '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
        f'<title>Guided advisor · fastest.ai</title><style>{STYLE}</style><main>'
        '<nav aria-label="Release navigation"><a href="/">fastest.ai</a><a href="/goals">Goal comparison wizard</a>'
        '<a href="/costs">Cost calculator</a></nav><h1>Guided advisor</h1>'
        '<p>Check a configuration or compare costs for the pinned text workload.</p>'
        '<p class="muted">The release server applies fixed rules and reads public evidence, including the price database '
        'when configured. External inference services used · none. Your selections reach the server. '
        'Keep workload content and credentials private.</p>'
        + result_link + '<div class="panel">' + _form(service, selection, entry) + '</div>'
        + _result(service, result) + '</main></html>\n'
    )
