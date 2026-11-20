import React, { useEffect, useId, useRef, useState } from "react";
import { ArrowUpRight, Check, Copy, MessageCircle, X } from "lucide-react";
import { feedbackId, maxFeedbackContextLength, maxFeedbackLength, minFeedbackLength } from "./feedback-policy.mjs";
import { useLocale } from "./locale";

const storeKey = "fastest-feedback-v1";
const publicIssue = "https://github.com/OmniMCP-AI/local-llm/issues/new";
const feedbackEndpoint = "/api/feedback";
const hosted = __FASTEST_PAGES__ && location.protocol !== "file:";
const categories = {
  correction: {
    label: ["Correct a result", "更正结果"],
    prompt: ["What looks wrong? Include the displayed value, expected value, and a source if you have one.", "哪里有误？请提供页面上的数值、你预期的数值，以及可用的来源。"],
    reply: ["A source link, tested configuration, and run conditions help a reviewer reproduce the correction.", "附上来源链接、实测配置和运行条件，可帮助审核者复核这条更正。"],
    link: { label: ["How to read the evidence", "如何阅读证据记录"], href: "#wiki/evidence-guide" },
  },
  missing: {
    label: ["Request a benchmark", "请求基准测试"],
    prompt: ["Which machine, model, and workload should we measure? Include what you’re trying to decide.", "希望测试哪台机器、哪个模型和哪种工作负载？也请说明你想据此做什么决定。"],
    reply: ["Good benchmark requests specify the exact hardware, model revision or quantization, and intended workload. Mark any details you don’t know yet.", "请注明具体硬件、模型版本或量化方式，以及预期工作负载。尚不确定的信息可标为未知。"],
    link: { label: ["Browse machine profiles", "浏览整机配置"], href: "#machines" },
  },
  confusing: {
    label: ["Improve the comparison", "改进比较"],
    prompt: ["What question were you trying to answer? Tell us where the comparison stopped helping.", "你原本想回答什么问题？比较页面在哪里没能帮到你？"],
    reply: ["Try a strict limit for anything you cannot compromise on, then use a single priority to sort the setups that meet those limits.", "先为必须满足的要求设定限值，再选择一项最重要的指标，对符合要求的配置排序。"],
    link: { label: ["Compare by goals", "按目标比较"], href: "#goals" },
  },
  other: {
    label: ["Something else", "其他"],
    prompt: ["Tell us what you expected and what happened. Please leave out passwords and personal information.", "请说明你的预期和实际发生的情况。请勿填写密码或个人信息。"],
    reply: ["A short example of what you were trying to do makes your note more useful. You can copy the note and its reference from here.", "附上一小段操作示例会有帮助。你可以在这里复制反馈内容和编号。"],
  },
};

function newId() {
  const suffix = globalThis.crypto?.randomUUID?.().slice(0, 8) ?? Math.random().toString(16).slice(2, 10);
  return "FB-" + suffix.toUpperCase();
}

function saveLocal(note) {
  try {
    const previous = JSON.parse(localStorage.getItem(storeKey) ?? "[]");
    const history = Array.isArray(previous) ? previous : [];
    localStorage.setItem(storeKey, JSON.stringify([...history.slice(-19), note]));
    return true;
  } catch {
    return false;
  }
}

