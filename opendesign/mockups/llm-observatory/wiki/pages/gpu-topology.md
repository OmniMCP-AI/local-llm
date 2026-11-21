---
title: GPU topology
status: published
kind: guide
use_cases: distributed-inference, model-fit, hardware-selection
summary: Compare one card, several cards, or several machines without treating them as the same thing.
---

Card count describes the hardware. The transport path, negotiated speed, and runtime split describe how the workload actually uses it.

## Read the link

- Keep local memory per device separate from measured usable capacity for a model.
- Distinguish physical slots from devices participating in the run. Record PCIe generation and negotiated lane width, peer paths, direct links, and host-staged copies.
- Compare measured transfer bandwidth by direction and protocol. Peak link ratings and whole-model throughput answer different questions.

Open a reported profile in the table for the source and missing fields. See the [benchmark method](#wiki/benchmark-method) before interpreting scaling, or browse the [runtime directory](#catalog/runtimes).

Open [Technology in motion](#wiki/technology) to explore the conceptual data path and its components.
