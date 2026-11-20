import assert from "node:assert/strict";
import test from "node:test";
import { onRequestGet } from "./functions/api/price-comparison.js";

const releaseId = "de47baaf-b7e4-4705-a730-9db61e664110";
const origin = "https://release.fastest.example";
const market = { market: "US", destination: "US-CA, ZIP 95814", currency: "USD", condition: "new" };
const price = {
  result_type: "regional-price-cohort", schema_version: 1, status: "published",
  release_id: releaseId, authorization_decision_id: "review-1",
  ...market, scope: { kind: "whole_build", id: "apple-m4", revision_id: "m4-rev" },
  data_class: "authorized_observations",
  offers: [{ listing_id: "a", price: "240.00", currency: "USD" }],
};

function request(query = {}, env = {}, headers) {
  const url = new URL("https://fastest.example/api/price-comparison");
  url.search = new URLSearchParams(query);
  return onRequestGet({ request: new Request(url, { headers }), env });
}

test("the hosted edge has a missing default with no demo or unknown price", async () => {
  const response = await request();
  assert.equal(response.status, 404);
  assert.equal(response.headers.get("Cache-Control"), "private, no-store");
  assert.deepEqual(await response.json(), { status: "missing", releaseId: null });
});

test("the edge preserves original offers, exact market, pinned release and decision independently of locale", async (t) => {
  const id = "a".repeat(64);
  const revision = "v1-" + "b".repeat(64);
  const goalPath = `/goals/${id}.json?entry=budget`;
  const costPath = `/costs.json?scenario=illustrative&revision=${revision}`;
  const decision = { release_id: id, market, rows: [{ id: "apple-m4", build_revision: "m4-rev", metrics: { budget: { release_id: releaseId } } }] };
  const economics = { revision, estimate_kind: "illustrative", payback: [{ payback_months: "18.18" }] };
  const paths = new Map([
    [`/price-releases/${releaseId}/prices.json`, price],
    [goalPath, decision],
    ["/costs.json?scenario=illustrative", economics],
  ]);
  const fetchMock = t.mock.method(globalThis, "fetch", async (url, options) => {
    assert.equal(url.origin, origin);
    assert.equal(options.cache, "no-store");
    assert.equal(options.redirect, "error");
    assert.equal(options.headers, undefined);
    return Response.json(paths.get(url.pathname + url.search));
  });
  const env = { FASTEST_RELEASE_ORIGIN: origin, FASTEST_PRICE_RELEASE: releaseId };
  const query = { goal: goalPath, cost: costPath };
  const first = await request(query, env, { "CF-Connecting-IP": "192.0.2.20", "Accept-Language": "zh-Hant" });
  const second = await request({ ...query, release: releaseId }, env, { "Accept-Language": "ar-SA" });
  assert.equal(first.status, 200);
  assert.equal(second.status, 200);
  const expected = { status: "published", releaseId, price, decision, economics };
  assert.deepEqual(await first.json(), expected);
  assert.deepEqual(await second.json(), expected);
  assert.equal(fetchMock.mock.callCount(), 6);

  const other = await request({ goal: "https://elsewhere.example" }, env);
  assert.equal(other.status, 400);
  decision.market = { ...market, destination: "US-NY" };
  const mismatched = await request(query, env);
  assert.equal((await mismatched.json()).decision, null);
});

test("a withdrawal from the origin removes offers, decisions and economics immediately", async (t) => {
  const env = { FASTEST_RELEASE_ORIGIN: origin };
  const fetchMock = t.mock.method(globalThis, "fetch", async () =>
    Response.json({ ...price, status: "withdrawn" }, { status: 410 }));
  const response = await request({ release: releaseId }, env);
  assert.equal(response.status, 410);
  assert.deepEqual(await response.json(), { status: "withdrawn", releaseId });
  assert.equal(fetchMock.mock.callCount(), 1);
});

test("a dated display FX basis documents each needed source and currency pairs can be missing", async () => {
  const { datedDisplayRate } = await import("./display-fx.mjs");
  assert.deepEqual(datedDisplayRate("USD", "USD"), { factor: 1, sources: [] });
  assert.equal(datedDisplayRate("USD", "TWD").factor, 32.87);
  assert.equal(datedDisplayRate("USD", "SAR").factor, 3.75);
  const yen = datedDisplayRate("TWD", "JPY");
  assert.deepEqual(yen.sources.map(({ date }) => date), ["2026-11-19", "2026-11-13"]);
  assert.equal(datedDisplayRate("USD", "BDT"), null);
  assert.equal(datedDisplayRate("CHF", "AFN"), null);
});

