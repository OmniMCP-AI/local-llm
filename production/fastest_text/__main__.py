import argparse
from html import escape
import json
from pathlib import Path
import re
import sys

from fastest_pilot_bundle import digest, json_text, write_bundle

from .capture import capture
from .intake import apply_record
from .review import write_review_packet


PLAN_PATH = Path(__file__).with_name("plan.json")
LATENCY_METRICS = {
    "ttft": ("Time to first token", "Client request start to first generated token."),
    "first_visible_answer": (
        "Time to first visible answer", "Client request start to first visibly rendered answer text."
    ),
}


def missing(label, unit, boundary, reason):
    return {
        "label": label, "unit": unit, "boundary": boundary,
        "status": "missing", "value": None, "sample_count": 0, "reason": reason,
    }


def blocked_cell(cell, phases):
    return {
        **cell,
        "status": "blocked",
        "attempts": [],
        "metrics": {
            **{
                key: missing(phase["label"], "tok/s", phase["boundary"], cell["blocker"])
                for key, phase in phases.items()
            },
            **{
                key: missing(label, "ms", boundary, "This runner does not instrument client latency.")
                for key, (label, boundary) in LATENCY_METRICS.items()
            },
        },
        "quality": {
            "review_count": 0, "output_count": 0,
            "accepted_count": 0, "disagreement_count": 0, "reviews": [],
        },
    }


def markdown_text(value):
    return re.sub(r"([\\`*_{}\[\]<>#!&|~])", r"\\\1", str(value))


