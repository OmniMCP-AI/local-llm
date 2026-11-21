# Used GPU provider access review

Reviewed 2026-11-22 for issue #54. No production provider response or daily
capture has been verified. The environment exposed no eBay, Amazon, JD or
price-feed credential variable names during this review. This does not prove
whether accounts or grants exist elsewhere. No prices below are observations.

| Provider | Candidate access and secondhand coverage | Retention, refresh and remaining action |
| --- | --- | --- |
| eBay | [Browse API](https://developer.ebay.com/api-docs/buy/static/api-browse.html) supports condition and buying-option refinements and item details. Its [application access token](https://developer.ebay.com/develop/api/buy/browse_api) uses client credentials; [production Buy API access](https://developer.ebay.com/api-docs/buy/static/buy-requirements.html) has eligibility and approval requirements. Actual used GPU listings and exact-variant matching were not verified with an account. | [API license](https://developer.ebay.com/support/api-license-agreement) requires displayed listing data to be at most six hours old, removal when no longer public, and separation from non-eBay content; some derivatives require express permission. Daily sampling alone does not satisfy the display freshness rule. Obtain the account, production scope and a written decision covering historical retention, derivatives, display and export before using this permanent-history publisher. |
| Amazon US | [Creators API](https://affiliate-program.amazon.com/creatorsapi/docs/en-us/onboarding/register-for-creators-api) requires a finally accepted Associates account and API credentials. [SearchItems](https://affiliate-program.amazon.com/creatorsapi/docs/en-us/api-reference/operations/search-items) describes `Any` as including new and used; [OffersV2](https://affiliate-program.amazon.com/creatorsapi/docs/en-us/api-reference/resources/offersV2) includes condition and merchant fields. Actual used GPU coverage, stable offer identity and delivery details remain unverified. | The US [IP license](https://affiliate-program.amazon.com/help/operating/policies) generally permits non-image content caching for up to 24 hours with refresh, and requires timestamps when less than hourly. It does not establish permission for this publisher's permanent history. Obtain account access and a specific retention/derivative grant, and review the target locale's terms. A comparison including Amazon prices has additional new/used display requirements. |
| JD.com | [JD Union/JOS](https://jos.jd.com/jdunion) documents an affiliate API and appkey route. The current platform and endpoint permissions must be confirmed for the chosen integration. Used GPU coverage, stable listing identity, delivery fields and a successful response remain unverified. | Applicable API terms, retention, historical derivatives, refresh quota and rights for the exact endpoint have not been established. Obtain JD Union application credentials and endpoint permissions, verify actual secondhand inventory, then document the applicable grant before collection into historical releases. |

The existing recurring adapter consumes an explicitly approved **direct seller**
cursor feed; it is not an eBay, Amazon or JD adapter. Marketplace access and
permission cannot be inferred from an illustrative fixture. Map only exact,
reviewed variants and preserve source event time independently of ingestion or
publication. If a provider omits an event date, do not substitute the check
time as a purported source event date. Obtain and retain a specific grant before
using source data in releases that persist after the provider's cache window.
