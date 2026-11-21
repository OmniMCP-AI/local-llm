import React, { useEffect, useState } from "react";
import { datedDisplayRate } from "./display-fx.mjs";
import { LocaleControls, useLocale } from "./locale";
import { priceCopy } from "./price-comparison-copy.mjs";
import { SiteName } from "./site-name";

const dataRoute = "/api/price-comparison";

function Source({ locator }) {
  return /^https?:\/\//i.test(locator) ? <a href={locator}><bdi>{locator}</bdi></a> : <bdi>{locator}</bdi>;
}

function Money({ amount, currency, unknown }) {
  return amount == null ? unknown : <bdi dir="ltr">{amount} {currency}</bdi>;
}

function offerStatus(offer, price, now) {
  const adapter = price.adapter_status;
  const expiry = Date.parse(offer.expires_at);
  if (offer.availability === "expired" || (Number.isFinite(expiry) && expiry <= now)) return "expired";
  if (offer.latest_for_listing === false || offer.availability === "historical") return "historical";
  const day = 86_400_000;
  const currentAge = Math.floor(now / day) - Math.floor(Date.parse(offer.observed_at) / day);
  const aged = Number.isFinite(price.stale_after_days) && currentAge > price.stale_after_days;
  if (offer.freshness === "stale" || offer.availability === "stale" || adapter === "stale" || aged) return "stale";
  if (["failed", "incomplete", "no_success"].includes(adapter) || offer.availability === "incomplete") return "incomplete";
  if (adapter === "fresh" && offer.availability === "available" && Number.isFinite(expiry)) return "availableAtRelease";
  return "availabilityUnknown";
}

function ObservationTime({ value, unknown }) {
  return value ? <time dateTime={value}><bdi dir="ltr">{value}</bdi></time> : unknown;
}

function Offers({ price, copy, currency, locale, now }) {
  const fx = datedDisplayRate(price.currency, currency);
  const exchange = Boolean(fx && fx.sources.length);
  const formatter = exchange && new Intl.NumberFormat(locale, { style: "currency", currency, currencyDisplay: "code" });
  return <section aria-labelledby="released-offers">
    <h2 id="released-offers">{copy.offers}</h2>
    {price.offers.length === 0 ? <p>{copy.empty}</p> : <>
      {!fx && <p role="status">{copy.noFX}</p>}
      {exchange && <p>{copy.fx} · {fx.sources.map(({ label, date, url }, index) =>
        <React.Fragment key={url}>{index > 0 && " / "}<a href={url}><bdi dir="ltr">{label} · {date}</bdi></a></React.Fragment>)}</p>}
      <div className="table-wrap" role="region" aria-labelledby="released-offers" tabIndex={0}>
        <table><thead><tr>
          <th scope="col">{copy.date}</th><th scope="col">{copy.seller}</th><th scope="col">{copy.availabilityLabel}</th>
          <th scope="col">{copy.original}</th>
          {exchange && <th scope="col">{copy.display}</th>}
          <th scope="col">{copy.landed}</th><th scope="col">{copy.evidence}</th>
        </tr></thead><tbody>{price.offers.map((offer) =>
          <tr key={JSON.stringify([offer.observed_at, offer.seller, offer.listing_id, offer.kind])}>
            <th scope="row"><ObservationTime value={offer.observed_at} unknown={copy.unknown} />
              <br /><small>{copy.ageDays} · {offer.age_days ?? copy.unknown}</small></th>
            <td><bdi>{offer.seller} / {offer.listing_id}</bdi><br /><small><bdi>{offer.kind}</bdi></small></td>
            <td>{copy[offerStatus(offer, price, now)]}
              <br /><small>{copy.expiry} · <ObservationTime value={offer.expires_at} unknown={copy.unknown} /></small></td>
            <td className="original-quote"><Money amount={offer.price} currency={offer.currency} unknown={copy.unknown} /></td>
            {exchange && <td className="display-quote"><bdi>{formatter.format(Number(offer.price) * fx.factor)}</bdi></td>}
            <td><Money amount={offer.landed_price} currency={offer.currency} unknown={copy.unknown} /></td>
            <td><Source locator={offer.source_locator} /><br /><small><bdi>{offer.review?.decision_id}</bdi></small></td>
          </tr>)}</tbody></table>
      </div>
    </>}
  </section>;
}