def render(dataset, data_hash):
    artifact = dataset["artifact"]
    runtime = dataset["runtime"]
    protocol = dataset["protocol"]
    rubric = dataset["rubric"]
    label = {
        "planned": "Planned comparison. The table gives the current blocker for each machine.",
        "synthetic": "Synthetic demonstration. Values and reviewer records illustrate the intake.",
        "measured": "Reviewed run records. Each row applies to the stated machine and phase.",
    }[dataset["evidence_kind"]]
    md = ["# Two-machine text pilot", label, "[Typed data](./text-pilot.json) · [Manifest](./manifest.json)"]
    html = [
        '<!doctype html><html lang="en"><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<title>Two-machine text pilot</title>',
        '<link rel="alternate" type="text/markdown" href="./text-pilot.md">',
        '<main><h1>Two-machine text pilot</h1>',
        f"<p>{escape(label)}</p>",
        '<p><a href="./text-pilot.md">Markdown</a> · <a href="./text-pilot.json">Typed data</a> · '
        '<a href="./manifest.json">Manifest</a></p>',
    ]

    def paragraph(value, lang=None):
        md.append(markdown_text(value))
        lang_attr = f' lang="{lang}"' if lang else ""
        html.append(f"<p{lang_attr}>{escape(value)}</p>")

    def source_link(label, url):
        md.append(f"[{label}]({url})")
        html.append(f'<p><a href="{escape(url)}">{escape(label)}</a></p>')

    def heading(value):
        md.append(f"## {markdown_text(value)}")
        html.append(f"<h2>{escape(value)}</h2>")

    def table(columns, rows):
        md.append(
            "| " + " | ".join(map(markdown_text, columns)) + " |\n"
            + "| " + " | ".join("---" for _ in columns) + " |\n"
            + "\n".join("| " + " | ".join(map(markdown_text, row)) + " |" for row in rows)
        )
        html.append(
            "<table><thead><tr>"
            + "".join(f'<th scope="col">{escape(column)}</th>' for column in columns)
            + "</tr></thead><tbody>"
            + "".join(
                f'<tr><th scope="row">{escape(str(row[0]))}</th>'
                + "".join(f"<td>{escape(str(item))}</td>" for item in row[1:]) + "</tr>"
                for row in rows
            )
            + "</tbody></table>"
        )

    paragraph(f"Typed dataset SHA-256 {data_hash}")
    paragraph(f"Initial access check recorded on {dataset['access_checked_on']}.")
    heading("Fixed-token throughput")
    paragraph(f"{artifact['repository']} at {artifact['revision']}, {artifact['quantization']}, {artifact['license']}.")
    source_link("Pinned model files", artifact["source"])
    paragraph(f"Tokenizer uses the {artifact['tokenizer']}.")
    for shard in artifact["shards"]:
        paragraph(f"{shard['path']} · SHA-256 {shard['sha256']}")
    paragraph(f"{runtime['name']} {runtime['tag']} at {runtime['revision']}. Protocol {protocol['id']}.")
    source_link("Pinned runtime source", runtime["source"])
    paragraph(f"Goal per machine: {protocol['warm_samples_per_phase']} warm samples per phase.")
    for item in ("warmup", "cache", "load", "input"):
        paragraph(protocol[item])
    for phase in protocol["phases"].values():
        paragraph(
            f"{phase['label']} uses {phase['input_tokens']} input and {phase['output_tokens']} output tokens "
            f"with a requested {phase['requested_context_tokens']}-token context. {phase['boundary']}"
        )
    paragraph("Runner settings · " + ", ".join(f"{key}={value}" for key, value in protocol["settings"].items()))
    paragraph("Throughput is the median of successful repetitions in each phase.")
    paragraph("TTFT measures " + LATENCY_METRICS["ttft"][1].lower())
    paragraph("First visible answer measures " + LATENCY_METRICS["first_visible_answer"][1].lower())
    table(
        ("Machine", "Backend", "Cell status", "Recorded attempts", "Failures", "Blocker"),
        [
            (
                cell["name"], cell["backend"], cell["status"], len(cell["attempts"]),
                sum(attempt["outcome"] != "success" for attempt in cell["attempts"]),
                cell["blocker"] or "—",
            )
            for cell in dataset["cells"]
        ],
    )

    rows = []
    for cell in dataset["cells"]:
        for metric in cell["metrics"].values():
            result = metric["reason"] if metric["status"] == "missing" else f"{metric['value']} {metric['unit']}"
            rows.append((cell["name"], metric["label"], metric["status"], metric["sample_count"], result))
    table(("Machine", "Metric", "Status", "Samples", "Result or blocker"), rows)

    for cell in dataset["cells"]:
        if not cell["attempts"]:
            continue
        heading(f"{cell['name']} run evidence")
        build = cell["runtime_build"]
        paragraph(f"{build['machine']} · {build['os_driver']} · {build['effective_placement']}")
        paragraph(f"Runner provenance: {build['provenance']} · SHA-256 {build['binary_sha256']}.")
        paragraph(f"Evidence: {cell['source']['locator']} at {cell['source']['revision']}.")
        paragraph(f"Public rights: {cell['rights']['decision_id']}. {cell['rights']['basis']}")
        table(
            ("Phase", "Attempt", "Outcome", "Elapsed ns or failure"),
            [
                (
                    protocol["phases"][attempt["phase"]]["label"], attempt["number"], attempt["outcome"],
                    attempt.get("elapsed_ns", attempt.get("reason")),
                )
                for attempt in cell["attempts"]
            ],
        )

    heading("Chinese task quality review")
    paragraph(rubric["rights"])
    paragraph(rubric["prompt"], "zh-Hans")
    paragraph(rubric["method"])
    for description in rubric["criteria"].values():
        paragraph(description, "zh-Hans")
    table(
        ("Machine", "Outputs reviewed", "Reviewer ratings", "Accepted", "Disagreements"),
        [
            (
                cell["name"],
                *(cell["quality"][key] for key in ("output_count", "review_count", "accepted_count", "disagreement_count")),
            )
            for cell in dataset["cells"]
        ],
    )
    reviews = [
        (
            cell["name"], review["output_id"], review["output_sha256"], review["reviewer"],
            *("Pass" if review["scores"][key] else "Fail" for key in rubric["criteria"]),
            review["note"],
        )
        for cell in dataset["cells"]
        for review in cell["quality"]["reviews"]
    ]
    if reviews:
        table(("Machine", "Output", "Output SHA-256", "Reviewer", *rubric["criteria"], "Review note"), reviews)
    return "\n\n".join(md) + "\n", "\n".join(html + ["</main></html>"]) + "\n"


