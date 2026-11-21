import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { runInNewContext } from "node:vm";
import { test } from "node:test";

const html = execFileSync("python3", ["-c", `import sys
sys.path.insert(0, 'production')
from fastest_chart import chart_with_labels
print(chart_with_labels('<svg></svg>', left=10, right=90, start=0, end=100))`], { encoding: "utf8" });
const source = html.match(/<script data-chart-zoom-script>([\s\S]*?)<\/script>/)[1];

function chart() {
  const buttons = Object.fromEntries(["in", "out", "previous", "next", "reset"].map(action =>
    [action, { dataset: { chartZoom: action }, disabled: false, focus() {} }]));
  const makeMark = x => ({ style: {}, attributes: {}, querySelector: () => ({ getAttribute: () => String(x) }),
    setAttribute(name, value) { this.attributes[name] = value; } });
  const marks = [makeMark(10), makeMark(50), makeMark(90)];
  const line = { points: "10,100 90,0", getAttribute() { return this.points; },
    setAttribute(_, value) { this.points = value; } };
  const labels = ["start", "end"].map(value => ({ dataset: { chartX: value }, textContent: "" }));
  const svg = { querySelectorAll(selector) { return selector === ".chart-point" ? marks : selector === "polyline" ? [line] : labels; } };
  const root = { querySelector: () => svg, querySelectorAll: () => Object.values(buttons), addEventListener(_, handler) { this.click = handler; } };
  runInNewContext(source, { document: { currentScript: { parentElement: root } }, Intl, Date });
  return { root, buttons, marks, line, labels };
}

test("release SVG zoom clips the range, preserves visible marks, and resets independently", () => {
  const a = chart(), b = chart();
  const click = (fixture, action) => fixture.root.click({ target: { closest: () => fixture.buttons[action] } });
  click(a, "in");
  assert.equal(a.marks[0].style.visibility, "hidden");
  assert.equal(a.marks[1].style.visibility, "");
  assert.equal(a.marks[2].style.visibility, "hidden");
  assert.deepEqual(a.labels.map(label => label.textContent), ["25", "75"]);
  assert.equal(a.line.points, "10,75 90,25");
  assert.equal(b.line.points, "10,100 90,0");
  click(a, "reset");
  assert.equal(a.marks[0].style.visibility, "");
  assert.equal(a.line.points, "10,100 90,0");
});