export function FeedbackBubble({ page, entity, release, onCopy }) {
  const { language, t } = useLocale();
  const dialog = useRef(null);
  const launch = useRef(null);
  const topic = useRef(null);
  const title = useRef(null);
  const attempt = useRef(null);
  const id = useId();
  const [category, setCategory] = useState("");
  const [message, setMessage] = useState("");
  const [attachedContext, setAttachedContext] = useState(null);
  const [delivery, setDelivery] = useState("");
  const [receipt, setReceipt] = useState(null);
  const guide = categories[category];
  const receiptGuide = receipt ? categories[receipt.note.category] : undefined;
  const number = new Intl.NumberFormat(language);
  const snapshot = { page: (page || "Explorer").slice(0, maxFeedbackContextLength) };
  if (entity) snapshot.entity = entity.slice(0, maxFeedbackContextLength);
  if (release) snapshot.release = release.slice(0, maxFeedbackContextLength);
  const formatContext = (context) => Object.entries(context).map(([key, value]) => key + ": " + value).join("\n");
  const valid = !!guide && message.trim().length >= minFeedbackLength;
  const sending = delivery === "sending";

  useEffect(() => {
    if (dialog.current?.open) (receipt ? title : topic).current?.focus();
  }, [receipt]);

  const submit = async (event) => {
    event.preventDefault();
    if (!valid || sending) return;
    const payload = {
      category,
      message: message.trim(),
      ...(attachedContext ? { context: attachedContext } : {}),
    };
    if (!hosted) {
      const note = { ...payload, id: newId(), createdAt: new Date().toISOString() };
      setReceipt({ note, saved: saveLocal(note) });
      return;
    }
    setDelivery("sending");
    try {
      const serialized = JSON.stringify(payload);
      if (attempt.current?.serialized !== serialized) {
        attempt.current = { serialized, requestId: crypto.randomUUID() };
      }
      const response = await fetch(feedbackEndpoint, {
        method: "POST",
        credentials: "omit",
        referrerPolicy: "no-referrer",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...payload, requestId: attempt.current.requestId }),
        signal: AbortSignal.timeout(12000),
      });
      if (!response.ok) throw new Error("Feedback write failed");
      const { id: receiptId, status } = await response.json();
      if (typeof receiptId !== "string" || !feedbackId.test(receiptId) || !["queued", "reviewed"].includes(status)) {
        throw new Error("Invalid feedback receipt");
      }
      attempt.current = null;
      setDelivery("");
      setReceipt({ note: { ...payload, id: receiptId }, status });
    } catch {
      setDelivery("failed");
    }
  };

  const reset = () => {
    setCategory("");
    setMessage("");
    setAttachedContext(null);
    setReceipt(null);
  };

  const copy = () => {
    if (!receipt || !onCopy) return;
    const { note } = receipt;
    const attached = note.context
      ? "\n\n" + t("View context", "页面状态") + "\n" + formatContext(note.context)
      : "";
    dialog.current?.close();
    onCopy(note.id + " / " + t(...categories[note.category].label) + "\n\n" + note.message + attached, t("Feedback note copied", "已复制反馈"));
  };

  return <div className="feedback-widget">
    <button ref={launch} type="button" className="feedback-launch" aria-haspopup="dialog" onClick={() => {
      dialog.current?.showModal();
      (receipt ? title : topic).current?.focus();
    }}>
      <MessageCircle size={18} aria-hidden="true" /><span>{t("Feedback", "反馈")}</span>
    </button>
    <dialog ref={dialog} className="feedback-dialog" aria-labelledby={id + "-title"} onClose={() => launch.current?.focus()}>
      <div className="feedback-head">
        <div><p>{t("Community feedback", "社区反馈")}</p><h2 ref={title} tabIndex={-1} id={id + "-title"}>{receipt ? t("Your feedback note", "你的反馈") : t("Help build fastest.ai", "一起建设 fastest.ai")}</h2></div>
        <button type="button" className="btn outline feedback-close" aria-label={t("Close feedback", "关闭反馈")} onClick={() => dialog.current?.close()}><X size={16} aria-hidden="true" /></button>
      </div>
      {receipt ? <div className="feedback-receipt">
        <div className="feedback-status" role="status">
          <Check size={16} aria-hidden="true" />
          <div><strong>{receipt.status ? t("Feedback received", "已收到反馈") : receipt.saved ? t("Saved on this device", "已保存在此设备") : t("Available for this session", "仅在本次会话中可用")}</strong>
            <p><bdi>{receipt.note.id}</bdi></p>
            <p>{receipt.status === "queued" ? t("Queued for review", "等待审核")
              : receipt.status === "reviewed" ? t("Reviewed", "已审核")
              : receipt.saved ? t("Nothing was sent.", "内容尚未发送。")
              : t("Browser storage wasn’t available. Copy your note to keep it.", "浏览器存储不可用。请复制反馈以便保留。")}</p>
          </div>
        </div>
        <div className="feedback-reply">
          <h3>{t("Automated suggestion", "自动建议")}</h3>
          <p>{t(...receiptGuide.reply)}</p>
          {receiptGuide.link && <a href={receiptGuide.link.href} onClick={() => dialog.current?.close()}>
            {t(...receiptGuide.link.label)} <ArrowUpRight size={14} aria-hidden="true" />
          </a>}
        </div>
        {receipt.status && <div className="feedback-reply">
          <a href={feedbackEndpoint + "?id=" + receipt.note.id} target="_blank" rel="noreferrer">
            {t("Check receipt status", "查看回执状态")} <ArrowUpRight size={14} aria-hidden="true" />
          </a>
        </div>}
        <div className="feedback-actions">
          <button type="button" className="btn outline" onClick={reset}>{t("Write another note", "再写一条")}</button>
          {onCopy && <button type="button" className="btn dark" onClick={copy}><Copy size={14} aria-hidden="true" />{t("Copy note", "复制反馈")}</button>}
        </div>
      </div> : <form className="feedback-form" onSubmit={submit}>
        <label htmlFor={id + "-category"}>{t("Topic", "主题")}</label>
        <select ref={topic} id={id + "-category"} value={category} onChange={(event) => setCategory(event.target.value)} disabled={sending} required>
          <option value="">{t("Choose a topic", "选择主题")}</option>
          {Object.entries(categories).map(([key, option]) => <option key={key} value={key}>{t(...option.label)}</option>)}
        </select>
        <label htmlFor={id + "-note"}>{t("Your feedback", "反馈内容")}</label>
        <p className="feedback-hint" id={id + "-hint"}>{guide ? t(...guide.prompt) : t("Tell us what to fix, measure, or explain.", "告诉我们需要更正、测试或解释什么。")}</p>
        <textarea id={id + "-note"} aria-describedby={id + "-hint " + id + "-length"} dir="auto" value={message}
          minLength={minFeedbackLength} maxLength={maxFeedbackLength} rows="4" readOnly={sending} required onChange={(event) => setMessage(event.target.value)} />
        <small id={id + "-length"} className="feedback-length">{t("{count} / {max} characters", "{count} / {max} 字符", { count: number.format(message.length), max: number.format(maxFeedbackLength) })}</small>
        <label className="feedback-context">
          <input type="checkbox" aria-describedby={id + "-context"} checked={!!attachedContext} disabled={sending}
            onChange={(event) => setAttachedContext(event.target.checked ? snapshot : null)} />
          <span>{t("Add current view details", "附上当前页面的设置")}</span>
        </label>
        <pre id={id + "-context"} className="feedback-preview">{formatContext(attachedContext ?? snapshot)}</pre>
        {delivery === "failed" && <p className="feedback-error" role="alert">
          {t("Delivery could not be confirmed. Your draft is still here.", "暂时无法确认送达。草稿仍保留在这里。")}
        </p>}
        <div className="feedback-actions">
          <p>{hosted ? t("Your feedback goes to the maintainers.", "反馈将发送给维护者。")
            : t("Prototype only. Feedback stays on this device.", "原型版的反馈只保存在此设备。")}</p>
          <button type="submit" className="btn dark" disabled={!valid} aria-disabled={sending || undefined}>
            {!hosted ? t("Save feedback", "保存反馈") : sending ? t("Sending feedback…", "正在发送反馈…")
              : delivery === "failed" ? t("Retry sending", "重试发送") : t("Send feedback", "发送反馈")}
          </button>
        </div>
      </form>}
      <div className="feedback-public">
        <a href={publicIssue} target="_blank" rel="noreferrer">{t("Open GitHub issue", "在 GitHub 提交议题")} <ArrowUpRight size={14} aria-hidden="true" /></a>
        <p>{t("GitHub issues are public. Share only the details you want others to see.", "GitHub 议题是公开的，请只分享你愿意公开的内容。")}</p>
      </div>
    </dialog>
  </div>;
}
