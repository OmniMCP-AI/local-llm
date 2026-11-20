from decimal import Decimal
from hashlib import sha256
from html import escape
import json
import re
from urllib.parse import quote, urlsplit


_VIEW_LINKS = "[Chart data](./chart.json) · [Table data](./table.json) · [Citation](#citation)"


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _digest(body):
    return sha256(body.encode("utf-8")).hexdigest()


def _markdown_text(text):
    return re.sub(r"([\\`*_{}\[\]<>#!&|])", r"\\\1", text)


def _unescape_markdown(text):
    return re.sub(r"\\([\\`*_{}\[\]<>#!&|])", r"\1", text)


def _write_markdown(snapshot, dataset_digest):
    row = snapshot["row"]
    release_id = snapshot["release_id"]
    evidence_id = row["evidence_id"]
    hardware, artifact = row["hardware"], row["artifact"]
    workload, metric = row["workload"], row["metric"]
    source, rights = row["source"], row["rights"]
    metadata = {
        "page_id": evidence_id,
        "path": f"/releases/{release_id}/benchmark.html",
        "release": release_id,
        "revision": snapshot["revision"],
        "evidence": [evidence_id],
        "hardware_revision": hardware["revision_id"],
        "widget": {
            "id": "benchmark-observation",
            "protocol": f"{workload['id']}@{workload['version']}",
            "metric": f"{metric['id']}@{metric['version']}",
            "unit": metric["unit"],
            "data": f"/releases/{release_id}/chart.json",
            "sha256": dataset_digest,
        },
    }
    introduction = {
        "synthetic": "This synthetic evidence demonstrates the release pipeline.",
        "measured": "This measurement applies to the configuration and protocol below.",
    }
    details = [
        introduction[row["kind"]],
        f"Result: {metric['value']} {metric['unit']} ({metric['statistic']}, n={metric['sample_count']}).",
        f"Evidence ID: {evidence_id}",
        f"Release: {release_id}, revision {snapshot['revision']}",
        f"Hardware: {hardware['name']}, revision {hardware['revision']} ({hardware['revision_id']}).",
        hardware["configuration"],
        f"Artifact: {artifact['repository']}@{artifact['revision']}/{artifact['path']} "
        f"({artifact['format']}, {artifact['quantization']}).",
        f"Artifact SHA-256: {artifact['sha256']}",
        f"Workload: {workload['id']}@{workload['version']}. {workload['description']}",
        f"Metric: {metric['id']}@{metric['version']}. {metric['boundary']}",
        f"Public rights decision: {rights['decision_id']}. {rights['basis']}",
    ]
    for name, field in sorted(row["fields"].items()):
        text = f"Missing. {field['reason']}" if field["status"] == "missing" else field["value"]
        details.append(f"{name.replace('_', ' ').capitalize()}: {text}")

    frontmatter = "\n".join(f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in metadata.items())
    paragraphs = "\n\n".join(map(_markdown_text, details))
    citation = _markdown_text(f"Source: {source['label']}, revision {source['revision']}.")
    locator = _source_url(source["locator"])
    source_locator = f"<{locator}>" if locator else _markdown_text(source["locator"])
    return (
        f"---\n{frontmatter}\n---\n\n# Benchmark observation\n\n{paragraphs}\n\n"
        f"{_VIEW_LINKS}\n\n<!-- benchmark-widget -->\n\n## Citation\n\n"
        f"{citation}\n\nSource locator: {source_locator}\n"
    )


def _widget(row, axis_max):
    metric = row["metric"]
    value, unit = escape(metric["value"]), escape(metric["unit"])
    evidence = escape(row["evidence_id"])
    label = f"{value} {unit}"
    return f"""<figure id="benchmark-chart" data-evidence-id="{evidence}">
<figcaption>Benchmark chart · {label}</figcaption>
<label for="benchmark-value">{escape(metric["id"])} ({unit})</label>
<meter id="benchmark-value" min="0" max="{axis_max}" value="{value}">{label}</meter>
<span>Scale 0–{axis_max} {unit}</span>
</figure>
<table id="benchmark-table">
<caption>Benchmark data</caption>
<thead><tr><th scope="col">Evidence</th><th scope="col">Value</th><th scope="col">Unit</th></tr></thead>
<tbody><tr data-evidence-id="{evidence}"><th scope="row"><a href="#citation">{evidence}</a></th>
<td>{value}</td><td>{unit}</td></tr></tbody>
</table>"""


