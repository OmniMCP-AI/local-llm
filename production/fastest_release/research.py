"""Reconcile the retained video seed into a private, replayable intake snapshot."""
import csv
from collections import defaultdict
from hashlib import sha256
import io
import json
from pathlib import Path

from . import _sql_text, ReleaseNotFound


SEED_ROOT = (
    Path(__file__).resolve().parents[2]
    / "docs" / "Local-AI-Comparison-Platform" / "YouTube-Local-LLM-Transcripts"
)
UPSTREAM_COMMIT = "26450cccaf3a3f14b1822875f2473847a744a718"
NOTICE = "llmfit/LICENSE.llmfit-MIT.txt"
EXPECTED_COUNTS = {
    "profiles": 116,
    "components": 487,
    "legacy_hardware": 99,
    "series": 242,
    "observations": 450,
    "qualified_associations": 293,
    "unassigned_observations": 157,
    "native_hardware_profiles": 16,
    "partial_hardware_profiles": 100,
    "complete_builds": 0,
    "structural_benchmarks": 127,
    "research_only_observations": 323,
    "partial_model_references": 140,
    "native_models": 0,
    "native_community_submissions": 0,
}


def _require(condition, context):
    if not condition:
        raise ValueError(f"Research seed disagrees at {context}")


class _Sources:
    def __init__(self, root):
        self.root = root
        self.digests = {}

    def read(self, path):
        data = (self.root / path).read_bytes()
        self.digests[path] = sha256(data).hexdigest()
        return data.decode("utf-8")

    def json(self, path):
        return json.loads(self.read(path))

    def csv(self, path):
        reader = csv.reader(io.StringIO(self.read(path), newline=""), strict=True)
        fields = next(reader, [])
        _require(fields and len(set(fields)) == len(fields), f"{path} header")
        line = reader.line_num + 1
        for values in reader:
            if values:
                _require(len(values) == len(fields), f"{path}:{line}")
                yield dict(zip(fields, values)), {"path": path, "line": line}
            line = reader.line_num + 1

    def index(self, path, key, *, envelope=None):
        if path.endswith(".csv"):
            located = self.csv(path)
        else:
            located = (
                (row, {"path": path, "pointer": f"/{index}"})
                for index, row in enumerate(self.json(path))
            )
        records = {}
        for row, source in located:
            identifier = (row if envelope is None else row[envelope])[key]
            _require(identifier and identifier not in records, f"{path}/{identifier}")
            records[identifier] = (row, source)
        return records


