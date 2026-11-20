import argparse
from html import escape
import json
from pathlib import Path

from .evidence import comparison
from .harness import TASK_BYTES, fingerprint, plan, read_tool


def json_text(value):
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def table(headers, rows, html):
    if html:
        headings = "".join(f'<th scope="col">{escape(label)}</th>' for label in headers)
        body = "".join("<tr>" + "".join(f"<td>{escape(str(value))}</td>" for value in row) + "</tr>" for row in rows)
        return f"<table><thead><tr>{headings}</tr></thead><tbody>{body}</tbody></table>"
    return "\n".join(
        "| " + " | ".join(map(str, row)) + " |" for row in (headers, ["---"] * len(headers), *rows)
    )


def details(label, item, html):
    data = json_text(item)
    if html:
        return f"<details><summary>{escape(label)}</summary><pre>{escape(data)}</pre></details>"
    return f"#### {label}\n\n```json\n{data}```"


def page(dataset, html):
    title = "Controlled inventory agent task"
    summary = f'{dataset["kind"]} · release {dataset["release_id"]}. {dataset["notice"]}'
    if html:
        head = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
        sections = [f"{head}<title>{title}</title><main><h1>{title}</h1><p>{escape(summary)}</p>",
                    '<p><a href="agent-task.json">Exact dataset</a> · <a href="task.json">Task fixture</a> · <a href="manifest.json">Manifest</a></p>']
    else:
        sections = [f"# {title}\n\n{summary}",
                    "[Exact dataset](agent-task.json) · [Task fixture](task.json) · [Manifest](manifest.json)"]
    for context in dataset["contexts"]:
        heading = f'{context["id"]} · {context["status"]}'
        sections.append(f"<h2>{escape(heading)}</h2>" if html else f"## {heading}")
        counts = context["counts"]
        text = (
            f'{counts["accepted_trials"]} accepted of {counts["attempted_trials"]} attempted trials '
            f'({counts["planned_trials"]} planned). {counts["failed_attempts"]} failed of {counts["attempts"]} attempts.'
        )
        sections.append(f"<p>{text}</p>" if html else text)
        if context["attempts"]:
            attempt_rows = [
                (a["trial"], a["attempt"], a["outcome"], a["wall_ns"],
                 json.dumps(a["accepted_output"]) if a["accepted_output"] is not None else "—")
                for a in context["attempts"]
            ]
            sections.append(table(("Trial", "Attempt", "Outcome", "Wall ns", "Accepted output"), attempt_rows, html))
            trial_rows = [(r["trial"], r["status"], r["recorded_attempt_wall_ns"]) for r in context["trials"]]
            sections.append(table(("Trial", "Status", "Total recorded attempt wall ns"), trial_rows, html))
        sections.append(details("Policy and review", {k: context[k] for k in ("allowed_reads", "sha256", "review")}, html))
    sections.append(details("Pinned conditions and environment", {
        **dataset["conditions"], "environment": dataset["environment"],
    }, html))
    if html:
        sections.append("</main></html>")
    return "\n\n".join(sections) + "\n"


def build(destination, demo, record_paths):
    if demo and record_paths:
        raise ValueError("Demo releases use scripted results only")
    records = [json.loads(path.read_bytes()) for path in record_paths]
    dataset = comparison(plan(demo), records, demo)
    files = {
        "agent-task.json": json_text(dataset).encode(),
        "agent-task.md": page(dataset, html=False).encode(),
        "agent-task.html": page(dataset, html=True).encode(),
        "task.json": TASK_BYTES,
    }
    manifest = {
        "schema_version": 1, "release_id": dataset["release_id"], "kind": dataset["kind"],
        "sha256": {name: fingerprint(content) for name, content in files.items()},
    }
    destination.mkdir(parents=True)
    for name, content in files.items():
        (destination / name).write_bytes(content)
    (destination / "manifest.json").write_bytes(json_text(manifest).encode())
    return dataset["release_id"]


def main():
    cli = argparse.ArgumentParser(description="Build a controlled inventory agent-task comparison.")
    commands = cli.add_subparsers(dest="command", required=True)
    commands.add_parser("plan", help="Show the exact conditions and context fingerprints for measured runs.")
    tool_parser = commands.add_parser("tool", help="Read one allowed fictional fixture resource.")
    for arg in ("context", "tool", "resource"):
        tool_parser.add_argument(arg)
    build_parser = commands.add_parser("build", help="Build an immutable release in a new directory.")
    build_parser.add_argument("directory", type=Path)
    build_parser.add_argument("--record", action="append", default=[], type=Path)
    build_parser.add_argument("--demo", action="store_true")
    args = cli.parse_args()
    try:
        if args.command == "plan":
            print(json_text(plan()), end="")
        elif args.command == "tool":
            print(json_text(read_tool(args.context, args.tool, args.resource)), end="")
        else:
            print(build(args.directory, args.demo, args.record))
    except (ValueError, OSError) as error:
        cli.error(str(error))


if __name__ == "__main__":
    main()
