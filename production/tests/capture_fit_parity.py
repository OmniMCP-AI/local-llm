"""Save the full public fit fixture responses for cross-worker comparison."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_fit import APPLE_REQUEST, MISSING, OFFLOAD, REQUEST, fit_server, read_estimate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("engine", type=Path)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    cases = {"gpu": REQUEST, "cpu_offload": OFFLOAD, "missing_input": MISSING, "apple_metal": APPLE_REQUEST}
    with fit_server(args.engine) as base:
        report = {name: read_estimate(base, selection) for name, selection in cases.items()}
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
