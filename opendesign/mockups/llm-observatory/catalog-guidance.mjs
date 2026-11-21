// Reviewed editorial templates. Increment the version when their wording or rules change.
export const guidanceVersion = "profile-guidance-v1";

export function profileGuidance(kind, row) {
  const strengths = [];
  const limitations = [];
  const add = (text, source) => strengths.push({ text, source });
  if (kind === "cards") {
    const vendor = row.vendorSpec;
    const memory = vendor?.facts?.["Memory configuration"] ?? vendor?.facts?.["Dedicated memory (GB)"];
    if (memory && vendor.source) add(`Manufacturer lists ${memory}; useful when screening model memory requirements.`, vendor.source);
    limitations.push({ text: "Runtime-usable memory and measured inference performance are unavailable for this card in this release; verify fit and speed on the intended setup." });
  } else if (kind === "machines") {
    if ((row.buildSource || row.kind === "Complete factory configuration") && row.memory?.system && row.source) add(`The source reports ${row.memory.system} system memory; useful for planning host memory needs.`, row.source);
    limitations.push({ text: "Runtime-usable memory and reviewed inference performance are unavailable for this build in this release; verify the intended workload." });
  } else if (kind === "models") {
    if (row.supplemental?.parameters && row.supplemental.cardUrl) add(`Publisher reports ${row.supplemental.parameters}; useful when identifying the model scale.`, row.supplemental.cardUrl);
    limitations.push({ text: "Tested local compatibility and inference performance are unavailable in this catalog; check the exact artifact and runtime before deployment." });
  } else if (kind === "runtimes") {
    if (row.formats && row.formatSource) add(`Documentation describes ${row.formats}; useful when checking deployment inputs.`, row.formatSource);
    limitations.push({ text: "A reviewed matching hardware, driver and runtime test is unavailable in this release; verify compatibility and performance for the intended configuration." });
  }
  return { version: guidanceVersion, review: "Reviewed editorial templates applied to source fields", strengths, limitations };
}

export function guidanceSections(kind, row) {
  const guidance = row.guidance ?? profileGuidance(kind, row);
  return [{
    title: `Profile guidance · ${guidance.version}`,
    fields: [
      ...guidance.strengths.map(({ text, source }) => ["Strengths", text, source]),
      ...(!guidance.strengths.length ? [["Strengths", "Evidence unavailable for a reviewed strength in this release."]] : []),
      ...guidance.limitations.map(({ text, source }) => ["Limitations", text, source]),
    ],
  }];
}