test("the Pages middleware sends only a supported language hint on private HTML", async (t) => {
  const { onRequestGet: middleware } = await import("./functions/_middleware.js");
  const { languages, resolveLanguage } = await import("./locale-settings.mjs");
  const { priceCopy } = await import("./price-comparison-copy.mjs");
  class Rewriter {
    on(selector, handler) {
      assert.equal(selector, "html");
      this.handler = handler;
      return this;
    }

    transform(response) {
      this.handler.element({ setAttribute: (name, value) => { this.hint = [name, value]; } });
      assert.equal(this.hint[0], "data-visitor-language");
      return response.text().then((body) => new Response(
        body.replace("<html", `<html data-visitor-language="${this.hint[1]}"`), response,
      ));
    }
  }
  globalThis.HTMLRewriter = Rewriter;
  t.after(() => { delete globalThis.HTMLRewriter; });
  const get = (country) => {
    const request = new Request("https://fastest.example/", { headers: { "CF-Connecting-IP": "192.0.2.10" } });
    Object.defineProperty(request, "cf", { value: { country } });
    return middleware({
      request,
      env: { ASSETS: { fetch: () => Response.json({ paths: [] }) } },
      next: async () => new Response('<!doctype html><html lang="en"></html>', {
        headers: { "Content-Type": "text/html", "Cache-Control": "public, max-age=86400", ETag: "public" },
      }),
    });
  };
  for (const [country, browsers, expected] of [
    ["TW", ["ar-SA"], "zh-Hant"],
    ["CN", ["zh-Hant"], "zh-Hans"],
    ["HK", ["nl", "zh-HK", "ar"], "zh-Hant"],
    ["MO", ["xx", "zh-Hans-MO", "ar"], "zh-Hans"],
    ["MO", ["zh-MO"], "zh-Hant"],
    ["ZZ", ["ru", "ar-SA"], "ar"],
    ["ZZ", ["ru", "nl"], "en"],
  ]) {
    const response = await get(country);
    assert.equal(response.headers.get("Cache-Control"), "private, no-store");
    assert.equal(response.headers.get("ETag"), null);
    const html = await response.text();
    assert.doesNotMatch(html, /192\.0\.2\.10/);
    const hint = html.match(/data-visitor-language="([^"]+)"/)?.[1];
    assert.equal(resolveLanguage(null, hint, browsers), expected);
    assert.equal(resolveLanguage("de", hint, browsers), "de");
  }
  assert.equal(languages.ar.direction, "rtl");
  assert.equal(new Set(Object.keys(languages).map((language) => priceCopy(language).title)).size, 10);
});

test("localized price release displays current expiry and pinned collection gaps", async () => {
  const { build } = await import("esbuild");
  const { createRequire } = await import("node:module");
  const { priceCopy } = await import("./price-comparison-copy.mjs");
  const { outputFiles: [{ text }] } = await build({
    stdin: { contents: `
      import React from "react";
      import { renderToStaticMarkup } from "react-dom/server";
      import { PriceRelease } from "./price-comparison.jsx";
      export default function render(props) { return renderToStaticMarkup(<PriceRelease {...props} />); }
    `, loader: "jsx", resolveDir: process.cwd() },
    bundle: true, platform: "node", format: "cjs", packages: "external", write: false,
  });
  const loaded = { exports: {} };
  new Function("module", "require", text)(loaded, createRequire(import.meta.url));
  const props = {
    data: { price: { ...price, adapter_status: "stale", as_of: "2026-11-10",
      last_success_at: "2026-11-08T12:00:00Z", last_success_age_days: 2,
      offers: [
        { ...price.offers[0], kind: "asking", seller: "Fixture seller", freshness: "fresh",
          observed_at: "2026-11-08T12:00:00Z", age_days: 2, availability: "available",
          expires_at: "2026-11-30T00:00:00Z", landed_price: "250.00", source_locator: "fixture/price" },
        { ...price.offers[0], listing_id: "b", kind: "asking", seller: "Fixture seller", freshness: "fresh",
          observed_at: "2026-11-07T12:00:00Z", age_days: 3, availability: "available",
          expires_at: "2026-11-20T00:00:00Z", source_locator: "fixture/expired" },
      ], days: [{ date: "2026-11-09", status: "capture_failed" }, { date: "2026-11-10", status: "not_checked" }],
    } }, query: new URLSearchParams(), currency: "USD",
  };
  for (const [language, locale, labels] of [
    ["en", "en", ["Collection status", "Stale", "Expired", "Capture failed", "Not checked"]],
    ["zh-Hant", "zh-TW", ["收集狀態", "已過時", "已到期", "收集失敗", "未查詢"]],
  ]) {
    const html = loaded.exports.default({
      ...props, copy: priceCopy(language), locale, now: new Date("2026-11-21T00:00:00Z"),
    });
    for (const label of [...labels, "2026-11-10", "2026-11-20T00:00:00Z", "250.00 USD"]) assert.ok(html.includes(label), label);
    assert.doesNotMatch(html, /Available at release|當時有貨/);
  }
  props.data.price.adapter_status = "fresh";
  props.data.price.stale_after_days = 3;
  const pinned = loaded.exports.default({
    ...props, copy: priceCopy("en"), locale: "en", now: new Date("2026-11-21T00:00:00Z"),
  });
  assert.match(pinned, /Fresh at release/);
  assert.match(pinned, /Stale/);
  assert.doesNotMatch(pinned, /Available at release/);
});
