"""Validate reviewed feed snapshots at the publisher boundary."""

from datetime import date, datetime, timedelta
import re
from urllib.parse import urlsplit

from fastest_release.validation import valid_expiry


class PriceError(ValueError):
    """The price input or requested release is invalid."""


def _fields(value, label, expected):
    if not isinstance(value, dict) or value.keys() != set(expected.split()):
        raise PriceError(f"{label} requires exactly these fields: {expected}")


def _text(value, label):
    if (
        not isinstance(value, str) or not value.strip() or len(value) > 500
        or any(ord(char) < 32 for char in value)
    ):
        raise PriceError(f"{label} must be nonempty single-line text")


def _choice(value, label, choices):
    if value not in choices:
        raise PriceError(f"{label} must be one of {', '.join(choices)}")


def _scope(value):
    _fields(value, "scope", "kind id revision_id")
    _choice(value["kind"], "scope kind", ("sku", "whole_build"))
    _text(value["id"], "scope ID")
    _text(value["revision_id"], "scope revision")


def _currency(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Z]{3}", value):
        raise PriceError("currency must be a three-letter original currency code")


def _integer(value, label, minimum, maximum):
    if type(value) is not int or not minimum <= value <= maximum:
        raise PriceError(f"{label} must be an integer between {minimum} and {maximum}")


def _timestamp(value, label):
    if not isinstance(value, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z", value
    ):
        raise PriceError(f"{label} must be an explicit UTC timestamp")
    try:
        return datetime.fromisoformat(value)
    except ValueError as error:
        raise PriceError(f"invalid {label}") from error


def _money(value, label):
    if not isinstance(value, str) or not re.fullmatch(r"\d{1,12}(?:\.\d{1,6})?", value):
        raise PriceError(f"{label} must be a nonnegative decimal string")


def _charge(value, label):
    _fields(value, label, "basis amount")
    _choice(value["basis"], label, ("included", "excluded", "not_applicable", "unknown"))
    if value["amount"] is not None:
        if value["basis"] in ("unknown", "not_applicable"):
            raise PriceError(f"{label} amount contradicts its basis")
        _money(value["amount"], label)


def _condition(value):
    _choice(value, "condition", ("new", "used", "refurbished", "open_box"))


def cohort(value):
    citation = isinstance(value, dict) and value.get("source_type") == "citation"
    common = "id source_id source_revision source_type market scope currency data_class authorization"
    if citation:
        _fields(value, "citation cohort", common + " source_name source_locator price_basis")
    else:
        _fields(value, "cohort", common + (
            " destination condition seller_aliases stale_after_days minimum_samples minimum_sellers"
        ))
    for field in ("id", "source_id", "source_revision", "market"):
        _text(value[field], field)
    _scope(value["scope"])
    _currency(value["currency"])
    if citation:
        _citation_policy(value)
    else:
        _offer_policy(value)
    _authorization(value["authorization"], citation)


def _citation_policy(value):
    _choice(value["scope"]["kind"], "citation scope kind", ("sku",))
    _choice(value["data_class"], "data class", ("reviewed_citations",))
    _choice(value["price_basis"], "citation price basis", ("post_coupon",))
    _text(value["source_name"], "citation source name")
    locator = value["source_locator"]
    _text(locator, "citation source URL")
    try:
        url = urlsplit(locator)
    except ValueError as error:
        raise PriceError("Use an exact HTTPS product page URL for the citation") from error
    if (
        url.scheme != "https" or not url.hostname or url.netloc != url.hostname
        or not url.path.startswith("/") or url.path == "/" or url.fragment or re.search(r"[\s<>\\]", locator)
    ):
        raise PriceError("Use an exact HTTPS product page URL for the citation")


def _offer_policy(value):
    _choice(value["source_type"], "source type", ("seller", "feed"))
    _text(value["destination"], "destination")
    _condition(value["condition"])
    _choice(value["data_class"], "data class", ("illustrative", "authorized_observations"))
    _integer(value["stale_after_days"], "stale_after_days", 0, 365)
    _integer(value["minimum_samples"], "minimum_samples", 3, 3660)
    _integer(value["minimum_sellers"], "minimum_sellers", 2, value["minimum_samples"])
    aliases = value["seller_aliases"]
    if not isinstance(aliases, dict) or not aliases:
        raise PriceError("seller_aliases must identify the reviewed seller(s)")
    for alias, seller in aliases.items():
        _text(alias, "seller alias")
        _text(seller, "canonical seller")
    if value["source_type"] == "seller" and len(set(aliases.values())) != 1:
        raise PriceError("a direct seller cohort must identify one canonical seller")

