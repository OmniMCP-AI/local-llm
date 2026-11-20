import React, { useEffect, useState } from "react";
import { datedDisplayRate } from "./display-fx.mjs";
import { LocaleControls, useLocale } from "./locale";
import { priceCopy } from "./price-comparison-copy.mjs";

const dataRoute = "/api/price-comparison";

function Source({ locator }) {
  return /^https?:\/\//i.test(locator) ? <a href={locator}><bdi>{locator}</bdi></a> : <bdi>{locator}</bdi>;
}

function Money({ amount, currency, unknown }) {
  return amount == null ? unknown : <bdi dir="ltr">{amount} {currency}</bdi>;
}

function Offers({ price, copy, currency, locale }) {
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
          <th scope="col">{copy.date}</th><th scope="col">{copy.seller}</th><th scope="col">{copy.original}</th>
          {exchange && <th scope="col">{copy.display}</th>}
          <th scope="col">{copy.landed}</th><th scope="col">{copy.evidence}</th>
        </tr></thead><tbody>{price.offers.map((offer) =>
          <tr key={JSON.stringify([offer.observed_at, offer.seller, offer.listing_id, offer.kind])}>
            <th scope="row"><time dateTime={offer.observed_at}><bdi dir="ltr">{offer.observed_at}</bdi></time></th>
            <td><bdi>{offer.seller} / {offer.listing_id}</bdi><br /><small><bdi>{offer.kind} · {offer.freshness}</bdi></small></td>
            <td className="original-quote"><Money amount={offer.price} currency={offer.currency} unknown={copy.unknown} /></td>
            {exchange && <td className="display-quote"><bdi>{formatter.format(Number(offer.price) * fx.factor)}</bdi></td>}
            <td><Money amount={offer.landed_price} currency={offer.currency} unknown={copy.unknown} /></td>
            <td><Source locator={offer.source_locator} /><br /><small><bdi>{offer.review?.decision_id}</bdi></small></td>
          </tr>)}</tbody></table>
      </div>
    </>}
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
      <a className="wordmark" href="/">fastest.ai</a>
      <LocaleControls datedRatesOnly sourceCurrency={price?.currency} />
    </header>
    <div className="page-heading"><h1>{copy.title}</h1></div>
    {price ? <>
      {price.data_class === "illustrative" && <p className="price-example">{copy.example}</p>}
      <dl className="price-terms">
        <div><dt>{copy.market}</dt><dd data-market={price.market}><bdi>{price.market}</bdi></dd></div>
        <div><dt>{copy.destination}</dt><dd><bdi>{price.destination}</bdi></dd></div>
        <div><dt>{copy.scope}</dt><dd><bdi>{price.scope.id} · {price.scope.revision_id}</bdi></dd></div>
        <div><dt>{copy.condition}</dt><dd><bdi>{price.condition}</bdi></dd></div>
        <div><dt>{copy.release}</dt><dd><bdi>{price.release_id}</bdi> · <bdi>{price.authorization_decision_id}</bdi></dd></div>
      </dl>
      <p className="price-links"><a href={"/prices?" + query}>{copy.pinned}</a><a href={dataRoute + "?" + query}>{copy.exact}</a></p>
      <Offers price={price} copy={copy} currency={currency} locale={locale} />
      {query.has("goal") && <Decision decision={data.decision} copy={copy} />}
      {query.has("cost") && <Economics economics={data.economics} copy={copy} />}
    </> : <p role="status">{!data ? copy.loading : copy[data.status] ?? copy.unavailable}</p>}
    <footer><a href="/wiki/research/" hrefLang="en">{copy.research}</a></footer>
  </main>;
}
