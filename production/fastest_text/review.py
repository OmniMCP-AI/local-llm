"""Prepare Chinese task outputs for independent review."""

from hashlib import sha256
import json
from random import SystemRandom
from uuid import uuid4

from fastest_pilot_bundle import digest
from fastest_pilot_capture import save_json, utc_now


def completion_text(raw, path):
    try:
        choices = json.loads(raw)["choices"]
        choice, = choices
        message = choice["message"]
        if message["role"] == "assistant" and isinstance(message["content"], str) and message["content"].strip():
            return message["content"]
    except (KeyError, TypeError, ValueError, RecursionError):
        pass
    raise ValueError(f"Expected one nonempty assistant completion in {path}.")


def write_review_packet(destination, response_paths, rubric):
    outputs = []
    private = {}
    seen_paths = set()
    for response in response_paths:
        response = response.resolve()
        if response in seen_paths:
            raise ValueError(f"Response file supplied more than once: {response}")
        seen_paths.add(response)
        raw = response.read_bytes()
        answer = completion_text(raw, response)
        output_id = str(uuid4())
        output_sha256 = digest(answer)
        outputs.append({
            "answer": answer,
            "rating": {
                "task_id": rubric["task_id"], "output_id": output_id, "output_sha256": output_sha256,
                "reviewer": "", "scores": dict.fromkeys(rubric["criteria"]), "note": "",
            },
        })
        private[output_id] = {
            "response_path": str(response), "response_sha256": sha256(raw).hexdigest(),
            "output_sha256": output_sha256,
        }
    SystemRandom().shuffle(outputs)
    destination.mkdir(mode=0o700)
    save_json(destination / "private-map.json", {
        "schema_version": 1, "rubric_id": rubric["id"], "created_utc": utc_now(), "outputs": private,
    })
    save_json(destination / "review-packet.json", {
        "schema_version": 1, "rubric_id": rubric["id"], "language": rubric["language"],
        "task_id": rubric["task_id"], "prompt": rubric["prompt"], "criteria": rubric["criteria"], "outputs": outputs,
    })