def _authorization(rights, citation):
    expires = isinstance(rights, dict) and "expires_at" in rights
    fields = "decision_id record status collect retain display export aggregate"
    _fields(rights, "authorization", fields + (" expires_at" if expires else ""))
    if expires and not valid_expiry(rights["expires_at"]):
        raise PriceError("authorization.expires_at must be a UTC timestamp at second precision")
    _text(rights["decision_id"], "authorization decision")
    _text(rights["record"], "authorization record")
    _choice(rights["status"], "authorization status", ("approved",))
    for permission in ("collect", "retain", "display", "export"):
        _choice(rights[permission], permission, ("allow",))
    _choice(rights["aggregate"], "aggregate", ("deny",) if citation else ("allow", "deny"))


def bundle(value):
    _fields(value, "bundle", "cohort captures")
    cohort(value["cohort"])
    if not isinstance(value["captures"], list):
        raise PriceError("captures must be a list")
    for item in value["captures"]:
        capture(item)


def capture(value):
    citation = isinstance(value, dict) and "references" in value
    field = "references" if citation else "observations"
    _fields(value, "capture", "id source_id source_revision checked_at status " + field)
    _text(value["id"], "capture ID")
    _text(value["source_id"], "source ID")
    _text(value["source_revision"], "source revision")
    checked_at = _timestamp(value["checked_at"], "checked_at")
    if citation:
        _choice(value["status"], "citation capture status", ("success",))
        _references(value["references"], checked_at)
        return
    _choice(value["status"], "capture status", ("success", "failed"))
    observations = value["observations"]
    if not isinstance(observations, list) or (value["status"] == "failed" and observations):
        raise PriceError("a failed capture must have an empty observation list")
    for observation in observations:
        _observation(observation, checked_at)


def _references(references, checked_at):
    if not isinstance(references, list) or not 1 <= len(references) <= 3:
        raise PriceError("A citation capture needs one to three price references")
    # A source date can be a calendar day ahead of the UTC review timestamp.
    latest_day = (checked_at + timedelta(hours=14)).date().isoformat()
    for item in references:
        _fields(item, "reference", "observed_on marketplace price")
        period(item["observed_on"], item["observed_on"])
        if item["observed_on"] > latest_day:
            raise PriceError("Citation date cannot follow its review")
        _text(item["marketplace"], "citation marketplace")
        _money(item["price"], "citation price")


def _observation(value, checked_at):
    _fields(
        value, "observation",
        "listing_id seller market destination scope condition currency kind confirmation "
        "stock observed_at price tax shipping discount source_locator review",
    )
    for field in ("listing_id", "seller", "market", "destination", "source_locator"):
        _text(value[field], field)
    _scope(value["scope"])
    _condition(value["condition"])
    _currency(value["currency"])
    _choice(value["kind"], "price kind", ("asking", "bid", "sale", "msrp", "historical_report"))
    _choice(value["confirmation"], "confirmation", ("seller_confirmed", "source_reported", "unknown"))
    _choice(value["stock"], "stock", ("in_stock", "out_of_stock", "backorder", "unknown"))
    _choice(value["discount"], "discount", ("unconditional", "conditional", "unknown"))
    if _timestamp(value["observed_at"], "observed_at") > checked_at:
        raise PriceError("observed_at cannot follow checked_at")
    _money(value["price"], "price")
    _charge(value["tax"], "tax")
    _charge(value["shipping"], "shipping")
    review = value["review"]
    _fields(review, "observation review", "decision_id status")
    _text(review["decision_id"], "observation review decision")
    _choice(review["status"], "observation review status", ("approved",))


def period(start, as_of):
    try:
        dates = [date.fromisoformat(value) for value in (start, as_of)]
    except (TypeError, ValueError) as error:
        raise PriceError("start and as_of must be ISO dates") from error
    if [item.isoformat() for item in dates] != [start, as_of] or not 0 <= (dates[1] - dates[0]).days < 366:
        raise PriceError("choose an ISO date window of 1 to 366 days")
    return start, as_of
