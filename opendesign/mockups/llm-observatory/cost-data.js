// Illustrative USD scenarios for the same small-model workload. These values
// are examples, not market quotes, measured runs, or a model-quality comparison.
export const COST_PROFILES = [
  {
    id: "rtx-3060", name: "1 × RTX 3060", gpuCount: 1, gpuName: "RTX 3060",
    gpuUnitUsd: 240, vramPerGpu: 12, cpuUsd: 160, ramUsd: 100,
    platformUsd: 320, storageUsd: 75, activeWatts: 205, idleWatts: 49, outputTps: 43,
  },
  {
    id: "rtx-3090", name: "1 × RTX 3090", gpuCount: 1, gpuName: "RTX 3090",
    gpuUnitUsd: 730, vramPerGpu: 24, cpuUsd: 215, ramUsd: 125,
    platformUsd: 420, storageUsd: 90, activeWatts: 390, idleWatts: 75, outputTps: 105,
  },
  {
    id: "dual-3090", name: "2 × RTX 3090", gpuCount: 2, gpuName: "RTX 3090",
    gpuUnitUsd: 730, vramPerGpu: 24, cpuUsd: 260, ramUsd: 230,
    platformUsd: 560, storageUsd: 110, activeWatts: 615, idleWatts: 108, outputTps: 155,
  },
  {
    id: "quad-3090", name: "4 × RTX 3090", gpuCount: 4, gpuName: "RTX 3090",
    gpuUnitUsd: 730, vramPerGpu: 24, cpuUsd: 375, ramUsd: 430,
    platformUsd: 1030, storageUsd: 150, activeWatts: 1050, idleWatts: 195, outputTps: 210,
  },
];

export const COST_DEFAULTS = {
  profileId: "rtx-3090", mode: "build", baseline: "api",
  monthlyOutputM: 18, inputPerOutput: 3, months: 36, onlineHours: 300,
  electricityUsdPerKwh: 0.17, coolingPct: 15, maintenanceUsd: 8,
  cloudInputUsdPerM: 0.6, cloudOutputUsdPerM: 2.4,
  rentalUsdPerHour: 0.55, rentalOutputTps: 130, rentalIdleHours: 0,
  annualDiscountPct: 8, resaleUsd: 0,
};

const HOURS_PER_MONTH = 730;
const TOKENS_PER_MILLION = 1e6;
const SECONDS_PER_HOUR = 3600;
const limits = (min, max, step) => ({ min, max, step });

export const COST_LIMITS = {
  monthlyOutputM: limits(0, 600, 1), inputPerOutput: limits(0, 100, 0.5),
  months: limits(1, 120, 1), onlineHours: limits(0, HOURS_PER_MONTH, 1),
  electricityUsdPerKwh: limits(0, 5, 0.01), coolingPct: limits(0, 300, 1),
  maintenanceUsd: limits(0, 10000, 1), cloudInputUsdPerM: limits(0, 1000, 0.01),
  cloudOutputUsdPerM: limits(0, 1000, 0.01), rentalUsdPerHour: limits(0, 1000, 0.01),
  rentalOutputTps: limits(1, 100000, 1), rentalIdleHours: limits(0, HOURS_PER_MONTH, 1),
  annualDiscountPct: limits(0, 100, 0.5), resaleUsd: limits(0, 100000, 1),
  gpuUnitUsd: limits(0, 100000, 1), cpuUsd: limits(0, 100000, 1),
  ramUsd: limits(0, 100000, 1), platformUsd: limits(0, 100000, 1), storageUsd: limits(0, 100000, 1),
  activeWatts: limits(0, 50000, 1), idleWatts: limits(0, 50000, 1), outputTps: limits(1, 100000, 1),
};

const profileFields = ["gpuUnitUsd", "cpuUsd", "ramUsd", "platformUsd", "storageUsd", "activeWatts", "idleWatts", "outputTps"];

