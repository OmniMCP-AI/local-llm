---
title: Benchmark method
kind: guide
use_cases: model-evaluation, evidence-research
summary: Which results can be compared, and what each metric measures.
---

A comparison is useful when it controls for the dimensions that matter to the decision. It should tell you what varied, what was held fixed, and what failed.

## Keep the workload fixed

- Align exact artifact and quantization, context length, prompt, runtime settings, and measurement scope before ranking decode speed across machines.
- For different models, use the same task and quality gate before comparing completion time. Different tokenizers can produce different units of work.

## Pick a metric that answers the question

- Decode throughput tells you how fast output arrives after generation starts.
- Time to first token and end-to-end task time include different parts of the user wait.
- Track missing runs, out-of-memory errors, and timeouts separately from completed observations.

Use the [Explorer](#explorer) to change the target, or read an [evidence record](#wiki/evidence-guide) to see why a row was included.

Use [Comparison methods](#methods) to choose a chart for decode, prefill, latency, serving capacity, or model evaluation. The [source guide](#wiki/comparison-methods) explains the research behind each method.