def _reconcile(root):
    sources = _Sources(root)
    source_log = sources.json("llmfit/upstream-source-log.json")
    _require(source_log["head_commit"] == UPSTREAM_COMMIT, "llmfit pin")
    sources.read(NOTICE)

    extension = "x_local_ai_research"
    profiles = sources.index("hardware-profiles.json", "profile_id")
    profile_maps = sources.index("llmfit/research/hardware.json", "profile_id", envelope=extension)
    legacy = sources.index("hardware-configurations.csv", "config_id")
    series = sources.index("test-series.csv", "series_id")
    series_mirror = sources.index("llmfit/research/test-series.json", "series_id")
    observations = sources.index("performance-observations.csv", "observation_id")
    series_rows = sources.index("performance-series-observations.csv", "observation_id")
    observation_maps = sources.index("llmfit/research/benchmarks.json", "observation_id", envelope=extension)
    associations = sources.index("profile-performance-links.csv", "observation_id")
    models = sources.index("llmfit/research/models.json", "model_reference_id", envelope=extension)
    conversions = sources.index("llmfit/research/unit-conversions.json", "observation_id")
    native_benchmarks = sources.index("llmfit/native/benchmark-entries.json", "id")
    native_models = sources.json("llmfit/native/models.json")
    community_submissions = sources.json("llmfit/native/community-submissions.json")

    _require(profiles.keys() == profile_maps.keys(), "profile mapping coverage")
    _require(series.keys() == series_mirror.keys(), "series coverage")
    _require(observations.keys() == series_rows.keys() == observation_maps.keys(), "observation coverage")
    _require(associations.keys() <= observations.keys(), "association observation IDs")
    _require(conversions.keys() <= native_benchmarks.keys() <= observations.keys(), "benchmark projection IDs")
    _require(native_models == [] and community_submissions == [], "native model/community payloads")

    records = []

    def add(kind, identifier, source, **details):
        records.append({"kind": kind, "id": identifier, "source": source, **details})

    components = defaultdict(list)
    for row, source in sources.csv("hardware-profile-components.csv"):
        profile_id = row["profile_id"]
        _require(profile_id in profiles, f"component profile {profile_id}")
        components[profile_id].append(row)
        add("component", str(source["line"]), source, original=row)

    native_hardware_paths = set()
    for identifier, (row, source) in profiles.items():
        mapping, mapping_source = profile_maps[identifier]
        notes = mapping[extension].copy()
        original = {k: v for k, v in row.items() if k != "bom"}
        _require(notes.pop("original_profile_and_BOM") == row, f"{identifier} research profile")
        _require(row["bom"] == components[identifier], f"{identifier} BOM")
        _require(set(row["source_hardware_record_ids"]) <= legacy.keys(), f"{identifier} legacy sources")
        core = mapping["llmfit_hardware_profile"]
        partial = mapping["llmfit_hardware_profile_partial"]
        native_source = None
        _require(mapping["native_hardware_profile_schema_compatible"] == (core is not None), identifier)
        _require((core is None) != (partial is None), f"{identifier} core status")
        if core is not None:
            path = f"llmfit/native/hardware/{identifier.lower()}.json"
            _require(sources.json(path) == core, f"{identifier} native hardware")
            native_hardware_paths.add(path)
            native_source = {"path": path}
        add(
            "profile", identifier, source, original=original, mapping_source=mapping_source,
            mapping_notes=notes, hardware_profile=core, hardware_profile_partial=partial,
            hardware_info=mapping["llmfit_hardware_info"], native_source=native_source,
            complete_build=False,
        )
    _require(
        native_hardware_paths == {
            path.relative_to(root).as_posix() for path in (root / "llmfit/native/hardware").glob("*.json")
        },
        "native hardware coverage",
    )
    for identifier, (row, source) in legacy.items():
        add("legacy_hardware", identifier, source, original=row)
    for identifier, (row, source) in series.items():
        _require(series_mirror[identifier][0] == row, f"{identifier} series mirror")
        add("series", identifier, source, original=row)
    for identifier, (row, source) in models.items():
        _require(row["llmfit_llm_model"] is None, f"{identifier} unresolved model")
        add(
            "model_reference", identifier, source, original=row[extension],
            llm_model=None, llm_model_partial=row["llmfit_llm_model_partial"],
        )

    for identifier, (row, source) in observations.items():
        mapped_row, series_source = series_rows[identifier]
        mapping, mapping_source = observation_maps[identifier]
        notes = mapping[extension].copy()
        _require(
            notes.pop("original_observation_and_conditions") == mapped_row
            and all(mapped_row[key] == value for key, value in row.items()),
            f"{identifier} observation mirrors",
        )
        _require(not row["config_id"] or row["config_id"] in legacy, f"{identifier} legacy config")
        series_id = mapped_row["series_id"]
        _require(series_id in series and series_id == notes["test_series_id"], f"{identifier} series")
        model_id = notes["model_reference_id"]
        _require(model_id in models, f"{identifier} model ID")
        model = models[model_id][0][extension]
        _require(
            str(model["video_position"]) == row["position"]
            and model["reported_label"] == row["model"]
            and model["source_quantization_label"] == row["quantization"],
            f"{identifier} video-scoped model label",
        )

        profile_id = None
        if identifier in associations:
            association, association_source = associations[identifier]
            profile_id = association["profile_id"]
            _require(profile_id in profiles and association["association"].strip(), f"{identifier} association")
            _require(association["source_url"] == row["source_url"], f"{identifier} association locator")
            add("profile_association", identifier, association_source, original=association)
        _require(
            profile_id == (mapped_row["hardware_profile_id"] or None) == notes["hardware_profile_id"],
            f"{identifier} profile association",
        )
        benchmark, native_source = native_benchmarks.get(identifier, (None, None))
        _require(benchmark == mapping["llmfit_benchmark_entry"], f"{identifier} benchmark projection")
        conversion, conversion_source = conversions.get(identifier, (None, None))
        if conversion is not None:
            _require(
                conversion["source_value"] == row["value"] and conversion["source_unit"] == row["unit"]
                and conversion["source_url"] == row["source_url"]
                and conversion["value"] == benchmark[conversion["field"]],
                f"{identifier} unit conversion",
            )
        add(
            "observation", identifier, source, original=row, mapping_source=mapping_source,
            series_source=series_source, series_id=series_id, metric_family=mapped_row["metric_family"],
            model_reference_id=model_id, hardware_profile_id=profile_id, mapping_notes=notes,
            benchmark_entry=benchmark, native_source=native_source,
            unit_conversion=None if conversion is None else {"original": conversion, "source": conversion_source},
        )

    counts = {
        "profiles": len(profiles), "components": sum(map(len, components.values())),
        "legacy_hardware": len(legacy), "series": len(series), "observations": len(observations),
        "qualified_associations": len(associations),
        "unassigned_observations": len(observations) - len(associations),
        "native_hardware_profiles": len(native_hardware_paths),
        "partial_hardware_profiles": len(profiles) - len(native_hardware_paths),
        "complete_builds": sum(record.get("complete_build", False) for record in records),
        "structural_benchmarks": len(native_benchmarks),
        "research_only_observations": len(observations) - len(native_benchmarks),
        "partial_model_references": len(models), "native_models": len(native_models),
        "native_community_submissions": len(community_submissions),
    }
    _require(counts == EXPECTED_COUNTS, f"seed coverage: {counts}")
    manifest = {
        "mapper_version": 1,
        "upstream_commit": UPSTREAM_COMMIT,
        "upstream_source_log": "llmfit/upstream-source-log.json",
        "upstream_notice": NOTICE,
        "source_digests": sources.digests,
        "counts": counts,
        "review_status": "unverified-caption-research",
        "publication_status": "private",
    }
    return manifest, records