function normalizeNumber(key, value, fallback) {
  const parsed = typeof value === "string" && value.trim() !== "" ? Number(value) : value;
  if (!Number.isFinite(parsed)) return fallback;
  const { min, max } = COST_LIMITS[key];
  return Math.min(max, Math.max(min, parsed));
}

function hardwareCosts(profile, mode) {
  const gpuUsd = profile.gpuCount * profile.gpuUnitUsd;
  const bom = [
    { id: "gpu", label: "Graphics cards", usd: gpuUsd, included: true },
    { id: "cpu", label: "CPU", usd: profile.cpuUsd },
    { id: "ram", label: "System memory", usd: profile.ramUsd },
    { id: "platform", label: "Board, case, PSU and cooling hardware", usd: profile.platformUsd },
    { id: "storage", label: "Storage", usd: profile.storageUsd },
  ].map((part) => ({ ...part, included: part.included || mode === "build" }));
  const vramGb = profile.gpuCount * profile.vramPerGpu;
  const hardware = {
    gpuUsd, vramGb, usdPerVramGb: gpuUsd / vramGb,
    fullBuildUsd: bom.reduce((sum, part) => sum + part.usd, 0),
    upfrontUsd: bom.reduce((sum, part) => sum + (part.included ? part.usd : 0), 0),
  };
  return { hardware, bom };
}

function hoursForOutput(outputM, outputTps) {
  return outputM * TOKENS_PER_MILLION / (outputTps * SECONDS_PER_HOUR);
}

function capacityFor(input, profile, outputM) {
  const rentalAvailableHours = HOURS_PER_MONTH - input.rentalIdleHours;
  const localActiveHours = hoursForOutput(outputM, profile.outputTps);
  const rentalActiveHours = hoursForOutput(outputM, input.rentalOutputTps);
  return {
    localActiveHours, rentalActiveHours,
    localMaxOutputM: input.onlineHours * profile.outputTps * SECONDS_PER_HOUR / TOKENS_PER_MILLION,
    rentalMaxOutputM: rentalAvailableHours * input.rentalOutputTps * SECONDS_PER_HOUR / TOKENS_PER_MILLION,
    localFeasible: localActiveHours <= input.onlineHours + 1e-9,
    rentalFeasible: rentalActiveHours <= rentalAvailableHours + 1e-9,
  };
}

function monthlyCosts(input, profile, outputM, capacity = capacityFor(input, profile, outputM)) {
  const activeHours = Math.min(capacity.localActiveHours, input.onlineHours);
  const activeKwh = activeHours * profile.activeWatts / 1000;
  const idleKwh = (input.onlineHours - activeHours) * profile.idleWatts / 1000;
  const itKwh = activeKwh + idleKwh;
  const coolingKwh = itKwh * input.coolingPct / 100;
  const itElectricityUsd = itKwh * input.electricityUsdPerKwh;
  const coolingUsd = coolingKwh * input.electricityUsdPerKwh;
  const inputM = outputM * input.inputPerOutput;
  const apiInputUsd = inputM * input.cloudInputUsdPerM;
  const apiOutputUsd = outputM * input.cloudOutputUsdPerM;
  const rentalBilledHours = Math.min(HOURS_PER_MONTH, capacity.rentalActiveHours + input.rentalIdleHours);
  return {
    outputM, inputM, activeKwh, idleKwh, coolingKwh, itElectricityUsd, coolingUsd,
    maintenanceUsd: input.maintenanceUsd,
    localUsd: capacity.localFeasible ? itElectricityUsd + coolingUsd + input.maintenanceUsd : null,
    apiInputUsd, apiOutputUsd, apiUsd: apiInputUsd + apiOutputUsd, rentalBilledHours,
    rentalUsd: capacity.rentalFeasible ? rentalBilledHours * input.rentalUsdPerHour : null,
  };
}

