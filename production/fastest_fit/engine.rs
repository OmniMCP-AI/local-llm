use llmfit_core::{
    fit::{CalcConfig, DEFAULT_ESTIMATION_CTX, FitLevel, ModelFit, RunMode, backend_compatible},
    hardware::{GpuBackend, GpuInfo, SystemSpecs},
    hwprofile::HardwareProfile,
    models::{LlmModel, ModelFormat, quant_is_recognized},
};
use serde::Deserialize;
use serde_json::{Value, json};
use std::{error::Error, io};

const REVISION: &str = env!("FASTEST_LLMFIT_COMMIT");
const PROFILE: &str = include_str!("../../data/hardware/nvidia-rtx-4090.json");
const CATALOG: &str = include_str!("../../data/hf_models.json");

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Request {
    machine: String,
    model: String,
    quantization: String,
    runtime: String,
    context_tokens: u32,
    ram_reserved_gib: f64,
    vram_reserved_gib: f64,
    vram_capacity_gib: f64,
    cpu_cores: Option<usize>,
}

fn analyze(request: Request) -> Result<Value, Box<dyn Error>> {
    if request.machine != "llmfit-nvidia-rtx-4090" || request.runtime != "llama.cpp" {
        return Err("unsupported machine or runtime".into());
    }
    let profile: HardwareProfile = serde_json::from_str(PROFILE)?;
    profile.validate_strict()?;
    let hardware = profile.hardware;
    let gpu_name = profile
        .matcher
        .ok_or("missing GPU identity")?
        .gpu_name_contains;
    let ddr = hardware.ddr_bandwidth_gbps.ok_or("missing DDR bandwidth")?;
    let gpu_bandwidth = hardware
        .gpu_memory_bandwidth_gbps
        .ok_or("missing GPU bandwidth")?;
    let ram = hardware.total_ram_gb - request.ram_reserved_gib;
    let vram = request.vram_capacity_gib - request.vram_reserved_gib;
    if hardware.unified_memory
        || request.ram_reserved_gib < 0.0
        || request.vram_reserved_gib < 0.0
        || !(ram > 0.0 && vram > 0.0)
        || !ddr.is_finite()
        || ddr <= 0.0
        || !gpu_bandwidth.is_finite()
        || gpu_bandwidth <= 0.0
    {
        return Err("invalid memory assumptions".into());
    }

    let mut model = serde_json::from_str::<Vec<LlmModel>>(CATALOG)?
        .into_iter()
        .find(|entry| entry.name == request.model)
        .ok_or("model missing from pinned catalog")?;
    if model.is_moe
        || model.format != ModelFormat::Gguf
        || !quant_is_recognized(&request.quantization)
        || model.parameters_raw.unwrap_or(0) == 0
    {
        return Ok(json!({
            "status": "unsupported", "qualification": "model_fit_inputs_unavailable", "estimate": null,
        }));
    }
    if request.context_tokens == 0 || request.context_tokens > model.context_length {
        return Ok(json!({
            "status": "insufficient_input",
            "qualification": "context_out_of_range",
            "maximum_context_tokens": model.context_length,
            "estimate": null,
        }));
    }
    model.quantization = request.quantization;

    // Both capacity fields must use the effective budget. llmfit's fit walk
    // reads total GPU VRAM while its speed model also consults free VRAM.
    let system = SystemSpecs {
        total_ram_gb: hardware.total_ram_gb,
        available_ram_gb: ram,
        total_cpu_cores: request.cpu_cores.unwrap_or(0),
        cpu_name: String::new(),
        has_gpu: true,
        gpu_vram_gb: Some(vram),
        total_gpu_vram_gb: Some(vram),
        gpu_available_gb: Some(vram),
        gpu_name: Some(gpu_name.clone()),
        gpu_count: 1,
        unified_memory: false,
        backend: GpuBackend::Cuda,
        gpus: vec![GpuInfo {
            name: gpu_name,
            vram_gb: Some(vram),
            backend: GpuBackend::Cuda,
            count: 1,
            unified_memory: false,
            free_vram_gb: Some(vram),
            free_vram_per_card_gb: vec![vram],
            pcie_links: Vec::new(),
        }],
        cluster_mode: false,
        cluster_node_count: 1,
    };
    if !backend_compatible(&model, &system) {
        return Ok(json!({
            "status": "unsupported", "qualification": "backend_incompatible", "estimate": null,
        }));
    }
    let config = CalcConfig {
        context_cap: Some(request.context_tokens),
        ddr_bandwidth_gbps: Some(ddr),
        gpu_bandwidth_gbps_override: Some(gpu_bandwidth),
        gpu_compute_tflops_fp16: hardware.gpu_compute_tflops_fp16,
        ..CalcConfig::default()
    };
    let fit = ModelFit::analyze_with_config(&model, &system, config.clone());
    let exact_memory = model.estimate_memory_gb(&model.quantization, request.context_tokens);

    let qualification = if fit.runtime.label() != request.runtime {
        Some("core_selected_different_runtime")
    } else if fit.best_quant != model.quantization {
        Some("core_selected_different_quantization")
    } else if fit.memory_required_gb != exact_memory
        || (fit.fit_level != FitLevel::TooTight && fit.usable_context < request.context_tokens)
    {
        Some("core_reduced_context")
    } else if fit.run_mode != RunMode::Gpu && request.cpu_cores.is_none() {
        Some("cpu_cores_required_for_offload")
    } else {
        None
    };
    // The dense offload roofline internally caps context even when the
    // fit's memory calculation honors the full requested window.
    let decode_capped =
        fit.run_mode == RunMode::CpuOffload && request.context_tokens > DEFAULT_ESTIMATION_CTX;
    let speed_available = fit.fit_level != FitLevel::TooTight && fit.reports_speed();
    let estimate = qualification.is_none().then(|| json!({
        "fit_level": fit.fit_level,
        "run_mode": fit.run_mode,
        "quantization": fit.best_quant,
        "memory_required_gib": fit.memory_required_gb,
        "memory_available_gib": fit.memory_available_gb,
        "usable_context_tokens": fit.usable_context,
        "decode_tokens_per_second": (speed_available && !decode_capped && fit.estimated_tps > 0.0).then_some(fit.estimated_tps),
        "decode_qualification": decode_capped.then_some("core_offload_context_cap"),
        "prefill_tokens_per_second": speed_available.then_some(fit.prefill_tps).flatten(),
        "ttft_ms": speed_available.then_some(fit.ttft_ms).flatten(),
        "decode_basis": (speed_available && !decode_capped).then_some(fit.estimate_basis),
    }));
    Ok(json!({
        "status": if qualification.is_some() { "qualified" } else { "estimated" },
        "qualification": qualification,
        "maximum_context_tokens": model.context_length,
        "requested_artifact_memory_required_gib": exact_memory,
        "engine_suggested_quantization": fit.best_quant,
        "engine_selected_runtime": fit.runtime.label(),
        "estimate": estimate,
        "calculation": {
            "config": config,
            "backend": system.backend,
            "gpu_count": system.gpu_count,
            "installed_ram_gib": system.total_ram_gb,
            "installed_vram_gib": request.vram_capacity_gib,
            "available_ram_gib": ram,
            "available_vram_gib": vram,
            "kv_cache_quantization": "FP16",
        },
    }))
}

fn main() -> Result<(), Box<dyn Error>> {
    if std::env::args().nth(1).as_deref() == Some("--revision") {
        println!("{REVISION}");
    } else {
        let request = serde_json::from_reader(io::stdin().lock())?;
        let response = analyze(request)?;
        serde_json::to_writer(io::stdout().lock(), &response)?;
    }
    Ok(())
}