function References({ price, copy }) {
  return <section aria-labelledby="price-references">
    <h2 id="price-references">{copy.references}</h2>
    {price.references.length === 0 ? <p>{copy.referencesEmpty}</p> : <>
      <p>{copy.referenceSource} · <a href={price.source_locator}><bdi>{price.source_name}</bdi></a></p>
      <div className="table-wrap" role="region" aria-labelledby="price-references" tabIndex={0}>
        <table><thead><tr>
          <th scope="col">{copy.sourceDate}</th><th scope="col">{copy.marketplace}</th><th scope="col">{copy.postCoupon}</th>
        </tr></thead><tbody>{price.references.map((reference, index) =>
          <tr key={index}>
            <th scope="row"><ObservationTime value={reference.observed_on} unknown={copy.unknown} /></th>
            <td><bdi>{reference.marketplace}</bdi></td>
            <td className="original-quote"><Money amount={reference.price} currency={price.currency} unknown={copy.unknown} /></td>
          </tr>)}</tbody></table>
      </div>
      <p>{copy.referenceTerms}</p>
    </>}
  </section>;
}

function Coverage({ price, copy }) {
  const days = price.days ?? [];
  if (days.length === 0) return null;
  return <section aria-labelledby="price-history">
    <h2 id="price-history">{copy.history}</h2>
    <div className="table-wrap" role="region" aria-labelledby="price-history" tabIndex={0}>
      <table><thead><tr><th scope="col">{copy.date}</th><th scope="col">{copy.collection}</th></tr></thead>
        <tbody>{days.map(({ date, status }) => <tr key={date}>
          <th scope="row"><ObservationTime value={date} unknown={copy.unknown} /></th>
          <td>{copy[status] ?? copy.unknown}</td>
        </tr>)}</tbody>
      </table>
    </div>
  </section>;
}

function Decision({ decision, copy }) {
  return <section><h2>{copy.ranks}</h2>
    {decision ? <>
      <p><bdi dir="ltr">{decision.release_id}</bdi></p>
      <ol>{decision.rows.map((row) => <li key={row.id}><bdi>{row.name} · {row.status}</bdi></li>)}</ol>
    </> : <p>{copy.rankMissing}</p>}
  </section>;
}

function Economics({ economics, copy }) {
  return <section><h2>{copy.cost}</h2>
    {economics && <>
      <p><bdi dir="ltr">{economics.revision}</bdi>{economics.estimate_kind === "illustrative" && <> · {copy.costExample}</>}</p>
      <p>{copy.payback}</p>
      <ul>{economics.payback.map(({ option, baseline, payback_months, status }) =>
        <li key={option + "/" + baseline}><bdi dir="ltr">{option} / {baseline}</bdi> · {payback_months == null
          ? copy.unknown : <bdi dir="ltr" data-payback={payback_months}>{payback_months}</bdi>} <small><bdi>{status}</bdi></small></li>)}</ul>
    </>}
    {!economics?.payback.some(({ payback_months }) => payback_months != null) && <p>{copy.costMissing}</p>}
  </section>;
}

export function PriceCohorts({ cohorts, releaseId, copy }) {
  if (!cohorts?.length) return null;
  return <nav className="price-cohorts" aria-labelledby="price-cohorts">
    <h2 id="price-cohorts">{copy.cohorts}</h2>
    <ul>{cohorts.map((cohort) => {
      const references = cohort.dataClass === "reviewed_citations";
      const terms = references ? [cohort.source] : [cohort.destination, cohort.condition];
      return <li key={cohort.releaseId}>
        <a href={"/prices?release=" + cohort.releaseId} aria-current={cohort.releaseId === releaseId ? "page" : undefined}>
          <strong><bdi>{cohort.scope.id}</bdi></strong>
          <span><bdi>{cohort.market}</bdi> · <bdi>{cohort.currency}</bdi> · <ObservationTime value={cohort.asOf} /></span>
          <small>{references ? copy.references : copy.offers}
            {terms.filter(Boolean).map((term, index) => <React.Fragment key={index}> · <bdi>{term}</bdi></React.Fragment>)}
          </small>
        </a>
      </li>;
    })}</ul>
  </nav>;
}

