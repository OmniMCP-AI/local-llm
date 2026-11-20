"""Content addressing and immutable local records for approved handoffs."""

from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from tempfile import NamedTemporaryFile

from fastest_release.validation import plain_text


def digest(record):
    canonical = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(canonical.encode("utf-8")).hexdigest()


def seal(record, field):
    return {**record, field: digest(record)}


def read_sealed(path, field):
    return decode_sealed(path.read_bytes(), field, path.name)


def decode_sealed(body, field, name):
    record = json.loads(body)
    if not isinstance(record, dict):
        raise ValueError(f"{name} must contain a JSON object")
    identifier = record.pop(field, None)
    if identifier != digest(record):
        raise ValueError(f"{name} failed {field} verification")
    return {**record, field: identifier}


def json_bytes(record):
    return (json.dumps(record, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def instant(value):
    timestamp = datetime.fromisoformat(value)
    if timestamp.utcoffset() is None:
        raise ValueError("timestamps must include a UTC offset")
    return timestamp.astimezone(timezone.utc)


def create_approval(*, channel, account, story_revision, payload_sha256, window_start, window_end,
                    approved_by, rights_reference):
    start, end = instant(window_start), instant(window_end)
    if start >= end:
        raise ValueError("approval window must end after it starts")
    if not plain_text(approved_by) or not plain_text(rights_reference):
        raise ValueError("approval requires an editor and a channel-use rights reference")
    destination = {"channel": channel, "account": account, "story_revision": story_revision}
    return seal({
        **destination,
        "schema_version": 1,
        "delivery_id": digest(destination),
        "payload_sha256": payload_sha256,
        "window_start": start.isoformat(),
        "window_end": end.isoformat(),
        "approved_by": approved_by,
        "rights_reference": rights_reference,
    }, "approval_id")


def require_window(approval, when):
    if not instant(approval["window_start"]) <= when < instant(approval["window_end"]):
        raise ValueError("time is outside the approved window")


def retain(path, body):
    """Record complete bytes once. Identical retries reuse that record."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=path.parent, prefix=".pending-") as pending:
        pending.write(body)
        pending.flush()
        os.fsync(pending.fileno())
        try:
            os.link(pending.name, path)
        except FileExistsError:
            if path.read_bytes() != body:
                raise ValueError(f"conflicting record already exists at {path}") from None
    return path.resolve()
