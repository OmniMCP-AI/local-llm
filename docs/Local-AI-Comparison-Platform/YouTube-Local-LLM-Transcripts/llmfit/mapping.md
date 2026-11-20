# Mapping video research into llmfit structures

Pinned upstream:`26450cccaf3a3f14b1822875f2473847a744a718`. See[schema.md](schema.md)for exactcontracts and[validation-report.json](validation-report.json)for checks. Nativecompatibility means field/schema compatibility,not independent factvalidation or tested import support.

## Primary files

-`native/hardware/*.json`:16actualHardwareProfile-schema-compatible files. Theirminimalnativecore omits unavailableestimation/calibrationvalues and discreteGPUVRAM.
-`research/hardware.json`:116losslessrecords;completecore or explicitly non-nativepartialprojection plusnativeHardwareInfo fieldprojection and`x_local_ai_research.original_profile_and_BOM`.
-`native/benchmark-entries.json`:127meaningful scalar BenchmarkEntryserializationprojections;not communitysubmissions.
-`research/benchmarks.json`:all450claims,includingnon-scalarranges,estimates,prefill,aggregate,quality,power and fullconditions/timestamps.
-`research/models.json`:140video-scopedmodel/artifactlabelreferences.0completecatalogmodels;minimumRAM/provider/maxcontext are not invented.
-`research/test-series.json`:all242originalseriesheaders;all293profilelinks preserved in existingCSV.
-`native/models.json`and`native/community-submissions.json`are empty intentionally,not missingextracts.

## Field-by-field semanticmapping

| Video/researchfield | llmfitnativefield | Guard / extensionboundary |
|---|---|---|
|ExplicitinstalledsystemRAM|HardwareProfile.hardware.total_ram_gb;HardwareInfo.ramGb|NotGPUVRAM,modelweightfootprint,usage orcap;sourceGBkeptnominal|
|ExplicitunifiedRAM|total_ram_gb +unified_memory=true;HardwareInfo.unifiedMemoryGb|Noinferencefromgeneric80GBmemory;clustertotalnotasinglemachine|
|Separatelydisclosed discreteGPU+systemRAM|unified_memory=false|Topologicalclassificationbasedonbothdisclosedcomponents,notdefaultfalse|
|Ambiguous94GB/46GB,unspecifiedmemorytype|Partialprojection/extension|Notpromotedto completeHardwareProfile|
|GPUname/CPU|HardwareInfo.gpuName/cpu|Captionlabelpreserved;unresolvedSKUconflicts stayextension-only|
|GPUcount/perGPU/aggregateVRAM|HardwareInfo.gpuCount;vramGb onlyexplicitcapacity+singleGPU|Do notguess totalVRAMmeaning onmulticard records;fullvalues inBOMextension|
|Motherboard,PSU,storage,cooling,chassis,prices,status|x_local_ai_research.original_profile_and_BOM|NoequivalentHardwareProfilefields;never discarded|
|Exactscalaroutputtokenrate|BenchmarkEntry.tokSOut|Mustbe outputgeneration/decode,tokens/s,non-estimate;no fabricatedmean fromrange|
|ExactscalarTTFTseconds/minutes|BenchmarkEntry.ttftMs ×1000/60000|Explicitconversionlog;no approximate/rangeconversion to scalar|
|Prefilltok/s|Originalmetricinextension|NotassignedtokSOut or assumedtokSTotal|
|Aggregateconcurrenttokens/s|Originalmetric+concurrencyinextension|NotassignedtokSTotal;not inferredbatchSize|
|ObservedVRAM/RAM|Originalmetricinextension|Notinstalledcapacity orpeakVramGb unless explicitpeak|
|KV/cache/prompt/outputlength/speculation/parallelism/numruns/statistic/temperature|Originalconditions+testseries inextension|NoexistingBenchmarkEntryfields cover most;unknownstaysunknown|
|Video modelname/quant|PartialLlmModel.name/quantization|No guessedprovider/HFid,rawparametercount,maxcontext orlicense|
|Modeltestcontext|Runextension|Notcatalogcontext_length(maxsupportedcontext)|
|Captionretrievaltimestamp|Researchprovenanceonly|NotBenchmarkEntry.createdAt orsubmittedAtUnix|
|Creatorclaim/estimate|Researchevidence_type|No verifiedflag or measuredcalibration invented|

## Example:budgetNASserver

Source:[video19](https://www.youtube.com/watch?v=mjR-LJmHg_I&t=14s). Nativecore:

```json
{
  "schema_version": 1,
  "name": "v019-hp-test",
  "hardware": {
    "total_ram_gb": 128,
    "unified_memory": false
  }
}
```

Thispasses upstreamhardwareJSONschema but saysnothingaboutT10VRAM,CPUmodel,PSU orstorage. ThelosslessextensionretainsX99-T8,4×32GBDDR3,singleT10andtemporary6600XTrole,separateCPU+boardbundlecost,source-paid/quote distinctions,WebUI/Q3_K_S/128Krunclaim andtimestamps. Itsreported~40and30–60tokens/s is **not collapsed into a nativeaveragetokSOut**. No sourcecode/runtimedata was executed.

## Example:scalarreporteddecode

```json
{
  "id": "V001-P001",
  "tokSOut": 53.0,
  "engineName": "llama.cpp community scoreboard",
  "hardware": {
    "gpuName": "Arc A770"
  },
  "notes": "Video-caption reported claim,not independently verified. https://www.youtube.com/watch?v=2L_RB-XqisE&t=301s;see externalresearchrecord V001-P001"
}
```

`hfId`isabsentbecauseexactcanonicalartifactidentitywas notverified. ThisobjectmatchesBenchmarkEntryserializationfields;itdoes NOT satisfy thecommunitysubmissioncontract or prove thatllmfitacceptsthisfileas animport. Fullconditions/sourceclaims remain attached in theresearchenvelope.

## Supportedvalidationandlimitations

OfficialcopiedHardwareProfileJSONschema ischecked for thekeywords ituses;BenchmarkEntry/HardwareInfochecksare reconstructed from pinnedRustdeclarations,not an officialupstreamJSONschema. NativeCLI/Rustdeserialization was NOT run. Strictadditional-propertycheckskeepresearchextensionsoutsidecore. Communityrequiredstats/toolmetadata werenotfabricated. Sourcefactsremaincaptionclaims;16nativehardwarecores do not mean16completebuilds or independentlyverifiedmachines.

NoLocalMaxxingbenchmarkcache,HFmodelcatalogrows orupstreamcommunityresults copied. Copiedschemas/derivedcontracts carrythefullMITnotice;modelweightlicensesremainseparate.
