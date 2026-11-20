import argparse
import json
from pathlib import Path

from fastest_pilot_bundle import digest, json_text, write_bundle

from .intake import apply_record, summarize
from .render import render


PACKAGE = Path(__file__).resolve().parent


def build(target, records, demo):
    dataset = json.loads((PACKAGE / "plan.json").read_text(encoding="utf-8"))
    local_artifacts = [dataset["workflow"], *(cell["lock"] for cell in dataset["cells"])]
    files = {}
    for artifact in local_artifacts:
        path = artifact["path"]
        content = (PACKAGE / path).read_bytes().decode("utf-8")
        if digest(content) != artifact["sha256"]:
            raise ValueError(f"{path} does not match the pinned SHA-256")
        files[path] = content

    kind = "synthetic" if demo else "measured"
    dataset["evidence_kind"] = kind if records else "planned"
    cells = {cell["id"]: cell for cell in dataset["cells"]}
    for path in records:
        record = json.loads(path.read_text(encoding="utf-8"))
        cell_id = record.get("cell_id") if isinstance(record, dict) else None
        if not isinstance(cell_id, str) or cell_id not in cells or "source" in cells[cell_id]:
            raise ValueError("each record must identify a distinct planned cell")
        cells[cell_id] = apply_record(record, dataset, cells[cell_id], kind)

    dataset["cells"] = [summarize(cell, dataset["protocol"]) for cell in cells.values()]
    payload = json_text(dataset)
    markdown, html = render(dataset, digest(payload))
    files.update({"image-pilot.json": payload, "image-pilot.md": markdown, "image-pilot.html": html})
    write_bundle(target, dataset["id"], files)


def main():
    parser = argparse.ArgumentParser(description="Build the two-machine image pilot.")
    commands = parser.add_subparsers(dest="command", required=True)
    publish = commands.add_parser("build", help="Write a new public report directory.")
    publish.add_argument("output", type=Path)
    publish.add_argument("--record", type=Path, action="append", default=[], help="Include a reviewed image run JSON record.")
    publish.add_argument("--demo", action="store_true", help="Require synthetic ledgers and label the report.")
    args = parser.parse_args()
    if args.demo and not args.record:
        parser.error("--demo requires at least one --record")
    try:
        build(args.output, args.record, args.demo)
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