function horizonCosts(input, upfrontUsd, monthly) {
  const monthlyRate = (1 + input.annualDiscountPct / 100) ** (1 / 12) - 1;
  const terminalFactor = (1 + monthlyRate) ** -input.months;
  const annuityFactor = monthlyRate === 0 ? input.months : (1 - terminalFactor) / monthlyRate;
  const localUsd = monthly.localUsd === null ? null : upfrontUsd + input.months * monthly.localUsd - input.resaleUsd;
  const apiUsd = input.months * monthly.apiUsd;
  const rentalUsd = monthly.rentalUsd === null ? null : input.months * monthly.rentalUsd;
  const discountedLocalUsd = localUsd === null ? null : upfrontUsd + annuityFactor * monthly.localUsd - input.resaleUsd * terminalFactor;
  const discountedApiUsd = annuityFactor * monthly.apiUsd;
  const discountedRentalUsd = rentalUsd === null ? null : annuityFactor * monthly.rentalUsd;
  return {
    localUsd, apiUsd, rentalUsd, discountedLocalUsd, discountedApiUsd, discountedRentalUsd,
    npvVsApiUsd: discountedLocalUsd === null ? null : discountedApiUsd - discountedLocalUsd,
    npvVsRentalUsd: discountedLocalUsd === null || discountedRentalUsd === null ? null : discountedRentalUsd - discountedLocalUsd,
  };
}

function simplePayback(upfrontUsd, localUsd, alternativeUsd) {
  const monthlySavingsUsd = localUsd === null || alternativeUsd === null ? null : alternativeUsd - localUsd;
  const months = monthlySavingsUsd > 0 ? upfrontUsd / monthlySavingsUsd : null;
  return { months, monthlySavingsUsd };
}

// Costs are linear in volume while both options have enough active hours.
function volumeCrossover(input, profile, upfrontUsd, maxVolumeM, baseline) {
  if (maxVolumeM <= 0) return { volumeM: null, maxVolumeM, cheaperBelow: null, cheaperAbove: null };
  const key = baseline + "Usd";
  const noLoad = monthlyCosts(input, profile, 0);
  const fullLoad = monthlyCosts(input, profile, maxVolumeM);
  const initialDelta = upfrontUsd - input.resaleUsd + input.months * (noLoad.localUsd - noLoad[key]);
  const terminalDelta = upfrontUsd - input.resaleUsd + input.months * (fullLoad.localUsd - fullLoad[key]);
  const span = terminalDelta - initialDelta;
  const volumeM = span === 0 ? null : -initialDelta / span * maxVolumeM;
  const winner = (delta) => delta < 0 ? "local" : delta > 0 ? baseline : "tie";
  return {
    volumeM: volumeM !== null && volumeM >= 0 && volumeM <= maxVolumeM ? volumeM : null,
    maxVolumeM, cheaperBelow: winner(initialDelta), cheaperAbove: winner(terminalDelta),
  };
}

function sensitivityData(input, profile, upfrontUsd) {
  const scenarios = [
    { id: "monthlyOutputM", label: "Monthly output", unit: "M output tokens" },
    { id: "electricityUsdPerKwh", label: "Electricity tariff", unit: "USD/kWh" },
    { id: "coolingPct", label: "External cooling load", unit: "%" },
    { id: "cloudOutputUsdPerM", label: "API output price", unit: "USD/M output tokens" },
    { id: "rentalUsdPerHour", label: "Rental price", unit: "USD/hour" },
  ];
  return scenarios.map((scenario) => {
    const { id } = scenario;
    const low = normalizeNumber(id, input[id] * 0.5, input[id]);
    const high = normalizeNumber(id, input[id] * 1.5, input[id]);
    const [lowCosts, highCosts] = [low, high].map((value) => {
      const scenarioInput = { ...input, [id]: value };
      return horizonCosts(scenarioInput, upfrontUsd, monthlyCosts(scenarioInput, profile, scenarioInput.monthlyOutputM));
    });
    return {
      ...scenario, low, high,
      apiLowUsd: lowCosts.npvVsApiUsd, apiHighUsd: highCosts.npvVsApiUsd,
      rentalLowUsd: lowCosts.npvVsRentalUsd, rentalHighUsd: highCosts.npvVsRentalUsd,
    };
  });
}

