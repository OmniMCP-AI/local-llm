import assert from 'node:assert/strict';
import { test } from 'node:test';
import runtimes from './catalog-runtimes.json' with { type: 'json' };
import { runtimeOverview, workloadSlice } from './runtime-overview.mjs';

test('overview keeps a reviewed shortlist and ranks only complete matching measurements, including ties and gaps', () => {
  const slice = { ...workloadSlice, artifactSha256: 'a'.repeat(64), cache: 'fp16' };
  const trial = (runtimeId, score, overrides = {}) => ({
    runtimeId, sliceId: workloadSlice.id, score, source: 'https://example.test/run',
    runDate: '2026-11-01', runtimeVersion: 'v1', backend: 'CUDA', driver: '550.54.15',
    artifactSha256: slice.artifactSha256, cache: 'fp16', inputTokens: 512, outputTokens: 128,
    hardware: 'RTX 4090', artifact: 'Qwen2.5-7B-Instruct Q4_K_M', context: 4096, concurrency: 1,
    ...overrides,
  });
  const overview = runtimeOverview(runtimes, [
    trial('llama.cpp', 40), trial('llama.cpp', 45), trial('vllm', 45),
    trial('sglang', 100, { sliceId: 'other' }), trial('ollama', 200, { runDate: null }),
  ], slice);
  assert.ok(runtimeOverview(runtimes, [trial('llama.cpp', 45)]).rows.every(row => !row.result));
  assert.equal(overview.rows.length, 7);
  assert.equal(overview.selection.version, '1');
  assert.deepEqual(overview.rows.filter(row => row.result).map(row => [row.id, row.rank, row.result.score]), [
    ['llama.cpp', 1, 45], ['vllm', 1, 45],
  ]);
  assert.ok(overview.rows.find(row => row.id === 'sglang').result === null);
  assert.ok(overview.rows.find(row => row.id === 'ollama').result === null);
  assert.equal(overview.rows.find(row => row.id === 'llama.cpp').formatSource, runtimes[0].formatSource);
});

test('review directory publishes the same source-linked shortlist in HTML and Markdown', async (t) => {
  const { mkdtemp, readFile, rm } = await import('node:fs/promises');
  const { join } = await import('node:path');
  const { tmpdir } = await import('node:os');
  const { writeModelRuntimeDirectories } = await import('./catalog-pages-review.mjs');
  const output = await mkdtemp(join(tmpdir(), 'runtime-overview-'));
  t.after(() => rm(output, { recursive: true, force: true }));
  const release = 'v1-' + 'a'.repeat(16);
  await writeModelRuntimeDirectories(output, {
    manifest: { release, snapshotId: 'a'.repeat(64), discovery: { capturedAt: '2026-11-22', source: 'https://example.test' } },
    shards: new Map(), runtimes,
  }, 'https://example.test');
  for (const extension of ['html', 'md']) {
    const body = await readFile(join(output, 'catalog', release, `runtimes.${extension}`), 'utf8');
    for (const text of ['Runtime overview', 'No eligible measurement', '4096-token context', 'ggml-org/llama.cpp', 'Review v1']) {
      assert.ok(body.includes(text), `${extension}: ${text}`);
    }
  }
});
