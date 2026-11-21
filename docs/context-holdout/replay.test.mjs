import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

test("replays both frozen releases on the two whole-source families", () => {
  const replay = fileURLToPath(new URL("./replay.mjs", import.meta.url));
  const report = JSON.parse(execFileSync(process.execPath, [replay], { encoding: "utf8" }));
  assert.equal(report.scope, "operator-only-holdout");
  assert.deepEqual(report.versions.map(({ calibration }) => [calibration.rulesVersion, calibration.ruleDigest]), [
    [1, "2940be1a7b631482da34a22f35044f7f6a88a99afe43258a17c628cf9471e037"],
    [2, "7ef3305747a2713b8ad15ca436a521c0e101ec915de2b365496567986aea0c62"],
  ]);
  for (const { calibration, predictions } of report.versions) {
    assert.deepEqual(calibration.heldOut, ["holdout-droid-llm-zh", "holdout-splitwise-v2"]);
    assert.equal(calibration.heldOutFamilies, 2);
    assert.equal(calibration.development, 0);
    assert.equal(calibration.researchRelease, null);
    assert.equal(calibration.automaticPromotion, false);
    assert.equal(calibration.facets.dimension.subjects, 18);
    assert.ok(predictions.some(({ subject, expected, locator }) =>
      subject === "splitwise-future-memory" && expected.includes("projection") && locator.endsWith("#S7.p5.1")));
  }
});
