export const FX_DATE = "2026-11-19";
export const FX_SOURCE = "https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html";
// Reference units per EUR from the ECB snapshot. Market quotes retain their source currency.
export const rates = {
  EUR: 1, USD: 1.0992, JPY: 175.84, CZK: 24.427, DKK: 7.4742, GBP: 0.83581, HUF: 369.43,
  PLN: 4.4170, RON: 5.3473, SEK: 11.1470, CHF: 0.9262, ISK: 137.20, NOK: 10.6475, TRY: 55.4737,
  AUD: 1.6378, BRL: 6.4765, CAD: 1.5719, CNY: 7.3280, HKD: 8.6239, IDR: 20073.10, ILS: 3.6149,
  INR: 102.5500, KRW: 1460.23, MXN: 20.7946, MYR: 4.5205, NZD: 1.9890, PHP: 70.014,
  SGD: 1.4176, THB: 37.268, ZAR: 18.9948,
};
export const supplementalRates = {
  TWD: { unitsPerUsd: 32.87, label: "Federal Reserve H.10", date: "2026-11-13", url: "https://fred.stlouisfed.org/series/DEXTAUS" },
  BDT: { unitsPerUsd: 124.6598, label: "Bangladesh Bank", url: "https://www.bb.org.bd/en/index.php/econdata/rfrexrate" },
  SAR: { unitsPerUsd: 3.75, label: "SAMA official peg", date: "2020-05-04", url: "https://www.sama.gov.sa/en-US/MediaCenter/News/Pages/news-557.aspx" },
};
export const hasReference = (code) => Object.hasOwn(rates, code) || Object.hasOwn(supplementalRates, code);

const ecb = { label: "ECB", date: FX_DATE, url: FX_SOURCE };

export function datedDisplayRate(from, to) {
  if (from === to) return { factor: 1, sources: [] };
  const fromSupplement = Object.hasOwn(supplementalRates, from) ? supplementalRates[from] : null;
  const toSupplement = Object.hasOwn(supplementalRates, to) ? supplementalRates[to] : null;
  const usable = (code, supplemental) => Object.hasOwn(rates, code) || Boolean(supplemental?.date);
  if (!usable(from, fromSupplement) || !usable(to, toSupplement)) return null;
  const sources = [fromSupplement, toSupplement].filter(Boolean);
  const useUSD = sources.length > 0;
  if (!useUSD || [from, to].some((code) => code !== "USD" && Object.hasOwn(rates, code))) {
    sources.unshift(ecb);
  }
  const amount = (code, supplement) => supplement?.unitsPerUsd ?? (useUSD ? rates[code] / rates.USD : rates[code]);
  return { factor: amount(to, toSupplement) / amount(from, fromSupplement), sources };
}
