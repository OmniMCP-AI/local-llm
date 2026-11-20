"""Project a pinned collection window into one public price dataset."""

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from .validation import PriceError


METHOD = "seller-day-landed-asking-v1"
REFRESH_METHOD = "seller-day-landed-asking-v2"

DAY_LABELS = {
    "observed": "Observed",
    "no_comparable_offer": "No comparable offer",
    "capture_failed": "Capture failed",
    "capture_incomplete": "Capture incomplete",
    "not_checked": "Not checked",
}

RANGE_LABELS = {
    "below_threshold": "Withheld (below threshold)",
    "rights_restricted": "Withheld (aggregation rights)",
    "published": "Published",
}


def _landed(offer):
    total = Decimal(offer["price"])
    for field in ("tax", "shipping"):
        charge = offer[field]
        if charge["basis"] == "unknown":
            return None
        if charge["basis"] == "excluded":
            if charge["amount"] is None:
                return None
            total += Decimal(charge["amount"])
    return total


def _comparable_offer(offer):
    return (
        offer["kind"] == "asking" and offer["stock"] == "in_stock"
        and offer["confirmation"] == "seller_confirmed" and offer["discount"] == "unconditional"
        and offer["landed_price"] is not None
    )


def eligible_offer(offer):
    return _comparable_offer(offer) and offer.get("availability", "available") == "available"


def _availability(offer, as_of, feed_status):
    expiry = offer.get("expires_at")
    if expiry and date.fromisoformat(expiry[:10]) <= as_of:
        return "expired"
    if not offer["latest_for_listing"]:
        return "historical"
    if not expiry or not _comparable_offer(offer):
        return "unavailable"
    if feed_status == "stale" or offer["freshness"] == "stale":
        return "stale"
    if feed_status != "fresh":
        return "incomplete"
    return "available"


def _quartile(values, index):
    lower, remainder = divmod((len(values) - 1) * index, 4)
    if not remainder:
        return values[lower]
    return values[lower] + (values[lower + 1] - values[lower]) * Decimal(remainder) / 4


def _sampling(values, seller_count, minimums, allowed):
    status = "rights_restricted"
    stats = dict.fromkeys(("min", "q1", "median", "q3", "max"))
    if allowed:
        status = "below_threshold"
        if len(values) >= minimums["minimum_samples"] and seller_count >= minimums["minimum_sellers"]:
            status = "published"
            ordered = sorted(values)
            stats = {name: format(_quartile(ordered, index), "f") for index, name in enumerate(stats)}
    return {
        **minimums,
        "sample_count": len(values) if allowed else None,
        "seller_count": seller_count if allowed else None,
        "range_status": status,
        **stats,
    }


def build_result(snapshot):
    recurring = snapshot["method"] == REFRESH_METHOD
    if snapshot["method"] not in (METHOD, REFRESH_METHOD):
        raise PriceError(f"Unsupported price cohort method: {snapshot['method']}")
    identity = {
        "result_type": "regional-price-cohort",
        "schema_version": 1,
        **{field: snapshot[field] for field in ("release_id", "cohort_id", "status", "method")},
    }
    if snapshot["status"] == "withdrawn":
        return identity

    cohort = snapshot["cohort"]
    start, as_of = (date.fromisoformat(snapshot[field]) for field in ("start", "as_of"))
    stale_after = cohort["stale_after_days"]
    allowed = snapshot["can_aggregate"]
    captures = {}
    successes = set()
    last_success = None
    for capture in snapshot["captures"]:
        day = capture["checked_at"][:10]
        captures[day] = capture["status"]
        if capture["status"] == "success":
            successes.add(day)
            last_success = capture["checked_at"]

    last_success_age = (as_of - date.fromisoformat(last_success[:10])).days if last_success else None
    freshness = "no_success"
    if last_success_age is not None:
        freshness = "stale" if last_success_age > stale_after else "fresh"

    last_attempt = snapshot["captures"][-1]["status"] if captures else None
    if recurring and freshness != "stale" and last_attempt in {"failed", "incomplete"}:
        freshness = last_attempt

    offers_by_day = defaultdict(list)
    comparable_days = set()
    best_quotes = {}
    latest = {}
    for offer in snapshot["offers"]:
        day = offer["observed_at"][:10]
        age = (as_of - date.fromisoformat(day)).days
        landed = _landed(offer)
        offer.update(
            age_days=age,
            freshness="stale" if age > stale_after else "fresh",
            landed_price=format(landed, "f") if landed is not None else None,
            sample_selected=False if allowed else None,
            latest_for_listing=False,
        )
        offers_by_day[day].append(offer)
        # The database orders the deduplicated rows by observation day.
        latest[(offer["seller"], offer["listing_id"], offer["kind"])] = offer
        if _comparable_offer(offer):
            comparable_days.add(day)
            if allowed:
                key = (day, offer["seller"])
                previous = best_quotes.get(key)
                if previous is None or landed < previous[0]:
                    best_quotes[key] = (landed, offer)

    for offer in latest.values():
        offer["latest_for_listing"] = True

    if recurring:
        for offer in snapshot["offers"]:
            offer.setdefault("expires_at", None)
            offer["availability"] = _availability(offer, as_of, freshness)

    values_by_day = defaultdict(list)
    for (day, seller), (price, offer) in best_quotes.items():
        values_by_day[day].append(price)
        offer["sample_selected"] = True

    days = []
    for offset in range((as_of - start).days + 1):
        day = (start + timedelta(days=offset)).isoformat()
        if day in comparable_days:
            state = "observed"
        elif day in successes or offers_by_day[day]:
            state = "no_comparable_offer"
        else:
            state = {
                "failed": "capture_failed", "incomplete": "capture_incomplete",
            }.get(captures.get(day), "not_checked")
        days.append({
            "date": day,
            "status": state,
            "last_attempt_status": captures.get(day),
            "offer_count": len(offers_by_day[day]) if allowed else None,
            "sample_count": len(values_by_day[day]) if allowed else None,
        })

    return {
        **identity,
        **{field: cohort[field] for field in (
            "source_id", "source_revision", "source_type", "market", "destination", "scope",
            "condition", "currency", "data_class", "stale_after_days",
        )},
        "authorization_decision_id": snapshot["decision_id"],
        **({"authorization_expires_at": snapshot["expires_at"]} if snapshot.get("expires_at") else {}),
        "start": snapshot["start"],
        "as_of": snapshot["as_of"],
        "last_success_at": last_success,
        "last_success_age_days": last_success_age,
        "last_attempt_status": last_attempt,
        "adapter_status": freshness,
        "sampling": _sampling(
            [price for price, _ in best_quotes.values()],
            len({seller for _, seller in best_quotes}),
            {field: cohort[field] for field in ("minimum_samples", "minimum_sellers")},
            allowed,
        ),
        "days": days,
        "offers": snapshot["offers"],
    }
