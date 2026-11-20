import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { DatabaseSync } from "node:sqlite";
import test from "node:test";
import { onRequestGet, onRequestPost } from "./functions/api/feedback.js";

const endpoint = "https://fastest.example/api/feedback";
const note = { category: "correction", message: "Private benchmark correction" };

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
    const first = await submit({ FEEDBACK_DB: d1(database) }, payload);
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
    const env = { FEEDBACK_DB: d1(reopened) };
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
  const response = await submit({}, { ...note, requestId: randomUUID() });
  assert.equal(response.status, 503);
  assert.deepEqual(await response.json(), { error: "feedback_unavailable" });
});

test("only the submitted message and explicitly shared context are accepted", async (t) => {
  const database = new DatabaseSync(":memory:");
  t.after(() => database.close());
  database.exec(await readFile(new URL("./feedback-schema.sql", import.meta.url), "utf8"));
  const env = { FEEDBACK_DB: d1(database) };
  const payload = { ...note, requestId: randomUUID() };
  assert.equal((await submit(env, { ...payload, settings: { currency: "CNY" } })).status, 400);
  assert.equal((await submit(env, { ...payload, message: "a".repeat(1201) })).status, 400);
  assert.equal((await submit(env, { ...payload, context: { page: "Models", currency: "CNY" } })).status, 400);
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
  const env = { FEEDBACK_DB: d1(database) };
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
