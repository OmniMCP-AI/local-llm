"""Bind an optional first-party link to the evidence in an approved package."""

import re
from urllib.parse import urlsplit
from uuid import UUID


ROUTE = "/pilot/evidence"
UUID_PATTERN = r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}"
LINK_PATH = re.compile(rf"{ROUTE}/({UUID_PATTERN})/({UUID_PATTERN})")


def evidence_link(draft, key=None):
    destination = draft["story"]["evidence_destination"]
    if key is None:
        return destination
    if not isinstance(key, str):
        raise ValueError("engagement key must be a canonical random UUID")
    identifier = UUID(key)
    if identifier.version != 4 or str(identifier) != key:
        raise ValueError("engagement key must be a canonical random UUID")
    citation = urlsplit(destination)
    return f"{citation.scheme}://{citation.netloc}{ROUTE}/{draft['release']['release_id']}/{key}#citation"


def verified_link(package, copy, observed):
    """Check the original handoff and an operator's exact live-link observation."""
    key = package.get("engagement_key")
    if key is None and observed is None:
        return {}
    link = evidence_link(package["draft"], key)
    if key is None or observed != link or link not in copy.decode("utf-8").splitlines():
        raise ValueError("the observed engagement link must match the exact approved post link")
    return {"engagement_url": link}
