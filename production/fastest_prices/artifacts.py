"""Render Markdown, accessible HTML and typed JSON from the same release result."""

from datetime import date
from decimal import Decimal
from hashlib import sha256
from html import escape
import json

from .result import DAY_LABELS, RANGE_LABELS, REFRESH_METHOD


ARTIFACT_NAMES = ("prices.md", "prices.html", "prices.json")


def _value(value):
    return "Unknown" if value is None else str(value)


def _section_value(value):
    if value is None:
        return "Unknown"
    return value.replace("_", " ").capitalize()


def _charge(charge):
    kind = charge["basis"].replace("_", " ")
    return kind if charge["amount"] is None else f"{kind} ({charge['amount']})"


def _tables(result):
    recurring = result["method"] == REFRESH_METHOD
    offers = [
        (
            offer["observed_at"], offer["captured_at"], offer["seller"], offer["listing_id"],
            offer["kind"], offer["confirmation"], offer["stock"], offer["discount"],
            f"{offer['price']} {offer['currency']}", _charge(offer["tax"]), _charge(offer["shipping"]),
            _value(offer["landed_price"]), f"{offer['age_days']} days ({offer['freshness']})",
            "Latest" if offer["latest_for_listing"] else "Earlier",
            *((_value(offer.get("expires_at")), _section_value(offer["availability"])) if recurring else ()),
            offer["source_locator"], offer["review"]["decision_id"],
        )
        for offer in result["offers"]
    ]
    coverage = [
        (
            day["date"], DAY_LABELS[day["status"]], _section_value(day["last_attempt_status"]),
            _value(day["offer_count"]), _value(day["sample_count"]),
        )
        for day in result["days"]
    ]
    return (
        ("Dated quotes", (
            "Observed at (UTC)", "Captured at (UTC)", "Seller", "Listing", "Price kind",
            "Confirmation", "Observed stock" if recurring else "Stock",
            "Discount eligibility", "Original quote", "Tax", "Shipping",
            f"Landed price ({result['currency']})", "Age at release", "Listing history",
            *(("Offer expires (UTC)", "Availability at release") if recurring else ()),
            "Source locator", "Review decision",
        ), offers),
        ("Daily coverage", ("Date (UTC)", "Status", "Last check", "Quotes", "Samples"), coverage),
    )


def _summary(result):
    scope = result["scope"]
    stats = result["sampling"]
    values = [
        ("As of", result["as_of"]),
        ("Window", f"{result['start']} to {result['as_of']} (UTC)"),
        ("Market and destination", f"{result['market']} · {result['destination']}"),
        ("Scope", f"{scope['kind']} · {scope['id']} · revision {scope['revision_id']}"),
        ("Condition and original currency", f"{result['condition']} · {result['currency']}"),
        ("Feed", f"{result['source_id']} at {result['source_revision']}"),
        ("Source approval", result["authorization_decision_id"]),
        ("Last successful check", _value(result["last_success_at"])),
        ("Age of last successful check (days)", _value(result["last_success_age_days"])),
        ("Most recent attempt", _section_value(result["last_attempt_status"])),
        ("Freshness", f"{_section_value(result['adapter_status'])} (stale after {result['stale_after_days']} days)"),
        ("Eligible seller-day samples", _value(stats["sample_count"])),
        ("Eligible sellers", _value(stats["seller_count"])),
        ("Declared minimum", f"{stats['minimum_samples']} samples and {stats['minimum_sellers']} sellers"),
        ("Historical range", RANGE_LABELS[stats["range_status"]]),
    ]
    if stats["range_status"] == "published":
        values.extend(
            (label, f"{stats[field]} {result['currency']}")
            for field, label in (
                ("min", "Minimum"), ("q1", "First quartile"), ("median", "Median"),
                ("q3", "Third quartile"), ("max", "Maximum"),
            )
        )
    return values


def _markdown_text(value):
    encoded = escape(str(value), quote=False).replace("|", "&#124;")
    for char in ("\\", "`", "*", "_", "[", "]", "~"):
        encoded = encoded.replace(char, f"&#{ord(char)};")
    return encoded


def _markdown_table(headers, rows):
    def row(items):
        return "| " + " | ".join(map(_markdown_text, items)) + " |"
    return "\n".join([row(headers), row(["---"] * len(headers)), *(row(items) for items in rows)])


def _html_table(title, headers, rows):
    def cells(tag, items, attribute=""):
        return "".join(f"<{tag}{attribute}>{escape(str(item))}</{tag}>" for item in items)
    body = "\n".join(f"<tr>{cells('td', row)}</tr>" for row in rows)
    return (
        f'<div class="table-wrap"><table><caption>{title}</caption>'
        f'<thead><tr>{cells("th", headers, " scope=col")}</tr></thead><tbody>{body}</tbody></table></div>'
    )


