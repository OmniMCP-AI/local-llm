"""Attach a public rights decision to the release-safe projection of a retained stream."""

from decimal import Decimal
import json
from subprocess import TimeoutExpired

from fastest_release import ReleaseError, _sql_text
from fastest_release.validation import keys

from .intake import require, require_digest, validate_release_rights
from .latency import BOUNDARIES, GENERATION_SETTINGS, PROTOCOL, SERVER_SETTINGS, runtime_profile


MISSING_BOUNDARIES = {
    "ttft": "The stream did not emit generated token ordinal 1.",
    "first_visible_answer": "The stream did not emit printable non-whitespace answer text.",
}


def read_eligible_latency(store, capture_sha256):
    require_digest(capture_sha256, "latency capture SHA-256")
    result = store._query(f"""
        SELECT row_to_json(evidence)
        FROM fastest_intake.eligible_text_latency AS evidence
        WHERE capture_sha256 = {_sql_text(capture_sha256)};
    """)
    return json.loads(result) if result else None


def apply_latency_reviews(dataset, reviews, reader):
    if not reviews:
        return
    require(reader is not None, "Reviewed latency requires access to the PostgreSQL eligible latency view.")
    require(dataset["evidence_kind"] != "synthetic", "Reviewed latency requires a production text report.")
    cells = {cell["id"]: cell for cell in dataset["cells"]}
    has_latency_sample = False
    for path in reviews:
        review = json.loads(path.read_text(encoding="utf-8"))
        keys(review, "capture_sha256 rights", "latency review")
        capture_sha256, rights = review["capture_sha256"], review["rights"]
        require_digest(capture_sha256, "latency capture SHA-256")
        validate_release_rights(rights)
        try:
            evidence = reader(capture_sha256)
        except (ReleaseError, OSError, TimeoutExpired):
            raise ValueError("Could not read reviewed latency from PostgreSQL. Check the eligible latency grant.") from None
        require(evidence is not None, "Latency review requires a retained, complete quiet-host capture.")
        cell = cells.get(evidence["cell_id"])
        require(cell is not None and "latency_review" not in cell,
                "Each latency review must identify a distinct planned cell.")
        cell["latency_review"] = {
            "capture_sha256": capture_sha256, "rights_decision_id": rights["decision_id"],
            **{field: evidence[field] for field in ("binary_sha256", "prompt_tokens", "output_tokens")},
        }
        for boundary, description in BOUNDARIES.items():
            nanos = evidence[f"{boundary}_ns"]
            available = nanos is not None
            has_latency_sample |= available
            cell["metrics"][boundary].update(
                boundary=description, status="available" if available else "missing",
                sample_count=int(available), statistic="single-observation" if available else None,
                value=format(Decimal(nanos).scaleb(-6), "f") if available else None,
                reason=None if available else MISSING_BOUNDARIES[boundary],
            )
    for cell in cells.values():
        if "latency_review" not in cell:
            for boundary, description in BOUNDARIES.items():
                cell["metrics"][boundary].update(
                    boundary=description, reason="No reviewed quiet-host stream is attached for this machine.",
                )
    if has_latency_sample:
        dataset["evidence_kind"] = "measured"
    dataset["latency_protocol"] = {
        "id": PROTOCOL, "runtime": runtime_profile(dataset), "server_settings": SERVER_SETTINGS,
        "generation_settings": GENERATION_SETTINGS,
        "conditions": "One foreground request on an operator-attested quiet host with one active accelerator. "
                      "The model is loaded before one explicit warmup. Each request clears KV and disables prefix reuse.",
    }
