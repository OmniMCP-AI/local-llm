import assert from "node:assert/strict";
import { test } from "node:test";
import { catalogDocument } from "./catalog-card.mjs";
import { verifyCatalogScripts } from "./verify-catalog-html.mjs";

test("catalog review allows its locale controls and rejects injected scripts", () => {
  const page = catalogDocument({ title: "Example", release: "v1-1234567890abcdef", main: "<h1>Example</h1>" });
  assert.doesNotThrow(() => verifyCatalogScripts(page));
  assert.throws(() => verifyCatalogScripts(page.replace("<h1>Example</h1>", "<h1>Example</h1><script>alert(1)</script>")));
  assert.throws(() => verifyCatalogScripts(page.replace("const key =", "alert(1); const key =")));
  assert.throws(() => verifyCatalogScripts(page.replace("<script>", "<script src=\"https://malicious.example/x.js\">")));
});