def _source_url(locator):
    try:
        parsed = urlsplit(locator)
        if parsed.scheme in ("https", "http") and parsed.hostname:
            return quote(locator, safe=":/?#[]@!$&'()*+,;=%")
    except ValueError:
        pass
    return None


def _render_markdown(markdown, chart):
    """Render the fixed public template's heading, paragraphs and widget marker."""
    frontmatter, _, body = markdown[4:].partition("\n---\n\n")
    metadata = {}
    for line in frontmatter.splitlines():
        key, value = line.split(": ", 1)
        metadata[key] = json.loads(value)
    dataset = json.loads(chart)
    row = dataset["rows"][0]
    workload, metric = row["workload"], row["metric"]
    widget = metadata["widget"]
    if (
        metadata["release"] != dataset["release_id"]
        or metadata["revision"] != dataset["revision"]
        or metadata["evidence"] != [row["evidence_id"]]
        or widget["sha256"] != _digest(chart)
        or widget["protocol"] != f"{workload['id']}@{workload['version']}"
        or widget["metric"] != f"{metric['id']}@{metric['version']}"
        or widget["unit"] != metric["unit"]
    ):
        raise ValueError("Markdown and chart data do not describe the same release")

    content = []
    for line in filter(None, body.splitlines()):
        if line.startswith("# "):
            content.append(f"<h1>{escape(line[2:])}</h1>")
        elif line == "## Citation":
            content.append('<h2 id="citation">Citation</h2>')
        elif line == _VIEW_LINKS:
            content.append(
                '<p><a href="./chart.json">Chart data</a> · '
                '<a href="./table.json">Table data</a> · '
                '<a href="#citation">Citation</a></p>'
            )
        elif line == "<!-- benchmark-widget -->":
            content.append(_widget(row, dataset["scale"]["maximum"]))
        elif line.startswith("Source locator: "):
            locator = row["source"]["locator"]
            href = _source_url(locator)
            visible = f'<a href="{escape(href)}">{escape(locator)}</a>' if href else escape(locator)
            content.append(f"<p>Source locator: {visible}</p>")
        else:
            content.append(f"<p>{escape(_unescape_markdown(line))}</p>")
    rendered = "\n".join(content)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Benchmark observation</title>
<link rel="alternate" type="text/markdown" href="./benchmark.md">
<style>
body {{ color: #232b35; background: #fff; font: 1rem/1.5 system-ui, sans-serif; margin: 2rem auto; max-width: 52rem; padding: 0 1rem; overflow-wrap: anywhere; }}
figure {{ margin: 2rem 0; }}
meter {{ display: block; width: min(100%, 25rem); height: 1.75rem; }}
table {{ border-collapse: collapse; }}
caption, th, td {{ text-align: left; padding: .35rem .8rem; }}
th, td {{ border-bottom: 1px solid #bac2cc; }}
</style>
</head>
<body>
<main>
{rendered}
<p><a href="./benchmark.md">Read as Markdown</a></p>
</main>
</body>
</html>
"""


def build_artifacts(snapshot):
    """Materialize the approved artifact set from one live public release read."""
    common = {key: value for key, value in snapshot.items() if key != "row"}
    if snapshot["status"] == "withdrawn":
        clear_text = f"Evidence was withdrawn from release {snapshot['release_id']}."
        artifacts = {
            "benchmark.md": f"# Evidence withdrawn\n\n{clear_text}\n",
            "benchmark.html": f'<!doctype html>\n<html lang="en"><meta charset="utf-8"><title>Evidence withdrawn</title><h1>Evidence withdrawn</h1><p>{escape(clear_text)}</p></html>\n',
            "chart.json": _json({**common, "rows": []}),
            "table.json": _json({**common, "rows": []}),
        }
    else:
        row = snapshot["row"]
        value = Decimal(row["metric"]["value"])
        maximum = format(Decimal(10) ** (value.adjusted() + 1) if value else Decimal(1), "f")
        dataset = {**common, "rows": [row]}
        chart = _json({**dataset, "scale": {"minimum": "0", "maximum": maximum}})
        markdown = _write_markdown(snapshot, _digest(chart))
        artifacts = {
            "benchmark.md": markdown,
            "benchmark.html": _render_markdown(markdown, chart),
            "chart.json": chart,
            "table.json": _json(dataset),
        }
    return {
        **artifacts,
        "manifest.json": _json({**common, "artifacts": {name: _digest(body) for name, body in artifacts.items()}}),
    }
