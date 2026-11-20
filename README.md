# fastest.ai

Compare an existing local AI machine, a hardware upgrade and a cloud service for a specific workload. The repository contains the research, product specification and interactive review prototype.

## Documentation

- [Product specification and milestones](docs/product-spec.md) covers the first decision pilot, what the prototype demonstrates and the acceptance criteria for five milestones. [GitHub issue #1](https://github.com/OmniMCP-AI/local-llm/issues/1)
- [Database and publishing design](docs/database-publishing-design.md) defines the llmfit boundary, evidence and comparison rules, and DB → Markdown → HTML, chart and table publication.
- [Twenty comparison methods](docs/youtube-comparison-methods.md) connects purchase, inference, evaluation and ownership questions to timestamped research and the milestones that can support them.
- [Platform research](docs/Local-AI-Comparison-Platform/Local-AI-Comparison-Platform.md), [video research inventory and seed data](docs/Local-AI-Comparison-Platform/YouTube-Local-LLM-Transcripts/README.md), and [domain research](docs/AI-Hardware-Project-Domains/AI-Hardware-Project-Domains.md) are the source notes.

## fastest.ai prototype

In `opendesign/mockups/llm-observatory`, run `npm ci` and `npm run build`, then open the generated `fastest-ai.html` preview. From **Wiki → Research library**, filter articles, posts, guides and video notes by use case and inspect the matching test conditions. The standalone preview uses browser preferences on a first visit. Both 简体中文 (CNY) and 繁體中文 (TWD) are available, and the display currency can be selected independently.

For Cloudflare Pages, set the project root to the prototype directory, the build command to `npm ci && npm run build:pages`, and the output directory to `dist`. The root `functions` directory provides the first-visit language hint from Cloudflare's IP country. A saved language or display currency takes priority over the corresponding automatic default. [Cloudflare Pages middleware](https://developers.cloudflare.com/pages/functions/middleware/)

**Catalog → Models** searches the 19,192 repository records in the pinned llmfit snapshot. Filter by task, reviewed artifact format or model license tag. The URL preserves filters and the page number. On Pages, model and runtime names open English release cards. Each card has an HTML and Markdown URL at `/catalog/<release>/models/<owner>/<model>.<html|md>` or `/catalog/<release>/runtimes/<id>.<html|md>`. The Pages Function renders both formats from the same build assets. The release manifest records source counts and hashes, and includes the llmfit MIT notice as a separate download. The standalone preview links to the upstream repositories and releases.

The catalog publishes repository metadata and selected artifact references. Model terms and file digests come from their pinned upstream sources. Runtime cards describe upstream support and list the coverage of fastest.ai compatibility tests. The release excludes external benchmark caches and model weight files. Archive the versioned `catalog/` and `catalog-data/` output together when retaining an older release.

The Pages research library is linked from **Wiki → Research library**. Its pinned `/research/<release>/library.html` URL carries the selected filters. The same release provides `library.md`, `index.json`, `graphify.json` and a checksum manifest. Each format uses the same reviewed topic assignments and observation records. Source dates and unknown tasks are preserved. The library links the twenty timestamped research methods to their use cases and evidence gates.

The default release contains the authored guides and editorial references. The standalone preview also includes the retained video-note fixtures. A publisher can include a reviewed video metadata projection by setting `FASTEST_RESEARCH_METADATA_APPROVALS` to the path of an approval JSON file kept outside the build output. Key each decision by source ID, such as `youtube/09GB4LtXUok`. Use `status: "approved-metadata"` with the publisher's `review` reference and a `sha256` of the UTF-8 bytes of `JSON.stringify(source)` for that exact entry in `wiki/research-index.json`. A changed source requires a new review. Set `status: "withdrawn"` to omit a source from the next build. Remove any separately hosted copies of withdrawn releases. The release builder consumes the editorial metadata index. The imported research database and transcript seed files stay outside the Pages build.

For hosted feedback, apply [the feedback schema](opendesign/mockups/llm-observatory/feedback-schema.sql) to a D1 database and bind it to Pages as `FEEDBACK_DB`. Use separate databases for preview and production. Set the binding before deploying the Pages build. The status link uses an unguessable receipt ID and exposes only review status. Maintainers can review submissions in D1. The standalone build saves notes on the device. [Cloudflare Pages D1 bindings](https://developers.cloudflare.com/pages/functions/bindings/#d1-databases)
