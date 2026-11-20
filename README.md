# fastest.ai

Compare an existing local AI machine, a hardware upgrade and a cloud service for a specific workload. The repository contains the research, product specification and interactive review prototype.

## Documentation

- [Product specification and milestones](docs/product-spec.md) covers the first decision pilot, what the prototype demonstrates and the acceptance criteria for five milestones. [GitHub issue #1](https://github.com/OmniMCP-AI/local-llm/issues/1)
- [Database and publishing design](docs/database-publishing-design.md) defines the llmfit boundary, evidence and comparison rules, and DB → Markdown → HTML, chart and table publication.
- [Twenty comparison methods](docs/youtube-comparison-methods.md) connects purchase, inference, evaluation and ownership questions to timestamped research and the milestones that can support them.
- [Platform research](docs/Local-AI-Comparison-Platform/Local-AI-Comparison-Platform.md), [video research inventory and seed data](docs/Local-AI-Comparison-Platform/YouTube-Local-LLM-Transcripts/README.md), and [domain research](docs/AI-Hardware-Project-Domains/AI-Hardware-Project-Domains.md) are the source notes.

## fastest.ai prototype

Browse the [research library](opendesign/mockups/llm-observatory/fastest-ai.html#wiki/research) to filter articles, posts, guides and video notes by use case and inspect the matching test conditions.

Open the [standalone preview](opendesign/mockups/llm-observatory/fastest-ai.html). To rebuild, run `npm ci` and `npm run build` in `opendesign/mockups/llm-observatory`. The preview uses browser preferences on a first visit. Both 简体中文 (CNY) and 繁體中文 (TWD) are available, and the display currency can be selected independently.

For Cloudflare Pages, set the project root to the prototype directory, the build command to `npm ci && npm run build:pages`, and the output directory to `dist`. The root `functions` directory provides the first-visit language hint from Cloudflare's IP country. A saved language or display currency takes priority over the corresponding automatic default. [Cloudflare Pages middleware](https://developers.cloudflare.com/pages/functions/middleware/)
