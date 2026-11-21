import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from fastest_release.validation import plain_text

from .feed import SOURCES
from .retest import approved_links


CATALOG = (
    Path(__file__).resolve().parents[2]
    / "opendesign/mockups/llm-observatory/catalog-hardware.json"
)
STATUSES = {
    "suggested": "Suggested",
    "upstream_documented": "Upstream documented",
    "contributor_reported": "Contributor reported",
    "fastest_ai_verified": "fastest.ai verified",
    "unsupported": "Unsupported",
    "unresolved": "Unresolved",
}
NOTE_KEYS = set("id revision_id card_id source_url source_label status technique prerequisites limits failure_modes configuration".split())
CONFIG_KEYS = set("id variant os driver backend build_sha flags workload_id workload_version model_artifact".split())
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}")


def https_url(value):
    if not plain_text(value) or any(character.isspace() for character in value) or "\\" in value:
        raise ValueError("Applicability sources require a public HTTPS URL")
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username is not None:
        raise ValueError("Applicability sources require a public HTTPS URL")
    return value


def apply_notes(report, notes_path, read_release=None, origin=""):
    revisions = {row["revision_id"]: row for row in report["releases"]}
    for row in revisions.values():
        row["applicability"] = []
    if notes_path is None:
        return report
    path = Path(notes_path)
    authored = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(authored, dict) or set(authored) != {"notes"} or not isinstance(authored["notes"], list):
        raise ValueError("Expected an object with an authored notes list")
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    cards = {card["id"]: card for card in catalog["cards"]}
    seen = set()
    for note in authored["notes"]:
        applicability = validate(note, cards, revisions, seen)
        release = revisions[note["revision_id"]]
        if note["status"] == "fastest_ai_verified":
            if read_release is None or "retest" not in note:
                raise ValueError("A verified note requires an approved matched retest")
            applicability["retest"] = approved_links(
                read_release, note, note["retest"], origin, runtime_id=release["runtime_id"],
            )
        release["applicability"].append(applicability)
    for row in revisions.values():
        row["applicability"].sort(key=lambda note: note["id"])
    return report


def validate(note, cards, revisions, seen):
    if not isinstance(note, dict) or set(note) - {"retest"} != NOTE_KEYS:
        raise ValueError("Unexpected or missing authored applicability fields")
    if not all(plain_text(note[key]) for key in NOTE_KEYS - {"configuration"}):
        raise ValueError("Applicability fields must be nonempty single-line text")
    if not IDENTIFIER.fullmatch(note["id"]) or note["id"] in seen:
        raise ValueError("Expected a unique authored applicability ID")
    seen.add(note["id"])
    if note["revision_id"] not in revisions or note["card_id"] not in cards:
        raise ValueError("Applicability must name a retained release revision and existing catalog card")
    if note["status"] not in STATUSES:
        raise ValueError("Expected an editorial applicability status")
    if "retest" in note and note["status"] != "fastest_ai_verified":
        raise ValueError("Retest links require a fastest.ai verified note")
    https_url(note["source_url"])
    config = note["configuration"]
    if not isinstance(config, dict) or set(config) != CONFIG_KEYS:
        raise ValueError("Applicability requires an exact configuration")
    if not all(plain_text(config[key]) for key in CONFIG_KEYS - {"flags", "workload_version"}):
        raise ValueError("Configuration fields must be nonempty single-line text")
    if not IDENTIFIER.fullmatch(config["id"]) or not IDENTIFIER.fullmatch(config["workload_id"]):
        raise ValueError("Expected stable configuration and workload IDs")
    if not re.fullmatch(r"[a-f0-9]{40}", config["build_sha"]):
        raise ValueError("Configuration requires a full lowercase Git commit SHA")
    if type(config["workload_version"]) is not int or not 0 < config["workload_version"] < 2**31:
        raise ValueError("Expected a positive workload version")
    flags = config["flags"]
    if not isinstance(flags, list) or not all(plain_text(flag) for flag in flags):
        raise ValueError("Configuration flags must be a list of arguments")
    card = cards[note["card_id"]]
    source = SOURCES[revisions[note["revision_id"]]["runtime_id"]]
    return {
        **note,
        "card": {"id": card["id"], "name": card["name"], "source_url": https_url(card["source"])},
        "build_url": f"https://github.com/{source.repository}/commit/{config['build_sha']}",
    }
