import { Client } from "pg";
import {
  evidenceUpdatePath, feedbackCategories, feedbackId, maxFeedbackContextLength, maxFeedbackLength, minFeedbackLength,
} from "../../feedback-policy.mjs";

const maxBodyBytes = 12 * 1024;
const responseHeaders = {
  "Cache-Control": "no-store",
  "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
  "Referrer-Policy": "no-referrer",
  "X-Content-Type-Options": "nosniff",
  "X-Robots-Tag": "noindex",
};
const contextFields = ["page", "entity", "release"];

const json = (body, status) => Response.json(body, { status, headers: responseHeaders });
const validText = (value) => value.isWellFormed() && !value.includes("\0");
const legacyDatabase = (env) => env.FEEDBACK_STORAGE === "legacy-d1" ? env.FEEDBACK_DB : undefined;

async function feedbackQuery(binding, sql, params) {
  const connectionString = binding.connectionString;
  if (!connectionString) throw new Error("Missing feedback database connection");
  const client = new Client({ connectionString, connectionTimeoutMillis: 3000, query_timeout: 5000 });
  try {
    await client.connect();
    const { rows } = await client.query(sql, params);
    return rows[0];
  } finally {
    await client.end();
  }
}

async function readPayload(request) {
  if (!request.body) return null;
  const reader = request.body.getReader();
  const bytes = new Uint8Array(maxBodyBytes);
  let size = 0;
  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      if (size + value.length > bytes.length) {
        await reader.cancel().catch(() => {});
        return null;
      }
      bytes.set(value, size);
      size += value.length;
    }
    return JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes.subarray(0, size)));
  } catch {
    return null;
  } finally {
    reader.releaseLock();
  }
}

function normalizePayload(payload) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) return null;
  const { requestId, category, message, context } = payload;
  if (typeof requestId !== "string" || !feedbackId.test(requestId) ||
      !feedbackCategories.includes(category) || typeof message !== "string") return null;
  const trimmed = message.trim();
  if (trimmed.length < minFeedbackLength || message.length > maxFeedbackLength || !validText(trimmed)) return null;
  if (Object.keys(payload).some((key) => !["requestId", "category", "message", "context"].includes(key))) return null;
  if (context === undefined) return { requestId, category, message: trimmed, contextJson: null };
  if (!context || typeof context !== "object" || Array.isArray(context) || !Object.hasOwn(context, "page") ||
      Object.entries(context).some(([key, value]) =>
        !contextFields.includes(key) || typeof value !== "string" || !value.trim() ||
        value.length > maxFeedbackContextLength || !validText(value)
      )) return null;
  const ordered = Object.fromEntries(contextFields.filter((key) => Object.hasOwn(context, key)).map((key) => [key, context[key]]));
  return { requestId, category, message: trimmed, contextJson: JSON.stringify(ordered) };
}

export async function onRequestPost({ request, env }) {
  const origin = request.headers.get("Origin");
  if (origin && origin !== new URL(request.url).origin) return json({ error: "origin_not_allowed" }, 403);
  const type = request.headers.get("Content-Type")?.split(";", 1)[0].trim().toLowerCase();
  if (type !== "application/json") return json({ error: "expected_json" }, 415);
  const note = normalizePayload(await readPayload(request));
  if (!note) return json({ error: "invalid_feedback" }, 400);

  try {
    if (env.FEEDBACK_PG) {
      const receipt = await feedbackQuery(env.FEEDBACK_PG,
        "SELECT id, status, outcome FROM fastest_feedback.submit_feedback($1, $2, $3, $4)",
        [note.requestId, note.category, note.message, note.contextJson]);
      if (receipt.outcome === "conflict") return json({ error: "request_id_conflict" }, 409);
      return json({ id: receipt.id, status: receipt.status }, receipt.outcome === "created" ? 201 : 200);
    }
    const db = legacyDatabase(env);
    if (!db) return json({ error: "feedback_unavailable" }, 503);
    const candidateId = crypto.randomUUID();
    const [insert, lookup] = await db.batch([
      db.prepare(`INSERT INTO feedback_submission (id, request_id, category, message, context_json)
        VALUES (?, ?, ?, ?, ?) ON CONFLICT(request_id) DO NOTHING`)
        .bind(candidateId, note.requestId, note.category, note.message, note.contextJson),
      db.prepare(`SELECT id, status, category, message, context_json
        FROM feedback_submission WHERE request_id = ?`).bind(note.requestId),
    ]);
    const stored = lookup.results[0];
    if (!insert.success || !lookup.success || !stored) return json({ error: "feedback_unavailable" }, 503);
    if (stored.category !== note.category || stored.message !== note.message || stored.context_json !== note.contextJson) {
      return json({ error: "request_id_conflict" }, 409);
    }
    return json({ id: stored.id, status: stored.status }, stored.id === candidateId ? 201 : 200);
  } catch {
    return json({ error: "feedback_unavailable" }, 503);
  }
}

export async function onRequestGet({ request, env }) {
  const id = new URL(request.url).searchParams.get("id");
  if (!id || !feedbackId.test(id)) return json({ error: "receipt_not_found" }, 404);
  let receipt;
  try {
    if (env.FEEDBACK_PG) {
      receipt = await feedbackQuery(env.FEEDBACK_PG,
        "SELECT id, status, public_path FROM fastest_feedback.read_feedback_receipt($1)", [id]);
    } else {
      const db = legacyDatabase(env);
      if (!db) return json({ error: "feedback_unavailable" }, 503);
      receipt = await db.prepare(`SELECT feedback_submission.id, status, public_path
        FROM feedback_submission LEFT JOIN feedback_resolution ON feedback_resolution.receipt_id = feedback_submission.id
        WHERE feedback_submission.id = ?`).bind(id).first();
    }
  } catch {
    return json({ error: "feedback_unavailable" }, 503);
  }
  if (!receipt) return json({ error: "receipt_not_found" }, 404);
  const resolution = receipt.public_path && evidenceUpdatePath.test(receipt.public_path) ? receipt.public_path : null;
  const reviewed = resolution || receipt.status === "reviewed";
  const result = { id: receipt.id, status: reviewed ? "reviewed" : "queued", ...(resolution && { resolution }) };
  if (!request.headers.get("Accept")?.includes("text/html")) return json(result, 200);
  const status = reviewed ? "Reviewed" : "Queued for review";
  const resolutionLink = resolution ? `<p><a href="${resolution}">Read the public resolution</a></p>` : "";
  return new Response(`<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Feedback status</title><main><h1>Feedback status</h1><p>${status}</p>${resolutionLink}<p>Receipt <bdi>${id}</bdi></p></main>`, {
    headers: { ...responseHeaders, "Content-Type": "text/html; charset=utf-8" },
  });
}
