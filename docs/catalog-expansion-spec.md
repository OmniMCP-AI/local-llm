# Local data and catalog expansion

## Problem Statement

A visitor can browse the current GPU and model directories, but the GPU entries vary widely in detail and the model list is too large for a first decision. A maintainer also needs a repeatable way to import the full repository seed into a queryable relational store and review its output locally. Manufacturer specifications, board designs, creator tests, retail listings and model popularity change independently and need separate provenance.

## Solution

A fresh local checkout provides the repository data and a documented command that imports it into a llmfit-compatible relational schema. The same imported snapshot generates Markdown and corresponding HTML. Every GPU identity in the reconciled inventory has a dedicated, visually structured profile. The model directory defaults to a few hundred popular local candidates and has a separate small-model view. The complete model inventory stays queryable for research and direct references.

## User Stories

1. As a maintainer, I want to reproduce an import from a clean clone, so that I can build the catalog on a second machine.
2. As a maintainer, I want the import to retain raw values, units and source revisions, so that I can reconcile updates and correct mistakes.
3. As an editor, I want to inspect source records, mappings and typed claims, so that I can review a match without losing the original context.
4. As an editor, I want incomplete model and board references to survive the import, so that missing identifiers remain visible for later resolution.
5. As an editor, I want repeated import to preserve IDs and membership, so that retries do not duplicate records.
6. As an editor, I want Markdown and HTML to agree on values, exclusions and citations, so that people and agents can verify the same fact.
7. As a buyer, I want to open a dedicated page from any GPU catalog entry, so that I can inspect its evidence without knowing its source database.
8. As a buyer, I want to distinguish the GPU family, board partner SKU and memory variant, so that I can compare the correct hardware.
9. As a buyer, I want a quick view of memory, bandwidth, interconnect and board power, so that I can shortlist plausible local AI hardware.
10. As an enthusiast, I want clocks, memory bus, interface, compute resources and physical constraints when sourced, so that I can assess a specific build.
11. As an enthusiast, I want specification graphics and approved product photos, so that I can understand the form factor and memory tradeoffs.
12. As a reader, I want each image to identify the pictured SKU and its source, so that I can recognize an illustrative diagram or family photo.
13. As a buyer, I want evidence labels and unknowns visible next to the specs, so that a retail listing or a fit estimate does not become a verified benchmark.
14. As a buyer, I want relevant regional shopping links with dates and purchase conditions, so that I can check the exact variant before buying.
15. As an editor, I want to refresh manufacturer and allowed retail sources without losing previous versions, so that I can review conflicts and delistings.
16. As a reader, I want related machine and benchmark links, so that I can see how a component behaves in the context of a system.
17. As a model shopper, I want the most popular local candidates surfaced first, so that I can start with a manageable list.
18. As a laptop user, I want a separate small-model view with source-backed parameter sizes, so that I can find compact candidates quickly.
19. As a model shopper, I want to know what defines the ranking, so that I do not confuse downloads with model quality or suitability.
20. As a developer, I want to find the full catalog and exact model artifacts, so that an unranked or superseded model retains its durable link.
21. As a keyboard or mobile user, I want readable tables, accessible images and responsive filters, so that I can use the same catalog data on any device.

## Implementation Decisions

