"""Render the exact public artifacts without writing private or temporary files."""

from .__main__ import json_text, page
from .evidence import comparison
from .harness import TASK_BYTES, fingerprint, plan


def report_artifacts(records=()):
    dataset = comparison(plan(), records, demo=False)
    files = {
        "agent-task.json": json_text(dataset),
        "agent-task.md": page(dataset, html=False),
        "agent-task.html": page(dataset, html=True),
        "task.json": TASK_BYTES.decode("utf-8"),
    }
    files["manifest.json"] = json_text({
        "schema_version": 1, "release_id": dataset["release_id"], "kind": dataset["kind"],
        "sha256": {name: fingerprint(content.encode("utf-8")) for name, content in files.items()},
    })
    return files
