from copy import deepcopy
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
TASK_FILE = HERE / "task.json"
TASK_BYTES = TASK_FILE.read_bytes()
TASK = json.loads(TASK_BYTES)
POLICIES = {
    "bundle": [{"tool": "read_bundle", "resource": "inventory"}],
    "split": [{"tool": "read_page", "resource": page} for page in TASK["pages"]],
}
BUDGET = {
    "trials": 2,
    "retries_per_trial": 1,
    "tool_reads_per_attempt": 2,
    "generated_tokens_per_attempt": 128,
    "reasoning_tokens_per_attempt": 0,
    "wall_ns_per_attempt": 30_000_000_000,
}


def fingerprint(data):
    return hashlib.sha256(data).hexdigest()


def identity(value):
    return fingerprint(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def read_tool(context_id, tool, resource):
    request = {"tool": tool, "resource": resource}
    if request not in POLICIES.get(context_id, ()):
        raise ValueError("Tool request is outside the pinned fixture read policy")
    if tool == "read_bundle":
        return {"pages": deepcopy(TASK["pages"])}
    return deepcopy(TASK["pages"][resource])


def plan(demo=False):
    pilot = json.loads((HERE.parent / "fastest_text" / "plan.json").read_bytes())
    source_files = {
        name: fingerprint((HERE / name).read_bytes())
        for name in ("harness.py", "evidence.py", "__main__.py")
    }
    harness_sha256 = identity(source_files)
    runtime_revision = pilot["runtime"]["revision"]
    shared = {
        "protocol_id": "inventory-agent-comparison@1",
        "harness": {"id": "fastest_agent_task@1", "sha256": harness_sha256, "files": source_files},
        "task": {
            "id": TASK["id"], "prompt": TASK["prompt"], "rubric": TASK["rubric"],
            "fixture": "task.json", "fixture_sha256": fingerprint(TASK_BYTES),
        },
        "artifact": pilot["artifact"],
        "runtime": {"name": "llama.cpp", "revision": runtime_revision},
        "settings": {
            "context_tokens": 2048, "temperature": 0, "top_k": 1, "seed": 42,
            "threads": 8, "gpu_layers": 99, "batch_tokens": 512, "parallel_requests": 1,
            "template": "Embedded GGUF chat template",
        },
        "budget": BUDGET,
        "controls": {
            "vary": "Fixture tool policy only.",
            "session": "Use one idle host, one loaded model, all layers offloaded to one device, and one unmeasured warmup per context. Start each attempt with empty KV and a new session.",
            "turns": "Send the task prompt, newline and 'Allowed tool requests: ' followed by the compact JSON list. Append each tool result as a compact JSON user turn.",
            "trial_order": "Bundle trial 1, split trial 1, split trial 2, bundle trial 2. Retry a failed attempt immediately, once, with the same input and limits.",
            "wall": "Monotonic elapsed nanoseconds from submission of the opening task message through completion of grading or abort, including tool work. Model load, warmup, session reset and gaps between attempts are excluded.",
            "privacy": "Use only the fictional fixture and local inference. The agent receives no private files, credentials, network, shell, arbitrary paths, write tools or user inputs. Keep raw logs private and publish only the reviewed structured record.",
        },
    }
    if demo:
        shared["artifact"] = {"name": "Offline scripted inventory responses", "sha256": harness_sha256}
        shared["runtime"] = {"name": "Scripted Python demo with illustrative timings"}
        shared["settings"] = {"mode": "scripted"}
        shared["controls"] = {
            **shared["controls"],
            "session": "Offline scripted responses run against the same fixture reads.",
            "wall": "Illustrative nanoseconds for testing the report.",
        }
    contexts = [{"id": name, "allowed_reads": reads} for name, reads in POLICIES.items()]
    return {
        **shared,
        "contexts": [{**context, "sha256": identity({"conditions": shared, "context": context})} for context in contexts],
    }


def demo_attempts(context_id):
    # The short first split attempt deliberately reads only page a and fails.
    order = [(1, 1), (1, 2), (2, 1)] if context_id == "split" else [(1, 1), (2, 1)]
    attempts = []
    for trial, attempt in order:
        reads = POLICIES[context_id]
        if len(order) == 3 and (trial, attempt) == (1, 1):
            reads = reads[:1]
        pages = []
        for request in reads:
            result = read_tool(context_id, request["tool"], request["resource"])
            pages.extend(result["pages"].values() if "pages" in result else [result])
        subtotal = sum(row["units"] for page in pages for row in page["rows"] if row["status"] == "open")
        attempts.append({
            "trial": trial, "attempt": attempt, "wall_ns": 10_000 * len(reads),
            "generated_tokens": None, "reasoning_tokens": 0, "termination": "answered",
            "answer": {"open_units": subtotal}, "tool_reads": reads,
        })
    return attempts