def _chart(result):
    points = [offer for offer in result["offers"] if offer["sample_selected"]]
    if not points:
        return ""
    start = date.fromisoformat(result["start"])
    span = max(1, (date.fromisoformat(result["as_of"]) - start).days)
    values = [Decimal(offer["landed_price"]) for offer in points]
    low, high = min(values), max(values)
    height = high - low or 1
    circles = []
    for offer, price in zip(points, values):
        day = offer["observed_at"][:10]
        x = 30 + 580 * (date.fromisoformat(day) - start).days / span
        y = 145 - 110 * float((price - low) / height)
        label = f"{day} · {offer['seller']} · {offer['landed_price']} {result['currency']}"
        circles.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4"><title>{escape(label)}</title></circle>')
    return (
        "<figure><figcaption>Comparable observed quotes by UTC day. Exact values and gaps appear below.</figcaption>"
        '<svg viewBox="0 0 640 180" role="img" aria-label="Dated seller-day price dots" fill="#2355a0">'
        '<path d="M 30 24 V 145 H 610" fill="none" stroke="#527190"/>'
        f'<text x="30" y="172">{result["start"]}</text>'
        f'<text x="610" y="172" text-anchor="end">{result["as_of"]}</text>'
        f'{"".join(circles)}</svg></figure>'
    )


def build_artifact(result, name):
    if name == "prices.json":
        return json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"

    title = "Regional price cohort"
    method_description = ""
    if result["status"] == "withdrawn":
        message = "This price release has been withdrawn."
        summary = []
        tables = ()
        chart = ""
    else:
        title = f"{title} · {result['as_of']}"
        illustrative = result["data_class"] == "illustrative"
        message = "Illustrative fixture. Prices and seller identities are fictional." if illustrative else ""
        method_description = (
            "The history uses one lowest comparable asking price per seller and UTC day. "
            "A comparable quote is seller-confirmed, in stock, unconditional, and has known tax and shipping treatment."
        )
        summary = _summary(result)
        tables = _tables(result)
        chart = _chart(result)
    identity = f"Release {result['release_id']} · cohort {result['cohort_id']} · method {result['method']}"
    if name == "prices.md":
        parts = [
            f"# {title}", _markdown_text(identity), message, method_description,
            "[Typed result](./prices.json) · [HTML](./prices.html)",
            *(f"- **{label}** · {_markdown_text(value)}" for label, value in summary),
        ]
        for label, headers, rows in tables:
            parts.append(f"## {label}\n\n" + (_markdown_table(headers, rows) if rows else "No quotes for this window."))
        metadata = {
            "page_id": result["cohort_id"],
            "release": result["release_id"],
            "method": result["method"],
            "status": result["status"],
            "view": {
                "type": result["result_type"],
                "cohort": result["cohort_id"],
                "data": "./prices.json",
                "sha256": sha256(build_artifact(result, "prices.json").encode("utf-8")).hexdigest(),
            },
        }
        frontmatter = "\n".join(f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in metadata.items())
        return f"---\n{frontmatter}\n---\n\n" + "\n\n".join(filter(None, parts)) + "\n"

    details = "".join(f"<dt>{escape(label)}</dt><dd>{escape(value)}</dd>" for label, value in summary)
    sections = "".join(
        f"<section><h2>{label}</h2>{_html_table(label, headers, rows) if rows else '<p>No quotes for this window.</p>'}</section>"
        for label, headers, rows in tables
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)}</title><link rel="alternate" type="text/markdown" href="./prices.md">
<style>
body{{font:1rem/1.5 system-ui,sans-serif;color:#18314a;margin:auto;padding:1.5rem;max-width:72rem}}
a{{color:#17468a}} dl{{display:grid;grid-template-columns:minmax(8rem,1fr) 2fr;gap:.35rem 1rem}}
dt{{font-weight:600}} dd{{margin:0;overflow-wrap:anywhere}} .table-wrap{{overflow:auto}}
table{{border-collapse:collapse;text-align:left;width:100%}} caption{{text-align:left}} td,th{{border-bottom:1px solid #b6c6d7;padding:.45rem .7rem}}
figure{{margin:1rem 0}} svg{{display:block;width:min(100%,35rem)}}
</style></head><body><main>
<h1>{escape(title)}</h1><p>{escape(identity)}</p>
{f"<p>{escape(message)}</p>" if message else ""}<p><a href="./prices.json">Typed result</a> · <a href="./prices.md">Markdown</a></p>
{f"<p>{escape(method_description)}</p>" if method_description else ""}
<dl>{details}</dl>{chart}{sections}
</main></body></html>
"""
