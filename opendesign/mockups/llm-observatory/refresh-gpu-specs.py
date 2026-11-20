"""Capture device specifications from the official NVIDIA and Intel tables."""

from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.request import urlopen


NVIDIA = "https://www.nvidia.com/en-us/geforce/graphics-cards/compare/"
INTEL = "https://dgpu-docs.intel.com/overview/architecture/gpu-architecture.html"
GEFORCE_FIELDS = {
    "Standard Memory Config": "Memory configuration",
    "Memory Interface Width": "Memory bus",
    "Memory Bandwidth": "Memory bandwidth",
    "NVIDIA CUDA® Cores": "CUDA cores",
    "NVIDIA Architecture": "Architecture",
    "NVIDIA Architecture Name": "Architecture",
    "Boost Clock (GHz)": "Boost clock (GHz)",
    "Base Clock (GHz)": "Base clock (GHz)",
    "Total Graphics Power (W)": "Rated graphics power (W)",
    "Graphics Card Power (W)": "Rated graphics power (W)",
    "Required System Power (W)": "Recommended system power (W)",
    "Supplementary Power Connectors": "Power connectors",
}
INTEL_FIELDS = {
    "Xe cores": "Xe cores",
    "PCIe interface": "Host interface",
    "Dedicated memory capacity (GB)": "Dedicated memory (GB)",
    "Memory type": "Memory type",
    "Memory bandwidth (GB/s)": "Memory bandwidth (GB/s)",
    "Memory interface width (bits)": "Memory bus (bits)",
    "Total board power (W)": "Rated graphics power (W)",
}


class Tables(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []
        self.table = self.row = self.cell = None

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.table = []
        if tag == "tr" and self.table is not None:
            self.row = []
        if tag in ("td", "th") and self.row is not None:
            self.cell = []
        if tag == "br" and self.cell is not None:
            self.cell.append(" / ")

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        if tag == "tr" and self.row is not None:
            self.table.append(self.row)
            self.row = None
        if tag == "table" and self.table is not None:
            self.tables.append(self.table)
            self.table = None

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)


def read_tables(url):
    parser = Tables()
    with urlopen(url, timeout=20) as response:
        parser.feed(response.read().decode("utf-8"))
    return parser.tables


def capture(tables, fields, source, identity):
    records = {}
    for header, *rows in filter(None, tables):
        for slot, heading in enumerate(header[1:], start=1):
            heading = heading.replace(" / ", " ")
            card_id = identity(heading)
            if not card_id:
                continue
            facts = {
                fields[row[0]]: row[slot]
                for row in rows if len(row) == len(header) and row[0] in fields and row[slot] not in ("", "-", "–")
            }
            if facts:
                if card_id in records:
                    raise ValueError(f"Duplicate manufacturer identity {card_id}")
                records[card_id] = {"source": source, "designation": heading, "facts": facts}
    return records


def geforce(name):
    return "nvidia-" + name.lower().replace(" ", "-") if re.fullmatch(r"GeForce (RTX|GTX) \d{4}( (?:Ti|Super|Ti Super))?", name, re.I) else None


def main():
    nvidia = capture(read_tables(NVIDIA), GEFORCE_FIELDS, NVIDIA, geforce)
    intel = capture(read_tables(INTEL), INTEL_FIELDS, INTEL,
                    lambda name: "intel-arc-pro-" + name.lower() if re.fullmatch(r"B\d{2}", name) else None)
    if len(nvidia) < 30 or len(intel) < 4:
        raise ValueError("The manufacturer tables are incomplete")
    cards = {**nvidia, **intel}
    path = Path(__file__).with_name("gpu-vendor-specs.json")
    payload = {"capturedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"), "cards": cards}
    staging = path.with_suffix(".tmp")
    staging.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    staging.replace(path)
    print(f"Captured {len(cards)} manufacturer rows")


if __name__ == "__main__":
    main()