export function HostedPrices() {
  const { language, locale, currency } = useLocale();
  const copy = priceCopy(language);
  const [data, setData] = useState(null);
  const query = new URLSearchParams(location.search);
  useEffect(() => {
    document.title = copy.title + " · fastest.ai";
  }, [copy.title]);
  useEffect(() => {
    const abort = new AbortController();
    fetch(dataRoute + location.search, { signal: abort.signal })
      .then((response) => response.json())
      .then(setData)
      .catch(() => { if (!abort.signal.aborted) setData({ status: "unavailable" }); });
    return () => abort.abort();
  }, []);
  const price = data?.price;
  if (data?.releaseId) query.set("release", data.releaseId);
  return <main className="main-shell hosted-prices">
    <header className="price-toolbar">
      <a className="wordmark" href="/"><SiteName /></a>
      <LocaleControls datedRatesOnly sourceCurrency={price?.currency} />
    </header>
    <div className="page-heading"><h1>{copy.title}</h1></div>
    <PriceCohorts cohorts={data?.cohorts} releaseId={data?.releaseId} copy={copy} />
    {price ? <PriceRelease data={data} copy={copy} currency={currency} locale={locale} query={query} /> : <p role="status">{!data ? copy.loading : copy[data.status] ?? copy.unavailable}</p>}
    <footer><a href="/wiki/research/" hrefLang="en">{copy.research}</a></footer>
  </main>;
}

export function PriceRelease({ data, query, copy, currency, locale, now = new Date() }) {
  const { price } = data;
  const citation = price.data_class === "reviewed_citations";
  return <>
    {price.data_class === "illustrative" && <p className="price-example">{copy.example}</p>}
    <dl className="price-terms">
      <div><dt>{copy.market}</dt><dd data-market={price.market}><bdi>{price.market}</bdi></dd></div>
      <div><dt>{copy.destination}</dt><dd><bdi>{price.destination ?? copy.unknown}</bdi></dd></div>
      <div><dt>{copy.scope}</dt><dd><bdi>{price.scope.id} · {price.scope.revision_id}</bdi></dd></div>
      <div><dt>{copy.condition}</dt><dd><bdi>{price.condition ?? copy.unknown}</bdi></dd></div>
      <div><dt>{copy.asOf}</dt><dd><ObservationTime value={price.as_of} unknown={copy.unknown} /></dd></div>
      {!citation && <>
        <div><dt>{copy.collection}</dt><dd>{copy[price.adapter_status] ?? copy.unknown}</dd></div>
        <div><dt>{copy.lastSuccess}</dt><dd><ObservationTime value={price.last_success_at} unknown={copy.unknown} />
          {price.last_success_age_days != null && <><br /><small>{copy.ageDays} · {price.last_success_age_days}</small></>}</dd></div>
      </>}
      <div><dt>{copy.release}</dt><dd><bdi>{price.release_id}</bdi> · <bdi>{price.authorization_decision_id}</bdi></dd></div>
    </dl>
    <p className="price-links"><a href={"/prices?" + query}>{copy.pinned}</a><a href={dataRoute + "?" + query}>{copy.exact}</a></p>
    {citation ? <References price={price} copy={copy} /> : <>
      <Offers price={price} copy={copy} currency={currency} locale={locale} now={now} />
      <Coverage price={price} copy={copy} />
      {query.has("goal") && <Decision decision={data.decision} copy={copy} />}
      {query.has("cost") && <Economics economics={data.economics} copy={copy} />}
    </>}
  </>;
}
