import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { DatabaseSync } from "node:sqlite";
import test from "node:test";
import { Client } from "pg";
import { onRequestGet, onRequestPost } from "./functions/api/feedback.js";

import { withLocalPages } from "./pages-test-server.mjs";

const endpoint = "https://fastest.example/api/feedback";
const note = { category: "correction", message: "Private benchmark correction" };

test("public issue handoff sends only a fixed form selection to GitHub", async () => {
  const { publicIssueHref } = await import("./public-issue.mjs");
  const origin = "https://github.com/OmniMCP-AI/local-llm";
  const templates = new URL("../../../.github/ISSUE_TEMPLATE/", import.meta.url);
  for (const [category, template] of [["missing", "benchmark-request.yml"], ["correction", "result-correction.yml"]]) {
    assert.equal(publicIssueHref(category), origin + "/issues/new?template=" + template);
    assert.match(await readFile(new URL(template, templates), "utf8"), /This issue will be public/);
  }
  for (const category of ["", "confusing", "other", "constructor", "?receipt=private&token=private"]) {
    assert.equal(publicIssueHref(category), origin + "/issues/new/choose");
  }
});

function d1(database) {
  return {
    prepare(sql) {
      return {
        bind(...params) {
          const statement = database.prepare(sql);
          return { all: () => statement.all(...params), first: () => statement.get(...params) };
        },
      };
    },
    async batch(statements) {
      database.exec("BEGIN");
      try {
        const results = statements.map((statement) => ({ success: true, results: statement.all() }));
        database.exec("COMMIT");
        return results;
      } catch (error) {
        database.exec("ROLLBACK");
        throw error;
      }
    },
  };
}

function submit(env, payload, headers = {}) {
  return onRequestPost({
    env,
    request: new Request(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...headers },
      body: JSON.stringify(payload),
    }),
  });
}

function lookup(env, id, headers) {
  return onRequestGet({ env, request: new Request(`${endpoint}?id=${id}`, { headers }) });
}

test("an accepted private submission survives a restart and retries return its original receipt", async (t) => {
  const dir = await mkdtemp(join(tmpdir(), "fastest-feedback-"));
  t.after(() => rm(dir, { recursive: true, force: true }));
  const file = join(dir, "feedback.db");
  const payload = { ...note, requestId: randomUUID() };
  let receipt;
  const database = new DatabaseSync(file);
  try {
    database.exec(await readFile(new URL("./feedback-schema.sql", import.meta.url), "utf8"));
    const first = await submit({ FEEDBACK_DB: d1(database), FEEDBACK_STORAGE: "legacy-d1" }, payload);
    assert.equal(first.status, 201);
    receipt = await first.json();
    assert.equal(receipt.status, "queued");
    assert.deepEqual(Object.keys(receipt).sort(), ["id", "status"]);
    assert.notEqual(receipt.id, payload.requestId);
  } finally {
    database.close();
  }
  const reopened = new DatabaseSync(file);
  try {
    const env = { FEEDBACK_DB: d1(reopened), FEEDBACK_STORAGE: "legacy-d1" };
    const status = await lookup(env, receipt.id);
    assert.equal(status.headers.get("Cache-Control"), "no-store");
    assert.deepEqual(await status.json(), receipt);
    const retry = await submit(env, payload);
    assert.equal(retry.status, 200);
    assert.deepEqual(await retry.json(), receipt);
    assert.equal((await submit(env, { ...payload, message: "Different private feedback" })).status, 409);
  } finally {
    reopened.close();
  }
});

test("unavailable storage never acknowledges delivery", async () => {
  const database = new DatabaseSync(":memory:");
  try {
    database.exec(await readFile(new URL("./feedback-schema.sql", import.meta.url), "utf8"));
    const FEEDBACK_DB = d1(database);
    for (const env of [{}, { FEEDBACK_DB }, { FEEDBACK_DB, FEEDBACK_STORAGE: "legacy-d1", FEEDBACK_PG: {} }]) {
      const response = await submit(env, { ...note, requestId: randomUUID() });
      assert.equal(response.status, 503);
      assert.deepEqual(await response.json(), { error: "feedback_unavailable" });
      assert.equal((await lookup(env, randomUUID())).status, 503);
    }
  } finally {
    database.close();
  }
});

