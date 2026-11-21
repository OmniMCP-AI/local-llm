// Reviewed editorial shortlist, independent of the workload and performance results.
export const runtimeSelection = {
  version: '1', reviewedAt: '2026-11-22',
  method: 'Editorial shortlist of widely used local inference and serving projects, selected for breadth of deployment styles; not a popularity ranking.',
  ids: ['llama.cpp', 'sglang', 'vllm', 'ollama', 'mlx-lm', 'tensorrt-llm', 'transformers'],
};

// A deliberately narrow cohort. Missing measurements remain visible; publication dates are not run dates.
export const workloadSlice = {
  id: 'qwen25-7b-q4km-4090-cuda-c4096-n1-v1',
  description: 'Qwen2.5-7B-Instruct Q4_K_M, one RTX 4090, CUDA driver 550.54.15, 512 input and 128 output tokens, 4096-token context, one concurrent request; artifact digest and cache configuration not yet pinned',
  metric: 'Decode throughput', unit: 'tokens/s', backend: 'CUDA', hardware: 'RTX 4090',
  artifact: 'Qwen2.5-7B-Instruct Q4_K_M', artifactSha256: null, cache: null, driver: '550.54.15',
  inputTokens: 512, outputTokens: 128, context: 4096, concurrency: 1,
};

export function runtimeOverview(runtimes, trials = [], slice = workloadSlice) {
  const selected = runtimeSelection.ids.map(id => runtimes.find(row => row.id === id)).filter(Boolean);
  const eligible = trial => /^[a-f0-9]{64}$/.test(slice.artifactSha256 ?? '') && Boolean(slice.cache) && trial.sliceId === slice.id && Number.isFinite(trial.score) && trial.score > 0 &&
    ['source', 'runDate', 'runtimeVersion', 'driver'].every(key => typeof trial[key] === 'string' && trial[key].trim()) &&
    /^https:\/\//.test(trial.source) && /^\d{4}-\d{2}-\d{2}$/.test(trial.runDate) &&
    !Number.isNaN(Date.parse(trial.runDate)) && new Date(trial.runDate).toISOString().slice(0, 10) === trial.runDate &&
    ['backend', 'hardware', 'artifact', 'artifactSha256', 'cache', 'driver', 'inputTokens', 'outputTokens', 'context', 'concurrency'].every(key => trial[key] === slice[key]);
  const rows = selected.map(row => {
    const result = trials.filter(trial => trial.runtimeId === row.id && eligible(trial))
      .sort((a, b) => b.score - a.score)[0] ?? null;
    return { ...row, result, rank: null };
  }).sort((a, b) => (b.result?.score ?? -Infinity) - (a.result?.score ?? -Infinity));
  let lastScore, rank = 0;
  rows.forEach((row, index) => {
    if (!row.result) return;
    if (row.result.score !== lastScore) rank = index + 1;
    lastScore = row.result.score;
    row.rank = rank;
  });
  return { selection: runtimeSelection, workload: slice, rows };
}
