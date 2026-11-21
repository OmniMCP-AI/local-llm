import assert from "node:assert/strict";
import { catalogDocument } from "./catalog-card.mjs";

// Review pages use the same fixed locale controller. Derive the expected bytes
// from the renderer so that no other inline or external script is permitted.
const template = catalogDocument({ title: "Verification", release: "v1-0000000000000000", main: "" });
const trustedScript = template.match(/<script>[\s\S]*?<\/script>/)?.[0];
assert.ok(trustedScript);

export function verifyCatalogScripts(html, path) {
  const index = html.indexOf(trustedScript);
  assert.notEqual(index, -1, path);
  const rest = html.slice(0, index) + html.slice(index + trustedScript.length);
  assert.doesNotMatch(rest, /<script\b/i, path);
}

export const catalogNavigationLinks = [...template.match(/<nav class="profile-nav"[^>]*>([\s\S]*?)<\/nav>/)[1]
  .matchAll(/href="(\/[^\"]*)"/g)].map(([, href]) => href);
