from html import escape
import json
import re
from urllib.parse import quote

from .applicability import STATUSES


RELEASE_STATUSES = {
    "current": "Current observed release",
    "prerelease": "Prerelease",
    "superseded_release": "Superseded release",
    "superseded_revision": "Superseded revision",
}


def lines(report):
    yield "h1", "llama.cpp release watch", None
    if "error" in report:
        yield "p", report["error"], None
        return
    if report["source"]["mode"] == "fixture":
        yield "p", "Synthetic fixture replay", None
    yield "p", "Official GitHub release feed", report["source"]["feed_url"]
    yield "p", "Last successful refresh: " + (report["last_successful_refresh"] or "Never"), None
    if report["stale"]:
        yield "p", "The feed is stale or has never been refreshed.", None
    if report["last_error"]:
        yield "p", f"Refresh failed at {report['last_attempt']}. {report['last_error']}", None
    for release in report["releases"]:
        yield "h2", f"{release['tag']} · {RELEASE_STATUSES[release['status']]}", None
        yield "p", f"Upstream release · {release['published_at']}", release["source_url"]
        yield "p", f"Retained revision · {release['revision_id']}", None
        if not release["applicability"]:
            yield "p", "No authored card or configuration mappings.", None
        for note in release["applicability"]:
            config, card = note["configuration"], note["card"]
            yield "h3", f"{card['name']} · {STATUSES[note['status']]}", None
            yield "p", f"Card source · {card['id']}", card["source_url"]
            yield "p", f"Configuration · {config['id']} · {config['variant']}", None
            yield "p", f"OS · {config['os']} · Driver · {config['driver']} · Backend · {config['backend']}", None
            yield "p", f"Runtime build · {config['build_sha']}", note["build_url"]
            yield "p", f"Model artifact · {config['model_artifact']}", None
            yield "p", f"Workload · {config['workload_id']}@{config['workload_version']}", None
            yield "p", "Flags · " + json.dumps(config["flags"], ensure_ascii=False), None
            yield "p", note["technique"], None
            yield "p", "Prerequisites · " + note["prerequisites"], None
            yield "p", "Limits · " + note["limits"], None
            yield "p", "Failure modes · " + note["failure_modes"], None
            yield "p", f"Applicability source · {note['source_label']}", note["source_url"]
            if "retest" in note:
                yield "p", "Matched retest · Baseline evidence", note["retest"]["baseline_url"]
                yield "p", "Matched retest · Tuned evidence", note["retest"]["tuned_url"]


def render(report, format_name):
    if format_name == "json":
        return json.dumps(report, ensure_ascii=False, indent=2)
    if format_name == "html":
        body = []
        for tag, text, href in lines(report):
            content = f'<a href="{escape(href)}">{escape(text)}</a>' if href else escape(text)
            body.append(f"<{tag}>{content}</{tag}>")
        return (
            '<!doctype html>\n<html lang="en">\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<title>llama.cpp release watch</title>\n<body>\n<main>\n'
            + "\n".join(body) + "\n</main>\n</body>\n</html>"
        )

    body = []
    for tag, text, href in lines(report):
        prefix = "#" * int(tag[1]) + " " if tag.startswith("h") else ""
        content = re.sub(r"([\\`*_{}\[\]<>#!&|])", r"\\\1", text)
        if href:
            content = f"[{content}](<{quote(href, safe=':/?#[]@!$&()*+,;=%~')}>)"
        body.append(prefix + content)
    return "\n\n".join(body)
