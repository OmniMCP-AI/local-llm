"""Build the reviewed research relationships and project their public search index."""

import csv
from datetime import date, datetime
from hashlib import sha256
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RESEARCH = ROOT / "docs/Local-AI-Comparison-Platform/YouTube-Local-LLM-Transcripts"
VERSION = 1

# Keys are the source taxonomy. A change in its meaning requires an explicit mapping.
DIMENSIONS = {
    "Single-request generation / reported speed claim (concurrency may be unknown)": "generation",
    "Reported generation throughput (concurrency scope unreported unless row states it)": "generation",
    "Prefill / input processing": "prefill",
    "TTFT / startup latency": "first-token",
    "Memory / fit (not throughput)": "memory",
    "Derived estimates / theoretical / ROI (not measured benchmarks)": "projection",
    "Aggregate / concurrent throughput (not single-request speed)": "serving",
    "Other reported observations / stability (not a comparable speed benchmark)": "other",
    "Power / energy (boundary-dependent)": "energy",
    "Elapsed workflow / phase time (not TTFT unless explicit)": "elapsed",
    "Auxiliary transport / compute / embedding (not LLM decode)": "transport",
    "Quality / task outcomes (not speed)": "quality",
}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def input_digests():
    names = ("video-topics.json", "case-tasks.json", "editorial-sources.json",
             "context-vocabulary.json", "research_graph.py")
    return {name: sha256((HERE / name).read_bytes()).hexdigest() for name in names}