def load_dataset(records=(), demo=False):
    dataset = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    kind = "synthetic" if demo else "measured"
    dataset["evidence_kind"] = kind if records else "planned"
    cells = {
        cell["id"]: blocked_cell(cell, dataset["protocol"]["phases"])
        for cell in dataset["cells"]
    }
    seen = set()
    for path in records:
        record = json.loads(path.read_text(encoding="utf-8"))
        cell_id = record.get("cell_id") if isinstance(record, dict) else None
        if not isinstance(cell_id, str) or cell_id not in cells or cell_id in seen:
            raise ValueError("each record must identify a distinct planned cell")
        cells[cell_id] = apply_record(record, dataset, cells[cell_id], kind)
        seen.add(cell_id)
    dataset["cells"] = list(cells.values())
    return dataset


def text_artifacts(dataset):
    payload = json_text(dataset)
    markdown, html = render(dataset, digest(payload))
    return {"text-pilot.json": payload, "text-pilot.md": markdown, "text-pilot.html": html}


def build(target, records, demo):
    dataset = load_dataset(records, demo)
    write_bundle(target, dataset["id"], text_artifacts(dataset))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build the two-machine text pilot.")
    commands = parser.add_subparsers(dest="command", required=True)
    publish = commands.add_parser("build", help="Write a new public report directory.")
    publish.add_argument("output", type=Path)
    publish.add_argument("--record", type=Path, action="append", default=[], help="Include a reviewed runner JSON record.")
    publish.add_argument("--demo", action="store_true", help="Require synthetic records and label their public output.")
    collect = commands.add_parser("capture", help="Run both pinned phases and retain private evidence.")
    collect.add_argument("output", type=Path, help="New operator-private evidence directory.")
    collect.add_argument("--cell", choices=("apple-m4", "rtx-4090"), required=True)
    collect.add_argument("--bench", type=Path, required=True, help="Pinned b5163 llama-bench executable.")
    collect.add_argument("--model-dir", type=Path, required=True, help="Directory containing both pinned shards.")
    collect.add_argument("--build-evidence", type=Path, required=True, help="Local build and linked-library provenance file.")
    collect.add_argument("--host-revision", required=True, help="Operator's stable physical host/configuration identifier.")
    collect.add_argument("--quiet-host", action="store_true", required=True, help="Attest to an otherwise idle host.")
    collect.add_argument("--timeout", type=int, default=900, help="Maximum seconds per phase.")
    review = commands.add_parser("review-packet", help="Prepare retained Chinese completions for blinded review.")
    review.add_argument("output", type=Path, help="New directory for the review packet and private source map.")
    review.add_argument("--response", type=Path, action="append", required=True, help="Retained chat completion JSON.")
    args = parser.parse_args(argv)
    try:
        if args.command == "capture":
            plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
            latency = {
                key: missing(label, "ms", boundary, "The fixed-token runner does not instrument client latency.")
                for key, (label, boundary) in LATENCY_METRICS.items()
            }
            if capture(args, plan, latency):
                return 0
            print(f"Capture incomplete. Private evidence retained in {args.output}.", file=sys.stderr)
            return 1
        if args.command == "review-packet":
            rubric = json.loads(PLAN_PATH.read_text(encoding="utf-8"))["rubric"]
            write_review_packet(args.output, args.response, rubric)
            return 0
        if args.demo and not args.record:
            parser.error("--demo requires at least one --record")
        build(args.output, args.record, args.demo)
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print(f"Capture interrupted. Check private evidence in {args.output}.", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
