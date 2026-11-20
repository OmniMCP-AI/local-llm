from html import escape
import re


def markdown_text(value):
    return re.sub(r"([\\`*_{}\[\]<>#!&|~])", r"\\\1", str(value))


def render(dataset, data_hash):
    label = {
        "planned": "Planned comparison. Both machines have recorded access blockers.",
        "synthetic": "Synthetic demonstration. These values illustrate the intake.",
        "measured": "Reviewed run records for the stated machines and protocol.",
    }[dataset["evidence_kind"]]
    title = "Two-machine image pilot"
    md = [f"# {title}"]
    html = [
        '<!doctype html><html lang="en"><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f'<title>{title}</title>',
        '<link rel="alternate" type="text/markdown" href="./image-pilot.md">',
        f'<main><h1>{title}</h1>',
    ]

    def paragraph(value):
        md.append(markdown_text(value))
        html.append(f"<p>{escape(str(value))}</p>")

    def heading(value):
        md.append(f"## {markdown_text(value)}")
        html.append(f"<h2>{escape(value)}</h2>")

    def links(items):
        md.append(" · ".join(f"[{markdown_text(name)}](<{url}>)" for name, url in items))
        html.append("<p>" + " · ".join(f'<a href="{escape(url, quote=True)}">{escape(name)}</a>' for name, url in items) + "</p>")

    def table(columns, rows):
        def line(values):
            return "| " + " | ".join(map(markdown_text, values)) + " |"

        md.append("\n".join([line(columns), line(["---"] * len(columns)), *(line(row) for row in rows)]))
        html.append(
            "<table><thead><tr>"
            + "".join(f'<th scope="col">{escape(column)}</th>' for column in columns)
            + "</tr></thead><tbody>"
            + "".join(
                f'<tr><th scope="row">{escape(str(row[0]))}</th>'
                + "".join(f"<td>{escape(str(item))}</td>" for item in row[1:]) + "</tr>"
                for row in rows
            )
            + "</tbody></table>"
        )

    paragraph(label)
    links([("Typed data", "./image-pilot.json"), ("Exact workflow", "./workflow.json"), ("Manifest", "./manifest.json")])
    paragraph(f"Typed dataset SHA-256 {data_hash}")
    paragraph(f"Initial access check recorded on {dataset['access_checked_on']}.")

    table(
        ("Machine", "Backend", "Status", "Repeats", "Failures", "Accepted", "Median completion", "Seconds per accepted image", "Access blocker"),
        [
            (
                cell["name"], cell["backend"], cell["status"], cell["repeat_count"], cell["failure_count"],
                cell["quality"]["accepted_count"], *(metric_display(metric) for metric in cell["metrics"].values()),
                cell["blocker"] or "—",
            )
            for cell in dataset["cells"]
        ],
    )
    protocol = dataset["protocol"]
    workflow, runtime, artifact = (dataset[key] for key in ("workflow", "runtime", "artifact"))
    heading("Fixed workflow and timing")
    paragraph(
        f"{workflow['width']} × {workflow['height']} pixels, batch {workflow['batch_size']}, "
        f"{workflow['sampler']} with {workflow['scheduler']}, {workflow['steps']} step, "
        f"CFG {workflow['cfg']}, denoise {workflow['denoise']}."
    )
    paragraph(f"Workflow SHA-256 {workflow['sha256']}.")
    paragraph(f"{runtime['name']} {runtime['tag']} at {runtime['revision']}. CPython {runtime['python']}.")
    paragraph(f"{artifact['repository']} at {artifact['revision']}. Checkpoint SHA-256 {artifact['sha256']}.")
    paragraph(f"{artifact['license']}. {artifact['components']}")
    paragraph("The report distributes protocol metadata and reviewed records. Commercial execution and any public distribution of generated images require a separate rights review.")
    links([
        ("Pinned ComfyUI source", runtime["source"]), ("Official checkpoint", artifact["source"]),
        ("Checkpoint terms", artifact["license_source"]),
        ("Comfy workflow reference", workflow["reference"]),
        *((f"{cell['name']} dependency lock", "./" + cell["lock"]["path"]) for cell in dataset["cells"]),
    ])
    paragraph(f"Protocol {protocol['id']}. Warmup seed {protocol['warmup_seed']}. Repeat seeds {', '.join(map(str, protocol['repeat_seeds']))}.")
    paragraph(f"Each request has a {protocol['timeout_s']}-second deadline.")
    paragraph(protocol["method"])
    paragraph(protocol["boundary"])
    table(("Client endpoint", "Timing boundary"), [(phase["id"], phase["boundary"]) for phase in protocol["phase_endpoints"]])
    paragraph("Median completion uses successful measured requests. Seconds per accepted image divides the total elapsed time of all five measured repeats, including failures and rejects, by the number accepted. The warmup has no weight in either metric.")

    rubric = dataset["rubric"]
    heading("Acceptance rubric")
    paragraph(rubric["provenance"])
    paragraph(rubric["method"])
    table(("Criterion", "Pass condition"), list(rubric["criteria"].items()))

    phases = [phase["id"] for phase in protocol["phase_endpoints"]]
    for cell in dataset["cells"]:
        if not cell["attempts"]:
            continue
        heading(f"{cell['name']} run evidence")
        build = cell["runtime_build"]
        paragraph(f"{build['machine']} · {build['os_driver']} · {build['effective_placement']}")
        paragraph(f"Runtime build {build['provenance']}. Dependency lock SHA-256 {cell['lock']['sha256']}.")
        links([("Reviewed evidence", cell["source"]["locator"])])
        paragraph(f"Evidence revision {cell['source']['revision']}. Public rights decision {cell['rights']['decision_id']}. {cell['rights']['basis']}")
        table(
            ("Phase", "Seed", "Outcome", "Elapsed ns", "Phase endpoints in ns from POST", "Failure or image digest", "Review"),
            [
                (
                    attempt["phase"], attempt["seed"], attempt["outcome"], attempt["elapsed_ns"],
                    ", ".join(f"{phase}={attempt['phase_end_ns'][phase]}" for phase in phases if phase in attempt["phase_end_ns"]) or "—",
                    attempt.get("reason") or attempt["output_sha256"], review_display(attempt),
                )
                for attempt in cell["attempts"]
            ],
        )
    html.append('<p><a href="./image-pilot.md">Markdown companion</a></p>')
    return "\n\n".join(md) + "\n", "\n".join(html + ["</main></html>"]) + "\n"


def metric_display(metric):
    if metric["status"] == "missing":
        return metric["reason"]
    return f"{metric['value']} {metric['unit']} ({metric['sample_count']} repeats)"


def review_display(attempt):
    review = attempt.get("review")
    if not review:
        return "Pending" if attempt["phase"] == "repeat" and attempt["outcome"] == "success" else "—"
    criteria = ", ".join(f"{criterion} {'pass' if passed else 'fail'}" for criterion, passed in sorted(review["scores"].items()))
    return f"{review['reviewer']} · {criteria} · {review['note']}"
