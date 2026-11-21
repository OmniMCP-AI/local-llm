"""Collect one bounded refresh from an approved, cursor-based seller feed."""

from contextlib import closing
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import http.client
import json
import os
import re
from time import monotonic
from urllib.parse import urlencode, urlsplit
from uuid import uuid4

from fastest_release import _sql_text

from . import _document, validation
from .validation import PriceError


REQUEST_TIMEOUT = 8
MAX_PAGE_BYTES = 512 * 1024
MAX_ROWS_PER_PAGE = 200


class RateLimited(PriceError):
    def __init__(self, retry_after):
        super().__init__("Seller feed rate limited the refresh")
        self.retry_after = retry_after


def register(store, cohort_id, config):
    """Bind the approved seller cohort to one HTTPS endpoint and request budget."""
    validation._fields(config, "refresh settings", "url minimum_interval_seconds max_pages")
    validation._text(config["url"], "seller feed URL")
    url = urlsplit(config["url"])
    if (
        url.scheme != "https" or not url.hostname or url.netloc != url.hostname
        or not url.path.startswith("/") or url.query or url.fragment
        or not re.fullmatch(r"/[A-Za-z0-9/_.~-]+", url.path)
    ):
        raise PriceError("Use a seller HTTPS URL with a hostname and fixed path")
    validation._integer(config["max_pages"], "max_pages", 1, 20)
    validation._integer(
        config["minimum_interval_seconds"], "minimum_interval_seconds",
        30 + REQUEST_TIMEOUT * config["max_pages"], 86400,
    )
    store._query(f"SELECT fastest_prices.register_refresh({_sql_text(cohort_id)}, {_document(config)});")


def _request(url, cursor):
    endpoint = urlsplit(url)
    path = endpoint.path if cursor is None else f"{endpoint.path}?{urlencode({'cursor': cursor})}"
    headers = {"Accept": "application/json", "User-Agent": "fastest.ai-price-refresh"}
    token = os.environ.get("FASTEST_PRICE_FEED_TOKEN")
    if token:
        if not re.fullmatch(r"[A-Za-z0-9._~+/=-]+", token):
            raise PriceError("Invalid seller bearer token format")
        headers["Authorization"] = f"Bearer {token}"
    deadline = monotonic() + REQUEST_TIMEOUT
    with closing(http.client.HTTPSConnection(endpoint.hostname, timeout=REQUEST_TIMEOUT)) as conn:
        conn.request("GET", path, headers=headers)
        with conn.getresponse() as response:
            if response.status == 429:
                raise RateLimited(response.getheader("Retry-After"))
            if response.status != 200:
                raise PriceError("Seller feed did not return a successful response")
            body = bytearray()
            while len(body) <= MAX_PAGE_BYTES:
                if monotonic() >= deadline:
                    raise TimeoutError
                chunk = response.read1(min(65536, MAX_PAGE_BYTES + 1 - len(body)))
                if not chunk:
                    return json.loads(body.decode("utf-8"))
                body.extend(chunk)
    raise PriceError("Seller feed page exceeds the byte limit")


def _decode(page, checked):
    validation._fields(page, "seller page", "cursor complete observations")
    validation._text(page["cursor"], "seller cursor")
    if type(page["complete"]) is not bool:
        raise PriceError("Seller page must declare completion")
    rows = page["observations"]
    if not isinstance(rows, list) or len(rows) > MAX_ROWS_PER_PAGE:
        raise PriceError("Seller page must contain a bounded observation list")
    observations = []
    for item in rows:
        validation._fields(item, "seller observation", "id version offer")
        validation._text(item["id"], "seller event ID")
        validation._integer(item["version"], "seller event version", 1, 2**63 - 1)
        if not isinstance(item["offer"], dict) or "expires_at" not in item["offer"]:
            raise PriceError("Seller offer must declare expiry or include a null expiry")
        offer = item["offer"]
        validation._observation({key: value for key, value in offer.items() if key != "expires_at"}, checked)
        if offer["expires_at"] is not None:
            expires = validation._timestamp(offer["expires_at"], "expires_at")
            observed = validation._timestamp(offer["observed_at"], "observed_at")
            if expires <= observed:
                raise PriceError("Offer expiry must follow its observation")
        observations.append({
            **offer, "source_event_id": item["id"], "source_event_version": item["version"],
        })
    return page["cursor"], page["complete"], observations


def _retry_at(value, checked):
    if not value:
        return None
    if re.fullmatch(r"[0-9]{1,10}", value):
        return checked + timedelta(seconds=int(value))
    try:
        retry = parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return retry if retry.tzinfo is not None else None


def _utc_now():
    return datetime.now(timezone.utc)


def _utc_text(value):
    return value.isoformat().replace("+00:00", "Z")


def refresh(store, cohort_id, fetch_page=None, *, checked_at=None):
    """Record one refresh. A failed or interrupted attempt leaves the checkpoint in place."""
    if checked_at is not None and fetch_page is None:
        raise PriceError("Only a recorded delivery can supply its check time")
    clock = _utc_now
    if checked_at is not None:
        fixture_time = validation._timestamp(checked_at, "checked_at")
        clock = lambda: fixture_time
    key = _sql_text(cohort_id)
    attempt = f"'{uuid4()}'::uuid"
    checked_sql = _sql_text(_utc_text(clock()))
    job = json.loads(store._query(
        f"SELECT fastest_prices.begin_refresh({key}, {attempt}, {checked_sql}, "
        f"{'true' if fetch_page is None else 'false'});"
    ))
    if job["status"] == "deferred":
        return job

    cursor = job["cursor"]
    seen = {cursor}
    records = []
    config = job["config"]
    status = "failed"
    retry_at = None
    reason = None
    try:
        for _ in range(config["max_pages"]):
            page = _request(config["url"], cursor) if fetch_page is None else fetch_page(cursor)
            cursor, complete, received = _decode(page, clock())
            records.extend(received)
            if complete:
                status = "success"
                break
            status = "incomplete"
            if cursor in seen:
                raise PriceError("Seller feed repeated a pagination cursor")
            seen.add(cursor)
        else:
            reason = "request_quota"
    except RateLimited as error:
        reason = "rate_limited"
        retry_at = _retry_at(error.retry_after, clock())
    except (OSError, http.client.HTTPException):
        reason = "transport_error"
    except (PriceError, ValueError):
        reason = "invalid_delivery"

    retry_sql = _sql_text(retry_at.isoformat()) if retry_at else "NULL"
    completed_sql = _sql_text(_utc_text(clock()))
    result = json.loads(store._query(f"""
        SELECT fastest_prices.finish_refresh({key}, {attempt}, {completed_sql}, {_sql_text(status)},
            {_sql_text(cursor) if cursor else 'NULL'}, {_document(records if status == 'success' else [])},
            {retry_sql});
    """))
    return {**result, "reason": reason} if reason else result
