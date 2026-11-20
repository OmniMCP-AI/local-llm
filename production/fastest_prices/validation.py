"""Validate reviewed feed snapshots at the publisher boundary."""

from datetime import date, datetime
import re


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
    _fields(
        value, "cohort",
        "id source_id source_revision source_type market destination scope condition currency "
        "seller_aliases data_class stale_after_days minimum_samples minimum_sellers authorization",
    )
    for field in ("id", "source_id", "source_revision", "market", "destination"):
        _text(value[field], field)
    _choice(value["source_type"], "source type", ("seller", "feed"))
    _scope(value["scope"])
    _condition(value["condition"])
    _currency(value["currency"])
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

    rights = value["authorization"]
    _fields(rights, "authorization", "decision_id record status collect retain display export aggregate")
    _text(rights["decision_id"], "authorization decision")
    _text(rights["record"], "authorization record")
    _choice(rights["status"], "authorization status", ("approved",))
    for permission in ("collect", "retain", "display", "export"):
        _choice(rights[permission], permission, ("allow",))
    _choice(rights["aggregate"], "aggregate", ("allow", "deny"))


def bundle(value):
    _fields(value, "bundle", "cohort captures")
    cohort(value["cohort"])
    if not isinstance(value["captures"], list):
        raise PriceError("captures must be a list")
    for item in value["captures"]:
        capture(item)


def capture(value):
    _fields(value, "capture", "id source_id source_revision checked_at status observations")
    _text(value["id"], "capture ID")
    _text(value["source_id"], "source ID")
    _text(value["source_revision"], "source revision")
    checked_at = _timestamp(value["checked_at"], "checked_at")
    _choice(value["status"], "capture status", ("success", "failed"))
    observations = value["observations"]
    if not isinstance(observations, list) or (value["status"] == "failed" and observations):
        raise PriceError("a failed capture must have an empty observation list")
    for observation in observations:
        _observation(observation, checked_at)


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
