# Regional prices

A dated release captures one reviewed seller or feed, market, delivery destination, original currency, condition and exact SKU or whole-build revision. The included bundle uses a fictional direct seller and an illustrative US delivery destination. A seller/feed rights decision and live capture are required for a release with real observations.

## Run the illustrative cohort

From `production/`, use Python 3.11+, PostgreSQL 13+, and `psql`. Set `FASTEST_DATABASE_URL` to a writable database using a libpq connection string. Keep credentials in the libpq password file or service configuration.

```sh
export FASTEST_DATABASE_URL='dbname=fastest_release'
python3 -m fastest_prices migrate
cohort_id=$(python3 -m fastest_prices ingest fixtures/synthetic-price-cohort.json)
release_id=$(python3 -m fastest_prices publish "$cohort_id" 2026-11-01 2026-11-04)
python3 -m fastest_prices artifact "$release_id" prices.md
python3 -m fastest_prices artifact "$release_id" prices.html
python3 -m fastest_prices artifact "$release_id" prices.json
```

The HTML and Markdown link to their companions by relative path. Keep all three files under the same release directory when serving a static export. The Markdown front matter pins its typed result by release ID and SHA-256. The typed result retains exact decimal strings in the original currency and explicit nulls. The HTML timeline uses the same rows as the dated quote table.

## Record a reviewed source

Use the [illustrative bundle](../fixtures/synthetic-price-cohort.json) as the input contract. Before onboarding a live source, an editor records permission to collect, retain, display and export the exact cohort, and records a separate aggregation decision. The private authorization record points to retained approval outside the public payload. The recurring seller adapter uses the same reviewed cohort and observation contract.

Register the seller aliases and use the same canonical listing ID for recurring appearances of a listing. Supply the exact market, destination, scope and condition on every observation. Each row needs a source locator and a review decision. Asking prices, bids, sales, MSRP and historical reports retain their separate price types. A capture records its own timestamp and success or failure independently of each observation timestamp. Use a successful capture with an empty list when the feed check returned no rows, and a failed capture with an empty list when the check failed.

Tax and shipping each record their basis and a nullable amount. Included amounts are already part of the quote. Use `excluded` with a known amount for a charge added to the quote, `not_applicable` when the charge does not apply, and `unknown` when the basis is unknown. Use a null amount when the amount is missing. Preserve stock, confirmation and discount eligibility as recorded in the reviewed source.

A bundle appends atomically. Replays of the same approval and capture IDs return the stored values. An amended capture needs a new ID. A changed cohort policy needs a new cohort ID. A dated release pins the approved policy, calculation method and capture cutoff. An additional eligible capture can create a new release for the same window. Older release IDs keep their original cutoff.

## Refresh one authorized seller feed

Register the reviewed cohort and bind it to an approved HTTPS endpoint and
request budget. The example endpoint is a placeholder. Use a private file for
the approved cohort and provide an optional bearer token through
`FASTEST_PRICE_FEED_TOKEN`.

```sh
python3 -m fastest_prices migrate
cohort_id=$(python3 -m fastest_prices approve approved-cohort.json)
python3 -m fastest_prices register-refresh "$cohort_id" approved-feed.json
python3 -m fastest_prices refresh "$cohort_id"
```

The configuration file contains these fields.

```json
{
  "url": "https://seller.example.test/reviewed-prices",
  "minimum_interval_seconds": 300,
  "max_pages": 3
}
```

The adapter requests the fixed path over HTTPS and passes the opaque
checkpoint as a `cursor` query parameter when one exists. A feed page
contains `cursor` (the checkpoint after the page), `complete` (a boolean),
and `observations` (an array). Each observation has an `id` stable across
edits, a positive integer `version`, and an `offer` with the same fields as a
reviewed bundle observation plus an explicit UTC `expires_at` or null.
A completed page with an empty array confirms a check with no new observations.
The feed can return prior deliveries unchanged and a higher version for an edit.

