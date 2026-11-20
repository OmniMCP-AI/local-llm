---
title: Crawler and agent discovery
status: published
kind: guide
use_cases: agent-integration, evidence-research
summary: Retrieve and cite the wiki and research library through stable public URLs.
---

Each released wiki article has a canonical HTML page and a Markdown companion. Use the release and page IDs to cite the same article across formats. Graphify backlinks connect related public articles.

## Find the current release

- The sitemap at `/sitemap.xml` lists canonical HTML routes. The [robots.txt standard](https://www.rfc-editor.org/rfc/rfc9309) describes crawler preferences.
- The index at `/llms.txt` follows the [llms.txt proposal](https://llmstxt.org/) and links to public Markdown and release manifests.
- The [research library](#wiki/research) exposes reviewed source metadata and timestamped methods. See the [evidence guide](#wiki/evidence-guide) to interpret a reported observation.