test("only the submitted message and explicitly shared context are accepted", async (t) => {
  const database = new DatabaseSync(":memory:");
  t.after(() => database.close());
  database.exec(await readFile(new URL("./feedback-schema.sql", import.meta.url), "utf8"));
  const env = { FEEDBACK_DB: d1(database), FEEDBACK_STORAGE: "legacy-d1" };
  const payload = { ...note, requestId: randomUUID() };
  assert.equal((await submit(env, { ...payload, settings: { currency: "CNY" } })).status, 400);
  assert.equal((await submit(env, { ...payload, message: "a".repeat(1201) })).status, 400);
  assert.equal((await submit(env, { ...payload, message: note.message + "\u0000" })).status, 400);
  assert.equal((await submit(env, { ...payload, context: { page: "Models", currency: "CNY" } })).status, 400);
  assert.equal((await submit(env, { ...payload, context: { page: "\uD800" } })).status, 400);
  assert.equal((await submit(env, payload, { Origin: "https://elsewhere.example" })).status, 403);

  const attached = { page: "Models", entity: "llama31-8b", release: "Review snapshot" };
  const accepted = await submit(env, { ...payload, context: attached });
  assert.equal(accepted.status, 201);
  const receipt = await accepted.json();
  const retry = await submit(env, { ...payload, context: { release: attached.release, entity: attached.entity, page: attached.page } });
  assert.deepEqual(await retry.json(), receipt);
  assert.equal((await submit(env, payload)).status, 409);
  const page = await lookup(env, receipt.id, { Accept: "text/html" });
  const html = await page.text();
  assert.match(html, /<h1>Feedback status<\/h1>/);
  assert.match(html, /Queued for review/);
  assert.ok(!html.includes(note.message) && !html.includes(attached.entity));
});

test("a resolved opted-in receipt reveals only its approved public resolution", async (t) => {
  const database = new DatabaseSync(":memory:");
  t.after(() => database.close());
  database.exec(await readFile(new URL("./feedback-schema.sql", import.meta.url), "utf8"));
  const env = { FEEDBACK_DB: d1(database), FEEDBACK_STORAGE: "legacy-d1" };
  const submitted = await submit(env, {
    ...note, requestId: randomUUID(), context: { page: "Wiki", entity: "research", release: "v1-aaaaaaaaaaaaaaaa" },
  });
  const { id } = await submitted.json();
  const resolution = "/wiki/evidence-updates#" + "9".repeat(64);
  database.prepare("INSERT INTO feedback_resolution (receipt_id, public_path) VALUES (?, ?)").run(id, resolution);
  const response = await lookup(env, id);
  const status = await response.json();
  assert.equal(response.headers.get("X-Robots-Tag"), "noindex");
  assert.deepEqual(status, { id, status: "reviewed", resolution });
  const html = await (await lookup(env, id, { Accept: "text/html" })).text();
  assert.ok(html.includes(resolution));
  assert.ok(!html.includes(note.message) && !html.includes("v1-aaaaaaaaaaaaaaaa"));
});

