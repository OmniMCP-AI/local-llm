import { observedAgentTask, observedAgentTaskModelId } from "./catalog-agent-task.mjs";

const highlight = {
  id: "observed-inventory-tool-policy",
  type: "news",
  priority: 40,
  title: "Observed inventory tool-policy benchmark",
  titleZh: "实测库存任务工具策略",
  summary: "Compare bundled and separate page reads for Qwen2.5 7B on shared CI CPU.",
  detailZh: "对比 Qwen2.5 7B 在共享 CI CPU 上合并读取和逐页读取的表现。",
};
const heading = "## Research highlights\n\n";
const htmlEntities = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
const escapeHtml = (value) => value.replace(/[&<>"']/g, (char) => htmlEntities[char]);

export async function observedHomeHighlight(env) {
  const report = await observedAgentTask(observedAgentTaskModelId, env);
  return report && { ...highlight, href: report.html, markdown: report.markdown, source: report.html };
}

export function homeHighlightHtml({ id, href, title, titleZh, summary, detailZh }) {
  return `<li data-observed-home-highlight="${escapeHtml(id)}" data-title-zh="${escapeHtml(titleZh)}" data-detail-zh="${escapeHtml(detailZh)}">`
    + `<a href="${escapeHtml(href)}">${escapeHtml(title)}</a> · <span>${escapeHtml(summary)}</span></li>\n`;
}

export function homeHighlightMarkdown(body, { title, markdown, summary }) {
  const entry = `- [${title}](${markdown}) · ${summary}\n`;
  return body.includes(heading) ? body.replace(heading, () => heading + entry) : body + "\n" + heading + entry;
}