def import_seed(store, root=SEED_ROOT):
    try:
        manifest, records = _reconcile(root)
    except (KeyError, TypeError, csv.Error) as error:
        raise ValueError(f"Malformed research seed: {error}") from error
    seed_id = sha256(json.dumps(manifest, sort_keys=True).encode("utf-8")).hexdigest()
    manifest["seed_id"] = seed_id
    manifest_json = _sql_text(json.dumps(manifest))
    records_json = _sql_text(json.dumps(records, ensure_ascii=False))
    store._query(f"""
        WITH inserted AS (
            INSERT INTO fastest_research.seed (id, manifest)
            VALUES ('{seed_id}', {manifest_json}::jsonb)
            ON CONFLICT DO NOTHING
            RETURNING id
        )
        INSERT INTO fastest_research.seed_record (seed_id, kind, id, document)
        SELECT inserted.id, record->>'kind', record->>'id', record
        FROM inserted CROSS JOIN jsonb_array_elements({records_json}::jsonb) AS record;
    """)
    return manifest


def read_seed(store, seed_id, kind=None, identifier=None):
    if len(seed_id) != 64 or any(char not in "0123456789abcdef" for char in seed_id):
        raise ValueError("Expected a lowercase SHA-256 seed ID")
    if kind is None:
        query = f"SELECT manifest FROM fastest_research.seed WHERE id = '{seed_id}';"
    else:
        match = f"seed_id = '{seed_id}' AND kind = {_sql_text(kind)}"
        if identifier is None:
            query = f"""
                SELECT jsonb_agg(document ORDER BY id)
                FROM fastest_research.seed_record WHERE {match};
            """
        else:
            query = f"""
                SELECT document FROM fastest_research.seed_record
                WHERE {match} AND id = {_sql_text(identifier)};
            """
    result = store._query(query)
    if not result:
        raise ReleaseNotFound("/".join(filter(None, (seed_id, kind, identifier))))
    return json.loads(result)
