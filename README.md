# fastest.ai

Compare an existing local AI machine, a hardware upgrade and a cloud service for a specific workload. The repository contains the research, product specification and interactive review prototype.

## Documentation

- [Product specification and milestones](docs/product-spec.md) covers the first decision pilot, what the prototype demonstrates and the acceptance criteria for five milestones. [GitHub issue #1](https://github.com/OmniMCP-AI/local-llm/issues/1)
- [Database and publishing design](docs/database-publishing-design.md) defines the llmfit boundary, evidence and comparison rules, and DB → Markdown → HTML, chart and table publication.
- [Twenty comparison methods](docs/youtube-comparison-methods.md) connects purchase, inference, evaluation and ownership questions to timestamped research and the milestones that can support them.
- [Platform research](docs/Local-AI-Comparison-Platform/Local-AI-Comparison-Platform.md), [video research inventory and seed data](docs/Local-AI-Comparison-Platform/YouTube-Local-LLM-Transcripts/README.md), and [domain research](docs/AI-Hardware-Project-Domains/AI-Hardware-Project-Domains.md) are the source notes.

## Local services and pilots

- Publish and inspect a versioned PostgreSQL benchmark release. The quickstart includes a labeled synthetic observation. [Release service](production/README.md)
- Prepare redacted case cards from consented interviews and hand them off to the buyer pilot. [Case intake](research-pilot/README.md)
- Generate a dated editorial proposal from an approved release, then approve and export a channel-ready X package. [Editorial drafts](production/fastest_editorial/README.md) · [X delivery](production/fastest_delivery/README.md)

## fastest.ai prototype

In `opendesign/mockups/llm-observatory`, run `npm ci` and `npm run build`, then open the generated `fastest-ai.html` preview. From **Wiki → Research library**, filter articles, posts, guides and video notes by use case and inspect the matching test conditions. The standalone preview uses browser preferences on a first visit. Both 简体中文 (CNY) and 繁體中文 (TWD) are available, and the display currency can be selected independently.

For Cloudflare Pages, set the project root to the prototype directory, the build command to `npm ci && npm run build:pages`, and the output directory to `dist`. The root `functions` directory provides the first-visit language hint from Cloudflare's IP country. A saved language or display currency takes priority over the corresponding automatic default. [Cloudflare Pages middleware](https://developers.cloudflare.com/pages/functions/middleware/)

The Pages build publishes a JavaScript-free wiki at `/wiki/` and Markdown companions such as `/wiki/benchmark-method.md`. The explorer has a readable initial page and highlights before JavaScript loads. Set `FASTEST_PUBLIC_ORIGIN` to the canonical site origin for `robots.txt`, `sitemap.xml` and `llms.txt`. It defaults to `https://fastest.ai`. Wiki citations carry page, source and release IDs in both formats. The wiki manifest also identifies the matching research and catalog releases.

To add or rename a wiki article, edit the reviewed Markdown in `wiki/pages/` and rebuild its Graphify index with `python wiki/rebuild_graph.py` in the installed Graphify environment. Set `status: published` after review and record comma-separated former slugs in `redirects`. Drafts and withdrawn pages are removed on the next build. The highlight records in `wiki/highlights.json` select a reviewed destination, source, publication dates and priority. Rebuild Pages when a publication window changes. The same Asia/Shanghai date window and priority order drive the carousel, initial HTML and homepage Markdown.

**Catalog → Models** searches the 19,192 repository records in the pinned llmfit snapshot. Filter by task, reviewed artifact format or model license tag. The URL preserves filters and the page number. On Pages, model and runtime names open English release cards. Each card has an HTML and Markdown URL at `/catalog/<release>/models/<owner>/<model>.<html|md>` or `/catalog/<release>/runtimes/<id>.<html|md>`. The Pages Function renders both formats from the same build assets. The release manifest records source counts and hashes, and includes the llmfit MIT notice as a separate download. The standalone preview links to the upstream repositories and releases.

The catalog publishes repository metadata and selected artifact references. Model terms and file digests come from their pinned upstream sources. Runtime cards describe upstream support and list the coverage of fastest.ai compatibility tests. The release excludes external benchmark caches and model weight files. Archive the versioned `catalog/` and `catalog-data/` output together when retaining an older release.

**Catalog → Cards** and **Catalog → Machines** use the hardware snapshot dated 2026-11-21. It reconciles the pinned llmfit discrete bandwidth lookup and three example presets with the retained research inventory. The manifest records 102 card references, 46 research component references, 70 partial configurations and zero complete builds. Component records remain discoverable by their original IDs. The hardware detail URLs are `/catalog/<release>/cards/<id>.<html|md>` and `/catalog/<release>/machines/<id>.<html|md>`. Each identifies whether the source supplies a product reference, a board variant, a partial configuration or an example preset. Reported capacity, configured limits and runtime-usable memory have separate fields. Creator-reported observations contribute coverage counts. Reviewed hardware measurements are unavailable in this snapshot.

The Pages research library is linked from **Wiki → Research library**. Its pinned `/research/<release>/library.html` URL carries the selected filters. The same release provides `library.md`, `index.json`, `graphify.json` and a checksum manifest. Each format uses the same reviewed topic assignments and observation records. Source dates and unknown tasks are preserved. The library links the twenty timestamped research methods to their use cases and evidence gates.

The default release contains the authored guides and editorial references. The standalone preview also includes the retained video-note fixtures. A publisher can include a reviewed video metadata projection by setting `FASTEST_RESEARCH_METADATA_APPROVALS` to the path of an approval JSON file kept outside the build output. Key each decision by source ID, such as `youtube/09GB4LtXUok`. Use `status: "approved-metadata"` with the publisher's `review` reference and a `sha256` of the UTF-8 bytes of `JSON.stringify(source)` for that exact entry in `wiki/research-index.json`. A changed source requires a new review. Set `status: "withdrawn"` to omit a source from the next build. Remove any separately hosted copies of withdrawn releases. The release builder consumes the editorial metadata index. The imported research database and transcript seed files stay outside the Pages build.

For hosted feedback, apply [the feedback schema](opendesign/mockups/llm-observatory/feedback-schema.sql) to a D1 database and bind it to Pages as `FEEDBACK_DB`. Use separate databases for preview and production. Set the binding before deploying the Pages build. The status link uses an unguessable receipt ID and exposes only review status. Maintainers can review submissions in D1. The standalone build saves notes on the device. [Cloudflare Pages D1 bindings](https://developers.cloudflare.com/pages/functions/bindings/#d1-databases)

### Review a correction or rights withdrawal

From the prototype directory, keep an exact copy of the current Pages output, any earlier snapshots and project downloads under `downloads/`. For a correction, rebuild the research index and Graphify from the reviewed revision and approve its new metadata digest. A withdrawal quarantines the entire reviewed research source when a record from that source is reported. Retain the source ID and locator in the private review request.

```sh
node resolve-evidence.mjs request.json previous-pages review-output approvals.json older-pages
```

Use `action` (`correct` or `withdraw`), `evidenceId` (the published source or record ID), `sourceId`, and the exact published `sourceLocator`. Set `intake.issue` to the reviewed public GitHub issue, or use the consented D1 row fields `intake.id`, `category`, `status`, and `context_json`. Omit the submission message from the request. Supply the current approval file if the release has source approvals or earlier withdrawals. For a linked benchmark with the same source locator, add `benchmark.evidenceId` and `benchmark.previousRelease`, add a validated `benchmark.correction` observation for a correction, and set `FASTEST_DATABASE_URL` to the authorized publisher database. The database action takes effect when the operator command runs and serializes against concurrent publication.

Deploy only `review-output/pages` through the existing Pages workflow. The review JSON contains the file and diff SHA-256 digests, cache purge paths, a notification draft for recipients of affected exports, and an optional receipt update statement. Retain the change report and approval file privately. After verifying the new Pages release and purging the listed URLs at any managed CDN, apply the receipt statement to the same D1 database, using the current feedback schema. Future Pages builds should use the resulting `approvals.json` as `FASTEST_RESEARCH_METADATA_APPROVALS` and the deployed `evidence-quarantine.json` as `FASTEST_EVIDENCE_STATE`. Disable public access to any earlier Pages deployment aliases or independent project mirrors that bypass the current policy. Previously saved third-party copies require the separate notification.
