use llmfit_core::{
    fit::{
        CalcConfig, DEFAULT_ESTIMATION_CTX, FitLevel, InferenceRuntime, ModelFit, RunMode,
        backend_compatible, resolve_gpu_bandwidth,
    },
    hardware::{GpuBackend, GpuInfo, SystemSpecs},
    hwprofile::HardwareProfile,
    models::{LlmModel, ModelFormat, quant_is_recognized},
};
use serde::Deserialize;
use serde_json::{Value, json};
use std::{error::Error, io};

const REVISION: &str = env!("FASTEST_LLMFIT_COMMIT");
const RTX_PROFILE: &str = include_str!("../../data/hardware/nvidia-rtx-4090.json");
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
    vram_reserved_gib: Option<f64>,
    vram_capacity_gib: Option<f64>,
    unified_memory_gib: Option<f64>,
    gpu_name: Option<String>,
    memory_bandwidth_gbps: Option<f64>,
    cpu_cores: Option<usize>,
}

struct Machine {
    gpu_name: String,
    backend: GpuBackend,
    installed_ram: f64,
    installed_vram: Option<f64>,
    gpu_pool: f64,
    bandwidth: f64,
    config: CalcConfig,
}

fn selected_machine(request: &Request) -> Result<Machine, Box<dyn Error>> {
    let config = CalcConfig {
        context_cap: Some(request.context_tokens),
        ..CalcConfig::default()
    };
    match request.machine.as_str() {
        "llmfit-nvidia-rtx-4090" => {
            let profile: HardwareProfile = serde_json::from_str(RTX_PROFILE)?;
            profile.validate_strict()?;
            let hardware = profile.hardware;
            let gpu_name = profile
                .matcher
                .ok_or("missing GPU identity")?
                .gpu_name_contains;
            let ddr = hardware.ddr_bandwidth_gbps.ok_or("missing DDR bandwidth")?;
            let bandwidth = hardware
                .gpu_memory_bandwidth_gbps
                .ok_or("missing GPU bandwidth")?;
            let vram = request.vram_capacity_gib.ok_or("missing VRAM capacity")?;
            let reserved = request
                .vram_reserved_gib
                .ok_or("missing VRAM reservation")?;
            if hardware.unified_memory || reserved < 0.0 || !ddr.is_finite() || ddr <= 0.0 {
                return Err("invalid discrete memory assumptions".into());
            }
            Ok(Machine {
                gpu_name,
                backend: GpuBackend::Cuda,
                installed_ram: hardware.total_ram_gb,
                installed_vram: Some(vram),
                gpu_pool: vram - reserved,
                bandwidth,
                config: CalcConfig {
                    ddr_bandwidth_gbps: Some(ddr),
                    gpu_bandwidth_gbps_override: Some(bandwidth),
                    gpu_compute_tflops_fp16: hardware.gpu_compute_tflops_fp16,
                    ..config
                },
            })
        }
        "apple-mac-mini-m4-24gb-512gb" => {
            let ram = request
                .unified_memory_gib
                .ok_or("missing unified memory capacity")?;
            if request.vram_capacity_gib.is_some()
                || request.vram_reserved_gib.is_some()
                || request.cpu_cores.is_none()
            {
                return Err("invalid unified memory assumptions".into());
            }
            Ok(Machine {
                gpu_name: request.gpu_name.clone().ok_or("missing GPU identity")?,
                backend: GpuBackend::Metal,
                installed_ram: ram,
                installed_vram: None,
                gpu_pool: ram - request.ram_reserved_gib,
                bandwidth: request
                    .memory_bandwidth_gbps
                    .ok_or("missing memory bandwidth")?,
                config,
            })
        }
        _ => Err("unsupported machine".into()),
    }
}

fn analyze(request: Request) -> Result<Value, Box<dyn Error>> {
    if request.runtime != "llama.cpp" {
        return Err("unsupported runtime".into());
    }
    let machine = selected_machine(&request)?;
    let unified = machine.installed_vram.is_none();
    let ram = machine.installed_ram - request.ram_reserved_gib;
    if request.ram_reserved_gib < 0.0
        || !(ram > 0.0 && machine.gpu_pool > 0.0)
        || !machine.bandwidth.is_finite()
        || machine.bandwidth <= 0.0
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

    // llmfit's GPU capacity fields take the effective budget. For Metal they
    // represent the same shared pool as available RAM, and we have no
    // separately observed GPU memory or Metal working-set limit.
    let gpu_pool = Some(machine.gpu_pool);
    let free_vram = machine.installed_vram.and(gpu_pool);
    let system = SystemSpecs {
        total_ram_gb: machine.installed_ram,
        available_ram_gb: ram,
        total_cpu_cores: request.cpu_cores.unwrap_or(0),
        cpu_name: String::new(),
        has_gpu: true,
        gpu_vram_gb: gpu_pool,
        total_gpu_vram_gb: gpu_pool,
        gpu_available_gb: free_vram,
        gpu_name: Some(machine.gpu_name.clone()),
        gpu_count: 1,
        unified_memory: unified,
        backend: machine.backend,
        gpus: vec![GpuInfo {
            name: machine.gpu_name,
            vram_gb: gpu_pool,
            backend: machine.backend,
            count: 1,
            unified_memory: unified,
            free_vram_gb: free_vram,
            free_vram_per_card_gb: free_vram.into_iter().collect(),
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
    let config = machine.config;
    let fit = if unified {
        // The pinned forced-runtime method uses the built-in GPU bandwidth
        // lookup. Check it against Apple's reviewed rating before estimation.
        // Dense GPU-only fit on a shared pool does not consult DDR bandwidth.
        if resolve_gpu_bandwidth(&system, &config) != Some(machine.bandwidth) {
            return Err("pinned GPU bandwidth disagrees with factory rating".into());
        }
        ModelFit::analyze_with_forced_runtime(
            &model,
            &system,
            config.context_cap,
            Some(InferenceRuntime::LlamaCpp),
        )
    } else {
        ModelFit::analyze_with_config(&model, &system, config.clone())
    };
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
    let mut calculation = json!({
        "config": config,
        "backend": system.backend,
        "gpu_count": system.gpu_count,
        "kv_cache_quantization": "FP16",
    });
    if unified {
        calculation["installed_unified_memory_gib"] = json!(system.total_ram_gb);
        calculation["available_unified_memory_gib"] = json!(ram);
        calculation["unified_memory_bandwidth_gbps"] = json!(machine.bandwidth);
        calculation["metal_working_set_limit_gib"] = Value::Null;
    } else {
        calculation["installed_ram_gib"] = json!(system.total_ram_gb);
        calculation["installed_vram_gib"] = json!(machine.installed_vram);
        calculation["available_ram_gib"] = json!(ram);
        calculation["available_vram_gib"] = json!(machine.gpu_pool);
    }
    Ok(json!({
        "status": if qualification.is_some() { "qualified" } else { "estimated" },
        "qualification": qualification,
        "maximum_context_tokens": model.context_length,
        "requested_artifact_memory_required_gib": exact_memory,
        "engine_suggested_quantization": fit.best_quant,
        "engine_selected_runtime": fit.runtime.label(),
        "estimate": estimate,
        "calculation": calculation,
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
