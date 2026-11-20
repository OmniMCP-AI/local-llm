"""Compile explicit links between this prototype's Markdown pages with Graphify."""

from hashlib import sha256
import json
from pathlib import Path
import re

from graphify.build import build_from_json
from graphify.export import to_json
from research_graph import VERSION, add_research, input_digests, public_index

HERE = Path(__file__).resolve().parent
PAGES = HERE / "pages"
PAGE_LINK = re.compile(r"\]\(#(?:(?:wiki|machines|models|catalog)/)?([a-z0-9-]+)\)")
ROUTE_PAGE = {"methods": "comparison-methods", "costs": "comparison-methods"}
TITLE = re.compile(r"^title: (.+)$", re.MULTILINE)


def main():
    paths = sorted(PAGES.glob("*.md"))
    slugs = {path.stem for path in paths}
    nodes = []
    edges = []
    digest = sha256()
    guides = {}
    for path in paths:
        source = f"pages/{path.name}"
        document = path.read_text(encoding="utf-8")
        digest.update(source.encode("utf-8") + b"\0" + document.encode("utf-8") + b"\0")
        _, frontmatter, body = document.split("---", 2)
        title = TITLE.search(frontmatter)[1]
        fields = dict(line.split(": ", 1) for line in frontmatter.strip().splitlines())
        if fields["kind"] == "guide" and fields.get("status") == "published" and path.stem != "index":
            guides[path.stem] = fields
        nodes.append({"id": path.stem, "label": title, "file_type": "document", "source_file": source})
        for number, line in enumerate(body.splitlines(), frontmatter.count("\n") + 1):
            for target in PAGE_LINK.findall(line):
                target = ROUTE_PAGE.get(target, target)
                if target not in slugs:
                    raise ValueError(f"Unresolved wiki link {target}: {source}:{number}")
                if target == path.stem:
                    continue
                edges.append({
                    "source": path.stem,
                    "target": target,
                    "relation": "references",
                    "confidence": "EXTRACTED",
                    "confidence_score": 1.0,
                    "source_file": source,
                    "source_location": f"L{number}",
                    "weight": 1.0,
                })

    sources = add_research(nodes, edges, guides)
    graph = build_from_json({"nodes": nodes, "edges": edges}, directed=True)
    graph.graph["source_sha256"] = digest.hexdigest()
    research_index = json.dumps(public_index(graph, sources), ensure_ascii=False, separators=(",", ":")) + "\n"
    (HERE / "research-index.json").write_text(research_index, encoding="utf-8")
    graph.graph["research_index_sha256"] = sha256(research_index.encode()).hexdigest()
    graph.graph["taxonomy_version"] = VERSION
    graph.graph["research_inputs"] = input_digests()
    to_json(graph, {}, str(HERE / "graphify.json"), force=True, built_at_commit="")
    public = {
        "nodes": [{"id": node, "title": data["label"]} for node, data in sorted(graph.nodes(data=True)) if node in slugs],
        "edges": [{"source": source, "target": target} for source, target in sorted(graph.edges()) if source in slugs and target in slugs],
    }
    (HERE / "graph.json").write_text(json.dumps(public, ensure_ascii=False, indent=2) + "\n")
    print(f"Graphify: {len(slugs)} wiki pages, {len(sources)} indexed sources, {graph.number_of_edges()} relationships")


if __name__ == "__main__":
    main()