export function calculateCost(options = {}) {
  const input = { ...COST_DEFAULTS };
  for (const key of Object.keys(COST_LIMITS)) {
    if (Object.hasOwn(COST_DEFAULTS, key)) input[key] = normalizeNumber(key, options[key], COST_DEFAULTS[key]);
  }
  input.months = Math.round(input.months);
  input.mode = options.mode === "reuse" ? "reuse" : "build";
  input.baseline = options.baseline === "rental" ? "rental" : "api";
  const preset = COST_PROFILES.find(({ id }) => id === options.profileId) ?? COST_PROFILES.find(({ id }) => id === input.profileId);
  input.profileId = preset.id;
  const profile = { ...preset };
  for (const key of profileFields) {
    profile[key] = normalizeNumber(key, options[key], preset[key]);
  }

  const { bom, hardware } = hardwareCosts(profile, input.mode);
  const { upfrontUsd } = hardware;
  const capacity = capacityFor(input, profile, input.monthlyOutputM);
  const monthly = monthlyCosts(input, profile, input.monthlyOutputM, capacity);
  const totals = horizonCosts(input, upfrontUsd, monthly);
  const volume = monthly.outputM;
  const unit = {
    localUsd: volume > 0 && totals.localUsd !== null ? totals.localUsd / (input.months * volume) : null,
    localRunningUsd: volume > 0 && monthly.localUsd !== null ? monthly.localUsd / volume : null,
    apiUsd: volume > 0 ? monthly.apiUsd / volume : null,
    rentalUsd: volume > 0 && monthly.rentalUsd !== null ? monthly.rentalUsd / volume : null,
  };
  const payback = {
    api: simplePayback(upfrontUsd, monthly.localUsd, monthly.apiUsd),
    rental: simplePayback(upfrontUsd, monthly.localUsd, monthly.rentalUsd),
  };
  const overlap = Math.min(capacity.localMaxOutputM, capacity.rentalMaxOutputM);
  const crossover = {
    api: volumeCrossover(input, profile, upfrontUsd, capacity.localMaxOutputM, "api"),
    rental: volumeCrossover(input, profile, upfrontUsd, overlap, "rental"),
  };
  const timeline = Array.from({ length: input.months + 1 }, (_, month) => ({
    month,
    localUsd: monthly.localUsd === null ? null : upfrontUsd + month * monthly.localUsd - (month === input.months ? input.resaleUsd : 0),
    apiUsd: month * monthly.apiUsd,
    rentalUsd: monthly.rentalUsd === null ? null : month * monthly.rentalUsd,
  }));
  const maxVolume = Math.max(1, volume * 1.1, capacity.localMaxOutputM * 1.08);
  const samples = Array.from({ length: 25 }, (_, index) => index * maxVolume / 24);
  samples.push(volume, capacity.localMaxOutputM);
  if (capacity.rentalMaxOutputM <= maxVolume) samples.push(capacity.rentalMaxOutputM);
  for (const alternative of Object.values(crossover)) {
    if (alternative.volumeM !== null) samples.push(alternative.volumeM);
  }
  const volumeCurve = [...new Set(samples)].sort((a, b) => a - b).map((volumeM) => {
    const costs = horizonCosts(input, upfrontUsd, monthlyCosts(input, profile, volumeM));
    return { volumeM, localUsd: costs.localUsd, apiUsd: costs.apiUsd, rentalUsd: costs.rentalUsd };
  });
  return { input, profile, bom, hardware, capacity, monthly, unit, totals, payback, crossover, timeline, volumeCurve, sensitivity: sensitivityData(input, profile, upfrontUsd) };
}
