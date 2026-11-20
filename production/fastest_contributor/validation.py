from datetime import datetime, timezone
import json
import re
from urllib.parse import urlsplit
from uuid import UUID

from fastest_release.validation import CONTRIBUTOR_COMPARISON, InvalidObservation, keys, plain_text, valid_expiry, validate


MAX_BYTES = 64 * 1024
CONDITIONS = ("runtime_revision", "runtime_sha256", "os_driver", "settings")
AMBIGUOUS = {"unknown", "unresolved", "unspecified", "missing", "n/a", "none", "latest", "main", "master", "default",
             "tbd", "-", "?"}


def identifier(value, label):
    try:
        if str(UUID(value)) == value:
            return
    except (AttributeError, TypeError, ValueError):
        pass
    raise ValueError(f"{label} must be a canonical UUID")


def version_number(value):
    if type(value) is not int or not 0 < value < 2**31:
        raise ValueError("Version must be a positive 32-bit integer")


def _object(pairs):
    fields = {}
    for key, value in pairs:
        if key in fields:
            raise ValueError("Duplicate JSON field")
        fields[key] = value
    return fields


def _constant(_):
    raise ValueError("Non-finite JSON number")


def json_object(raw):
    if not isinstance(raw, str) or len(raw.encode("utf-8")) > MAX_BYTES or "\0" in raw:
        raise ValueError("Provide a UTF-8 JSON object within 64 KiB")
    try:
        value = json.loads(raw, object_pairs_hook=_object, parse_constant=_constant)
    except RecursionError as error:
        raise ValueError("JSON is too deeply nested") from error
    if not isinstance(value, dict):
        raise ValueError("Input must be a JSON object")
    return value


def decode(raw):
    record = json_object(raw)
    identifier(record.get("submission_id"), "Submission ID")
    version_number(record.get("version"))
    return record


def _specific(value):
    return plain_text(value) and value.casefold() not in AMBIGUOUS


def _digest(value):
    return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) is not None


def _locator(value):
    if not plain_text(value) or "\\" in value or any(character.isspace() for character in value):
        return False
    try:
        parsed = urlsplit(value)
        return (
            parsed.scheme == "https" and "." in (parsed.hostname or "") and parsed.port in (None, 443)
            and parsed.username is None and parsed.password is None and not parsed.query
            and bool(parsed.path.strip("/")) and "?" not in value.partition("#")[0]
        )
    except ValueError:
        return False


def _authorization(authorization):
    if not isinstance(authorization, dict):
        return ["invalid_authorization"], None
    issues = []
    expected = {"contributor_id", "consent", "scope", "reference"}
    if authorization.keys() - {"expires_at"} != expected:
        issues.append("invalid_authorization")
    owner = authorization.get("contributor_id")
    if not _specific(owner):
        owner = None
        issues.append("ambiguous_contributor")
    if authorization.get("consent") is not True:
        issues.append("consent_required")
    if authorization.get("scope") != "public-release":
        issues.append("public_scope_required")
    if not _specific(authorization.get("reference")):
        issues.append("missing_authorization_reference")
    if "expires_at" in authorization:
        expiry = authorization["expires_at"]
        if not valid_expiry(expiry):
            issues.append("invalid_authorization_expiry")
        elif datetime.fromisoformat(expiry) <= datetime.now(timezone.utc):
            issues.append("expired_authorization")
    return issues, owner


def _evidence_issue(record):
    try:
        keys(record, "submission_id version authorization hardware artifact workload metric conditions source", "submission")
        keys(record["source"], "label locator revision sha256", "source")
        keys(record["conditions"], " ".join(CONDITIONS), "conditions")
        # Validate the same immutable core projection the editor would submit to the release service.
        validate(candidate(record, record["submission_id"], record["submission_id"], include_expiry=False))
    except InvalidObservation:
        return "invalid_observation"
    for group, fields in (
        ("hardware", ("name", "configuration")),
        ("artifact", ("repository", "revision", "path", "format", "quantization")),
        ("workload", ("id", "description")),
        ("source", ("label", "revision")),
    ):
        if any(not _specific(record[group][field]) for field in fields):
            return "ambiguous_identity"
    artifact_path = record["artifact"]["path"]
    if "\\" in artifact_path or any(segment in ("", ".", "..") for segment in artifact_path.split("/")):
        return "ambiguous_identity"
    if not _locator(record["source"]["locator"]) or not _digest(record["source"]["sha256"]):
        return "invalid_locator"
    conditions = record["conditions"]
    if not _digest(conditions["runtime_sha256"]) or any(
        not _specific(conditions[key]) for key in CONDITIONS
    ):
        return "invalid_conditions"
    return None


def submission_issues(record):
    issues, owner = _authorization(record.get("authorization"))
    issue = _evidence_issue(record)
    if issue:
        issues.append(issue)
    return issues, owner


def review_decision(decision):
    keys(decision, "decision_id editor_id outcome reason authorization_reference", "editorial review")
    identifier(decision["decision_id"], "Decision ID")
    if decision["outcome"] not in ("publish", "reject"):
        raise ValueError("Editorial outcome must be publish or reject")
    if not _specific(decision["editor_id"]) or not _specific(decision["reason"]):
        raise ValueError("Editorial review requires an editor ID and a reason")
    if decision["outcome"] == "publish" and not _specific(decision["authorization_reference"]):
        raise ValueError("Publication requires an independently reviewed authorization reference")
    if decision["outcome"] == "reject" and decision["authorization_reference"] is not None and not _specific(
        decision["authorization_reference"]
    ):
        raise ValueError("Authorization reference must use specific single-line text or null")


def candidate(record, evidence_id, decision_id, *, include_expiry=True):
    source = record["source"]
    rights = {
        "decision_id": decision_id,
        "destination": "public-release",
        "core": "allow",
        "basis": "An editor verified the contributor’s permission for this scoped public evidence.",
    }
    if include_expiry and "expires_at" in record["authorization"]:
        rights["expires_at"] = record["authorization"]["expires_at"]
    return {
        "evidence_id": evidence_id,
        "kind": "contributor",
        **{key: record[key] for key in ("hardware", "artifact", "workload", "metric")},
        "source": {key: source[key] for key in ("label", "locator", "revision")},
        "rights": rights,
        "fields": {
            key: {"status": "known", "rights": "allow", "value": value}
            for key, value in {
                **record["conditions"], "source_sha256": source["sha256"],
                "comparison_eligibility": CONTRIBUTOR_COMPARISON,
            }.items()
        },
    }
