from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import http.client
import json
import re
from time import monotonic
from urllib.parse import quote


RUNTIME = "llama.cpp"
HOST = "api.github.com"
PAGE_SIZE = 10
MAX_BYTES = 4 * 1024 * 1024
REQUEST_TIMEOUT = 8
TAG = re.compile(r"[A-Za-z0-9_][A-Za-z0-9._/+~-]{0,127}")


@dataclass(frozen=True)
class Source:
    name: str
    repository: str

    @property
    def releases_path(self):
        return f"/repos/{self.repository}/releases"

    @property
    def feed_path(self):
        return f"{self.releases_path}?per_page={PAGE_SIZE}&page=1"


SOURCES = {
    RUNTIME: Source("llama.cpp", "ggml-org/llama.cpp"),
    "sglang": Source("SGLang", "sgl-project/sglang"),
    "vllm": Source("vLLM", "vllm-project/vllm"),
    "ollama": Source("Ollama", "ollama/ollama"),
}


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def timestamp(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", value):
        raise ValueError("Expected a UTC timestamp such as 2026-11-21T01:00:00Z")
    return datetime.fromisoformat(value)


def json_text(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fetch(token=None, *, runtime_id=RUNTIME):
    source = SOURCES[runtime_id]
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "fastest.ai-release-watch",
        "X-GitHub-Api-Version": "2026-03-10",
    }
    if token:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", token):
            raise ValueError("Invalid release-watch GitHub token")
        headers["Authorization"] = f"Bearer {token}"
    deadline = monotonic() + REQUEST_TIMEOUT
    try:
        with closing(http.client.HTTPSConnection(HOST, timeout=REQUEST_TIMEOUT)) as connection:
            connection.request("GET", source.feed_path, headers=headers)
            with connection.getresponse() as response:
                if response.status != 200:
                    raise ValueError(f"GitHub release feed returned HTTP {response.status}")
                body = bytearray()
                while len(body) <= MAX_BYTES:
                    if monotonic() >= deadline:
                        raise TimeoutError
                    chunk = response.read1(min(65_536, MAX_BYTES + 1 - len(body)))
                    if not chunk:
                        return body
                    body.extend(chunk)
                raise ValueError("GitHub release feed exceeds the byte limit")
    except TimeoutError as error:
        raise ValueError("GitHub release feed timed out") from error
    except (OSError, http.client.HTTPException) as error:
        raise ValueError("Could not read the GitHub release feed over HTTPS") from error


def decode(body, *, runtime_id=RUNTIME):
    if len(body) > MAX_BYTES:
        raise ValueError("GitHub release feed exceeds the byte limit")
    rows = json.loads(body.decode("utf-8"))
    if not isinstance(rows, list) or len(rows) > PAGE_SIZE:
        raise ValueError("Expected a bounded GitHub release page")
    releases = {}
    for row in rows:
        if not isinstance(row, dict) or row.get("draft") is not False:
            raise ValueError("Expected a published GitHub release record")
        release = release_revision(row, runtime_id=runtime_id)
        external_id = release["release_id"]
        if external_id in releases and releases[external_id] != release:
            raise ValueError("GitHub page contains conflicting revisions of the same release")
        releases[external_id] = release
    return releases.values()


def release_revision(row, *, runtime_id=RUNTIME):
    source = SOURCES[runtime_id]
    release_id = row.get("id")
    tag = row.get("tag_name")
    prerelease = row.get("prerelease")
    published_at = row.get("published_at")
    if type(release_id) is not int or not 0 < release_id < 2**63:
        raise ValueError("Invalid GitHub release ID")
    api_url = f"https://{HOST}{source.releases_path}/{release_id}"
    if row.get("url") != api_url or not isinstance(tag, str) or not TAG.fullmatch(tag):
        raise ValueError(f"Release does not identify an official {source.name} record")
    if type(prerelease) is not bool:
        raise ValueError("Expected a prerelease flag")
    timestamp(published_at)
    public = {
        "release_id": release_id,
        "runtime_id": runtime_id,
        "tag": tag,
        "published_at": published_at,
        "prerelease": prerelease,
        "source_url": f"https://github.com/{source.repository}/releases/tag/{quote(tag, safe='')}",
        "source_api_url": api_url,
    }
    assets = row.get("assets")
    if not isinstance(assets, list) or any(not isinstance(asset, dict) for asset in assets):
        raise ValueError("Expected a GitHub release asset list")
    fingerprint = {
        **public,
        **{key: row.get(key) for key in ("name", "body", "target_commitish", "immutable")},
        "assets": sorted(json_text({
            key: asset.get(key)
            for key in ("id", "name", "digest", "size", "state", "updated_at")
        }) for asset in assets),
    }
    digest = sha256(json_text(fingerprint).encode("utf-8")).hexdigest()
    return {**public, "revision_id": f"github:{source.repository}:{release_id}:{digest}"}