def read_rows(name):
    with (RESEARCH / name).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def add_research(nodes, edges, guides):
    vocabulary = read_json(HERE / "context-vocabulary.json")
    node_ids = {node["id"] for node in nodes}
    source_ids = []

    def node(key, label, source_file, **data):
        if key in node_ids:
            raise ValueError(f"Duplicate research ID {key}")
        node_ids.add(key)
        nodes.append({"file_type": "concept", "id": key, "label": label, "source_file": source_file, **data})

    def link(start, end, relation, source_file, locator):
        if start not in node_ids or end not in node_ids or not locator:
            raise ValueError(f"Unresolved {relation} link {start} → {end} at {locator}")
        edge = dict(source=start, target=end, relation=relation, confidence="EXTRACTED",
                    confidence_score=1.0, weight=1.0, source_file=source_file, source_location=locator)
        if relation in ("discusses", "describes_task", "has_dimension"):
            # EXTRACTED means read directly from an explicit assignment, not proof of a measurement.
            edge["taxonomy_version"] = VERSION
            if relation == "discusses":
                edge["annotation_file"] = "video-topics.json" if start.startswith("youtube/") else source_file
            elif relation == "describes_task":
                edge["annotation_file"] = "case-tasks.json"
            else:
                edge["annotation_file"] = "research_graph.py#DIMENSIONS"
        edges.append(edge)

    def publication(key, title, fmt, publisher, published, url, context, source_file):
        if not url.startswith(("https://", "#wiki/")) or not context or not publisher:
            raise ValueError(f"Incomplete source {key}")
        if published:
            date.fromisoformat(published)
        if key not in guides:
            node(key, title, source_file, file_type="document")
        source_ids.append(key)
        data = dict(publisher=publisher, date=published, url=url, context=context)
        link(key, "formats/"+fmt, "has_format", source_file, url)
        return data

    for group in ("topics", "dimensions", "formats"):
        for slug, labels in vocabulary[group].items():
            node(f"{group}/{slug}", labels[0], "context-vocabulary.json")

    metadata = {}
    for key, fields in guides.items():
        source = "pages/" + key + ".md"
        metadata[key] = publication(key, fields["title"], "guide", "fastest.ai", None,
                                    "#wiki/" + key, fields["summary"], source)
        for topic in fields["use_cases"].split(", "):
            link(key, "topics/"+topic, "discusses", source, "frontmatter.use_cases")

    for entry in read_json(HERE / "editorial-sources.json"):
        key, url = entry["id"], entry["url"]
        metadata[key] = publication(key, entry["title"], entry["format"], entry["publisher"],
                                    entry["date"], url, entry["context"], "editorial-sources.json")
        for topic in entry["topics"]:
            link(key, "topics/"+topic, "discusses", "editorial-sources.json", url)

    video_topics = read_json(HERE / "video-topics.json")
    revision = subprocess.check_output(["git", "log", "-1", "--format=%H", "--", str(RESEARCH)],
                                       cwd=ROOT, text=True).strip()
    archive = f"https://github.com/OmniMCP-AI/local-llm/blob/{revision}/{RESEARCH.relative_to(ROOT)}"
    by_position = {}
    case_sections = {}
    for entry in read_json(RESEARCH / "inventory.json"):
        filename = entry.get("summary_file")
        if not filename:
            continue
        vid = entry["id"]
        source = str(RESEARCH.relative_to(ROOT) / filename)
        note = (RESEARCH / filename).read_text(encoding="utf-8")
        cur = video_topics[vid]
        published = entry.get("published_date")
        if published:
            published = datetime.strptime(published, "%Y%m%d").date().isoformat()
        key = "youtube/" + vid
        metadata[key] = publication(key, entry["title"], "video", entry["channel"], published,
                                    entry["url"], cur["context"], source)
        metadata[key]["note"] = archive + "/" + filename
        by_position[str(entry["position"])] = key
        for line, heading in enumerate(note.splitlines(), start=1):
            m = re.match(r"^### (V[0-9]+-S[0-9]+) ", heading)
            if m:
                case_sections[m[1]] = metadata[key]["note"] + f"?plain=1#L{line}"
        for topic, stamp in cur["topics"].items():
            mins, secs = map(int, stamp.split(":"))
            location = f"https://www.youtube.com/watch?v={vid}&t={mins * 60 + secs}s"
            if location + ")" not in note:
                raise ValueError(f"Topic locator missing in {filename}: {location}")
            link(key, "topics/"+topic, "discusses", source, location)
    if set(by_position.values()) != {"youtube/" + vid for vid in video_topics}:
        raise ValueError("Video topic registry and imported notes have different IDs")

    series = {}
    for row in read_rows("test-series.csv"):
        sid = row["series_id"]
        category = row["category"]
        owner = by_position[row["position"]]
        series[sid] = (owner, category)
        node(sid, sid, str(RESEARCH.relative_to(ROOT) / "test-series.csv"), category=category, url=case_sections[sid])
        link(owner, sid, "reports_series", str(RESEARCH.relative_to(ROOT) / "test-series.csv"), sid)

    case_tasks = read_json(HERE / "case-tasks.json")
    observations = set()
    for row in read_rows("performance-series-observations.csv"):
        oid, sid = row["observation_id"], row["series_id"]
        if series[sid] != ("youtube/" + row["video_id"], row["metric_family"]):
            raise ValueError(f"Observation does not match series {oid}")
        src = str(RESEARCH.relative_to(ROOT) / "performance-series-observations.csv")
        locator = row["source_url"]
        cur = case_tasks.get(oid, {})
        node(oid, row["metric"], src, task=cur.get("task"), url=locator,
             timestamp=row["timestamp"], hardware=row["hardware"], model=row["model"],
             runtime=row["runtime"], quant=row["quantization"], conditions=row["conditions"],
             evidence=row["evidence_type"])
        observations.add(oid)
        link(sid, oid, "contains_observation", src, oid)
        link(oid, "dimensions/"+DIMENSIONS[row["metric_family"]], "has_dimension", src, locator)
        for topic in cur.get("topics", []):
            link(oid, "topics/"+topic, "describes_task", src, locator)
    if case_tasks.keys() - observations:
        raise ValueError("Task assignment refers to an absent observation")

    # Store publication fields in the graph itself for non-UI consumers.
    for n in nodes:
        if n["id"] in metadata:
            n.update(metadata[n["id"]])
    return source_ids


def public_index(graph, source_ids):
    def targets(key, relation):
        return [(target, edge["source_location"]) for _, target, edge in graph.out_edges(key, data=True)
                if edge["relation"] == relation]

    result = []
    for key in source_ids:
        n = graph.nodes[key]
        source = {k: n[k] for k in ("publisher", "date", "context", "url")}
        if n.get("note"):
            source["note"] = n["note"]
        source.update(id=key, title=n["label"], format=targets(key, "has_format")[0][0].split("/")[1],
                      topics={t.split("/")[1]: loc for t, loc in targets(key, "discusses")}, records=[])
        for sid, _ in targets(key, "reports_series"):
            for oid, _ in targets(sid, "contains_observation"):
                obs = graph.nodes[oid]
                record = {k: obs[k] for k in ("hardware", "model", "runtime", "quant", "conditions",
                                               "evidence", "url", "timestamp", "task")}
                record.update(id=oid, series=sid, seriesUrl=graph.nodes[sid]["url"], metric=obs["label"],
                              dimension=targets(oid, "has_dimension")[0][0].split("/")[1],
                              topics=[t.split("/")[1] for t, _ in targets(oid, "describes_task")])
                source["records"].append(record)
        result.append(source)
    return {"taxonomyVersion": VERSION, "sources": result}