Call `refresh` once for each authorized collection window. It enforces the
configured per-run page limit, the minimum interval between attempts, and
`Retry-After` on HTTP 429. It reports `deferred` and the next allowed check
when a job is too early. Each attempt starts with an incomplete record.
Observations and the new cursor commit together after the final page is
validated. After a failure or interruption the next attempt resumes from the
last completed cursor. Repeated event versions are idempotent and conflicting
payloads for an existing version abort the attempt. The command records a
capture. Use `publish` to pin the reviewed window afterward.

Live requests require a cohort classified as `authorized_observations`.
The test replays a fictional direct seller through the same capture service
with a recorded transport. There is no live endpoint or periodic job
configured in this repository.

## Read the history

Days use UTC. The daily table distinguishes successful coverage, gaps in comparable offers, failed checks and unchecked days. The result discloses the last successful check, latest attempt and quote age at the release date. The illustrative policy marks quotes and checks older than two days as stale.

The latest observation for each canonical seller, listing, UTC day and price type supplies the displayed quote. When an observation timestamp ties, the latest capture and then the last row in that capture decide which record is displayed. Seller aliases resolve before deduplication. Each quote identifies whether it is the latest record for that listing and price type within the release window. Historical samples use the lowest eligible landed asking price per seller, scope and day. Eligibility requires a seller-confirmed, in-stock, unconditional quote whose tax and shipping can be resolved. The result offers the individual dated quotes even when the range is withheld. Recurring captures use method `seller-day-landed-asking-v2`. The newest event version known to the pinned release supplies the dated quote. The coverage table shows interrupted refreshes alongside failed and unchecked days. The offer table retains observed stock and price, with separate availability at the end of the release’s UTC date. A quote needs a known expiry beyond that date and fresh, complete coverage to appear as available.

Method `seller-day-landed-asking-v1` uses linear interpolation for the quartiles and median. The illustrative policy requires three samples and two distinct sellers. The direct seller cannot meet the second threshold. Aggregation denied by the source policy withholds the counts and range.

## Read-only access and withdrawal

The schema owner can grant a serving role access to the rights-filtered read function.

```sql
GRANT USAGE ON SCHEMA fastest_prices TO fastest_price_reader;
GRANT EXECUTE ON FUNCTION fastest_prices.read_release(uuid) TO fastest_price_reader;
```

Run `python3 -m fastest_prices withdraw COHORT_ID "editorial reason"` as the publisher to withdraw approval. Subsequent reads of affected release IDs emit a withdrawal notice. A static host must replace or remove existing exports and invalidate cached copies.

From `production/`, run `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_prices.py'` for the PostgreSQL, CLI, and rendering checks. The tests use an isolated database over a temporary local socket.

## Hosted comparison

The Pages build serves the localized comparison at `/prices`. Set
`FASTEST_RELEASE_ORIGIN` in Pages to the HTTPS origin of
`python3 -m fastest_release serve`. The origin reads each pinned UUID at
`/price-releases/UUID/prices.json` using the schema-restricted database reader.
Keep the database connection details at the origin. Set `FASTEST_PRICE_RELEASE`
to the reviewed UUID to make it available at the unpinned entry point. A shared
`/prices?release=UUID` link retains its release. With no configured release,
the entry point shows the missing state.

Add `goal` and `cost` URL parameters for optional decision and economics
context. Use the exact same-origin paths from the release service, including
the decision selection and cost scenario parameters. URL-encode each path
as the value of the enclosing parameter.

- `goal=/goals/DECISION_SHA256.json?entry=budget` shows the existing result
  order only for an exact market, currency, destination and condition match
  and when the decision used this whole-build price release for that revision.
- `cost=/costs.json?scenario=evidence&revision=v1-SCENARIO_SHA256` shows the
  pinned scenario's break-even values. The values use that scenario's own
  inputs and units. The evidence scenario reports unavailable when inputs
  are missing.

An illustrative cohort can be pinned explicitly against a test origin. The
comparison labels the fictional seller and quotes. Each original amount
keeps its decimal string and source currency. The selected display currency
uses the dated reference rates listed beside the table, or shows the original
currency when no dated rate covers the currency pair. A withdrawn price
release returns a notice in place of the offers on each subsequent read.
