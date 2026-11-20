use llmfit_core::{
    benchmarks::{BenchmarkEntry, HardwareInfo, community_submissions},
    hwprofile,
    models::{LlmModel, ModelDatabase},
};
use serde_json::Value;
use std::{
    collections::HashSet,
    fs,
    path::{Path, PathBuf},
};

fn seed_dir() -> PathBuf {
    PathBuf::from(std::env::var_os("FASTEST_RESEARCH_LLMFIT_SEED").expect("seed directory"))
}

fn upstream_data() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("data")
}

fn read(path: &Path) -> Value {
    let bytes = fs::read(path).unwrap_or_else(|error| panic!("{}: {error}", path.display()));
    serde_json::from_slice(&bytes).unwrap_or_else(|error| panic!("{}: {error}", path.display()))
}

fn validator(path: &Path) -> jsonschema::Validator {
    jsonschema::validator_for(&read(path)).unwrap()
}

#[test]
fn hardware_cores_load_as_strict_native_profiles() {
    let seed = seed_dir();
    let schema_path = upstream_data().join("hardware/schema.json");
    assert_eq!(
        read(&schema_path),
        read(&seed.join("schemas/hardware-profile.upstream.schema.json"))
    );
    let schema = validator(&schema_path);
    let mut count = 0;
    for entry in fs::read_dir(seed.join("native/hardware")).unwrap() {
        let path = entry.unwrap().path();
        if path.extension().and_then(|value| value.to_str()) != Some("json") {
            continue;
        }
        schema
            .validate(&read(&path))
            .unwrap_or_else(|error| panic!("{}: {error}", path.display()));
        let profile = hwprofile::load_file(&path).unwrap();
        profile.validate_strict().unwrap();
        count += 1;
    }
    assert_eq!(count, 16);
}

#[test]
fn benchmarks_and_hardware_info_deserialize_with_native_field_names() {
    let seed = seed_dir();
    let schema = validator(&seed.join("schemas/benchmark-entry.derived.schema.json"));
    let payload = read(&seed.join("native/benchmark-entries.json"));
    let entries: Vec<BenchmarkEntry> = serde_json::from_value(payload.clone()).unwrap();
    assert_eq!(entries.len(), 127);
    assert_eq!(
        entries
            .iter()
            .map(|entry| &entry.id)
            .collect::<HashSet<_>>()
            .len(),
        127
    );
    for row in payload.as_array().unwrap() {
        schema
            .validate(row)
            .unwrap_or_else(|error| panic!("{}: {error}", row["id"]));
    }
    let first = entries
        .iter()
        .find(|entry| entry.id == "V001-P001")
        .unwrap();
    assert_eq!(first.tok_s_out, Some(53.0));
    assert_eq!(
        first.hardware.as_ref().unwrap().gpu_name.as_deref(),
        Some("Arc A770")
    );
    let ttft = entries
        .iter()
        .find(|entry| entry.id == "V001-P021")
        .unwrap();
    assert_eq!(ttft.ttft_ms, Some(31_000.0));

    let schema = validator(&seed.join("schemas/hardware-info.derived.schema.json"));
    let mappings = read(&seed.join("research/hardware.json"));
    let mut count = 0;
    for row in mappings.as_array().unwrap() {
        let info = &row["llmfit_hardware_info"];
        if !info.is_null() {
            schema
                .validate(info)
                .unwrap_or_else(|error| panic!("{info}: {error}"));
            let _: HardwareInfo = serde_json::from_value(info.clone()).unwrap();
            count += 1;
        }
    }
    assert_eq!(count, 103);
}

#[test]
fn upstream_catalog_loads_and_video_references_remain_partial() {
    let upstream = fs::read(upstream_data().join("hf_models.json")).unwrap();
    let raw: Vec<LlmModel> = serde_json::from_slice(&upstream).unwrap();
    assert_eq!(raw.len(), 19_192);
    assert_eq!(ModelDatabase::embedded().get_all_models().len(), 18_044);

    let seed = seed_dir();
    let native: Vec<LlmModel> =
        serde_json::from_value(read(&seed.join("native/models.json"))).unwrap();
    assert!(native.is_empty());
    let records = read(&seed.join("research/models.json"));
    let partial = records.as_array().unwrap();
    assert_eq!(partial.len(), 140);
    for row in partial {
        assert!(row["llmfit_llm_model"].is_null());
        assert!(
            serde_json::from_value::<LlmModel>(row["llmfit_llm_model_partial"].clone()).is_err()
        );
    }
}

#[test]
fn upstream_submission_loader_accepts_its_corpus_and_seed_projects_no_submissions() {
    let seed = seed_dir();
    let schema_path = upstream_data().join("community/schema.json");
    assert_eq!(
        read(&schema_path),
        read(&seed.join("schemas/community-benchmark.upstream.schema.json"))
    );
    let schema = validator(&schema_path);
    let upstream = community_submissions();
    assert_eq!(upstream.len(), 546);
    for row in upstream {
        schema
            .validate(row)
            .unwrap_or_else(|error| panic!("upstream community submission: {error}"));
    }
    let native = read(&seed.join("native/community-submissions.json"));
    assert!(native.as_array().unwrap().is_empty());
    let projections = read(&seed.join("native/benchmark-entries.json"));
    for row in projections.as_array().unwrap() {
        assert!(
            !schema.is_valid(row),
            "{} became a community submission",
            row["id"]
        );
    }
}
