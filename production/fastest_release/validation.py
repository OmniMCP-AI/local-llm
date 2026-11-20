from datetime import datetime
import re
import uuid


CONTRIBUTOR_COMPARISON = "Excluded from controlled comparisons. The measurement is contributor-reported."


class InvalidObservation(ValueError):
    """The submitted observation is ineligible for the public release."""


def keys(record, expected, label):
    if not isinstance(record, dict) or set(record) != set(expected.split()):
        raise InvalidObservation(f"{label} requires these fields: {expected}")


def plain_text(value):
    return (
        isinstance(value, str)
        and 0 < len(value) <= 2048
        and value == value.strip()
        and all(character.isprintable() for character in value)
    )


def valid_expiry(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", value):
        return False
    try:
        datetime.fromisoformat(value)
    except ValueError:
        return False
    return True


def _text(value, label):
    if not plain_text(value):
        raise InvalidObservation(f"{label} must be nonempty, single-line text")


def _uuid(value, label):
    try:
        identifier = str(uuid.UUID(value))
    except (AttributeError, TypeError, ValueError) as error:
        raise InvalidObservation(f"{label} must be a UUID") from error
    if identifier != value:
        raise InvalidObservation(f"{label} must be a canonical UUID")


def _positive_int(value, label):
    if type(value) is not int or not 0 < value < 2**31:
        raise InvalidObservation(f"{label} must be a positive 32-bit integer")


def _strings(record, group, expected):
    for field in expected.split():
        _text(record[field], f"{group}.{field}")


def validate(observation):
    keys(observation, "evidence_id kind hardware artifact workload metric source rights fields", "observation")
    _uuid(observation["evidence_id"], "evidence_id")
    if observation["kind"] not in ("synthetic", "measured", "contributor"):
        raise InvalidObservation("kind must be synthetic, measured, or contributor")

    hardware = observation["hardware"]
    keys(hardware, "revision_id revision name configuration", "hardware")
    _uuid(hardware["revision_id"], "hardware.revision_id")
    _positive_int(hardware["revision"], "hardware.revision")
    _strings(hardware, "hardware", "name configuration")

    artifact = observation["artifact"]
    keys(artifact, "artifact_id repository revision path sha256 format quantization", "artifact")
    _uuid(artifact["artifact_id"], "artifact.artifact_id")
    _strings(artifact, "artifact", "repository revision path sha256 format quantization")
    if not re.fullmatch(r"[a-f0-9]{64}", artifact["sha256"]):
        raise InvalidObservation("artifact.sha256 must be a lowercase SHA-256 digest")

    workload = observation["workload"]
    keys(workload, "id version description", "workload")
    _positive_int(workload["version"], "workload.version")
    _strings(workload, "workload", "id description")

    metric = observation["metric"]
    keys(metric, "id version value unit statistic boundary sample_count", "metric")
    _positive_int(metric["version"], "metric.version")
    _positive_int(metric["sample_count"], "metric.sample_count")
    _strings(metric, "metric", "id value unit statistic boundary")
    if not re.fullmatch(r"(0|[1-9][0-9]{0,19})(\.[0-9]{1,12})?", metric["value"]):
        raise InvalidObservation("metric.value must be a nonnegative decimal string")

    source = observation["source"]
    keys(source, "label locator revision", "source")
    _strings(source, "source", "label locator revision")

    rights = observation["rights"]
    expires = isinstance(rights, dict) and "expires_at" in rights
    keys(rights, "decision_id destination core basis" + (" expires_at" if expires else ""), "rights")
    if expires and not valid_expiry(rights["expires_at"]):
        raise InvalidObservation("rights.expires_at must be a UTC timestamp at second precision")
    _uuid(rights["decision_id"], "rights.decision_id")
    _text(rights["basis"], "rights.basis")
    if rights["destination"] != "public-release" or rights["core"] != "allow":
        raise InvalidObservation("The core evidence requires an allow decision for public-release")

    fields = observation["fields"]
    if not isinstance(fields, dict):
        raise InvalidObservation("fields must be an object")
    if observation["kind"] == "contributor" and fields.get("comparison_eligibility") != {
        "status": "known", "rights": "allow", "value": CONTRIBUTOR_COMPARISON,
    }:
        raise InvalidObservation("Contributor observations require the public comparison exclusion")
    for key, field in fields.items():
        if not isinstance(key, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", key):
            raise InvalidObservation("field names must use lowercase letters, digits and underscores")
        if not isinstance(field, dict) or field.get("rights") not in ("allow", "deny"):
            raise InvalidObservation(f"{key} requires an explicit rights decision")
        if field.get("status") == "missing":
            keys(field, "rights status reason", key)
            _text(field["reason"], f"{key}.reason")
        else:
            keys(field, "rights status value", key)
            if field["status"] != "known":
                raise InvalidObservation(f"{key}.status must be known or missing")
            _text(field["value"], f"{key}.value")
