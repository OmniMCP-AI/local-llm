"""Refresh a dated shortlist from the Hugging Face Hub's downloads sort."""

from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

ROOT = Path(__file__).parent
LIMIT = 1000
SMALL = 4_000_000_000
PROPERTIES = ("downloads", "safetensors", "baseModels", "gated")
SOURCE = "https://huggingface.co/api/models?" + urlencode([
    ("pipeline_tag", "text-generation"), ("sort", "downloads"), ("limit", LIMIT),
    *[("expand[]", name) for name in PROPERTIES],
])


def main():
    known = {row["id"] for row in json.loads((ROOT / "catalog-models.json").read_text())["models"]}
    with urlopen(SOURCE, timeout=25) as response:
        records = json.load(response)
    candidates = []
    for row in records:
        identifier = row["id"]
        downloads = row.get("downloads")
        size = row.get("safetensors", {}).get("total")
        lineage = row.get("baseModels", {})
        if identifier not in known or type(size) is not int or size <= 0 or type(downloads) is not int or downloads < 0:
            continue
        if lineage.get("relation") in ("quantized", "adapter", "merge"):
            continue
        bases = lineage.get("models", [])
        family = bases[0]["id"] if len(bases) == 1 and lineage.get("relation") == "finetune" and (
            bases[0]["id"].split("/")[0] == identifier.split("/")[0]
        ) else identifier
        candidates.append({"id": identifier, "family": family, "parameters": size, "downloads": downloads,
                           "gated": bool(row.get("gated"))})

    ranked = sorted(candidates, key=lambda row: (-row["downloads"], row["id"]))
    unique = {}
    for row in ranked:
        unique.setdefault(row["family"], row)
    popular = list(unique.values())[:300]
    small = [row for row in unique.values() if row["parameters"] <= SMALL][:75]
    if len(popular) < 250 or len(small) < 50:
        raise ValueError("Insufficient Hub metadata for discovery. Keep the previous snapshot.")
    payload = {"source": SOURCE, "capturedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "sourceRows": len(records), "eligibleFamilies": len(unique), "smallLimit": SMALL,
               "popular": popular, "small": small}
    output = ROOT / "model-discovery.json"
    staging = output.with_suffix(".tmp")
    staging.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    staging.replace(output)
    print(f"Captured {len(popular)} popular and {len(small)} small-model entries")


if __name__ == "__main__":
    main()
