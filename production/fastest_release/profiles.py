"""Reciprocal machine and model pages for the two pinned pilot cohorts."""

from decimal import Decimal
from hashlib import sha256
from html import escape
import json
import re
from urllib.parse import quote
from uuid import UUID

from fastest_text.__main__ import PLAN_PATH as TEXT_PLAN
from fastest_image.__main__ import PACKAGE as IMAGE_PACKAGE

from .artifacts import _markdown_text, _source_url


MODELS = {
    "qwen2.5-7b-instruct": ("Qwen2.5 7B Instruct", TEXT_PLAN),
    "sdxl-turbo": ("SDXL Turbo", IMAGE_PACKAGE / "plan.json"),
}


RUN_ID = re.compile(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}")
EXCLUSIONS = {
    "artifact_mismatch": "The exact artifact repository, revision, file or digest differs from the pin.",
    "backend_mismatch": "The approved backend differs from the planned backend for this machine.",
    "contributor": "The release labels this measurement contributor-reported. It is excluded from controlled comparisons.",
    "insufficient_samples": "The observation has fewer samples than the cohort requires.",
    "metric_mismatch": "The metric definition differs from the pinned unit, statistic or measurement boundary.",
    "missing_primary": "The approved run lacks the ranking metric.",
    "setup_mismatch": "Multiple observations for this run conflict on the setup or metric revision.",
    "runtime_mismatch": "The runtime or image workflow revision differs from the pin.",
    "synthetic": "The release labels this observation synthetic.",
    "unavailable": "An underlying source release is unavailable.",
    "unknown_run": "The approved observation does not identify a run.",
    "withdrawn": "An underlying source release has been withdrawn.",
    "workload_mismatch": "The workload protocol differs from the pin.",
}


def metric_definitions(plan):
    protocol = plan["protocol"]
    if "phases" in protocol:
        return {
            "llama-bench-" + phase: {
                "label": protocol["phases"][phase]["label"] + " throughput", "unit": "tok/s",
                "statistic": "median", "direction": "higher", "boundary": protocol["phases"][phase]["boundary"],
                "min_samples": protocol["warm_samples_per_phase"], "version": 1,
            }
            for phase in ("decode", "prefill")
        }
    return {
        "comfyui-seconds-per-accepted-image": {
            "label": "Seconds per accepted image", "unit": "s/image", "statistic": "ratio", "direction": "lower",
            "boundary": "Sum of repeat elapsed times including failed and rejected attempts divided by accepted repeats.",
            "min_samples": len(protocol["repeat_seeds"]), "version": 1,
        },
        "comfyui-median-completion": {
            "label": "Median completion time", "unit": "s", "statistic": "median", "direction": "lower",
            "boundary": protocol["boundary"], "min_samples": len(protocol["repeat_seeds"]), "version": 1,
        },
    }


def public_field(row, key):
    field = row["fields"].get(key, {})
    return field.get("value") if field.get("status") == "known" else None


def exclusion_reason(plan, cell, row, metrics):
    if row["kind"] == "contributor":
        return "contributor"
    if row["kind"] != "measured":
        return "synthetic"
    if not RUN_ID.fullmatch(public_field(row, "run_id") or ""):
        return "unknown_run"
    workload = row["workload"]
    if f"{workload['id']}@{workload['version']}" != plan["protocol"]["id"]:
        return "workload_mismatch"
    if public_field(row, "runtime_revision") != plan["runtime"]["revision"]:
        return "runtime_mismatch"
    if public_field(row, "backend") != cell["backend"]:
        return "backend_mismatch"
    pin = plan["artifact"]
    exact_file = pin["shards"][0] if "shards" in pin else pin
    artifact = row["artifact"]
    if any(artifact[key] != pin[key] for key in ("repository", "revision")) or any(
        artifact[key] != exact_file[key] for key in ("sha256", "path")
    ):
        return "artifact_mismatch"
    if "shards" in pin:
        if artifact["format"] != "GGUF" or artifact["quantization"] != pin["quantization"] or (
            public_field(row, "artifact_companion_sha256") != pin["shards"][1]["sha256"]
        ):
            return "artifact_mismatch"
    elif artifact["format"] != "Safetensors" or artifact["quantization"] != "FP16":
        return "artifact_mismatch"
    if "workflow" in plan and public_field(row, "workflow_sha256") != plan["workflow"]["sha256"]:
        return "runtime_mismatch"
    metric = row["metric"]
    definition = metrics.get(metric["id"])
    if definition is None or any(metric[key] != definition[key] for key in ("version", "unit", "statistic", "boundary")):
        return "metric_mismatch"
    if metric["sample_count"] < definition["min_samples"]:
        return "insufficient_samples"
    return None


