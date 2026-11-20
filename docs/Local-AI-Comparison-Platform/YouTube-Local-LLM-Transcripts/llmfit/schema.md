# llmfit data-structure contract (pinned)

Upstream:[AlexsJones/llmfit](https://github.com/AlexsJones/llmfit/blob/26450cccaf3a3f14b1822875f2473847a744a718/README.md),defaultbranch`main`,head`26450cccaf3a3f14b1822875f2473847a744a718` verified on2026-11-20T21:50:55.958610+08:00(Asia/Shanghai);sameSHAas earlier licensingresearch. No clone,build or runtime-behavior investigation.

## Boundary

The primary machine-readable research files now use upstream type/field names in `llmfit/research/`. Complete compatible cores are separately emitted under `llmfit/native/`;allBOM/provenance/partialconditions live **outside** strict upstream objects under `x_local_ai_research`. ExistingCSV/profile artifacts remain preserved evidence/humanviews,not an alternative newcore schema. A wrapper is NOT a native llmfitfile. No upstream importer was installed or exercised.

## HardwareProfile (snake_case)

Actualcontracts:[schema](https://github.com/AlexsJones/llmfit/blob/26450cccaf3a3f14b1822875f2473847a744a718/llmfit-core/data/hardware/schema.json),[types](https://github.com/AlexsJones/llmfit/blob/26450cccaf3a3f14b1822875f2473847a744a718/llmfit-core/src/hwprofile.rs),[documentation](https://github.com/AlexsJones/llmfit/blob/26450cccaf3a3f14b1822875f2473847a744a718/llmfit-core/data/hardware/README.md). Copiedschema is `schemas/hardware-profile.upstream.schema.json`.

Required:`schema_version`integer=1;`name`nonempty`^[a-z0-9][a-z0-9._-]*$`,equalfile stem;`hardware`object requiring`total_ram_gb`number>0≤16384 and`unified_memory`boolean. Requiredvalues cannot be null. Optionalnumeric hardwarekeys:`gpu_memory_bandwidth_gbps`,`ddr_bandwidth_gbps`,`gpu_compute_tflops_fp16`,each>0≤100000;JSONschemaomitsratherthanacceptsnull. Units:GBnominalRAM,GB/sbandwidth,FP16TFLOP/s. No discreteVRAM/CPU/GPUcount/BOMfield exists here. **DiscreteVRAM remains host-detected;validminimalprofiles are not complete hardwareblueprints.**

Optional`match`requiresstring`gpu_name_contains`and is provenanceonly,not auto-selection. Optional`estimation.efficiency`is>0≤1;`run_mode_factors`may useonly`gpu`,`tensor_parallel`,`moe_offload`,`cpu_offload`,`cpu_only`,each>0≤10. We do not invent estimatorinputs. Optional`calibration[]`requires`model`nonemptystring and`measured_tps`>0≤100000;optional`quant`,`run_mode`(same5enumvalues),`source`. Calibration is validated but not applied in schemaversion1,perupstreamdocs. No calibrationanchors synthesized here.

Strictschema disallowsadditionalproperties at eachdefinedobject;do not nest BOM/provenance inside nativehardwareobject. Rustloading toleratesunknownkeys but strictvalidation rejects them,so extensions are separate.

## BenchmarkEntry / HardwareInfo (camelCase)

Actualdeclarations:[benchmarks.rs](https://github.com/AlexsJones/llmfit/blob/26450cccaf3a3f14b1822875f2473847a744a718/llmfit-core/src/benchmarks.rs). `schemas/benchmark-entry.derived.schema.json` and`hardware-info.derived.schema.json` are **locallyreconstructed serializationchecks**,NOT upstream-publishedschemas. `BenchmarkEntry.id`is requiredString;`hfId`,`engineName`,`quantization`are String withserde defaultempty. We OMITunknowns,not invent them. Optionfields defaultNone/acceptnull:`tokSOut`,`tokSTotal`,`ttftMs`,`peakVramGb`:f64;`contextLength`,`batchSize`:u32;`notes`,`username`,`createdAt`:String;`verified`:bool;`hardware`:HardwareInfo.

Units explicitly expressed byfieldname:tok/s,TTFTms,VRAMGB;context/batchintegercounts. `tokSTotal`is NOT assumed to mean sumofconcurrentdecode rates. Prefill has no dedicatedfield in thisrecord;we preserveit in extensions. No concurrency/cache/KVprecision/repeatstatistic is inferred from`batchSize`. `createdAt`isnot captionretrievaltime. Sourceverificationunknown does not become`verified=true/false`.

AllHardwareInfofieldsare optional/null:strings`hwClass`,`gpuName`,`chipVendor`,`chipFamily`,`chipVariant`,`cpu`,`os`;f64`vramGb`,`unifiedMemoryGb`,`ramGb`;u32`gpuCount`. RustHardwareInfo usesString forhwClass/os,not the narrowercommunityenums. PerGPUversusaggregateVRAM ambiguity remains in extensions;we only mapvramGbwhen capacity is explicit andgpuCount=1. PeakVRAMusage is not installedcapacity.

## Communitysubmission is a DIFFERENT schema

Actual[schema](https://github.com/AlexsJones/llmfit/blob/26450cccaf3a3f14b1822875f2473847a744a718/llmfit-core/data/community/schema.json),[docs](https://github.com/AlexsJones/llmfit/blob/26450cccaf3a3f14b1822875f2473847a744a718/llmfit-core/data/community/README.md). Copiedschema is`community-benchmark.upstream.schema.json`. Requiredroot:`schemaVersion`=1,`submittedAtUnix`integer≥0,`tool`(name/versionstrings),`hardware`,`results`nonemptyarray. Requiredhardware:`hwClass`enumDISCRETE_GPU/UNIFIED/CPU_ONLY;gpuCountinteger≥0;unifiedMemorybool;cpuString;cpuCoresinteger≥1;ramGbnumber≥0;os enumlinux/macos/windows. OptionalhardwareNameString/null,memTierGbinteger/null≥0,vramGbnumber/null≥0. OptionalpcieLinksrequires perlinkindex(nullableu32),generation(nullable1..255),width1..255,max_generation(nullable1..255),max_width(nullable1..255). UnknownPCIewidths cannot be fabricated.

Eachresult requiresmodel(nonemptyString),provider enumollama/vllm/ferrum/lmstudio/mlx/llamacpp,numRunsinteger≥1,avgTps/minTps/maxTpsnumber0..100000,avgTotalMs/avgOutputTokensnumber≥0;optionalavgTtftMsnumber/null≥0. Defaultedstats/numRuns=1 would invent evidence. Therefore0submissions emitted;no videos were falsely labelledllmfit-generatedruns.

## Modelcatalog LlmModel

[Declaredtype](https://github.com/AlexsJones/llmfit/blob/26450cccaf3a3f14b1822875f2473847a744a718/llmfit-core/src/models.rs);catalogpath`llmfit-core/data/hf_models.json` verified in recursiveGitHubtree(17,293,734bytes),not copied/downloaded. Names/requiredmetadata below derive from actualtype,not guessed from modelmarketingnames. Units:RAM/VRAMGB;contexttoken-count;rawparameter fieldsintegercounts. Catalogminimum/recommendedmemory and maximumcontext are NOT a particularrun's allocation/promptlength.

| Field | Rusttype | Missing/null semantics |
|---|---|---|
|`name`|`String`|Required;nonnull|
|`provider`|`String`|Required;nonnull|
|`parameter_count`|`String`|Required;nonnull|
|`parameters_raw`|`Option<u64>`|Optional/missing→None;JSONnull accepted|
|`min_ram_gb`|`f64`|Required;nonnull|
|`recommended_ram_gb`|`f64`|Required;nonnull|
|`min_vram_gb`|`Option<f64>`|Optional/missing→None;JSONnull accepted|
|`quantization`|`String`|Required;nonnull|
|`context_length`|`u32`|Required;nonnull|
|`use_case`|`String`|Required;nonnull|
|`is_moe`|`bool`|Missing→false;JSONnullrejected;do not apply to unknownvideo model|
|`num_experts`|`Option<u32>`|Optional/missing→None;JSONnull accepted|
|`active_experts`|`Option<u32>`|Optional/missing→None;JSONnull accepted|
|`active_parameters`|`Option<u64>`|Optional/missing→None;JSONnull accepted|
|`release_date`|`Option<String>`|Optional/missing→None;JSONnull accepted|
|`gguf_sources`|`Vec<GgufSource>`|Missing→emptylist;JSONnullrejected;not proof of absence|
|`capabilities`|`Vec<Capability>`|Missing→emptylist;JSONnullrejected;not proof of absence|
|`languages`|`Vec<String>`|Missing→emptylist;JSONnullrejected;not proof of absence|
|`format`|`ModelFormat`|Missing→gguf;JSONnullrejected;do not apply to unknownformat|
|`num_attention_heads`|`Option<u32>`|Optional/missing→None;JSONnull accepted|
|`num_key_value_heads`|`Option<u32>`|Optional/missing→None;JSONnull accepted|
|`num_hidden_layers`|`Option<u32>`|Optional/missing→None;JSONnull accepted|
|`head_dim`|`Option<u32>`|Optional/missing→None;JSONnull accepted|
|`attention_layout`|`Option<AttentionLayout>`|Optional/missing→None;JSONnull accepted|
|`license`|`Option<String>`|Optional/missing→None;JSONnull accepted|
|`hidden_size`|`Option<u32>`|Optional/missing→None;JSONnull accepted|
|`moe_intermediate_size`|`Option<u32>`|Optional/missing→None;JSONnull accepted|
|`vocab_size`|`Option<u32>`|Optional/missing→None;JSONnull accepted|
|`shared_expert_intermediate_size`|`Option<u32>`|Optional/missing→None;JSONnull accepted|
|`architecture`|`Option<String>`|Optional/missing→None;JSONnull accepted|


ModelFormat serialization:gguf/awq/gptq/autoround/mlx/safetensors/onnx;defaultgguf must notbe applied when unknown. Capabilityenumserialization:vision/tool_use/audio/tts. `use_case`is a String inLlmModel;the separateUseCaseenum hasGeneral/Coding/Reasoning/Chat/Multimodal/Embedding. NestedGgufSource requiresrepo/providerStrings;AttentionLayout requiresfull/linearu32. No fullmodelrecords emitted because videoevidence lacks requiredcatalogRAM/provider/contextmetadata. **Modelweightlicenses are separate;no weightlicense inherited from MITschema.**

## Other referencedfiles are not hardwarebenchmarktables

[`benchmarks.yaml`](https://github.com/AlexsJones/llmfit/blob/26450cccaf3a3f14b1822875f2473847a744a718/llmfit-core/data/benchmarks.yaml)is role/test/prompt/rule qualityrubric,currentlyrubric_version2. [`baselines.json`](https://github.com/AlexsJones/llmfit/blob/26450cccaf3a3f14b1822875f2473847a744a718/llmfit-core/data/baselines.json)containsfrontiermodelrolequality/speed/compositebaselines,whoseownnote identifiesrubric_version1 andwarns toregenerate fornewerrubric. Neitheris a schema for transcribing these hardwareperformanceclaims;no suchscores/prompts imported. NoLocalMaxxing`benchmark_cache.json`orcommunitythird-partyresultrow was ingested.

## Attribution

Upstreamstructures/schema source licensed MIT,Copyright(c)2026AlexJones. Fullnotice:`LICENSE.llmfit-MIT.txt`;retain it with copiedschemas/derivedcontracts. This is not a blanketlicense for modelweights,third-partybenchmarkdatasets orvideos.