const feedbackDatabaseUrl = process.env.FASTEST_TEST_FEEDBACK_DATABASE_URL;
const testDatabaseUrl = process.env.FASTEST_TEST_DATABASE_URL;
test("hosted Pages acknowledges a feedback receipt persisted in PostgreSQL", {
  skip: !feedbackDatabaseUrl || !testDatabaseUrl, timeout: 60_000,
}, async (t) => {
  const assets = await mkdtemp(join(tmpdir(), "fastest-feedback-pages-"));
  t.after(() => rm(assets, { recursive: true, force: true }));
  await writeFile(join(assets, "index.html"), "<title>Feedback test</title>");
  const payload = { ...note, requestId: randomUUID() };
  const context = { page: "Research library", entity: "source/owner's \\ location", release: "v1-aaaaaaaaaaaaaaaa" };
  const correction = { ...note, requestId: randomUUID(), context };
  const resolution = "/wiki/evidence-updates#" + "a".repeat(64);
  const post = (origin, submission) => fetch(origin + "/api/feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json", Origin: origin },
    body: JSON.stringify(submission),
  });
  let receipt;
  let correctionReceipt;

  await withLocalPages(assets, t.signal, async (origin) => {
    const duplicates = await Promise.all(Array.from({ length: 4 }, () => post(origin, payload)));
    assert.deepEqual(duplicates.map(({ status }) => status).sort(), [200, 200, 200, 201]);
    receipt = await duplicates[0].json();
    assert.deepEqual(Object.keys(receipt).sort(), ["id", "status"]);
    assert.notEqual(receipt.id, payload.requestId);
    assert.equal(receipt.status, "queued");
    for (const duplicate of duplicates.slice(1)) assert.deepEqual(await duplicate.json(), receipt);
    assert.equal((await post(origin, { ...payload, message: "Different private feedback" })).status, 409);
    const accepted = await post(origin, correction);
    assert.equal(accepted.status, 201);
    correctionReceipt = await accepted.json();
    assert.equal((await post(origin, { ...correction, context: undefined })).status, 409);
  }, { feedbackDatabaseUrl });

  const publisher = new Client({ connectionString: testDatabaseUrl });
  const pagesRole = new Client({ connectionString: feedbackDatabaseUrl });
  try {
    await publisher.connect();
    await pagesRole.connect();
    const { rows } = await publisher.query(`SELECT id, context_json
      FROM fastest_feedback.feedback_submission WHERE request_id = ANY($1) ORDER BY context_json NULLS FIRST`,
    [[payload.requestId, correction.requestId]]);
    assert.deepEqual(rows, [{ id: receipt.id, context_json: null }, { id: correctionReceipt.id, context_json: context }]);
    await assert.rejects(pagesRole.query("SELECT message FROM fastest_feedback.feedback_submission"), { code: "42501" });
    const link = (client, id, shared, path) => client.query(
      "SELECT fastest_feedback.link_feedback_resolution($1, $2, $3) AS linked", [id, shared, path]);
    await assert.rejects(link(pagesRole, correctionReceipt.id, context, resolution), { code: "42501" });
    assert.deepEqual((await link(publisher, receipt.id, context, resolution)).rows, [{ linked: false }]);
    assert.deepEqual((await link(publisher, correctionReceipt.id, { ...context, entity: "other" }, resolution)).rows,
      [{ linked: false }]);
    await assert.rejects(link(publisher, correctionReceipt.id, context, "https://external.example/"), { code: "23514" });
    assert.deepEqual((await publisher.query(
      "SELECT status FROM fastest_feedback.feedback_submission WHERE id = $1", [correctionReceipt.id])).rows, [{ status: "queued" }]);
    assert.deepEqual((await link(publisher, correctionReceipt.id, context, resolution)).rows, [{ linked: true }]);
  } finally {
    await Promise.all([publisher.end(), pagesRole.end()]);
  }

  await withLocalPages(assets, t.signal, async (origin) => {
    const status = await fetch(origin + "/api/feedback?id=" + receipt.id);
    assert.equal(status.status, 200);
    assert.equal(status.headers.get("Cache-Control"), "no-store");
    assert.deepEqual(await status.json(), receipt);
    const correctionStatusUrl = origin + "/api/feedback?id=" + correctionReceipt.id;
    const reviewed = await fetch(correctionStatusUrl);
    assert.equal(reviewed.headers.get("X-Robots-Tag"), "noindex");
    assert.deepEqual(await reviewed.json(), { id: correctionReceipt.id, status: "reviewed", resolution });
    const page = await fetch(correctionStatusUrl, { headers: { Accept: "text/html" } });
    assert.equal(page.headers.get("Referrer-Policy"), "no-referrer");
    const html = await page.text();
    assert.ok(html.includes(resolution));
    assert.ok(!html.includes(context.entity) && !html.includes(note.message));
    const retry = await post(origin, { ...correction, context: { release: context.release, page: context.page, entity: context.entity } });
    assert.equal(retry.status, 200);
    assert.deepEqual(await retry.json(), { id: correctionReceipt.id, status: "reviewed" });
    assert.equal((await fetch(origin + "/api/feedback?id=" + randomUUID())).status, 404);
  }, { feedbackDatabaseUrl });
});