def accessible_table(caption, columns, rows):
    header = "".join(f'<th scope="col">{escape(column)}</th>' for column in columns)
    return (
        f"<table><caption>{escape(caption)}</caption><thead><tr>{header}</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def safe_source(source):
    location = source["locator"]
    url = _source_url(location)
    return (f'<a href="{escape(url)}">{escape(source["label"])}</a>' if url
            else f'{escape(source["label"])} · {escape(location)}')


def html_page(title, content, markdown=None, script=None):
    alternate = f'<link rel="alternate" type="text/markdown" href="{escape(markdown)}">' if markdown else ""
    javascript = f'<script src="{escape(script)}" defer></script>' if script else ""
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} · fastest.ai</title>{alternate}
<style>
body {{ font: 1rem/1.5 system-ui,sans-serif; color: #232b35; max-width: 70rem; margin: 2rem auto; padding: 0 1rem; overflow-wrap: anywhere; }}
main {{ display: grid; gap: 1.5rem; }}
.chart-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(min(25rem, 100%), 1fr)); gap: 1.5rem; }}
.chart-grid figure {{ margin: 0; }}
.ranking {{ padding-inline-start: 1.5rem; }}
.ranking li {{ margin: .4rem 0; }}
.ranking a {{ display: block; padding: .4rem; }}
.overview-map {{ width: min(100%, 28rem); height: auto; color: #006450; }}
.overview-map .axis {{ stroke: #62767a; stroke-width: 1; fill: none; }}
.overview-map circle {{ fill: currentColor; }}
.overview-map .hit {{ fill: transparent; }}
.overview-map [data-selected="true"] .mark, .overview-map a:hover .mark, .overview-map a:focus-visible .mark {{ stroke: #232b35; stroke-width: 2; }}
[data-selected="true"] {{ background: #e5f3ef; }}
.run-drawer {{ margin-top: 1rem; padding: 1rem; border: 1px solid #bac2cc; }}
.run-drawer summary {{ cursor: pointer; font-weight: 700; }}
[data-profile-preview] {{ min-height: 1.5em; }}
h1, h2, h3 {{ margin: 0; }}
section {{ padding: 1rem 0; border-top: 1px solid #bac2cc; }}
table {{ width: 100%; border-collapse: collapse; }}
caption, th, td {{ text-align: left; padding: .5rem; }}
caption {{ font-weight: 700; }}
th, td {{ border-bottom: 1px solid #bac2cc; vertical-align: top; }}
:focus-visible {{ outline: 2px solid #006450; outline-offset: 3px; }}
</style>{javascript}</head><body><main>{content}</main></body></html>
"""


class ProfileRelease:
    def __init__(self, store=None, release_ids=()):
        self.store = store
        self.release_ids = sorted({str(UUID(release_id)) for release_id in release_ids})
        if self.release_ids and store is None:
            raise ValueError("Profile measurements require a release store.")
        self.plans = {model: json.loads(path.read_text(encoding="utf-8")) for model, (_, path) in MODELS.items()}
        self.machines = {cell["id"]: cell["name"] for plan in self.plans.values() for cell in plan["cells"]}
        manifest = {
            "models": {key: value[0] for key, value in MODELS.items()}, "plans": self.plans,
            "observation_releases": self.release_ids,
            "metrics": {key: metric_definitions(plan) for key, plan in self.plans.items()},
        }
        manifest = json.dumps(manifest, ensure_ascii=False, sort_keys=True).encode("utf-8")
        self.id = "v1-" + sha256(manifest).hexdigest()[:16]
        self.base = f"/profiles/{self.id}"

    def url(self, kind, identity, extension="html"):
        return f"{self.base}/{kind}/{quote(identity)}.{extension}"

    def catalog(self):
        return [
            {"kind": kind, "id": identity, "name": name}
            for kind, items in (("machines", self.machines), ("models", {key: value[0] for key, value in MODELS.items()}))
            for identity, name in items.items()
        ]

    def index(self):
        profiles = self.catalog()
        groups = "".join(
            f'<section id="{kind}"><h2>{kind.title()}</h2><ul>'
            + "".join(f'<li><a href="{self.url(kind, entry["id"])}">{escape(entry["name"])}</a></li>'
                      for entry in profiles if entry["kind"] == kind)
            + "</ul></section>"
            for kind in ("machines", "models")
        )
        return html_page("Machine and model comparisons", "<header><h1>Machine and model comparisons</h1>"
                         f"<p>Release <code>{self.id}</code></p></header>{groups}")

    def data(self, kind, identity):
        names = self.machines if kind == "machines" else {key: value[0] for key, value in MODELS.items()}
        if identity not in names:
            raise LookupError(identity)
        snapshots = self.store.read_many(self.release_ids) if self.release_ids else []
        identities = {}
        for snapshot in snapshots:
            row = snapshot.get("row")
            if row and row["kind"] == "measured":
                run_id = public_field(row, "run_id")
                setup = (public_field(row, "profile_cell"), row["artifact"]["repository"], row["workload"]["id"])
                if run_id:
                    identities.setdefault(run_id, set()).add(setup)
        ambiguous_runs = {run_id for run_id, setups in identities.items() if len(setups) > 1}
        cohorts = [self.cohort(kind, identity, model, plan, snapshots, ambiguous_runs) for model, plan in self.plans.items()
                   if kind == "machines" or model == identity]
        return {"release": self.id, "profile": {"id": identity, "kind": kind, "name": names[identity]}, "cohorts": cohorts}

    def cohort(self, kind, identity, model, plan, snapshots, ambiguous_runs):
        cells = {cell["id"]: cell for cell in plan["cells"] if kind == "models" or cell["id"] == identity}
        metrics = metric_definitions(plan)
        primary, secondary = metrics
        model_name = MODELS[model][0]
        exclusions = []

        def exclude(status, cell=None, release_id=None):
            counterpart = None
            if kind == "machines":
                counterpart = ("models", model, model_name)
            elif cell:
                counterpart = ("machines", cell["id"], cell["name"])
            exclusions.append({
                "status": status, "cell_id": cell["id"] if cell else None,
                "reason": cell["blocker"] if status == "blocked" else EXCLUSIONS[status],
                "backend": cell["backend"] if cell else None, "profile_name": counterpart[2] if counterpart else None,
                "profile_url": self.url(*counterpart[:2]) if counterpart else None, "source_release": release_id,
            })

        groups = {}
        for snapshot in snapshots:
            release_id = snapshot["release_id"]
            if snapshot["status"] != "published":
                exclude(snapshot["status"], release_id=release_id)
                continue
            row = snapshot["row"]
            cell = cells.get(public_field(row, "profile_cell"))
            # A candidate must identify this pilot by repository, workload or metric family.
            if not cell or not (
                row["artifact"]["repository"] == plan["artifact"]["repository"]
                or f"{row['workload']['id']}@{row['workload']['version']}" == plan["protocol"]["id"]
                or row["metric"]["id"] in metrics
            ):
                continue
            reason = exclusion_reason(plan, cell, row, metrics)
            if reason:
                exclude(reason, cell, release_id)
                continue
            run_id = public_field(row, "run_id")
            if run_id in ambiguous_runs:
                exclude("setup_mismatch", cell, release_id)
                continue
            groups.setdefault(run_id, []).append((cell, row, release_id))

        rows = []
        for run_id, observations in groups.items():
            cell, row, _ = observations[0]
            by_metric = {source["metric"]["id"]: {**source["metric"], "evidence_id": source["evidence_id"],
                         "release_id": release_id, "source": source["source"], "rights": source["rights"]}
                         for _, source, release_id in observations}
            if len(by_metric) != len(observations) or any(
                record[0]["id"] != cell["id"] or record[1]["hardware"] != row["hardware"] or record[1]["artifact"] != row["artifact"]
                for record in observations
            ):
                exclude("setup_mismatch", cell)
                continue
            if primary not in by_metric:
                exclude("missing_primary", cell)
                continue
            suffix = f"?run={run_id}#run-{run_id}"
            rows.append({
                "run_id": run_id, "cell_id": cell["id"], "backend": cell["backend"], "hardware": row["hardware"],
                "model": model_name, "machine_url": self.url("machines", cell["id"]) + suffix,
                "model_url": self.url("models", model) + suffix, "metrics": by_metric,
            })
        def rank_key(run):
            value = Decimal(run["metrics"][primary]["value"])
            return (value.copy_negate() if metrics[primary]["direction"] == "higher" else value, run["run_id"])

        rows.sort(key=rank_key)
        for cell in cells.values():
            if not any(row["cell_id"] == cell["id"] for row in rows) and not any(
                exclusion["cell_id"] == cell["id"]
                for exclusion in exclusions
            ):
                exclude("blocked", cell)
        return {
            "id": plan["id"], "plan_date": plan["access_checked_on"], "model": model_name,
            "workload": plan["protocol"]["id"], "artifact": plan["artifact"], "runtime": plan["runtime"],
            "workflow": plan.get("workflow"), "metrics": metrics, "primary_metric": primary, "secondary_metric": secondary,
            "ranking": [row["run_id"] for row in rows], "map": [row["run_id"] for row in rows if secondary in row["metrics"]],
            "rows": rows, "exclusions": sorted(exclusions, key=lambda entry: (entry["status"], entry["source_release"] or "")),
        }

    @staticmethod
    def row_label(run, kind):
        return run["model"] if kind == "machines" else run["hardware"]["name"]

    @staticmethod
    def run_selector(run, selected):
        run_id = run["run_id"]
        preview = f"{run['hardware']['name']} · {run['model']} · {run['backend']} · {run['hardware']['configuration']}"
        return (f'data-run-id="{run_id}" data-selected="{str(run_id == selected).lower()}" '
                f'data-preview="{escape(preview)}" href="?run={run_id}#run-{run_id}"')

    def overview(self, cohort, kind, selected):
        primary, secondary = cohort["primary_metric"], cohort["secondary_metric"]
        rows = [run for run in cohort["rows"] if run["run_id"] in cohort["map"]]
        if not rows:
            return "<figure><figcaption>Overview map</figcaption><p>No eligible run has both map metrics.</p></figure>"
        x_max = max(Decimal(1), *(Decimal(run["metrics"][secondary]["value"]) for run in rows))
        y_max = max(Decimal(1), *(Decimal(run["metrics"][primary]["value"]) for run in rows))
        points = []
        for run in rows:
            x = 42 + 228 * Decimal(run["metrics"][secondary]["value"]) / x_max
            y = 150 - 120 * Decimal(run["metrics"][primary]["value"]) / y_max
            values = ", ".join(f'{run["metrics"][metric]["value"]} {run["metrics"][metric]["unit"]}'
                               for metric in (secondary, primary))
            label = escape(f"{self.row_label(run, kind)} · {values}")
            points.append(f'<a {self.run_selector(run, selected)} aria-label="{label}"><title>{label}</title>'
                          f'<circle class="hit" cx="{x:.3f}" cy="{y:.3f}" r="14"/>'
                          f'<circle class="mark" cx="{x:.3f}" cy="{y:.3f}" r="5"/></a>')
        horizontal, vertical = cohort["metrics"][secondary], cohort["metrics"][primary]
        return ("<figure><figcaption>Overview map</figcaption>"
                '<svg class="overview-map" role="group" aria-label="Measured run overview" viewBox="0 0 300 180">'
                '<path class="axis" d="M42 25 V150 H275"/><text x="32" y="166" font-size="9">0</text>'
                f'<text x="270" y="166" text-anchor="end" font-size="9">{x_max}</text>'
                f'<text x="36" y="34" text-anchor="end" font-size="9">{y_max}</text>'
                + "".join(points) + '</svg>'
                f'<p>Horizontal · {horizontal["label"]} ({horizontal["unit"]})<br>'
                f'Vertical · {vertical["label"]} ({vertical["unit"]})</p></figure>')

    def measurements(self, cohort, kind, selected):
        if not cohort["rows"]:
            return f'<p>No eligible measured runs. Access checked on {cohort["plan_date"]}.</p>'
        primary, secondary = cohort["primary_metric"], cohort["secondary_metric"]
        metric = cohort["metrics"][primary]
        bullets, table_rows, drawers = [], [], []
        for run in cohort["rows"]:
            run_id = run["run_id"]
            label = escape(self.row_label(run, kind))
            selector = self.run_selector(run, selected)
            exact = [escape(f'{run["metrics"][axis]["value"]} {run["metrics"][axis]["unit"]} '
                            f'(n={run["metrics"][axis]["sample_count"]})') if axis in run["metrics"] else "Missing"
                     for axis in (primary, secondary)]
            bullets.append(f'<li><a {selector}>{label} · {exact[0]}</a></li>')
            table_rows.append(f'<tr><th scope="row"><a {selector}>{label}</a></th>'
                              f'<td>{run["backend"]}</td><td>{exact[0]}</td><td>{exact[1]}</td></tr>')
            counterpart = "model" if kind == "machines" else "machine"
            evidence = "".join(f'<li>{escape(cohort["metrics"][axis]["label"])} · {safe_source(observation["source"])} '
                               f'(revision <code>{escape(observation["source"]["revision"])}</code>) · '
                               f'<a href="/releases/{observation["release_id"]}/benchmark.html">Evidence {observation["evidence_id"]}</a> '
                               f'· Rights decision <code>{observation["rights"]["decision_id"]}</code></li>'
                               for axis, observation in run["metrics"].items())
            missing = "<p>The secondary metric is unavailable, so this run has no map point.</p>" if secondary not in run["metrics"] else ""
            opened = " open" if run_id == selected else ""
            drawers.append(f'<details class="run-drawer" id="run-{run_id}"{opened}><summary>{label} run evidence</summary>'
                           f'<p>{escape(run["hardware"]["configuration"])} · {run["backend"]}.</p>'
                           f'<p>Hardware revision <code>{run["hardware"]["revision_id"]}</code> · Run <code>{run_id}</code>.</p>'
                           f'{missing}<ul>{evidence}</ul><p><a href="{run[counterpart + "_url"]}">Open {counterpart} profile</a></p></details>')
        ranking = (f'<div><h3>{metric["label"]} ranking</h3><p>{metric["direction"].title()} is better.</p>'
                   f'<ol class="ranking">{"".join(bullets)}</ol></div>')
        table = accessible_table("Exact run values", ["Profile", "Backend", metric["label"], cohort["metrics"][secondary]["label"]], table_rows)
        return (f'<div class="chart-grid">{ranking}{self.overview(cohort, kind, selected)}</div>'
                '<p data-profile-preview aria-live="polite"></p>' + table + "".join(drawers))

    def render(self, data, selected=None):
        profile = data["profile"]
        json_url = self.url(profile["kind"], profile["id"], "json")
        md_url = self.url(profile["kind"], profile["id"], "md")
        cohorts = []
        for cohort in data["cohorts"]:
            artifact = cohort["artifact"]
            files = [artifact] if "sha256" in artifact else artifact["shards"]
            file_list = "".join(f"<li>{escape(file['path'])} · <code>{file['sha256']}</code></li>" for file in files)
            workflow = cohort["workflow"]
            if workflow:
                file_list += f"<li>Workflow <code>{workflow['sha256']}</code></li>"
            exclusions = []
            for item in cohort["exclusions"]:
                link = f'<a href="{item["profile_url"]}">{escape(item["profile_name"])}</a>' if item["profile_url"] else "Source release"
                status = item["status"].replace("_", " ").title()
                exclusions.append(f'<tr><th scope="row">{link}</th><td>{item["backend"] or "—"}</td>'
                                  f'<td>{status}</td><td>{escape(item["reason"])}</td></tr>')
            excluded_table = accessible_table("Cohort exclusions", ["Profile", "Backend", "Status", "Access blocker or exclusion reason"], exclusions) if exclusions else ""
            rules = "".join(f'<li>{metric["label"]} ({metric["unit"]}, {metric["statistic"]}, '
                            f'minimum {metric["min_samples"]} samples). {escape(metric["boundary"])}</li>'
                            for metric in cohort["metrics"].values())
            cohorts.append(f"""<section data-cohort><h2>{escape(cohort['model'])}</h2>
<p>Workload <code>{escape(cohort['workload'])}</code> · Artifact <a href="{escape(artifact['source'])}">{escape(artifact['repository'])}</a> at <code>{artifact['revision']}</code></p>
<p>{escape('GGUF ' + artifact['quantization'] if 'shards' in artifact else 'Safetensors FP16')} · {escape(artifact['license'])}</p>
<p>Runtime {escape(cohort['runtime']['name'])} at <code>{cohort['runtime']['revision']}</code>. The planned machine and backend vary together.</p>
<details><summary>Exact files and ranking rules</summary><ul>{file_list}</ul><ul>{rules}</ul></details>
{self.measurements(cohort, profile['kind'], selected)}{excluded_table}</section>""")
        header = (f'<header><p><a href="{self.base}/index.html">Machine and model comparisons</a></p>'
                  f'<h1>{escape(profile["name"])}</h1><p>Release <code>{self.id}</code> · '
                  f'<a href="{json_url}">Typed comparison data</a> · <a href="{md_url}">Markdown</a></p></header>')
        script = "/profiles/interaction.js" if any(cohort["rows"] for cohort in data["cohorts"]) else None
        return html_page(profile["name"], header + "".join(cohorts), md_url, script)

    def markdown(self, data):
        profile = data["profile"]
        metadata = {"page_id": profile["id"], "release": self.id, "kind": profile["kind"], "locale": "en",
                    "path": self.url(profile["kind"], profile["id"]),
                    "data": self.url(profile["kind"], profile["id"], "json"),
                    "methods": [cohort["workload"] for cohort in data["cohorts"]],
                    "evidence": sorted({metric["evidence_id"] for cohort in data["cohorts"] for row in cohort["rows"]
                                        for metric in row["metrics"].values()})}
        lines = ["---", *(f"{key}: {json.dumps(value)}" for key, value in metadata.items()), "---", "", f"# {profile['name']}"]
        for cohort in data["cohorts"]:
            artifact = cohort["artifact"]
            lines.extend(["", f"## {cohort['model']}", "", f"Workload `{cohort['workload']}`.",
                          f"Artifact [{artifact['repository']}]({artifact['source']}) at `{artifact['revision']}`.",
                          f"Runtime {cohort['runtime']['name']} at `{cohort['runtime']['revision']}`.", ""])
            for file in artifact.get("shards", [artifact]):
                lines.append(f"- `{file['path']}` · `{file['sha256']}`")
            if cohort["workflow"]:
                lines.append(f"- Workflow `{cohort['workflow']['sha256']}`")
            lines.append("")
            primary = cohort["primary_metric"]
            if cohort["rows"]:
                lines.extend([f"{cohort['metrics'][primary]['label']} ranking · {cohort['metrics'][primary]['direction']} is better.", ""])
                for row in cohort["rows"]:
                    label = _markdown_text(self.row_label(row, profile["kind"]))
                    url = row["model_url"] if profile["kind"] == "machines" else row["machine_url"]
                    values = " · ".join(f"{cohort['metrics'][metric_id]['label']} {metric['value']} {metric['unit']} (n={metric['sample_count']}) "
                                       f"([evidence](/releases/{metric['release_id']}/benchmark.html))"
                                       for metric_id, metric in row["metrics"].items())
                    lines.append(f"- [{label}]({url}) · `{row['run_id']}` · {values}")
            else:
                lines.append(f"No eligible measured runs. Access checked on {cohort['plan_date']}.")
            if cohort["exclusions"]:
                lines.extend(["", "Cohort exclusions", ""])
                for item in cohort["exclusions"]:
                    pointer = f"[{item['profile_name']}]({item['profile_url']})" if item["profile_url"] else "Source release"
                    lines.append(f"- {pointer} · {item['status'].replace('_', ' ')} · {item['reason']}")
        return "\n".join(lines) + "\n"
