import {
  feedbackCategories, feedbackId, maxFeedbackContextLength, maxFeedbackLength, minFeedbackLength,
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
  if (trimmed.length < minFeedbackLength || message.length > maxFeedbackLength) return null;
  if (Object.keys(payload).some((key) => !["requestId", "category", "message", "context"].includes(key))) return null;
  if (context === undefined) return { requestId, category, message: trimmed, contextJson: null };
  if (!context || typeof context !== "object" || Array.isArray(context) || !Object.hasOwn(context, "page") ||
      Object.entries(context).some(([key, value]) =>
        !contextFields.includes(key) || typeof value !== "string" || !value.trim() || value.length > maxFeedbackContextLength
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
    const db = env.FEEDBACK_DB;
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
    receipt = await env.FEEDBACK_DB.prepare("SELECT id, status FROM feedback_submission WHERE id = ?").bind(id).first();
  } catch {
    return json({ error: "feedback_unavailable" }, 503);
  }
  if (!receipt) return json({ error: "receipt_not_found" }, 404);
  if (!request.headers.get("Accept")?.includes("text/html")) return json(receipt, 200);
  const status = receipt.status === "reviewed" ? "Reviewed" : "Queued for review";
  return new Response(`<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Feedback status</title><main><h1>Feedback status</h1><p>${status}</p><p>Receipt <bdi>${id}</bdi></p></main>`, {
    headers: { ...responseHeaders, "Content-Type": "text/html; charset=utf-8" },
  });
}
