import textPlan from "../../../production/fastest_text/plan.json" with { type: "json" };
import { releaseOrigin } from "./release-origin.mjs";

export const observedAgentTaskModelId = "Qwen/Qwen2.5-7B-Instruct";
const { artifact } = textPlan;
const protocolId = "inventory-agent-comparison-shared-ci-cpu@1";

function isObservedComparison(report) {
  const observed = report?.conditions?.artifact;
  return report?.schema_version === 1 && report.kind === "measured" &&
    report.conditions?.protocol_id === protocolId && report.environment?.backend === "CPU" &&
    artifact.repository === observedAgentTaskModelId + "-GGUF" && observed?.repository === artifact.repository &&
    observed.revision === artifact.revision && observed.quantization === artifact.quantization &&
    Array.isArray(observed.shards) && observed.shards.length === artifact.shards.length &&
    artifact.shards.every(({ path, sha256, bytes }, i) =>
      observed.shards[i]?.path === path && observed.shards[i]?.sha256 === sha256 && observed.shards[i]?.bytes === bytes) &&
    Array.isArray(report.contexts) && ["bundle", "split"].every(id => report.contexts.some(context =>
      context?.id === id && context.review?.decision === "allow" &&
      Array.isArray(context.attempts) && context.attempts.length > 0));
}

export async function observedAgentTask(id, env) {
  if (id !== observedAgentTaskModelId) return null;
  const origin = releaseOrigin(env.FASTEST_RELEASE_ORIGIN);
  const pin = env.FASTEST_AGENT_TASK_RELEASE;
  if (!origin || !/^[a-f0-9]{64}$/.test(pin ?? "")) return null;

  const base = `${origin}/agent-task/${pin}/agent-task`;
  try {
    const response = await fetch(base + ".json", {
      cache: "no-store", redirect: "manual", signal: AbortSignal.timeout(8000),
    });
    if (response.status !== 200 || !isObservedComparison(await response.json())) return null;
  } catch {
    return null;
  }

  const files = `https://huggingface.co/${artifact.repository}/blob/${artifact.revision}/`;
  const html = base + ".html";
  return {
    title: "Observed agent benchmark for the exact GGUF artifact",
    html,
    markdown: base + ".md",
    fields: [
      ["Report", "Observed inventory tool-policy benchmark", html],
      ["Benchmark artifact", artifact.repository + " · " + artifact.quantization, artifact.source],
      ["Artifact revision", artifact.revision],
      ...artifact.shards.map(({ path }) => ["GGUF shard", path, files + path]),
      ["Execution scope", "Shared CI CPU (4 vCPUs, no GPU offload). Physical host load is unknown."],
    ],
  };
}