- Extend the existing PostgreSQL import and release boundary. Relate sources and revisions, hardware identities and variants, builds and parts, model repositories and artifacts, test series, observations, and qualified associations. Retain raw records and the pinned upstream shapes as part of the import. A source-scoped reference with no exact match remains unresolved.
- Keep the join between a card, its claims, its assets and its offers explicit. A claim carries its field, value, original unit, source locator, capture time and applicable variant. Preserve conflicting observations for review. Keep rated board power, measured power, installed VRAM, usable VRAM, theoretical bandwidth and measured bandwidth distinct.
- Give each memory-modified GPU a separate card identity with stock and reported modified capacity, source and evidence scope. Link the exact stock variant where it is in the catalog. For mining accelerators, record whether a capacity is installed HBM, detected framebuffer, or usable memory demonstrated on a specific board. Show seller listings, retrofit services, experiments and unverified market leads distinctly. A listed SKU does not establish available stock or validated runtime performance. [Memory-modified GPU market survey](modified-gpu-market.md)
- Use an allowlisted mix of manufacturer product/spec pages, board-partner pages and permitted retail feeds or listing pages. Use shared source tables and adapters for series-level catalogs. Store source basis, refresh history and coverage. Prefer the exact manufacturer or board-partner spec for technical claims. Extract retail offers only when the exact SKU, market, date, condition, currency and availability are identifiable. Route recurring price collection through the existing regional refresh work.
- Export every eligible GPU identity from the same release to local Markdown and corresponding HTML. Include a quick specification panel, detailed spec sections, a variant and machine cross-link, and a source list. Include multiple labeled visuals where data supports them. Use original spec graphics for broad coverage and add multiple attributable product views where approved assets exist. Link to manufacturer galleries when image reuse is unavailable. Use released bench rows only in measured charts.
- Use the same GPU chart data and renderer across card pages. Chart rated memory capacity and bandwidth when sourced. Chart decode throughput only for matched measured workloads. Highlight the current card and identify missing measurements. Charts label both axes and units, show both point values on hover or keyboard focus, and offer a point label toggle.
- Route both Machines entries to the PostgreSQL-backed build catalog. Add source-reviewed builds from YouTube, X, GitHub, and local AI communities. Keep up to three credited, reusable build views per source. Prefer the creator's images and approved video thumbnails or embeds. Preserve the original link and mark reference photos that show only the platform exterior.
- Publish the Graphify-backed `awesome-local-llm` wiki with a dedicated inference framework registry and grouped links to GPU resources, small model repositories, and card-specific tuning reports.
- Start with up to 300 ranked model families from a dated Hugging Face Hub downloads snapshot. Choose an eligible local-weight repository per family and preserve conversions as artifact links. Rank by recent downloads with stable tie-breaking. Provide a small-model view ranked by the same signal using documented total parameters of at most 4 billion. Unknown size stays outside the small filter. Popularity, parameter size, llmfit estimates and measured quality remain separate fields.
- Keep the full model catalog in the data layer and accessible through exact search and direct links. Keep the current runtime directory, exact-artifact citations, versioned routes, Markdown companions and language controls.

## Testing Decisions

- Run the documented workflow from a clean clone through relational import, release and local Markdown/HTML. Reimport the same snapshot, compare counts and sorted IDs, and verify that failed input leaves the previous successful release available.
- Use the existing research seed reconciliation and catalog release tests. Extend the release checks to traverse all GPU cards, compare Markdown and HTML facts and citations, and verify missing values, unresolved variants, and image provenance.
- Replay manufacturer and retail snapshots to verify exact SKU joins, preserved conflicts and correct handling of unavailable, stale or expired offers. Test one source failure without hiding previous successful observations.
- Verify ranked and small-model views against a captured Hub response. Cover ties, unknown sizes, gated access state, family duplicates, orphaned conversion variants, and exact lookup outside the ranked list.
- Smoke-test real profile routes and catalog filters on desktop and mobile. A visitor must be able to reach a GPU page from its directory row and see the same essential information through an accessible table.

## Out of Scope

- Global inventory guarantees for unpublished, unresolved or counterfeit SKUs.
- Unreviewed manufacturer or retailer images, benchmark promotion from marketing copy, and model weight mirroring.
- Replacing the native llmfit contract, running the blocked hardware pilots, or deploying the site as part of local catalog generation.

## Further Notes

Use the [catalog and market coverage specification](catalog-and-market-coverage-spec.md#card-photography) and [per-card photo audit](gpu-photo-source-audit.md) for the all-card photography acceptance gate under issue #38. The issue also specifies chart zoom, Costs and Price Watch layout fixes, consistent current-card emphasis, and removal of the generic GPU schematic.

Reuse the existing M1 work for data and directories, and M3 for recurring offers. [Relational import #3](https://github.com/OmniMCP-AI/local-llm/issues/3) · [GPU profiles #4](https://github.com/OmniMCP-AI/local-llm/issues/4) · [Model discovery #5](https://github.com/OmniMCP-AI/local-llm/issues/5) · [Price refresh #21](https://github.com/OmniMCP-AI/local-llm/issues/21)

Use the discovery sources to check missing hardware, model families, tools and vocabulary. Keep each topic attached to its scope, such as a GPU identity, a runtime, a workload, or a measurement dimension. Trace technical values back to the manufacturer, model publisher or measurement source before admitting them to a release. [抡锤者 hardware](https://lcz.me/hardware) · [抡锤者 tags](https://lcz.me/tags) · [localrig](https://localrig.com/) · [The Local Bench](https://thelocalbench.com/) · [local-bench](https://local-bench.ai/)
