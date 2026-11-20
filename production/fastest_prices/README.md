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

Use the [illustrative bundle](../fixtures/synthetic-price-cohort.json) as the input contract. Before onboarding a live source, an editor records permission to collect, retain, display and export the exact cohort, and records a separate aggregation decision. The private authorization record points to retained approval outside the public payload. An automated collector can submit reviewed captures through the same contract. The repository currently ships the reviewed file entry point.

Register the seller aliases and use the same canonical listing ID for recurring appearances of a listing. Supply the exact market, destination, scope and condition on every observation. Each row needs a source locator and a review decision. Asking prices, bids, sales, MSRP and historical reports retain their separate price types. A capture records its own timestamp and success or failure independently of each observation timestamp. Use a successful capture with an empty list when the feed check returned no rows, and a failed capture with an empty list when the check failed.

Tax and shipping each record their basis and a nullable amount. Included amounts are already part of the quote. Use `excluded` with a known amount for a charge added to the quote, `not_applicable` when the charge does not apply, and `unknown` when the basis is unknown. Use a null amount when the amount is missing. Preserve stock, confirmation and discount eligibility as recorded in the reviewed source.

A bundle appends atomically. Replays of the same approval and capture IDs return the stored values. An amended capture needs a new ID. A changed cohort policy needs a new cohort ID. A dated release pins the approved policy, calculation method and capture cutoff. An additional eligible capture can create a new release for the same window. Older release IDs keep their original cutoff.

## Read the history

Days use UTC. The daily table distinguishes successful coverage, gaps in comparable offers, failed checks and unchecked days. The result discloses the last successful check, latest attempt and quote age at the release date. The illustrative policy marks quotes and checks older than two days as stale.

The latest observation for each canonical seller, listing, UTC day and price type supplies the displayed quote. When an observation timestamp ties, the latest capture and then the last row in that capture decide which record is displayed. Seller aliases resolve before deduplication. Each quote identifies whether it is the latest record for that listing and price type within the release window. Historical samples use the lowest eligible landed asking price per seller, scope and day. Eligibility requires a seller-confirmed, in-stock, unconditional quote whose tax and shipping can be resolved. The result offers the individual dated quotes even when the range is withheld.

Method `seller-day-landed-asking-v1` uses linear interpolation for the quartiles and median. The illustrative policy requires three samples and two distinct sellers. The direct seller cannot meet the second threshold. Aggregation denied by the source policy withholds the counts and range.

## Read-only access and withdrawal

The schema owner can grant a serving role access to the rights-filtered read function.

```sql
GRANT USAGE ON SCHEMA fastest_prices TO fastest_price_reader;
GRANT EXECUTE ON FUNCTION fastest_prices.read_release(uuid) TO fastest_price_reader;
```

Run `python3 -m fastest_prices withdraw COHORT_ID "editorial reason"` as the publisher to withdraw approval. Subsequent reads of affected release IDs emit a withdrawal notice. A static host must replace or remove existing exports and invalidate cached copies.

From `production/`, run `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_prices.py'` for the PostgreSQL, CLI, and rendering checks. The tests use an isolated database over a temporary local socket.
